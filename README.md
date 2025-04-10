# MDScraper

A specialized tool for extracting clean, structured content from webpages and converting it to Markdown format.

Ideal for:

- Preparing web content for LLM embeddings
- Semantic search applications
- Converting webdocs to GitHub/GitLab wikis

## Features

- Clean and normalize web content for optimal LLM processing
- Extract relevant content while filtering out noise, navigation, ads, and irrelevant elements
- Transform HTML content into consistent, well-structured Markdown format
- Process single URLs or batch process multiple URLs from a file or webpage
- Intelligent content detection for various webpage layouts
- Options to customize markdown content
  - Ignore images and links to reduce token usage in embeddings
  - Add extra spacing before headings for improved document structure
  - Prepend source link at the top of document for reference
  - Convert links to relative links by specifying the root URL
    - Useful for download a site so that links will work between markdown files
  - For extra detailed control you can exclude webpage parts by CSS selectors
  - Set custom content detection with a list of class or id names
- Use a json or YAML settings file when dealing with lots of options
- Verbose output levels to monitor progress
- Debug mode for troubleshooting extraction issues

## Installation

First, ensure you have UV installed ([official UV installation guide](https://github.com/astral-sh/uv)).

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Option 1: Install from PyPI

```bash
uv pip install mdscraper
```

### Option 2: Install from source

Clone and install the repository:

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
### Process multiple URLs from a webpage
Only URLs on the specified site will be captured as markdown. This will not "crawl" a site to try and download all possible webpages.

```bash
# Eaxmple
mdscraper --site https://example.com --outdir output_directory

# Better example
mdscraper --site https://help.prusa3d.com/filament-material-guide --outdir filament_material_guide --content table
```

To exclude webpages you can add an exclusion page name list:

```bash
mdscraper --site https://example.com --outdir output_directory --exclude-pages terms
```

### Using as a library

MDScraper can also be imported and used programmatically:

```python
from mdscraper import MdScraper

# Use the default options
mds = MdScraper()

# Or set options
mds = MdScraper(no_images = True,  # Remove images
                no_links = True,   # Remove links
                debug = True,      # Enable debug output
                extra_heading_space = "2"  # Add extra newlines before headings
                prepend_source_link = True # Prepend source link
)

# Fetch content as markdown (default)
markdown_content = mds.fetch_content("https://example.com")
```

### Options

#### Required options

Must include at least one of these options:

```bash
  --url URL             URL of a single webpage to fetch and convert
  --file FILE           Text file containing URLs (one per line) to fetch and convert
  --site SITE           A URL of a page to scrape for URLS to download a site
```

#### Optional options

```bash
  -h, --help            show this help message and exit
  --output OUTPUT       Output Markdown file name. Default (%TITLE) will generate a filename based on the Webpage Title. If you prefer to use the URL set this to %URL. Otherwise, use to set as the desired filename
  --outdir OUTDIR       Output directory for markdown files, used with --file, --site, or with generated --output
  --root-url ROOT_URL, -r ROOT_URL
                        The URL of the desired root path to generate relatives links for downloaded pages.
  --content [CONTENT [CONTENT ...]], -c [CONTENT [CONTENT ...]]
                        Additional list of div id or classes to use as the main content
  --no-images, -i       Ignore all images in the content
  --no-links            Ignore all links in the content
  --prepend-source-link Prepend source link in markdown file
  --exclude-pages [EXCLUDE_PAGES [EXCLUDE_PAGES ...]], -p [EXCLUDE_PAGES [EXCLUDE_PAGES ...]]
                        Space separated list of page names to ignore, can unix filename pattern matching.
  --exclude-selectors [EXCLUDE_SELECTORS [EXCLUDE_SELECTORS ...]], -s [EXCLUDE_SELECTORS [EXCLUDE_SELECTORS ...]]
                        Space separated list of CSS selectors to exclude
  --extra-heading-space LEVELS
                        Add additional newlines before specified heading levels (e.g., "1,2,3" for h1,h2,h3 or "all" for all headings)
  --settings SETTINGS   All the options can be passed in as a yaml or json file. CLI options will take precedence
  --save-settings       Save the settings as a yaml file, and skip running. Filename will be mdscrapper_{YYYmmdd_HHMM}.yaml
  --debug, -d           Enable debug mode for more information
  --verbose, -v         Display runtime information. Use more than once to increase the verbosity level. Default level is silent.
```

## Development

First ensure you have the development dependencies installed:

```bash
uv pip install -e ".[dev]"
```

### Running Tests

```bash
# Run tests without coverage
pytest tests/

# Run tests with coverage report
pytest tests/ --cov
```

The coverage report will show you which parts of the code are covered by tests and which lines are missing coverage.

### Versioning

Manage the version with [bump2version · PyPI](https://pypi.org/project/bump2version/)

```bash
# Bump the major version number X.0.0
bumpversion major

# Bump the minor version number 0.X.0
bumpversion minor

# Bump the patch version number 0.0.X
bumpversion patch
````

## License

MIT
