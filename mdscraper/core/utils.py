#!/usr/bin/env python
# -*- coding: utf-8 -*-
# pylint: disable=line-too-long

"""
This module provides utility functions for various common tasks such as URL parsing, 
HTML content extraction, text cleaning, file operations, and configuration management.
"""

import os
import re
import html
import json
import datetime
from urllib.parse import urlparse

import yaml
from bs4.element import Tag

# logging.basicConfig(level=logging.INFO)

def get_last_url_part(url):
    """
    Extracts and returns the last part of the path from a given URL.

    Args:
        url (str): The URL from which to extract the last part of the path.

    Returns:
        str: The last segment of the path in the URL. If the path ends with a
        slash, an empty string is returned.
    """
    parsed_url = urlparse(url)

    # Get the path part of the URL ignoring parameters and domain
    path = parsed_url.path

    # Get the last part of the path
    path_parts = path.split("/")
    last_part = path_parts[-1]
    return last_part

def get_div_attrs(soup):
    """
    Extracts the class and id attributes from all <div> elements in a BeautifulSoup object.

    Args:
        soup (BeautifulSoup): A BeautifulSoup object representing the parsed HTML document.

    Returns:
        tuple: A tuple containing two lists:
            - class_list (list): A list of all class attribute values found in <div> elements.
            - id_list (list): A list of all id attribute values found in <div> elements.
    """
    class_list = []
    id_list = []
    for div in soup.find_all('div'):
        # Only Tag elements have the get method, not NavigableString
        if isinstance(div, Tag):
            div_classes = div.get('class')
            if div_classes:
                class_list.extend(div_classes)
            div_id = div.get('id')
            if div_id:
                id_list.append(div_id)
    return class_list,id_list

def clean_text(text):
    """
    Clean and normalize text content.

    Args:
        text (str): Text to clean

    Returns:
        str: Cleaned text
    """
    if not text:
        return ""
    # Replace multiple spaces with a single space
    text = re.sub(r'\s+', ' ', text)
    # Decode HTML entities
    text = html.unescape(text)
    # Remove leading/trailing whitespace
    return text.strip()

def sanitize_filename(filename):
    """
    Convert a string into a valid filename by replacing invalid characters.

    Args:
        filename (str): Original filename

    Returns:
        str: Sanitized filename
    """
    # Replace invalid filename characters with underscores
    return re.sub(r'[\\/*?:"<>|]', '_', filename)

def save_markdown_to_file(markdown, output_file):
    """
    Save markdown content to a file.

    Args:
        markdown (str): Markdown content to save
        output_file (str): Path to the output file
    """
    with open(output_file, 'w', encoding='utf-8') as md_file:
        md_file.write(markdown)

def get_size_kb(file_path):
    """
    Get the size of a file in kilobytes.

    Args:
        file_path (str): Path to the target file

    Returns:
        float: Size of the saved file in KB
    """
    file_size = os.path.getsize(file_path) / 1024  # size in KB
    return file_size

def load_config_file(file_path):
    """
    Load a YAML or JSON file and return its content as a Python object.

    Args:
        file_path (str): The path to the YAML or JSON file.

    Returns:
        dict: The content of the file as a Python dictionary.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            try:
                # Try to load the file as YAML
                return yaml.safe_load(file)
            except yaml.YAMLError:
                # Try to load the file as JSON
                file.seek(0)  # Reset the file pointer
                try:
                    return json.load(file)
                except json.JSONDecodeError as json_err:
                    print(f"Error: Failed to load {file_path} as JSON: {json_err}")
                    raise ValueError(f"Invalid file format: {file_path}") from json_err
    except FileNotFoundError:
        print(f"Error: File not found: {file_path}")
        raise
    except Exception as err:
        print(f"Error: An unexpected error occurred: {err}")
        raise

def create_config_file(config_dict, filename):
    """
    Creates a configuration file in YAML format.

    Args:
        config_dict (dict): A dictionary containing the configuration data to be written to the file.
        filename (str): The name (and path) of the file where the configuration will be saved.

    Raises:
        Exception: If an error occurs during file writing, it will be caught and printed.

    Notes:
        - The YAML file is created with a block-style format (default_flow_style=False).
    """
    try:
        with open(filename, 'w', encoding='utf-8') as config_file:
            yaml.dump(config_dict, config_file, default_flow_style=False)
        print(f"Config file created successfully: {filename}")
    except (IOError, yaml.YAMLError) as err:
        print(f"An error occurred: {err}")

def generate_filename(prefix, ext):
    """
    Generates a filename using the given prefix and extension then appending the current timestamp.

    Args:
        prefix (str): The prefix to use for the filename.
        ext (str): The file extension to use (e.g., 'txt', 'csv').

    Returns:
        str: A string representing the generated filename in the format 
             '<prefix>_YYYYMMDD_HHMM.<ext>', where the timestamp is based on the current date and time.
    """
    current_time = datetime.datetime.now()
    filename = f"{prefix}_{current_time.strftime('%Y%m%d_%H%M')}.{ext}"
    return filename
