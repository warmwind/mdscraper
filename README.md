# MDScraper - HTML to Markdown Converter

This tool fetches content from any website and converts it to Markdown format. It intelligently identifies the main content area and properly formats headings, lists, tables, images, and links.

## Requirements

- Python 3.6+
- Required packages:
  - requests
  - beautifulsoup4
  - markdownify

## Installation

```bash
# Clone the repository
git clone https://github.com/warmwind/mdscraper.git
cd mdscraper

# Install required packages
pip install -r requirements.txt
```

## Usage

Run the script with a URL:

```bash
python mdscraper.py [URL] [OUTPUT_FILE] [--debug]
```

### Arguments

- `URL` (optional): The URL of the webpage to fetch and convert. Default is 'https://example.com'.
- `OUTPUT_FILE` (optional): The name of the output Markdown file. Default is 'output.md'.
- `--debug` or `-d` (optional): Enable debug mode for more information.

### Examples

```bash
# Fetch the default URL and save to default output file
python mdscraper.py

# Fetch a specific URL and save to custom output file
python mdscraper.py https://example.com/article custom_output.md

# Run with debug mode enabled to get more information
python mdscraper.py --debug

# Fetch a specific URL with debug mode enabled
python mdscraper.py https://example.com/blog/post --debug
```

## Features

- Automatically detects the main content container in any HTML page
- Properly formats headings (h1-h5)
- Maintains list structure (ordered and unordered)
- Converts HTML tables to Markdown tables
- Handles images and links with proper URLs
- Supports basic text formatting (bold, italic)
- Cleans up excessive whitespace

## Debug Mode

If you're having issues with the script not finding the correct content container, you can enable debug mode by using the `--debug` or `-d` flag. This will:

1. Print all available div classes in the HTML
2. Save the raw HTML to 'debug_html.html' for inspection
3. Output more information about what content containers were found

## Limitations

- Complex nested structures may not render perfectly
- Some advanced HTML features might not be fully supported
- JavaScript-rendered content won't be parsed (the script only processes static HTML)
- The script may not handle extremely large pages efficiently

## License

This script is provided under the MIT License.
