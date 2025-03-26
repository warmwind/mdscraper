#!/usr/bin/env python
# -*- coding: utf-8 -*-

import requests
from bs4 import BeautifulSoup
import re
import html
import sys
import os
import argparse
from markdownify import markdownify as md

def clean_text(text):
    if not text:
        return ""
    # Replace multiple spaces with a single space
    text = re.sub(r'\s+', ' ', text)
    # Decode HTML entities
    text = html.unescape(text)
    # Remove leading/trailing whitespace
    return text.strip()

def fetch_and_convert_to_markdown(url, debug=False, ignore_images=False):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise an exception for HTTP errors
        response.encoding = 'utf-8'  # Ensure correct encoding
    except requests.exceptions.RequestException as e:
        print(f"Error fetching URL: {e}")
        return None, None
    
    soup = BeautifulSoup(response.text, 'html.parser')
    
    if debug:
        # Print all div classes to help identify the content container
        print("Available div classes:")
        for div in soup.find_all('div'):
            div_classes = div.get('class')
            if div_classes:
                print(f"- {div_classes}")
    
    # Extract the title
    title_element = soup.find('h1') or soup.find('title')
    title = clean_text(title_element.text) if title_element else "Webpage"
    
    # Find the main content container - try different common content container classes
    content = None
    possible_content_classes = [
        'article_content', 
        'content',
        'article-content',
        'article',
        'main-content',
        'main',
        'post-content',
        'entry-content',
        'blog-content',
        'body-content'
    ]
    
    for class_name in possible_content_classes:
        content = soup.find('div', class_=class_name)
        if content:
            if debug:
                print(f"Found content container with class: {class_name}")
            break
    
    # If no content container found by class, try to find it by article tag
    if not content:
        content = soup.find('article')
        if content and debug:
            print("Found content in <article> tag")
    
    # Last resort: look for the largest div that might contain the content
    if not content:
        divs = soup.find_all('div')
        if divs:
            # Sort divs by the length of their text content
            divs_sorted = sorted(divs, key=lambda x: len(x.get_text()), reverse=True)
            content = divs_sorted[0]  # Take the div with the most text
            if debug:
                print("Using largest div as content container")
    
    if not content:
        print("Could not find the main content container.")
        if debug:
            # Save the HTML for inspection
            with open('debug_html.html', 'w', encoding='utf-8') as f:
                f.write(response.text)
            print("Saved HTML to debug_html.html for inspection")
        return None, None
    
    # If ignore_images is True, remove all img tags before conversion
    if ignore_images and hasattr(content, 'find_all'):
        for img in content.find_all('img'):
            if hasattr(img, 'decompose'):
                img.decompose()
        if debug:
            print("All images have been removed from the content")
    
    # Convert the content to markdown using markdownify
    markdown_content = md(str(content), heading_style="ATX")
    
    # Add the title at the beginning
    markdown = f"# {title}\n\n{markdown_content}"
    
    # Clean up any multiple consecutive newlines
    markdown = re.sub(r'\n{3,}', '\n\n', markdown)
    
    return markdown, title

def sanitize_filename(filename):
    # Replace invalid filename characters with underscores
    return re.sub(r'[\\/*?:"<>|]', '_', filename)

def process_url_file(url_file, output_dir="outs", debug=False, ignore_images=False):
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    success_count = 0
    failure_count = 0
    
    with open(url_file, 'r', encoding='utf-8') as f:
        urls = [line.strip() for line in f if line.strip()]
    
    total_urls = len(urls)
    print(f"Found {total_urls} URLs to process")
    
    for i, url in enumerate(urls, 1):
        print(f"\nProcessing URL {i}/{total_urls}: {url}")
        
        markdown, title = fetch_and_convert_to_markdown(url, debug=debug, ignore_images=ignore_images)
        if markdown and title:
            # Create a sanitized filename from the title
            filename = sanitize_filename(title)
            output_file = os.path.join(output_dir, f"{filename}.md")
            
            # If file exists, add a number suffix
            counter = 1
            while os.path.exists(output_file):
                output_file = os.path.join(output_dir, f"{filename}_{counter}.md")
                counter += 1
            
            # Save to file
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(markdown)
            
            file_size = os.path.getsize(output_file) / 1024  # size in KB
            print(f"Successfully saved to {output_file} ({file_size:.2f} KB)")
            success_count += 1
        else:
            print(f"Failed to parse the webpage at {url}")
            failure_count += 1
    
    print(f"\nSummary: Processed {total_urls} URLs")
    print(f"Success: {success_count}, Failed: {failure_count}")
    print(f"Markdown files saved to the '{output_dir}' directory")

def main():
    parser = argparse.ArgumentParser(description='Fetch webpages and convert them to Markdown format.')
    
    # Create a mutually exclusive group for single URL vs file input
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument('--url', help='URL of a single webpage to fetch and convert')
    input_group.add_argument('--file', help='Text file containing URLs (one per line) to fetch and convert')
    
    parser.add_argument('--output', default='output.md',
                        help='Output Markdown file name (only used with --url)')
    parser.add_argument('--outdir', default='outs',
                        help='Output directory for markdown files (used with --file)')
    parser.add_argument('--debug', '-d', action='store_true',
                        help='Enable debug mode for more information')
    parser.add_argument('--no-images', action='store_true',
                        help='Ignore all images in the content')
    
    args = parser.parse_args()
    
    if args.url:
        # Process a single URL
        print(f"Fetching and parsing {args.url}...")
        markdown, title = fetch_and_convert_to_markdown(args.url, debug=args.debug, ignore_images=args.no_images)
        if markdown:
            # Save to file
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(markdown)
            print(f"Successfully parsed {args.url} and saved to {args.output}")
            
            # Print file stats
            file_size = os.path.getsize(args.output) / 1024  # size in KB
            print(f"File size: {file_size:.2f} KB")
            
            # Also print to console a preview
            preview_length = min(300, len(markdown))
            print("\n--- Markdown Content Preview ---\n")
            print(markdown[:preview_length] + ("..." if preview_length < len(markdown) else ""))
            print("\n--- End of Preview ---")
        else:
            print(f"Failed to parse the webpage at {args.url}.")
            print("Make sure the URL is correct and the website is accessible.")
            print("Use --debug flag for more information.")
    
    elif args.file:
        # Process multiple URLs from a file
        process_url_file(args.file, output_dir=args.outdir, debug=args.debug, ignore_images=args.no_images)

if __name__ == "__main__":
    main() 