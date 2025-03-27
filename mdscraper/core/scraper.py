#!/usr/bin/env python
# -*- coding: utf-8 -*-

import requests
from bs4 import BeautifulSoup
import re
from markdownify import markdownify as md
import os
from mdscraper.core.utils import clean_text, sanitize_filename, save_markdown_to_file
from bs4.element import Tag, NavigableString

def fetch_and_convert_to_markdown(url, debug=False, ignore_images=False, ignore_links=False, extra_heading_space=None):
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
            # Only Tag elements have the get method, not NavigableString
            if isinstance(div, Tag):
                div_classes = div.get('class')
                if div_classes:
                    print(f"- {div_classes}")
    
    # Extract the title
    title_element = soup.find('h1') or soup.find('title')
    title = clean_text(title_element.text) if title_element else "Webpage"
    
    # Find the main content container - try different common content container classes
    content = find_content_container(soup, debug)
    
    if not content:
        print("Could not find the main content container.")
        if debug:
            # Save the HTML for inspection
            with open('debug_html.html', 'w', encoding='utf-8') as f:
                f.write(response.text)
            print("Saved HTML to debug_html.html for inspection")
        return None, None
    
    # If ignore_images is True, remove all img tags before conversion
    if ignore_images and isinstance(content, Tag):
        for img in content.find_all('img'):
            if isinstance(img, Tag):
                img.decompose()
        
        # Also remove empty paragraph tags that might have contained only images
        for p in content.find_all('p'):
            if isinstance(p, Tag) and not p.get_text(strip=True):
                p.decompose()
                
        if debug:
            print("All images and empty paragraphs have been removed from the content")
    
    # If ignore_links is True, remove all a tags (links) or replace them with their text content
    if ignore_links and isinstance(content, Tag):
        for a in content.find_all('a'):
            if isinstance(a, Tag):
                # Replace the link with its text content
                text_content = a.get_text()
                new_tag = soup.new_string(text_content)
                a.replace_with(new_tag)
        if debug:
            print("All links have been removed from the content")
    
    # Convert the content to markdown using markdownify
    markdown_content = md(str(content), heading_style="ATX")
    
    # Add the title at the beginning
    markdown = f"# {title}\n\n{markdown_content}"
    
    # Clean up consecutive newlines
    # Always clean up more than 2 consecutive newlines regardless of heading space setting
    markdown = re.sub(r'\n{3,}', '\n\n', markdown)
    
    # Remove empty paragraphs (lines that only contain whitespace)
    markdown = re.sub(r'\n\s*\n\s*\n', '\n\n', markdown)
    
    # Add additional newlines before markdown headings if enabled
    if extra_heading_space:
        markdown = add_newlines_before_headings(markdown, extra_heading_space, debug=debug)
    
    return markdown, title

def add_newlines_before_headings(markdown, heading_levels='all', debug=False):
    """
    Add additional newlines before markdown heading tags
    
    Args:
        markdown (str): The markdown text to process
        heading_levels (str): Comma-separated list of heading levels (1-6) or 'all'
        debug (bool): Whether to print debug information
    
    Returns:
        str: The markdown text with additional newlines before headings
    """
    # Parse heading levels
    if heading_levels == 'all':
        levels = list(range(1, 7))
    else:
        try:
            levels = [int(level.strip()) for level in heading_levels.split(',') if level.strip()]
            levels = [level for level in levels if 1 <= level <= 6]
        except ValueError:
            levels = list(range(1, 7))
    
    if not levels:
        return markdown
    
    if debug:
        print(f"Debug: Adding extra newlines before heading levels: {levels}")
    
    # Process lines
    lines = markdown.split('\n')
    result = []
    
    for i, line in enumerate(lines):
        # Check if the line is a heading of interest
        for level in levels:
            if line.startswith('#' * level + ' '):
                if debug:
                    print(f"Debug: Found h{level} tag: {line[:30]}...")
                # Add three empty lines before heading (if not first line)
                if i > 0:
                    result.extend(['', '', ''])
                break
        
        # Add the current line
        result.append(line)
    
    return '\n'.join(result)

def find_content_container(soup, debug=False):
    content = None
    
    # Find the main content container - try different common content container classes
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
                
    return content

def process_url_file(url_file, output_dir="outs", debug=False, ignore_images=False, ignore_links=False, extra_heading_space=None):
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
        
        markdown, title = fetch_and_convert_to_markdown(url, debug=debug, ignore_images=ignore_images, 
                                                       ignore_links=ignore_links, 
                                                       extra_heading_space=extra_heading_space)
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
            file_size = save_markdown_to_file(markdown, output_file)
            print(f"Successfully saved to {output_file} ({file_size:.2f} KB)")
            success_count += 1
        else:
            print(f"Failed to parse the webpage at {url}")
            failure_count += 1
    
    print(f"\nSummary: Processed {total_urls} URLs")
    print(f"Success: {success_count}, Failed: {failure_count}")
    print(f"Markdown files saved to the '{output_dir}' directory")

def process_single_url(url, output_file, debug=False, ignore_images=False, ignore_links=False, extra_heading_space=None):
    print(f"Fetching and parsing {url}...")
    markdown, title = fetch_and_convert_to_markdown(url, debug=debug, ignore_images=ignore_images, 
                                                  ignore_links=ignore_links, 
                                                  extra_heading_space=extra_heading_space)
    
    if markdown:
        # Save to file
        file_size = save_markdown_to_file(markdown, output_file)
        print(f"Successfully parsed {url} and saved to {output_file}")
        print(f"File size: {file_size:.2f} KB")
        
        # Print preview to console
        preview_length = min(300, len(markdown))
        print("\n--- Markdown Content Preview ---\n")
        print(markdown[:preview_length] + ("..." if preview_length < len(markdown) else ""))
        print("\n--- End of Preview ---")
        return True
    else:
        print(f"Failed to parse the webpage at {url}.")
        print("Make sure the URL is correct and the website is accessible.")
        print("Use --debug flag for more information.")
        return False 