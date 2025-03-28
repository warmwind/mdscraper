#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Command-line interface for MDScraper
"""

import argparse
from mdscraper.core.scraper import scraper_cli

def main():
    parser = argparse.ArgumentParser(description='Fetch webpages and convert them to Markdown format.')

    # Create a mutually exclusive group for single URL vs file input
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument('--url', help='URL of a single webpage to fetch and convert')
    input_group.add_argument('--file', help='Text file containing URLs (one per line) to fetch and convert')
    input_group.add_argument('--site', help='A URL of a page to scrape for URLS to download a site')

    parser.add_argument('--output', default='$TITLE',
                        help=('Output Markdown file name. Default (%%TITLE) will generate a filename based on '
                              'the Webpage Title. If you prefer to use the URL set this to %%URL. Otherwise, use '
                              'to set as the desired filename'))
    parser.add_argument('--outdir', default='',
                        help='Output directory for markdown files, used with --file, --site, or with generated --output')
    parser.add_argument('--root-url', '-r',
                        help='The URL of the desired root path to generate relatives links for downloaded pages.')
    parser.add_argument('--content', '-c', nargs='*',
                        help='Additional list of div id or classes to use as the main content')
    parser.add_argument('--no-images', '-i', action='store_true',
                        help='Ignore all images in the content')
    parser.add_argument('--no-links', action='store_true',
                        help='Ignore all links in the content')
    parser.add_argument('--prepend-source-link', action='store_true',
                        help='Prepend source link in markdown file')
    parser.add_argument('--exclude-pages', '-p', nargs='*',
                        help='Space separated list of page names to ignore, can unix filename pattern matching.')
    parser.add_argument('--exclude-selectors', '-s', nargs='*',
                        help='Space separated list of CSS selectors to exclude')
    parser.add_argument('--extra-heading-space', metavar='LEVELS', type=str, default=None,
                        help='Add additional newlines before specified heading levels (e.g., "1,2,3" for h1,h2,h3 or "all" for all headings)')
    parser.add_argument('--settings',
                        help='All the options can be passed in as a yaml or json file. CLI options will take precedence')
    parser.add_argument('--save-settings', action='store_true',
                        help='Save the settings as a yaml file, and skip running. Filename will be mdscrapper_{YYYmmdd_HHMM}.yaml')
    parser.add_argument('--debug', '-d', action='store_true',
                        help='Enable debug mode for more information')
    parser.add_argument('--verbose', '-v', action='count', default=0,
                        help='Display runtime information. Use more than once to increase the verbosity level. Default level is 0')

    args = parser.parse_args()
    scraper_cli(**vars(args))

if __name__ == "__main__":
    main()
