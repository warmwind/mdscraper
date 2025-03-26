#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import html
import os

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
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(markdown)
    
    file_size = os.path.getsize(output_file) / 1024  # size in KB
    return file_size 