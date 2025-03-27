#!/usr/bin/env python
# -*- coding: utf-8 -*-
# pylint: disable=line-too-long
# pylint: disable=too-few-public-methods
# pylint: disable=import-error
# pylint: disable=wildcard-import

"""Tools and CLI handler for fetching webpages and converting them to markdown files"""

import os
import re
import pprint
import fnmatch
from collections.abc import Mapping

import requests
from bs4 import BeautifulSoup
from bs4.element import Tag

from markdownify import markdownify as md
from markdownify import _todict
from utils import *

class MdScraper():
    """A set of tools for fetching webpages and converting them to markdown files"""
    class DefaultOptions:
        """A class to provide a robust method of setting options"""
        debug = False
        verbose = 0
        no_images = False
        no_links = False
        outdir = ''
        output = '%TITLE'
        requests_timeout = 60
        user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        root_url = ''
        exclude_pages = None
        exclude_selectors = None

        # Used to find the main content container by div class or id names
        custom_content_names = None
        default_content_names = [
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

    class Options(DefaultOptions):
        """Class to manage options"""

    def __init__(self, **options):
        # Create an options dictionary. Use DefaultOptions as a base so that
        # the options dictionary doesn't have to be extended.
        self.options = _todict(self.DefaultOptions)
        self.options.update(_todict(self.Options))
        self.set_options(options)

    def set_options(self, options):
        self.options.update(options)
        self.post_options_update()

    def post_options_update(self):
        """Actions taken after updating options"""
        if self.options['debug']:
            print("Options:")
            if self.options['verbose'] == 0:
                self.options['verbose'] = 9
            pprint.pprint(self.options)

    def process_config_file(self, file_path):
        """Loads options from of a config file as"""
        config_file_options = load_config_file(file_path)
        if isinstance(config_file_options, Mapping):
            # Only use config file options if the current options are set to the default value
            default_options = _todict(self.DefaultOptions)
            for key in config_file_options:
                if self.options[key] == default_options[key]:
                    self.options[key] = config_file_options[key]
            self.post_options_update()
        else:
            print('Config file content must be a dictionary')

    def save_settings(self):
        output_dir = self.options['outdir']
        filename = generate_filename('mdscrapper', 'yaml')
        filepath = os.path.join(output_dir, filename)
        create_config_file(self.options, filepath)

    def get_relative_url_path(self, url):
        """Returns the relative path to the root path if it exists"""
        if self.options['root_url']:
            root_url = self.options['root_url']
            paresd_root = urlparse(root_url)
            root_path = paresd_root.path

            parsed_url = urlparse(url)
            url_path = parsed_url.path
            # page_name = url_path.split("/")[-1]
            # url_dir = url_path[:-len(page_name)]

            new_url = url_path.replace(root_path, '')
            if self.options['debug']:
                print(f'new_url ({new_url}) = url_path ({url_path}) - root_path({root_path})')

            if new_url != url_path:
                return new_url

        return url

    def fetch_page(self, url):
        """Captures a page as a BeautifulSoup object"""
        headers = {'User-Agent': self.options['user_agent']}

        try:
            response = requests.get(url, headers=headers, timeout=self.options['requests_timeout'])
            response.raise_for_status()  # Raise an exception for HTTP errors
            response.encoding = 'utf-8'  # Ensure correct encoding
        except requests.exceptions.RequestException as err:
            print(f"Error fetching URL: {err}")
            return None

        return BeautifulSoup(response.text, 'html.parser')

    def add_newlines_before_headings(self, markdown):
        """
        Add additional newlines before markdown heading tags
        
        Args:
            markdown (str): The markdown text to process
        
        Returns:
            str: The markdown text with additional newlines before headings
        """
        # Parse heading levels
        heading_levels = self.options['extra_heading_space']
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
        
        if self.options['debug']:
            print(f"Debug: Adding extra newlines before heading levels: {levels}")
        
        # Process lines
        lines = markdown.split('\n')
        result = []
        
        for i, line in enumerate(lines):
            # Check if the line is a heading of interest
            for level in levels:
                if line.startswith('#' * level + ' '):
                    if self.options['debug']:
                        print(f"Debug: Found h{level} tag: {line[:30]}...")
                    # Add three empty lines before heading (if not first line)
                    if i > 0:
                        result.extend(['', '', ''])
                    break
            
            # Add the current line
            result.append(line)
        
        return '\n'.join(result)

    def html_to_markdown(self, html_str, title=None):
        """Converts html string to markdown with optional new title"""

        # Convert the content to markdown using markdownify
        markdown_content = md(html_str, heading_style="ATX")

        if title:
            # Add the title at the beginning if it doesn't already exist
            title_str = f"# {title}\n\n"
            if markdown_content.startswith(title_str):
                markdown = markdown_content
            else:
                markdown = title_str + markdown_content

        # Clean up any multiple consecutive newlines
        markdown = re.sub(r'\n{3,}', '\n\n', markdown)

        # Add additional newlines before markdown headings if enabled
        if self.options['extra_heading_space']:
            markdown = self.add_newlines_before_headings(markdown)
        else: # Skip cleaning up consecutive newlines when using extra_heading_space
            # Clean up any multiple consecutive newlines
            markdown = re.sub(r'\n{3,}', '\n\n', markdown)
        return markdown

    def extract_page_title(self, soup):
        """Extract the title from BeautifulSoup object"""

        title_element = soup.find('h1') or soup.find('title')
        title = clean_text(title_element.text) if title_element else "Webpage"

        if self.options['debug']:
            if title:
                print(f'Extracted title as: {title}')
            else:
                print('Could not extract the title')

        return title

    def extract_page_content(self, soup):
        """Finds and extracts main webpage content with the option of ignoring images"""

        content = self.find_content_container(soup)

        if not content:
            print("Could not find the main content container.")
            if self.options['debug']:
                # Save the HTML for inspection
                with open('debug_html.html', 'w', encoding='utf-8') as html_file:
                    html_file.write(str(soup))
                print("Saved HTML to debug_html.html for inspection")
            return None

        # If no_images is True, remove all img tags before conversion
        if self.options['no_images'] and isinstance(content, Tag):
            for img in content.find_all('img'):
                if isinstance(img, Tag):
                    img.decompose()

            if self.options['debug']:
                print("All images have been removed from the content")

        return content

    def fetch_and_convert_to_markdown(self, url):
        """Fetches and converts a single webpage to a markdown file by extracting only the main content"""
        soup = self.fetch_page(url)
        content = self.extract_page_content(soup)
        if not content:
            return None, None

        self.process_exclude_selectors(content)
        self.remove_links(content)
        self.make_urls_relative(content)

        title = self.extract_page_title(soup)
        return self.html_to_markdown(str(content), title), title

    def remove_links(self, content):
        # If ignore_links is True, remove all a tags (links) or replace them with their text content
        if self.options['no_links'] and isinstance(content, Tag):
            for anchor in content.find_all('a'):
                if isinstance(anchor, Tag):
                    # Replace the link with its text content
                    anchor_text = anchor.get_text()
                    new_tag = BeautifulSoup.new_string(anchor_text)
                    anchor.replace_with(new_tag)
            if self.options['debug']:
                print("All links have been removed from the content")

    def process_exclude_selectors(self, content):
        if self.options['exclude_selectors']:
            for selector in self.options['exclude_selectors']:
                to_exclude = content.select(selector)
                if to_exclude:
                    for element in to_exclude:
                        element.decompose()

    def make_urls_relative(self, content):
        """Use root_url to fix all relevant URLs to relative links"""
        if self.options['root_url'] and isinstance(content, Tag):
            for anchor in content.find_all('a'):
                if isinstance(anchor, Tag):
                    # Replace the link with relative link
                    url = anchor['href']
                    anchor['href'] = self.get_relative_url_path(url)

    def find_content_by_div_attr(self, soup, attr, filter_list):
        """Searches a BeautifulSoup object for div with either a class or id in the filter_list"""
        content = None
        for content_name in filter_list:
            if attr == 'class':
                content = soup.find('div', class_=content_name)
            elif attr == 'id':
                content = soup.find('div', id_=content_name)
                for div in soup.find_all('div'):
                    # Only Tag elements have the get method, not NavigableString
                    if isinstance(div, Tag):
                        div_id = div.get('id')
                        if div_id == content_name:
                            content = div
                            break
            else:
                raise NameError(f"unknown div attr {attr}")

            if content:
                if self.options['debug']:
                    print(f"Found content container with {attr}: {content_name}")
                break
        return content

    def find_content_container(self, soup):
        """Attempts to intelligently detect and extract main webpage content"""
        if soup:
            content = None

            if self.options['debug']:
                # Print all div classes to help identify the content container
                print("Available div attributes:")
                class_list, id_list = get_div_attrs(soup)
                print(f"- id: {id_list}")
                print(f"- class: {class_list}")

            if self.options['content']:
                custom_content_names = self.options['content']
                content = self.find_content_by_div_attr(soup, 'id', custom_content_names)

                # If no content container found by id, try to find it by class
                if not content:
                    content = self.find_content_by_div_attr(soup, 'class', custom_content_names)

            # If no content container found by custom container name, try to find it by static name list
            if not content:
                content = self.find_content_by_div_attr(soup, 'id', self.options['default_content_names'])

            # If no content container found by id, try to find it by class
            if not content:
                content = self.find_content_by_div_attr(soup, 'class', self.options['default_content_names'])

            # If no content container found by class, try to find it by article tag
            if not content:
                content = soup.find('article')
                if content and self.options['debug']:
                    print("Found content in <article> tag")

            # Last resort: look for the largest div that might contain the content
            if not content:
                divs = soup.find_all('div')
                if divs:
                    # Sort divs by the length of their text content
                    divs_sorted = sorted(divs, key=lambda x: len(x.get_text()), reverse=True)
                    content = divs_sorted[0]  # Take the div with the most text
                    if self.options['debug']:
                        print("Using largest div as content container")

            return content

        if self.options['debug']:
            print('No Soup!')
        return None

    def content_to_url_list(self, content, site_root):
        """Converts a BeautifulSoup object into a list of full urls"""
        anchor_list = content.find_all('a')
        url_list = []
        for anchor in anchor_list:
            url = anchor['href']
            parsed_url = urlparse(url)
            url_path = parsed_url.path

            # Get the page name as the last part of the path
            page_name = url_path.split("/")[-1]

            # Skip any excluded urls
            exclude_pages = self.options['exclude_pages']
            if exclude_pages:
                if any(fnmatch.fnmatch(page_name, text) for text in exclude_pages):
                    if self.options['debug']:
                        print('Ignoring webpage: {page_name}')
                else:
                    full_url = site_root + url_path
                    url_list.append(full_url)

        if self.options['debug']:
            print('Url list:')
            pprint.pprint(url_list)

        return url_list

    def process_url_list(self, url_list, output_dir=None):
        """Downloads and converts a list of URLs to markdown"""

        if output_dir:
            self.options['outdir'] = output_dir
        else:
            output_dir = self.options['outdir']

        success_count = 0
        failure_count = 0

        total_urls = len(url_list)

        if self.options['verbose'] > 0:
            print(f"Found {total_urls} URLs to process")

        for i, url in enumerate(url_list, 1):
            if self.options['verbose'] > 0:
                print(f"\nProcessing URL {i}/{total_urls}:")

            if self.process_single_url(url):
                success_count += 1
            else:
                failure_count += 1

        if self.options['verbose'] > 0:
            print(f"\nSummary: Processed {total_urls} URLs")
            print(f"Success: {success_count}, Failed: {failure_count}")
            print(f"Markdown files saved to the '{output_dir}' directory")

    def process_url_file(self, url_file_path, output_dir=None):
        """Downloads and converts a list of URLs from a file of URLs"""
        with open(url_file_path, 'r', encoding='utf-8') as url_file:
            url_list = [line.strip() for line in url_file if line.strip()]

        self.process_url_list(url_list, output_dir)

    def process_site_url(self, site_url, output_dir=None):
        """Downloads and converts a list of URLs from a webpage"""
        soup = self.fetch_page(site_url)
        content = self.extract_page_content(soup)

        parsed_url = urlparse(site_url)
        site_root =  f'{parsed_url.scheme}://{parsed_url.hostname}'
        url_list = self.content_to_url_list(content, site_root)
        self.process_url_list(url_list, output_dir)

    def process_single_url(self, url, output_file=None):
        """Downloads and converts a single webpage to a markdown file"""
        output_dir = self.options['outdir']

        if not output_file:
            output_file = self.options['output']

        if self.options['verbose'] > 0:
            print(f"Fetching and parsing {url}...")

        markdown, title = self.fetch_and_convert_to_markdown(url)
        if markdown and title:
            if output_file == '%TITLE':
                # Create a sanitized filename from the title
                filename = sanitize_filename(title)
                output_file = os.path.join(output_dir, f"{filename}.md")
                if self.options['debug']:
                    print(f'Generated filename "{output_file}" from title "{title}"')

            elif output_file == '%URL':
                # Create a sanitized filename from the URL
                last_url_part = get_last_url_part(url)
                filename = sanitize_filename(last_url_part)
                output_file = os.path.join(output_dir, f"{filename}.md")
                if self.options['debug']:
                    print(f'Generated filename "{output_file}" from url "{url}"')
            
            else:
                output_file = os.path.join(output_dir, self.options['output'])

            # If needed, create output directory if it doesn't exist
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)

            # Save to file
            save_markdown_to_file(markdown, output_file)

            if self.options['verbose'] > 0:
                file_size = get_size_kb(output_file)
                print(f"Successfully saved to {output_file} ({file_size:.2f} KB)")

            if self.options['verbose'] > 1:
                # Print preview to console
                preview_length = min(300, len(markdown))
                print("\n--- Markdown Content Preview ---\n")
                print(markdown[:preview_length] + ("..." if preview_length < len(markdown) else ""))
                print("\n--- End of Preview ---")

            return True

        if self.options['verbose'] > 0:
            print(f"Failed to parse the webpage at {url}.")

        if not self.options['debug']:
            print("Make sure the URL is correct and the website is accessible.")
            print("Use --debug flag for more information.")
        return False


def scraper_cli(**options):
    """The CLI handler for MdScraper class"""
    url = options.pop('url')
    url_file = options.pop('file')
    site_url = options.pop('site')
    settings_file = options.pop('settings')
    save_settings = options.pop('save_settings')
    
    ms = MdScraper(**options)
    
    if settings_file:
        ms.process_config_file(settings_file)

    if save_settings:
        ms.save_settings()
    else:
        if url:
            ms.process_single_url(url)
        elif url_file:
            ms.process_url_file(url_file)
        elif site_url:
            ms.process_site_url(site_url)
