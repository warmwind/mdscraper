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

def fetch_and_convert_to_markdown(url, debug=False):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise an exception for HTTP errors
        response.encoding = 'utf-8'  # Ensure correct encoding
    except requests.exceptions.RequestException as e:
        print(f"Error fetching URL: {e}")
        return None
    
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
        return None
    
    # Convert the content to markdown using markdownify
    markdown_content = md(str(content), heading_style="ATX")
    
    # Add the title at the beginning
    markdown = f"# {title}\n\n{markdown_content}"
    
    # Clean up any multiple consecutive newlines
    markdown = re.sub(r'\n{3,}', '\n\n', markdown)
    
    return markdown

def main():
    parser = argparse.ArgumentParser(description='Fetch any webpage and convert it to Markdown format.')
    parser.add_argument('url', nargs='?', default='https://example.com',
                        help='URL of the webpage to fetch and convert')
    parser.add_argument('output', nargs='?', default='output.md',
                        help='Output Markdown file name')
    parser.add_argument('--debug', '-d', action='store_true',
                        help='Enable debug mode for more information')
    
    args = parser.parse_args()
    
    print(f"Fetching and parsing {args.url}...")
    
    markdown = fetch_and_convert_to_markdown(args.url, debug=args.debug)
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

if __name__ == "__main__":
    main() 