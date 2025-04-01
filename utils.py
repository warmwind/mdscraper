#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re
import html
import json
import yaml
import datetime
# import logging
from bs4.element import Tag
from urllib.parse import urlparse

# logging.basicConfig(level=logging.INFO)

def get_last_url_part(url):
    parsed_url = urlparse(url)

    # Get the path part of the URL ignoring parameters and domain
    path = parsed_url.path

    # Get the last part of the path
    path_parts = path.split("/")
    last_part = path_parts[-1]
    return last_part

def get_div_attrs(soup):
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
    if not text:
        return ""
    # Replace multiple spaces with a single space
    text = re.sub(r'\s+', ' ', text)
    # Decode HTML entities
    text = html.unescape(text)
    # Remove leading/trailing whitespace
    return text.strip()

def sanitize_filename(filename):
    # Replace invalid filename characters with underscores
    return re.sub(r'[\\/*?:"<>|]', '_', filename)

def save_markdown_to_file(markdown, output_file):
    with open(output_file, 'w', encoding='utf-8') as md_file:
        md_file.write(markdown)

def get_size_kb(file_path):
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
        with open(file_path, 'r') as file:
            try:
                # Try to load the file as YAML
                # logging.info(f"Loading {file_path} as YAML")
                return yaml.safe_load(file)
            except yaml.YAMLError as err:
                # logging.warning(f"Failed to load {file_path} as YAML: {err}")
                # Try to load the file as JSON
                file.seek(0)  # Reset the file pointer
                try:
                    # logging.info(f"Loading {file_path} as JSON")
                    return json.load(file)
                except json.JSONDecodeError as err:
                    # logging.error(f"Failed to load {file_path} as JSON: {err}")
                    raise ValueError(f"Invalid file format: {file_path}") from err
    except FileNotFoundError:
        # logging.error(f"File not found: {file_path}")
        raise
    except Exception as err:
        # logging.error(f"An error occurred: {err}")
        raise

def create_config_file(config_dict, filename):
    try:
        with open(filename, 'w') as config_file:
            yaml.dump(config_dict, config_file, default_flow_style=False)
        print(f"Config file created successfully: {filename}")
    except Exception as err:
        print(f"An error occurred: {err}")

def generate_filename(prefix, ext):
    current_time = datetime.datetime.now()
    filename = f"{prefix}_{current_time.strftime('%Y%m%d_%H%M')}.{ext}"
    return filename
