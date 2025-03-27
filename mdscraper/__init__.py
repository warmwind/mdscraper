"""
MDScraper - A tool to fetch webpages and convert their content to clean Markdown format
"""

__version__ = "0.1.0"

from mdscraper.core.scraper import (
    fetch_and_convert_to_markdown,
    process_single_url,
    process_url_file,
    find_content_container,
    add_newlines_before_headings,
)

__all__ = [
    "fetch_and_convert_to_markdown",
    "process_single_url",
    "process_url_file",
    "find_content_container",
    "add_newlines_before_headings",
] 