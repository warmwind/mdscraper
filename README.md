# MDScraper

A tool to fetch webpages and convert their content to Markdown format.

## Features

- Extract content from webpages and convert to Markdown
- Process single URLs or batch process multiple URLs from a file
- Intelligent content detection for various webpage layouts
- Option to ignore images in the output
- Option to ignore links in the output
- Option to add extra spacing before headings for improved readability
- Debug mode for troubleshooting

## Installation

Clone the repository:

```
git clone https://github.com/yourusername/mdscraper.git
cd mdscraper
```

Install required packages

```
pip install -r requirements.txt

```

## Usage

### Process a single URL

```bash
python mdscraper.py --url https://example.com --output example.md
```

### Process multiple URLs from a file

Create a text file with one URL per line, then run:

```bash
python mdscraper.py --file urls.txt --outdir output_directory
```

### Additional options

- `--debug` or `-d`: Enable debug mode for more information
- `--no-images`: Ignore all images in the content
- `--no-links`: Ignore all links in the content
- `--extra-heading-space LEVELS`: Add newlines before specific heading levels for better readability. LEVELS can be:
  - `all`: Add spacing to all heading levels (h1-h6)
  - `1,2,3`: Comma-separated list of specific heading levels to apply spacing to

## License

MIT
