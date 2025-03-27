#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import sys
from scraper import process_single_url, process_url_file

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
    parser.add_argument('--no-links', action='store_true',
                        help='Ignore all links in the content')
    
    args = parser.parse_args()
    
    if args.url:
        # Process a single URL
        process_single_url(args.url, args.output, debug=args.debug, ignore_images=args.no_images, ignore_links=args.no_links)
    elif args.file:
        # Process multiple URLs from a file
        process_url_file(args.file, output_dir=args.outdir, debug=args.debug, ignore_images=args.no_images, ignore_links=args.no_links)

if __name__ == "__main__":
    main() 