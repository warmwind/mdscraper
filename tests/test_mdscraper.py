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
from mdscraper.core.scraper import fetch_and_convert_to_markdown, process_single_url, process_url_file, find_content_container, add_newlines_before_headings

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
        markdown, title = fetch_and_convert_to_markdown("https://example.com", debug=False)
        self.assertIsNotNone(markdown)
        self.assertIn("# Test Article", markdown)
        self.assertIn("This is a test paragraph", markdown)
        self.assertIn("![Test Image]", markdown)
        self.assertIn("Section Heading", markdown)
        
        # Test with image removal
        markdown, title = fetch_and_convert_to_markdown("https://example.com", ignore_images=True)
        self.assertIsNotNone(markdown)
        self.assertNotIn("![Test Image]", markdown)
        self.assertNotIn("![Section Image]", markdown)
        
        # Test with link removal
        markdown, title = fetch_and_convert_to_markdown("https://example.com", ignore_links=True)
        self.assertIsNotNone(markdown)
        self.assertNotIn("](https://example.com)", markdown)
        self.assertIn("a link", markdown)
        
        # Test with extra heading space
        markdown, title = fetch_and_convert_to_markdown("https://example.com", extra_heading_space="2,3")
        self.assertIsNotNone(markdown)
        self.assertTrue(markdown.count("\n\n\n## Section Heading") > 0 or markdown.count("\n\n\n##Section Heading") > 0)
    
    @patch('mdscraper.core.scraper.fetch_and_convert_to_markdown')
    @patch('mdscraper.core.scraper.save_markdown_to_file')
    def test_process_single_url(self, mock_save, mock_fetch):
        """Test processing a single URL"""
        # Setup mocks
        mock_fetch.return_value = ("# Test Markdown", "Test Title")
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
        mock_fetch.assert_called_with("https://example.com", debug=True, ignore_images=False, ignore_links=False, extra_heading_space=None)
        
        # Test with options
        mock_fetch.reset_mock()
        result = process_single_url("https://example.com", output_file, ignore_images=True, ignore_links=True, extra_heading_space="all")
        mock_fetch.assert_called_with("https://example.com", debug=False, ignore_images=True, ignore_links=True, extra_heading_space="all")
        
        # Test failure case
        mock_fetch.return_value = (None, None)
        result = process_single_url("https://example.com", output_file)
        self.assertFalse(result)
    
    @patch('mdscraper.core.scraper.fetch_and_convert_to_markdown')
    @patch('mdscraper.core.scraper.save_markdown_to_file')
    def test_process_url_file(self, mock_save, mock_fetch):
        """Test processing multiple URLs from a file"""
        # Create a test URL file
        url_file = os.path.join(self.test_dir, "urls.txt")
        with open(url_file, 'w') as f:
            f.write("https://example.com/1\nhttps://example.com/2\n")
        
        output_dir = os.path.join(self.test_dir, "outputs")
        
        # Setup mock for successful fetches
        mock_fetch.return_value = ("# Test Markdown", "Test Title")
        mock_save.return_value = 1.5  # 1.5 KB file size
        
        # Test with default options
        process_url_file(url_file, output_dir=output_dir)
        self.assertEqual(mock_fetch.call_count, 2)
        self.assertEqual(mock_save.call_count, 2)
        
        # Check if the output directory was created
        self.assertTrue(os.path.exists(output_dir))
        
        # Test with various options
        mock_fetch.reset_mock()
        mock_save.reset_mock()
        process_url_file(url_file, output_dir=output_dir, debug=True, ignore_images=True, ignore_links=True, extra_heading_space="1,2")
        self.assertEqual(mock_fetch.call_count, 2)
        mock_fetch.assert_called_with("https://example.com/2", debug=True, ignore_images=True, ignore_links=True, extra_heading_space="1,2")
        
        # Test handling failure cases
        mock_fetch.reset_mock()
        mock_save.reset_mock()
        mock_fetch.side_effect = [(None, None), ("# Test Markdown", "Test Title")]
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
            markdown, _ = fetch_and_convert_to_markdown("https://example.com", ignore_images=True)
            
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

if __name__ == '__main__':
    unittest.main() 