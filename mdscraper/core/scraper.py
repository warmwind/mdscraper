#!/usr/bin/env python
# -*- coding: utf-8 -*-
# pylint: disable=line-too-long
# pylint: disable=too-few-public-methods
# pylint: disable=import-error
# pylint: disable=wildcard-import
# pylint: disable=too-many-public-methods

"""Tools and CLI handler for fetching webpages and converting them to markdown files"""

import os
import re
import pprint
import fnmatch
from collections.abc import Mapping
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from bs4.element import Tag

from markdownify import markdownify as md
from markdownify import _todict

from mdscraper.core.utils import (load_config_file,
                                 generate_filename,
                                 create_config_file,
                                 get_div_attrs,
                                 sanitize_filename,
                                 save_markdown_to_file,
                                 get_last_url_part,
                                 get_size_kb,
                                 clean_text)

class MdScraper():
    """
    MdScraper: A class for scraping webpages and converting them into Markdown files.
    This class provides a comprehensive set of tools for fetching webpages, extracting
    content, and converting it into Markdown format. It includes options for customization,
    such as excluding specific elements, removing images or links, and adding extra
    formatting to the Markdown output.

    Classes:
        - DefaultOptions: A nested class that defines the default configuration options.
        - Options: A nested class that extends DefaultOptions for managing options.

    Methods:
        - __init__(**options): Initializes the scraper with default and user-provided options.
        - set_options(options): Updates the scraper's options and triggers post-update actions.
        - post_options_update(): Executes actions after updating options, such as debugging output.
        - process_config_file(file_path): Loads options from a configuration file.
        - get_default_options(): Returns the default options as a dictionary.
        - save_settings(): Saves the current settings to a configuration file.
        - get_relative_url_path(url): Converts a URL to a relative path based on the root URL.
        - fetch_webpage(url): Fetches a webpage and returns it as a BeautifulSoup object.
        - add_newlines_before_headings(markdown): Adds extra newlines before Markdown headings.
        - html_to_markdown(html_str, title=None, source_url=None): Converts HTML content to Markdown.
        - extract_page_title(soup): Extracts the title from a BeautifulSoup object.
        - extract_page_content(soup): Extracts the main content from a webpage.
        - fetch_content(url): Fetches content from a URL and returns it as Markdown.
        - _fetch_content(url): Internal method to fetch and process content from a URL.
        - convert_to_markdown(content, title=None, source_url=None): Converts HTML content to Markdown.
        - remove_images(content): Removes all images from the content if the no_images option is enabled.
        - remove_links(content): Removes or replaces links in the content if the no_links option is enabled.
        - process_exclude_selectors(content): Removes elements matching exclude selectors from the content.
        - make_urls_relative(content): Converts absolute URLs to relative URLs based on the root URL.
        - find_content_by_div_attr(soup, attr, filter_list): Finds content by div attributes (class or id).
        - find_content_container(soup): Attempts to detect and extract the main content container.
        - content_to_url_list(content, site_root): Extracts a list of URLs from the content.
        - process_url_list(url_list, output_dir=None): Processes a list of URLs and converts them to Markdown.
        - process_url_file(url_file_path, output_dir=None): Processes URLs from a file and converts them to Markdown.
        - process_site_url(site_url, output_dir=None): Processes URLs from a webpage and converts them to Markdown.
        - process_single_url(url, output_file=None): Processes a single URL and saves it as a Markdown file.
        - extract_md_title(markdown): Extracts the title from a Markdown string.

    Attributes:
        - options: A dictionary containing the current configuration options.

    Usage:
        scraper = MdScraper(debug=True, verbose=2)
        scraper.process_single_url("https://example.com", output_file="example.md")
    """

    class DefaultOptions:
        """
        DefaultOptions is a configuration class that provides a robust method for setting
        default options for a web scraper. It includes various attributes to control the
        scraper's behavior, such as debugging, verbosity, output settings, and content
        extraction preferences.
        """
        debug = False
        verbose = 0
        no_images = False
        no_links = False
        extra_heading_space = None
        prepend_source_link = False
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
        """
        A class to manage configuration options for the scraper.

        Inherits:
            DefaultOptions: The base class providing default option handling.
        """

    def __init__(self, **options):
        # Create an options dictionary. Use DefaultOptions as a base so that
        # the options dictionary doesn't have to be extended.
        self.options = _todict(self.DefaultOptions)
        self.options.update(_todict(self.Options))
        self.set_options(options)

    def set_options(self, options):
        """
        Updates the scraper's options with the provided dictionary and performs
        any necessary post-update actions.

        Args:
            options (dict): A dictionary containing the options to update. The keys
                            and values in this dictionary will overwrite or add to
                            the existing options.
        """
        self.options.update(options)
        self.post_options_update()

    def post_options_update(self):
        """
        Perform actions after updating the options.

        This method checks the current state of the `options` dictionary and performs
        specific actions based on its values. If the `debug` option is enabled, it
        prints the current options. Additionally, if the `verbose` option is set to 0,
        it updates its value to 9.

        Side Effects:
            - Prints the `options` dictionary if `debug` is True.
            - Modifies the `verbose` option to 9 if its current value is 0.
        """
        if self.options['debug']:
            print("Options:")
            if self.options['verbose'] == 0:
                self.options['verbose'] = 9
            pprint.pprint(self.options)

    def process_config_file(self, file_path):
        """
        Processes a configuration file and updates the object's options based on its content.

        Args:
            file_path (str): The path to the configuration file to be processed.

        Behavior:
            - Loads the configuration file and expects its content to be a dictionary-like object.
            - Compares the loaded configuration options with the object's current options.
            - Updates the object's options only if they are set to their default values.
            - Calls `post_options_update` after updating the options.

        Notes:
            - If the configuration file content is not a dictionary, a message is printed
              indicating that the content must be a dictionary.
        """
        config_file_options = load_config_file(file_path)
        if isinstance(config_file_options, Mapping):
            # Only use config file options if the current options are set to the default value
            default_options = self.get_default_options()
            for key in config_file_options:
                if self.options[key] == default_options[key]:
                    self.options[key] = config_file_options[key]
            self.post_options_update()
        else:
            print('Config file content must be a dictionary')

    def get_default_options(self):
        """
        Retrieve the default options for the scraper.

        Returns:
            dict: A dictionary representation of the default options.
        """
        return _todict(self.DefaultOptions)

    def save_settings(self):
        """
        Saves the current scraper settings to a YAML configuration file.

        This method generates a filename for the configuration file, constructs
        the full file path using the output directory specified in the options,
        and creates the configuration file with the current settings.
        """
        output_dir = self.options['outdir']
        filename = generate_filename('mdscrapper', 'yaml')
        filepath = os.path.join(output_dir, filename)
        create_config_file(self.options, filepath)

    def get_relative_url_path(self, url):
        """
        Returns the relative path of a given URL with respect to the root URL, if specified.
        This method calculates the relative path by removing the root path (defined in the
        `root_url` option) from the given URL's path. If the `root_url` option is not set
        or the URL does not match the root path, the original URL is returned.
        Args:
            url (str): The full URL from which the relative path is to be extracted.
        Returns:
            str: The relative path to the root path if it exists, otherwise the original URL.
        Notes:
            - The method uses `urlparse` to parse the URLs and extract their paths.
        """
        if self.options['root_url']:
            root_url = self.options['root_url']
            paresd_root = urlparse(root_url)
            root_path = paresd_root.path

            parsed_url = urlparse(url)
            url_path = parsed_url.path

            new_url = url_path.replace(root_path, '')
            if self.options['debug']:
                print(f'new_url ({new_url}) = url_path ({url_path}) - root_path({root_path})')

            if new_url != url_path:
                return new_url

        return url

    def fetch_webpage(self, url):
        """
        Fetches the content of a webpage and parses it into a BeautifulSoup object.

        Args:
            url (str): The URL of the webpage to fetch.

        Returns:
            BeautifulSoup: A BeautifulSoup object containing the parsed HTML content of the webpage,
            or None if an error occurs during the request.
        """
        headers = {'User-Agent': self.options['user_agent']}

        try:
            response = requests.get(url, headers=headers, timeout=self.options['requests_timeout'])
            response.raise_for_status()  # Raise an exception for HTTP errors
            response.encoding = 'utf-8'  # Ensure correct encoding
        except Exception as err:
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

    def html_to_markdown(self, html_str, title=None, source_url=None):
        """
        Converts and tidies an HTML string to Markdown format with optional title and source URL.

        Args:
            html_str (str): The HTML content to be converted to Markdown.
            title (str, optional): A title to prepend to the Markdown content. Defaults to None.
            source_url (str, optional): A source URL to prepend as a reference. Defaults to None.

        Returns:
            str: The converted Markdown content, or None if the conversion fails.
        """

        # Convert the content to markdown using markdownify
        markdown = md(html_str, heading_style="ATX")

        if not markdown:
            if self.options['debug']:
                print("Debug: No content found to convert to markdown")
            return None

        if title:
            # Add the title at the beginning if it doesn't already exist
            title_str = f"# {title}\n\n"
            if not markdown.startswith(title_str):
                markdown = title_str + markdown

        # Clean up consecutive newlines
        # Always clean up more than 2 consecutive newlines regardless of heading space setting
        markdown = re.sub(r'\n{3,}', '\n\n', markdown)

        # Remove empty paragraphs (lines that only contain whitespace)
        markdown = re.sub(r'\n\s*\n\s*\n', '\n\n', markdown)

        # Add additional newlines before markdown headings if enabled
        if self.options['extra_heading_space']:
            markdown = self.add_newlines_before_headings(markdown)
        else: # Skip cleaning up consecutive newlines when using extra_heading_space
            # Clean up any multiple consecutive newlines
            markdown = re.sub(r'\n{3,}', '\n\n', markdown)

        if source_url:
            markdown = f"Source: <{source_url}>\n\n{markdown}"

        return markdown

    def extract_page_title(self, soup):
        """
        Extracts the title of a webpage from the provided BeautifulSoup object.

        This method attempts to find the title of a webpage by first looking for
        an <h1> element. If no <h1> is found, it falls back to the <title> element.
        If neither is found, a default title of "Webpage" is returned.

        Args:
            soup (BeautifulSoup): A BeautifulSoup object representing the parsed HTML of the webpage.

        Returns:
            str: The extracted title of the webpage, or "Webpage" if no title is found.
        """

        title_element = soup.find('h1') or soup.find('title')
        title = clean_text(title_element.text) if title_element else "Webpage"

        if self.options['debug']:
            if title:
                print(f'Extracted title as: {title}')
            else:
                print('Could not extract the title')

        return title

    def extract_page_content(self, soup):
        """
        Extracts the main content from a BeautifulSoup object.
        This method attempts to locate the primary content container within the
        provided BeautifulSoup object. If the container is not found, it optionally
        saves the HTML to a file for debugging purposes if the 'debug' option is enabled.

        Args:
            soup (BeautifulSoup): The BeautifulSoup object representing the parsed HTML.

        Returns:
            object: The main content container if found, otherwise None.
        """

        content = self.find_content_container(soup)

        if not content:
            print("Could not find the main content container.")
            if self.options['debug']:
                # Save the HTML for inspection
                with open('debug_html.html', 'w', encoding='utf-8') as html_file:
                    html_file.write(str(soup))
                print("Saved HTML to debug_html.html for inspection")
            return None

        return content

    def fetch_content(self, url):
        """
        Fetches the content from the given URL and return it as markdown.

        Args:
            url (str): The URL of the content to fetch.

        Returns:
            str or None: The content converted to markdown, or None if the conversion fails.
        """
        content, title, _ = self._fetch_content(url)

        if self.options['prepend_source_link']:
            markdown = self.convert_to_markdown(content, title, url)
        else:
            markdown = self.convert_to_markdown(content, title)

        return markdown

    def _fetch_content(self, url):
        """
        Internal function to fetch and process content from a URL.

        Args:
            url (str): URL to fetch

        Returns:
            tuple: (content, title, soup) or (None, None, None) if fetching fails
        """
        soup = self.fetch_webpage(url)
        content = self.extract_page_content(soup)
        if not content:
            return None, None, None

        self.process_exclude_selectors(content)

        if self.options['no_images']:
            self.remove_images(content)

        if self.options['no_links']:
            self.remove_links(content)
        else:
            self.make_urls_relative(content)

        title = self.extract_page_title(soup)

        return content, title, soup

    def convert_to_markdown(self, content, title=None, source_url=None):
        """
        Converts the given HTML content into Markdown format.

        Args:
            content (str): The HTML content to be converted.
            title (str): The title of the content.
            url (str): The URL of the source content.
        """
        if not content:
            return None

        return self.html_to_markdown(str(content), title, source_url)

    def remove_images(self, content):
        """
        Removes all image elements and empty paragraph tags from the provided content.

        This method processes the given content to remove all <img> tags. Additionally, it
        removes any <p> tags that are empty or contain only whitespace, which might
        have been left behind after removing images.

        Args:
            content (Tag): The HTML content to process. It is expected to be a
                           BeautifulSoup Tag object.

        Note:
            This method modifies the `content` object in place.
        """

        if isinstance(content, Tag):
            for img in content.find_all('img'):
                if isinstance(img, Tag):
                    img.decompose()

            # Also remove empty paragraph tags that might have contained only images
            for paragraph in content.find_all('p'):
                if isinstance(paragraph, Tag) and not paragraph.get_text(strip=True):
                    paragraph.decompose()

            if self.options['debug']:
                print("All images have been removed from the content")

    def remove_links(self, content):
        """
        Removes all hyperlink tags (<a>) from the given content and replaces them with their text content.

        Args:
            content (Tag): The HTML content to process. It should be a BeautifulSoup Tag object.

        Note:
            This method modifies the `content` object in place.

        """

        if isinstance(content, Tag):
            for anchor in content.find_all('a'):
                if isinstance(anchor, Tag):
                    # Replace the link with its text content
                    anchor_text = anchor.get_text()
                    new_tag = BeautifulSoup().new_string(anchor_text)
                    anchor.replace_with(new_tag)
            if self.options['debug']:
                print("All links have been removed from the content")

    def process_exclude_selectors(self, content):
        """
        Removes elements from the provided content based on the exclude selectors
        specified in the options.

        Args:
            content (BeautifulSoup): The parsed HTML content to process.

        Note:
            This method modifies the `content` object in place.
        """
        if self.options['exclude_selectors']:
            for selector in self.options['exclude_selectors']:
                to_exclude = content.select(selector)
                if to_exclude:
                    for element in to_exclude:
                        element.decompose()

    def make_urls_relative(self, content):
        """
        Converts URLs in anchor tags within the provided HTML content to relative URLs.

        Args:
            content (Tag): The HTML content to process, represented as a BeautifulSoup Tag object.

        Note:
            This method modifies the `content` object in place.
        """
        if self.options['root_url'] and isinstance(content, Tag):
            for anchor in content.find_all('a'):
                if isinstance(anchor, Tag):
                    # Replace the link with relative link
                    url = anchor['href']
                    anchor['href'] = self.get_relative_url_path(url)

    def find_content_by_div_attr(self, soup, attr, filter_list):
        """
        Finds a <div> element in the provided BeautifulSoup object based on a specified
        attribute and a list of possible attribute values.

        Args:
            soup (BeautifulSoup): The BeautifulSoup object to search within.
            attr (str): The attribute to filter by ('class' or 'id').
            filter_list (list): A list of possible values for the specified attribute.

        Returns:
            Tag or None: The first matching <div> element if found, otherwise None.
        """
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
        """
        Attempts to intelligently detect and extract the main content container from a BeautifulSoup object.

        This method uses a series of heuristics to locate the primary content container within
        the provided BeautifulSoup object.

            1. If `self.options['content']` is provided, it attempts to find the container by `id` or `class`.
            2. Falls back to `self.options['default_content_names']` to find the container by `id` or `class`.
            3. Searches for an `<article>` tag as a potential content container.
            4. As a last resort, selects the largest `<div>` based on the length of its text content.

        Args:
            soup (BeautifulSoup): A BeautifulSoup object representing the parsed HTML of the webpage.

        Returns:
            Tag or None: The detected content container as a BeautifulSoup Tag object, or None if no
            suitable container is found.
        """
        if soup:
            content = None

            if self.options['debug']:
                # Print all div classes to help identify the content container
                print("Available div attributes:")
                class_list, id_list = get_div_attrs(soup)
                print(f"- id: {id_list}")
                print(f"- class: {class_list}")

            if self.options.get('content'):
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
        """
        Extracts a list of URLs from the given HTML content, filters them based on
        exclusion criteria, and returns the full URLs.

        Args:
            content (BeautifulSoup): Parsed HTML content to extract anchor tags from.
            site_root (str): The root URL of the site to prepend to relative paths.

        Returns:
            list: A list of full URLs that are not excluded by the exclusion criteria.
        """
        anchor_list = content.find_all('a')
        if self.options['debug']:
            print(f'site_root: {site_root}')
            print('anchor_list:')
            pprint.pprint(anchor_list)

        url_list = []
        for anchor in anchor_list:
            url = anchor['href']
            parsed_url = urlparse(url)
            url_path = parsed_url.path

            # Get the page name as the last part of the path
            page_name = url_path.split("/")[-1]

            # Ensure exclude_pages is a list (or empty list) to avoid NoneType issues
            exclude_pages = self.options['exclude_pages']
            exclude_pages = exclude_pages or []

            # Skip any excluded urls
            if any(fnmatch.fnmatch(page_name, text) for text in exclude_pages):
                if self.options['debug']:
                    print(f'Ignoring webpage: {page_name}')
            else:
                full_url = site_root + url_path
                url_list.append(full_url)

        if self.options['debug']:
            print('Url list:')
            pprint.pprint(url_list)

        return url_list

    def process_url_list(self, url_list, output_dir=None):
        """
        Processes a list of URLs and generates markdown files for each URL.

        Args:
            url_list (list): A list of URLs to process.
            output_dir (str, optional): The directory where the generated markdown files
                will be saved. If not provided, the default output directory specified
                in `self.options['outdir']` will be used.

        Side Effects:
            - Updates `self.options['outdir']` if `output_dir` is provided.
            - Prints verbose output to the console if `self.options['verbose'] > 0`.
        """

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
        """
        Processes a file containing a list of URLs, extracting and processing each URL.

        Args:
            url_file_path (str): The file path to the text file containing URLs,
                with one URL per line. Empty lines are ignored.
            output_dir (str, optional): The directory where the output of the
                processed URLs will be stored. Defaults to None.
        """

        with open(url_file_path, 'r', encoding='utf-8') as url_file:
            url_list = [line.strip() for line in url_file if line.strip()]

        self.process_url_list(url_list, output_dir)

    def process_site_url(self, site_url, output_dir=None):
        """
        Processes a website by downloading its content, extracting URLs,
        and converting each URL to a markdown file.

        Args:
            site_url (str): The URL of the website to process.
            output_dir (str, optional): The directory where processed data
                will be saved. Defaults to None.
        """
        soup = self.fetch_webpage(site_url)
        content = self.extract_page_content(soup)

        parsed_url = urlparse(site_url)
        site_root =  f'{parsed_url.scheme}://{parsed_url.hostname}'
        url_list = self.content_to_url_list(content, site_root)
        self.process_url_list(url_list, output_dir)

    def process_single_url(self, url, output_file=None):
        """
        Processes a single URL by fetching its content, converting it to markdown, and saving it to a file.

        Args:
            url (str): The URL to fetch and process.
            output_file (str, optional): The name of the output file. If not provided, it defaults to the value
                                         specified in the options. Special values '%TITLE' and '%URL' can be used
                                         to generate filenames dynamically based on the content or URL.

        Returns:
            bool: True if the URL was successfully processed and saved, False otherwise.
        """
        output_dir = self.options['outdir']

        if not output_file:
            output_file = self.options['output']

        if self.options['verbose'] > 0:
            print(f"Fetching and parsing {url}...")

        markdown = self.fetch_content(url)
        if markdown:
            if output_file in ('%TITLE', '%URL'):
                if output_file == '%TITLE':
                    # Use the markdown content title as the filename
                    extracted_filename = self.extract_md_title(markdown)
                    if not extracted_filename:
                        if self.options['debug']:
                            print("No title found, using URL as filename")
                        output_file = '%URL'

                if output_file == '%URL':
                    # Use the last part of the URL as the filename
                    extracted_filename = get_last_url_part(url)

                filename = sanitize_filename(extracted_filename)
                filename_source = output_file[1:]  # Remove the % sign
                output_file = os.path.join(output_dir, f"{filename}.md")
                if self.options['debug']:
                    print(f'Generated filename "{output_file}" from {filename_source} "{extracted_filename}"')
            else:
                output_file = os.path.join(output_dir, output_file)

            # Create output directory if it doesn't exist
            output_dir = os.path.dirname(output_file)
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

    def extract_md_title(self, markdown):
        """
        Extracts the title from a Markdown string.

        This method scans the provided Markdown content line by line to find
        the first line that starts with a single '#' followed by a space,
        which is typically used to denote a top-level heading in Markdown.
        The '#' and the space are removed from the line, and the remaining
        text is returned as the title.

        Args:
            markdown (str): The Markdown content as a string.

        Returns:
            str or None: The extracted title if a top-level heading is found,
            otherwise None.
        """
        title = None
        for line in markdown.split('\n'):
            if line.startswith('# '):
                title = line.replace('# ', '')
                break
        return title


def scraper_cli(**options):
    """
    The command-line interface (CLI) handler for MdScraper class

    This function processes various input options provided via the CLI,
    initializes an instance of the MdScraper class, and performs the
    appropriate scraping operations based on the provided arguments.

    Parameters:
        **options: Arbitrary keyword arguments containing at least the following keys:
            - url (str): A single URL to scrape.
            - file (str): Path to a file containing multiple URLs to scrape.
            - site (str): A site URL to scrape.
            - settings (str): Path to a settings configuration file.
            - save_settings (bool): Flag to save the current settings.
    """
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
