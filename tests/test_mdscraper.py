#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys

import unittest
import tempfile
import shutil
from unittest.mock import patch, MagicMock
from bs4 import BeautifulSoup

from mdscraper.core.scraper import MdScraper

# Add the parent directory to the Python path for proper imports
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

class TestMDScraper(unittest.TestCase):
    
    def setUp(self):
        # Create a temporary directory for test files
        self.test_dir = tempfile.mkdtemp()

        # Create a MD Scraper object with default options
        self.mds = MdScraper()
        
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
        content = self.mds.find_content_container(soup)
        self.assertIsNotNone(content)
        self.assertEqual(content.name, 'article')
        self.assertEqual(content.get('class'), ['content'])
    
    def test_add_newlines_before_headings(self):
        """Test adding extra spacing before headings"""
        markdown = "# Title\nSome text\n## Section\nMore text\n### Subsection\nEven more text"
        
        # Test 'all' heading levels
        self.mds.options['extra_heading_space'] = 'all'
        result = self.mds.add_newlines_before_headings(markdown)
        # We expect one ## heading but there might be more in different implementations
        self.assertGreaterEqual(result.count('\n\n\n##'), 1)
        self.assertGreaterEqual(result.count('\n\n\n###'), 1)
        
        # Test specific heading levels
        self.mds.options['extra_heading_space'] = '2'
        result = self.mds.add_newlines_before_headings(markdown)
        self.assertGreaterEqual(result.count('\n\n\n##'), 1)
        self.assertEqual(result.count('\n\n\n###'), 0)

        # Reset MD Scraper options to default
        self.mds.options = self.mds.get_default_options()
    
    @patch('requests.get')
    def test_fetch_and_convert_to_markdown(self, mock_get):
        """Test fetching and converting HTML to Markdown"""
        # Setup the mock
        mock_response = MagicMock()
        mock_response.text = self.sample_html
        mock_response.encoding = 'utf-8'
        mock_get.return_value = mock_response
        
        # Test basic conversion
        content, title, soup = self.mds._fetch_content("https://example.com")
        markdown = self.mds.convert_to_markdown(content, title)
        self.assertIsNotNone(markdown)
        assert markdown is not None  # Type assertion
        self.assertIn("# Test Article", markdown)
        self.assertIn("This is a test paragraph", markdown)
        self.assertIn("![Test Image]", markdown)
        self.assertIn("Section Heading", markdown)
        
        # Test with image removal
        self.mds.options['no_images'] = True
        content, title, soup = self.mds._fetch_content("https://example.com")
        markdown = self.mds.convert_to_markdown(content, title)
        self.assertIsNotNone(markdown)
        assert markdown is not None  # Type assertion
        self.assertNotIn("![Test Image]", markdown)
        self.assertNotIn("![Section Image]", markdown)

        # Reset MD Scraper options to default
        self.mds.options = self.mds.get_default_options()
        
        # Test with link removal
        self.mds.options['no_links'] = True
        content, title, soup = self.mds._fetch_content("https://example.com")
        markdown = self.mds.convert_to_markdown(content, title)
        self.assertIsNotNone(markdown)
        assert markdown is not None  # Type assertion
        self.assertNotIn("](https://example.com)", markdown)
        self.assertIn("a link", markdown)

        # Reset MD Scraper options to default
        self.mds.options = self.mds.get_default_options()
        
        # Test with extra heading space
        self.mds.options['extra_heading_space'] = '2,3'
        content, title, soup = self.mds._fetch_content("https://example.com")
        markdown = self.mds.convert_to_markdown(content, title)
        self.assertIsNotNone(markdown)
        assert markdown is not None  # Type assertion
        self.assertTrue(markdown.count("\n\n\n## Section Heading") > 0 or markdown.count("\n\n\n##Section Heading") > 0)

        # Reset MD Scraper options to default
        self.mds.options = self.mds.get_default_options()
    
    @patch.object(MdScraper, 'fetch_content')
    @patch('mdscraper.core.scraper.save_markdown_to_file')
    def test_process_single_url(self, mock_save, mock_fetch):
        """Test processing a single URL"""
        # Setup mocks
        mock_fetch.return_value = "# Test Markdown"
        mock_save.return_value = 1.5  # 1.5 KB file size
        
        output_file = os.path.join(self.test_dir, "output.md")
        
        # Test successful processing
        result = self.mds.process_single_url("https://example.com", output_file)
        self.assertTrue(result)
        mock_fetch.assert_called_once()
        mock_save.assert_called_once()
        
        # Test with debug flag
        mock_fetch.reset_mock()
        mock_save.reset_mock()
        self.mds.options['debug'] = True
        result = self.mds.process_single_url("https://example.com", output_file)
        self.assertTrue(result)
        mock_fetch.assert_called_with("https://example.com")

        # Reset MD Scraper options to default
        self.mds.options = self.mds.get_default_options()
        
        # Test with options including prepend_source_link
        mock_fetch.reset_mock()
        self.mds.options['no_images'] = True
        self.mds.options['no_links'] = True
        self.mds.options['extra_heading_space'] = "all"
        self.mds.options['prepend_source_link'] = True
        result = self.mds.process_single_url("https://example.com", output_file)
        mock_fetch.assert_called_with("https://example.com")

        # Reset MD Scraper options to default
        self.mds.options = self.mds.get_default_options()
        
        # Test failure case
        mock_fetch.return_value = (None)
        result = self.mds.process_single_url("https://example.com", output_file)
        self.assertFalse(result)
    
    @patch.object(MdScraper, 'fetch_content')
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
        self.mds.process_url_file(url_file, output_dir=output_dir)
        self.assertEqual(mock_fetch.call_count, 2)
        self.assertEqual(mock_save.call_count, 2)
        
        # Check if the output directory was created
        self.assertTrue(os.path.exists(output_dir))
        
        # Test with various options including prepend_source_link
        mock_fetch.reset_mock()
        mock_save.reset_mock()
        self.mds.options['debug'] = True
        self.mds.options['no_images'] = True
        self.mds.options['no_links'] = True
        self.mds.options['extra_heading_space'] = "1,2"
        self.mds.process_url_file(url_file, output_dir=output_dir)
        self.assertEqual(mock_fetch.call_count, 2)
        mock_fetch.assert_called_with("https://example.com/2")

        # Reset MD Scraper options to default
        self.mds.options = self.mds.get_default_options()
        
        # Test handling failure cases
        mock_fetch.reset_mock()
        mock_save.reset_mock()
        mock_fetch.side_effect = [None, "# Test Markdown"]
        self.mds.process_url_file(url_file, output_dir=output_dir)
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
            self.mds.options['no_images'] = True
            markdown = self.mds.fetch_content("https://example.com")
            
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
        
        # Reset MD Scraper options to default
        self.mds.options = self.mds.get_default_options()
    
    @patch('requests.get')
    def test_fetch_content(self, mock_get):
        """Test fetching content from a URL without downloading"""
        # Setup the mock
        mock_response = MagicMock()
        mock_response.text = self.sample_html
        mock_response.encoding = 'utf-8'
        mock_get.return_value = mock_response
        
        # Test basic content fetching
        content = self.mds.fetch_content("https://example.com")
        self.assertIsNotNone(content)
        assert content is not None
        self.assertIn("Test Article", content)
        self.assertIn("This is a test paragraph", content)
        self.assertIn("a link", content)
        
        # Test with image removal
        self.mds.options["no_images"] = True
        content = self.mds.fetch_content("https://example.com")
        self.assertIsNotNone(content)
        assert content is not None
        self.assertNotIn("Test Image", content)

        # Reset MD Scraper options to default
        self.mds.options = self.mds.get_default_options()
        
        # Test with link removal
        self.mds.options["no_links"] = True
        content = self.mds.fetch_content("https://example.com")
        self.assertIsNotNone(content)
        assert content is not None
        self.assertIn("a link", content)  # Text of link should remain
        self.assertNotIn("https://example.com", content)  # URL should be removed

        # Reset MD Scraper options to default
        self.mds.options = self.mds.get_default_options()
        
        # Test with extra heading space
        self.mds.options['extra_heading_space'] = '2,3'
        content = self.mds.fetch_content("https://example.com")
        self.assertIsNotNone(content)
        assert content is not None
        self.assertTrue(content.count("\n\n\n## Section Heading") > 0 or content.count("\n\n\n##Section Heading") > 0)

        # Reset MD Scraper options to default
        self.mds.options = self.mds.get_default_options()
        
        # Test with request failure
        mock_get.side_effect = Exception("Connection error")
        content = self.mds.fetch_content("https://example.com")
        self.assertIsNone(content)

if __name__ == '__main__':
    unittest.main()
