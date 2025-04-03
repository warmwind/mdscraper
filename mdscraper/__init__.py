"""
MDScraper - A tool to fetch webpages and convert their content to clean Markdown format
"""

__version__ = "0.1.3"

from mdscraper.core.scraper import (
    fetch_content,
    convert_to_markdown,
    process_single_url,
    process_url_file,
    find_content_container,
    add_newlines_before_headings,
)

__all__ = [
    "fetch_content",
    "convert_to_markdown",
    "process_single_url",
    "process_url_file",
    "find_content_container",
    "add_newlines_before_headings",
] 