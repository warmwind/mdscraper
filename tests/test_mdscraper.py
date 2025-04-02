#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys

# Add the parent directory to the Python path for proper imports
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

import unittest
import tempfile
import shutil
from unittest.mock import patch, MagicMock
from bs4 import BeautifulSoup
from mdscraper.core.scraper import process_single_url, process_url_file, find_content_container, add_newlines_before_headings, fetch_content, _fetch_content, convert_to_markdown

class TestMDScraper(unittest.TestCase):
    
    def setUp(self):
        # Create a temporary directory for test files
        self.test_dir = tempfile.mkdtemp()
        
        # Sample HTML content for testing
        self.sample_html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Test Page</title>
        </head>
        <body>
            <article class="content">
                <h1>Test Article</h1>
                <p>This is a test paragraph.</p>
                <img src="test.jpg" alt="Test Image">
                <p>Another paragraph with <a href="https://example.com">a link</a>.</p>
                <h2>Section Heading</h2>
                <p>Content in a section.</p>
                <p><img src="section.jpg" alt="Section Image"></p>
                <h3>Subsection</h3>
                <p>More content.</p>
            </article>
        </body>
        </html>
        """
    
    def tearDown(self):
        # Remove the temporary directory
        shutil.rmtree(self.test_dir)
    
    def test_find_content_container(self):
        """Test content container identification"""
        soup = BeautifulSoup(self.sample_html, 'html.parser')
        content = find_content_container(soup)
        self.assertIsNotNone(content)
        self.assertEqual(content.name, 'article')
        self.assertEqual(content.get('class'), ['content'])
    
    def test_add_newlines_before_headings(self):
        """Test adding extra spacing before headings"""
        markdown = "# Title\nSome text\n## Section\nMore text\n### Subsection\nEven more text"
        
        # Test 'all' heading levels
        result = add_newlines_before_headings(markdown, 'all')
        # We expect one ## heading but there might be more in different implementations
        self.assertGreaterEqual(result.count('\n\n\n##'), 1)
        self.assertGreaterEqual(result.count('\n\n\n###'), 1)
        
        # Test specific heading levels
        result = add_newlines_before_headings(markdown, '2')
        self.assertGreaterEqual(result.count('\n\n\n##'), 1)
        self.assertEqual(result.count('\n\n\n###'), 0)
    
    @patch('requests.get')
    def test_fetch_and_convert_to_markdown(self, mock_get):
        """Test fetching and converting HTML to Markdown"""
        # Setup the mock
        mock_response = MagicMock()
        mock_response.text = self.sample_html
        mock_response.encoding = 'utf-8'
        mock_get.return_value = mock_response
        
        # Test basic conversion
        content, title, soup = _fetch_content("https://example.com", debug=False)
        markdown = convert_to_markdown(content, title)
        self.assertIsNotNone(markdown)
        assert markdown is not None  # Type assertion
        self.assertIn("# Test Article", markdown)
        self.assertIn("This is a test paragraph", markdown)
        self.assertIn("![Test Image]", markdown)
        self.assertIn("Section Heading", markdown)
        
        # Test with image removal
        content, title, soup = _fetch_content("https://example.com", debug=False, ignore_images=True)
        markdown = convert_to_markdown(content, title)
        self.assertIsNotNone(markdown)
        assert markdown is not None  # Type assertion
        self.assertNotIn("![Test Image]", markdown)
        self.assertNotIn("![Section Image]", markdown)
        
        # Test with link removal
        content, title, soup = _fetch_content("https://example.com", debug=False, ignore_links=True)
        markdown = convert_to_markdown(content, title)
        self.assertIsNotNone(markdown)
        assert markdown is not None  # Type assertion
        self.assertNotIn("](https://example.com)", markdown)
        self.assertIn("a link", markdown)
        
        # Test with extra heading space
        content, title, soup = _fetch_content("https://example.com", debug=False)
        markdown = convert_to_markdown(content, title, extra_heading_space="2,3")
        self.assertIsNotNone(markdown)
        assert markdown is not None  # Type assertion
        self.assertTrue(markdown.count("\n\n\n## Section Heading") > 0 or markdown.count("\n\n\n##Section Heading") > 0)
    
    @patch('mdscraper.core.scraper.fetch_content')
    @patch('mdscraper.core.scraper.save_markdown_to_file')
    def test_process_single_url(self, mock_save, mock_fetch):
        """Test processing a single URL"""
        # Setup mocks
        mock_fetch.return_value = "# Test Markdown"
        mock_save.return_value = 1.5  # 1.5 KB file size
        
        output_file = os.path.join(self.test_dir, "output.md")
        
        # Test successful processing
        result = process_single_url("https://example.com", output_file)
        self.assertTrue(result)
        mock_fetch.assert_called_once()
        mock_save.assert_called_once()
        
        # Test with debug flag
        mock_fetch.reset_mock()
        mock_save.reset_mock()
        result = process_single_url("https://example.com", output_file, debug=True)
        self.assertTrue(result)
        mock_fetch.assert_called_with("https://example.com", debug=True, ignore_images=False, ignore_links=False, extra_heading_space=None, prepend_source_link=False)
        
        # Test with options including prepend_source_link
        mock_fetch.reset_mock()
        result = process_single_url("https://example.com", output_file, ignore_images=True, ignore_links=True, extra_heading_space="all", prepend_source_link=True)
        mock_fetch.assert_called_with("https://example.com", debug=False, ignore_images=True, ignore_links=True, extra_heading_space="all", prepend_source_link=True)
        
        # Test failure case
        mock_fetch.return_value = None
        result = process_single_url("https://example.com", output_file)
        self.assertFalse(result)
    
    @patch('mdscraper.core.scraper.fetch_content')
    @patch('mdscraper.core.scraper.save_markdown_to_file')
    def test_process_url_file(self, mock_save, mock_fetch):
        """Test processing multiple URLs from a file"""
        # Create a test URL file
        url_file = os.path.join(self.test_dir, "urls.txt")
        with open(url_file, 'w') as f:
            f.write("https://example.com/1\nhttps://example.com/2\n")
        
        output_dir = os.path.join(self.test_dir, "outputs")
        
        # Setup mock for successful fetches
        mock_fetch.return_value = "# Test Markdown"
        mock_save.return_value = 1.5  # 1.5 KB file size
        
        # Test with default options
        process_url_file(url_file, output_dir=output_dir)
        self.assertEqual(mock_fetch.call_count, 2)
        self.assertEqual(mock_save.call_count, 2)
        
        # Check if the output directory was created
        self.assertTrue(os.path.exists(output_dir))
        
        # Test with various options including prepend_source_link
        mock_fetch.reset_mock()
        mock_save.reset_mock()
        process_url_file(url_file, output_dir=output_dir, debug=True, ignore_images=True, ignore_links=True, extra_heading_space="1,2", prepend_source_link=True)
        self.assertEqual(mock_fetch.call_count, 2)
        mock_fetch.assert_called_with("https://example.com/2", debug=True, ignore_images=True, ignore_links=True, extra_heading_space="1,2", prepend_source_link=True)
        
        # Test handling failure cases
        mock_fetch.reset_mock()
        mock_save.reset_mock()
        mock_fetch.side_effect = [None, "# Test Markdown"]
        process_url_file(url_file, output_dir=output_dir)
        self.assertEqual(mock_fetch.call_count, 2)
        self.assertEqual(mock_save.call_count, 1)
    
    def test_image_removal_empty_lines(self):
        """Test that image removal doesn't leave multiple empty lines"""
        # Create HTML with empty paragraphs and images
        html_with_images = """
        <!DOCTYPE html>
        <html>
        <body>
            <div class="content">
                <h1>Test</h1>
                <p>Text before image</p>
                <p><img src="test.jpg" alt="Test"></p>
                <p></p>
                <p>Text after image</p>
                <p><img src="test2.jpg" alt="Test2"></p>
                <p>More text</p>
            </div>
        </body>
        </html>
        """
        
        # Mock the request
        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.text = html_with_images
            mock_response.encoding = 'utf-8'
            mock_get.return_value = mock_response
            
            # Test with image removal
            markdown = fetch_content("https://example.com", ignore_images=True)
            
            self.assertIsNotNone(markdown)
            assert markdown is not None  # Type assertion
            
            # The resulting markdown should not have more than 2 consecutive newlines
            self.assertNotIn("\n\n\n", markdown)
            
            # Check that empty paragraphs are properly cleaned
            self.assertNotIn("\n\n\n\n", markdown)
            
            # Make sure text before and after images is properly connected
            self.assertTrue("Text before image" in markdown)
            self.assertTrue("Text after image" in markdown)
            
            # Content should flow without excessive spacing
            paragraphs = [p for p in markdown.split("\n\n") if p.strip()]
            self.assertTrue(len(paragraphs) >= 3)  # At least 3 paragraphs (title, before image, after image)
    
    @patch('requests.get')
    def test_fetch_content(self, mock_get):
        """Test fetching content from a URL without downloading"""
        # Setup the mock
        mock_response = MagicMock()
        mock_response.text = self.sample_html
        mock_response.encoding = 'utf-8'
        mock_get.return_value = mock_response
        
        # Test basic content fetching
        content = fetch_content("https://example.com")
        self.assertIsNotNone(content)
        assert content is not None
        self.assertIn("Test Article", content)
        self.assertIn("This is a test paragraph", content)
        self.assertIn("a link", content)
        
        # Test with image removal
        content = fetch_content("https://example.com", ignore_images=True)
        self.assertIsNotNone(content)
        assert content is not None
        self.assertNotIn("Test Image", content)
        
        # Test with link removal
        content = fetch_content("https://example.com", ignore_links=True)
        self.assertIsNotNone(content)
        assert content is not None
        self.assertIn("a link", content)  # Text of link should remain
        self.assertNotIn("https://example.com", content)  # URL should be removed
        
        # Test with extra heading space
        content = fetch_content("https://example.com", extra_heading_space="2,3")
        self.assertIsNotNone(content)
        assert content is not None
        self.assertTrue(content.count("\n\n\n## Section Heading") > 0 or content.count("\n\n\n##Section Heading") > 0)
        
        # Test with request failure
        mock_get.side_effect = Exception("Connection error")
        content = fetch_content("https://example.com")
        self.assertIsNone(content)

    @patch('mdscraper.core.scraper.fetch_content')
    @patch('mdscraper.core.scraper.save_markdown_to_file')
    def test_title_extraction_with_prepended_source(self, mock_save, mock_fetch):
        """Test that title is correctly extracted even when source link is prepended"""
        # Create a URL file
        url_file = os.path.join(self.test_dir, "title_test_urls.txt")
        with open(url_file, 'w') as f:
            f.write("https://example.com/article")

        output_dir = os.path.join(self.test_dir, "title_test_outputs")
        
        # Create markdown with source link prepended
        markdown_with_source = "https://example.com/article\n\n# Test Article Title\n\nThis is the content."
        mock_fetch.return_value = markdown_with_source
        mock_save.return_value = 1.0
        
        # Test title extraction with prepended source link
        with patch('os.path.exists') as mock_exists:
            # Make sure we don't actually create files
            mock_exists.return_value = False
            
            # Capture calls to save_markdown_to_file to check filenames
            process_url_file(url_file, output_dir=output_dir, prepend_source_link=True)
            
            # Check that the saved filename contains the title
            filename_used = mock_save.call_args[0][1]
            self.assertIn("Test Article Title", filename_used)
            self.assertNotIn("https", filename_used)  # URL should not be in filename

        # Test fallback when no h1 tag is found
        markdown_without_h1 = "https://example.com/article\n\nThis is content without an h1 tag."
        mock_fetch.return_value = markdown_without_h1
        
        with patch('os.path.exists') as mock_exists:
            mock_exists.return_value = False
            
            process_url_file(url_file, output_dir=output_dir, prepend_source_link=True)
            
            # Check that the fallback filename is used
            filename_used = mock_save.call_args[0][1]
            self.assertIn("Article_article", filename_used)

if __name__ == '__main__':
    unittest.main() 