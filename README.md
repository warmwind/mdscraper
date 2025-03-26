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
# For a single URL
python mdscraper.py --url [URL] --output [OUTPUT_FILE] [--debug] [--no-images]

# For multiple URLs from a text file
python mdscraper.py --file [URL_FILE] --outdir [OUTPUT_DIRECTORY] [--debug] [--no-images]
```

### Arguments

- `--url`: The URL of a single webpage to fetch and convert
- `--file`: Text file containing URLs (one per line) to fetch and convert
- `--output` (optional): The name of the output Markdown file when using --url. Default is 'output.md'.
- `--outdir` (optional): Output directory for markdown files when using --file. Default is 'outs'.
- `--debug` or `-d` (optional): Enable debug mode for more information.
- `--no-images` (optional): Ignore all images in the content and exclude them from the markdown output.

### Examples

```bash
# Fetch a specific URL and save to custom output file
python mdscraper.py --url https://example.com/article --output custom_output.md

# Run with debug mode enabled to get more information
python mdscraper.py --url https://example.com/blog/post --debug

# Process multiple URLs from a text file
python mdscraper.py --file urls.txt

# Process multiple URLs and save to a custom directory
python mdscraper.py --file urls.txt --outdir my_markdown_files

# Process a URL without including any images
python mdscraper.py --url https://example.com/article --no-images
```

## Multiple URL Processing

When processing multiple URLs from a file:

- Each URL should be on a separate line in the text file
- The output will be saved in the specified directory (default: 'outs')
- Each file will be named based on the title of the webpage
- A summary will be displayed showing the number of successful and failed conversions

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
