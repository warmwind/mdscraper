import os
import shutil
import pytest

@pytest.fixture(autouse=True)
def cleanup_test_files():
    """Automatically clean up test files after each test."""
    # Run the test
    yield

    # Clean up files after the test
    test_files = [
        'test_with_images.md',
        'test_without_images.md',
        'python_basic.md',
        'python_without_images.md',
        'python_no_links.md',
        'python_with_headings.md',
        'python_combined.md',
        'python_docs_with_images.md',
        'python_docs_without_images.md',
        'sample_urls.txt',
        'cli_basic.md'
    ]

    # Remove individual files
    for file in test_files:
        if os.path.exists(file):
            try:
                os.remove(file)
            except OSError:
                pass  # Ignore errors if file can't be removed

    # Remove test output directory if it exists
    if os.path.exists('test_batch_output'):
        try:
            shutil.rmtree('test_batch_output')
        except OSError:
            pass  # Ignore errors if directory can't be removed
