#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Specific test for the empty lines bug fix after image removal.
This script creates a simple HTML file with images and empty paragraphs,
then tests if the MDScraper correctly removes images without leaving excessive empty lines.
"""

import os
import sys

# Add the parent directory to the Python path for proper imports
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

import tempfile
from bs4 import BeautifulSoup
from mdscraper.core.scraper import fetch_and_convert_to_markdown
from unittest.mock import patch, MagicMock

def create_test_html():
    """Create a test HTML file with various image scenarios"""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Test Empty Lines</title>
    </head>
    <body>
        <div class="content">
            <h1>Test Document</h1>
            
            <p>This is a paragraph before an image.</p>
            
            <p><img src="image1.jpg" alt="Image 1"></p>
            
            <p>This is a paragraph between two images.</p>
            
            <p><img src="image2.jpg" alt="Image 2"></p>
            
            <p></p>
            
            <p>This is a paragraph after an empty paragraph.</p>
            
            <div>
                <img src="image3.jpg" alt="Image 3">
            </div>
            
            <p>Text after a div with only an image.</p>
            
            <p>
                Some text with an inline image: <img src="inline.jpg" alt="Inline"> and more text.
            </p>
            
            <h2>Multiple Empty Paragraphs</h2>
            
            <p><img src="multiple1.jpg" alt="Multiple 1"></p>
            <p></p>
            <p></p>
            <p></p>
            
            <p>Text after multiple empty paragraphs and an image.</p>
            
            <p>Final paragraph.</p>
        </div>
    </body>
    </html>
    """
    return html

def test_empty_lines_fix():
    """Test if the fix for empty lines after image removal is working"""
    print("=== Testing empty lines fix after image removal ===")
    
    # Create test HTML
    test_html = create_test_html()
    
    # Mock the requests.get to return our test HTML
    with patch('requests.get') as mock_get:
        mock_response = MagicMock()
        mock_response.text = test_html
        mock_response.encoding = 'utf-8'
        mock_get.return_value = mock_response
        
        # First test without image removal (baseline)
        print("\nTesting with images (baseline)...")
        markdown_with_images, _ = fetch_and_convert_to_markdown("https://example.com", ignore_images=False)
        
        # Save to a file for inspection
        with open('test_with_images.md', 'w', encoding='utf-8') as f:
            f.write(markdown_with_images)
        
        # Now test with image removal
        print("\nTesting with images removed...")
        markdown_without_images, _ = fetch_and_convert_to_markdown("https://example.com", ignore_images=True)
        
        # Save to a file for inspection
        with open('test_without_images.md', 'w', encoding='utf-8') as f:
            f.write(markdown_without_images)
    
    # Check for excessive newlines
    excessive_newlines = '\n\n\n\n'
    if excessive_newlines in markdown_without_images:
        print("❌ FAIL: Found excessive newlines (4 or more consecutive) after image removal")
        
        # Get the context around the excessive newlines
        start = markdown_without_images.find(excessive_newlines) - 50
        end = markdown_without_images.find(excessive_newlines) + 50
        start = max(0, start)
        end = min(len(markdown_without_images), end)
        
        print("\nContext around excessive newlines:")
        print("..." + markdown_without_images[start:end] + "...")
        
        return False
    else:
        # Check for three consecutive newlines
        three_newlines = '\n\n\n'
        count_three_newlines = markdown_without_images.count(three_newlines)
        if count_three_newlines > 0:
            print(f"⚠️ Warning: Found {count_three_newlines} instances of three consecutive newlines")
            # This is a lesser issue, so we don't fail the test for it
        
        print("✅ PASS: No excessive newlines found after image removal")
        
        # Verify paragraphs flow correctly
        paragraphs = [p for p in markdown_without_images.split('\n\n') if p.strip()]
        
        # Check if "paragraph before" and "paragraph between" are properly connected
        found_proper_flow = False
        for i in range(len(paragraphs) - 1):
            if "paragraph before" in paragraphs[i] and "paragraph between" in paragraphs[i+1]:
                found_proper_flow = True
                break
        
        if not found_proper_flow:
            print("⚠️ Warning: Text flow might not be optimal after image removal")
        else:
            print("✅ PASS: Paragraphs flow correctly after image removal")
        
        return True

if __name__ == "__main__":
    result = test_empty_lines_fix()
    print("\nTest result:", "PASS" if result else "FAIL")
    
    print("\nFor manual inspection:")
    print("1. Check 'test_with_images.md' to see the original markdown with images")
    print("2. Check 'test_without_images.md' to see the markdown with images removed")
    print("3. Compare the files to ensure proper whitespace handling") 