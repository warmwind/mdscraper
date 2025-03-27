# MDScraper

A specialized tool for extracting clean, structured content from webpages and converting it to Markdown format. Ideal for preparing web content for LLM embeddings and semantic search applications.

## Features

- Clean and normalize web content for optimal LLM processing
- Extract relevant content while filtering out noise, navigation, ads, and irrelevant elements
- Transform HTML content into consistent, well-structured Markdown format
- Process single URLs or batch process multiple URLs from a file
- Intelligent content detection for various webpage layouts
- Options to ignore images and links to reduce token usage in embeddings
- Option to add extra spacing before headings for improved document structure
- Debug mode for troubleshooting extraction issues

## Installation

### Option 1: Install from PyPI

```bash
uv pip install mdscraper
```

### Option 2: Install from source

First, ensure you have UV installed. If not, install it following the [official UV installation guide](https://github.com/astral-sh/uv):

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Then clone and install the repository:

```bash
git clone https://github.com/yourusername/mdscraper.git
cd mdscraper
uv pip install .
```

## Usage

### Process a single URL

```bash
mdscraper --url https://example.com --output example.md
```

### Process multiple URLs from a file

Create a text file with one URL per line, then run:

```bash
mdscraper --file urls.txt --outdir output_directory
```

### Additional options

- `--debug` or `-d`: Enable debug mode for more information
- `--no-images`: Ignore all images in the content
- `--no-links`: Ignore all links in the content
- `--extra-heading-space LEVELS`: Add newlines before specific heading levels for better readability. LEVELS can be:
  - `all`: Add spacing to all heading levels (h1-h6)
  - `1,2,3`: Comma-separated list of specific heading levels to apply spacing to

## Development

### Running Tests

To run the test suite, first ensure you have the development dependencies installed:

```bash
uv pip install -e ".[dev]"
```

Then run the tests:

```bash
# Run tests without coverage
pytest tests/

# Run tests with coverage report
pytest tests/ --cov
```

The coverage report will show you which parts of the code are covered by tests and which lines are missing coverage.

## License

MIT
