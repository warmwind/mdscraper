#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Integration tests for MDScraper - test all features with real-world URLs.
This script provides a quick way to verify that all features are working correctly.
"""

import os
import sys

# Add the parent directory to the Python path for proper imports
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

import argparse
import time
from mdscraper.core.scraper import process_single_url, process_url_file

def test_single_url_basic():
    """Test basic functionality with a single URL"""
    print("\n=== Testing basic functionality with Python.org ===")
    url = "https://www.python.org/doc/"
    output_file = "python_basic.md"
    
    if os.path.exists(output_file):
        os.remove(output_file)
    
    result = process_single_url(url, output_file)
    if result and os.path.exists(output_file):
        print(f"✅ Basic functionality test PASSED. Output saved to {output_file}")
        return True
    else:
        print("❌ Basic functionality test FAILED")
        return False

def test_single_url_no_images():
    """Test functionality with images removed"""
    print("\n=== Testing with images removed ===")
    url = "https://www.python.org/doc/"
    output_file = "python_without_images.md"
    
    if os.path.exists(output_file):
        os.remove(output_file)
    
    result = process_single_url(url, output_file, ignore_images=True)
    if result and os.path.exists(output_file):
        print(f"✅ No images test PASSED. Output saved to {output_file}")
        
        # Basic validation - check if markdown image tags are absent
        with open(output_file, 'r', encoding='utf-8') as f:
            content = f.read()
            if '![' in content:
                print("⚠️ Warning: Image tags still found in output despite ignore_images=True")
                return False
        return True
    else:
        print("❌ No images test FAILED")
        return False

def test_single_url_no_links():
    """Test functionality with links removed"""
    print("\n=== Testing with links removed ===")
    url = "https://www.python.org/doc/"
    output_file = "python_no_links.md"
    
    if os.path.exists(output_file):
        os.remove(output_file)
    
    result = process_single_url(url, output_file, ignore_links=True)
    if result and os.path.exists(output_file):
        print(f"✅ No links test PASSED. Output saved to {output_file}")
        
        # Basic validation - check if markdown link tags are absent
        with open(output_file, 'r', encoding='utf-8') as f:
            content = f.read()
            # Look for []() pattern
            if '](' in content:
                print("⚠️ Warning: Link tags still found in output despite ignore_links=True")
                return False
        return True
    else:
        print("❌ No links test FAILED")
        return False

def test_single_url_with_heading_space():
    """Test functionality with extra heading space"""
    print("\n=== Testing with extra heading space ===")
    url = "https://www.python.org/doc/"
    output_file = "python_with_headings.md"
    
    if os.path.exists(output_file):
        os.remove(output_file)
    
    result = process_single_url(url, output_file, extra_heading_space="all")
    if result and os.path.exists(output_file):
        print(f"✅ Extra heading space test PASSED. Output saved to {output_file}")
        
        # Validate that consecutive headings have extra spacing
        with open(output_file, 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.split('\n')
            heading_lines = []
            for i, line in enumerate(lines):
                if line.startswith('#') and len(line) > 1 and line[1] in [' ', '#']:
                    heading_lines.append(i)
            
            # Check spacing between consecutive headings
            for i in range(1, len(heading_lines)):
                curr_heading = heading_lines[i]
                prev_heading = heading_lines[i-1]
                if curr_heading - prev_heading <= 2:  # Should have at least 3 lines between
                    print("⚠️ Warning: Heading spacing not correctly applied")
                    return False
        return True
    else:
        print("❌ Extra heading space test FAILED")
        return False

def test_multiple_urls():
    """Test processing multiple URLs from a file"""
    print("\n=== Testing multiple URLs processing ===")
    
    # Create a sample URL file
    url_file = "sample_urls.txt"
    with open(url_file, 'w', encoding='utf-8') as f:
        f.write("https://www.python.org/doc/\n")
        f.write("https://docs.python.org/3/library/index.html\n")
    
    output_dir = "test_batch_output"
    if os.path.exists(output_dir):
        import shutil
        shutil.rmtree(output_dir)
    
    process_url_file(url_file, output_dir=output_dir)
    
    if os.path.exists(output_dir) and len(os.listdir(output_dir)) > 0:
        print(f"✅ Multiple URLs test PASSED. Outputs saved to {output_dir}/")
        return True
    else:
        print("❌ Multiple URLs test FAILED")
        return False

def test_combined_features():
    """Test combining multiple features together"""
    print("\n=== Testing combined features (no images, no links, heading space) ===")
    url = "https://www.python.org/doc/"
    output_file = "python_combined.md"
    
    if os.path.exists(output_file):
        os.remove(output_file)
    
    result = process_single_url(url, output_file, ignore_images=True, ignore_links=True, extra_heading_space="2,3")
    if result and os.path.exists(output_file):
        print(f"✅ Combined features test PASSED. Output saved to {output_file}")
        
        # Validate combined features
        with open(output_file, 'r', encoding='utf-8') as f:
            content = f.read()
            if '![' in content:
                print("⚠️ Warning: Image tags found despite ignore_images=True")
                return False
            if '](' in content:
                print("⚠️ Warning: Link tags found despite ignore_links=True")
                return False
        return True
    else:
        print("❌ Combined features test FAILED")
        return False

def test_empty_paragraphs():
    """Test that the image removal doesn't leave empty paragraphs"""
    print("\n=== Testing image removal with empty paragraphs ===")
    
    # Use a URL known to have images with empty paragraphs
    url = "https://docs.python.org/3/tutorial/index.html"
    output_with_images = "python_docs_with_images.md"
    output_without_images = "python_docs_without_images.md"
    
    # First fetch with images
    process_single_url(url, output_with_images)
    
    # Then fetch without images
    process_single_url(url, output_without_images, ignore_images=True)
    
    if os.path.exists(output_with_images) and os.path.exists(output_without_images):
        # Compare both files to see if there are excessive empty lines
        with open(output_without_images, 'r', encoding='utf-8') as f:
            content = f.read()
            if '\n\n\n\n' in content:
                print("⚠️ Warning: Found more than three consecutive newlines, which suggests empty paragraphs")
                return False
            print(f"✅ Empty paragraphs test PASSED.")
            return True
    else:
        print("❌ Empty paragraphs test FAILED")
        return False

def main():
    parser = argparse.ArgumentParser(description='Integration tests for MDScraper')
    parser.add_argument('--test', choices=['all', 'basic', 'images', 'links', 'headings', 'batch', 'combined', 'empty'],
                       help='Specific test to run', default='all')
    
    args = parser.parse_args()
    
    all_tests = {
        'basic': test_single_url_basic,
        'images': test_single_url_no_images,
        'links': test_single_url_no_links,
        'headings': test_single_url_with_heading_space,
        'batch': test_multiple_urls,
        'combined': test_combined_features,
        'empty': test_empty_paragraphs
    }
    
    start_time = time.time()
    
    if args.test == 'all':
        print("Running all integration tests...")
        results = []
        
        for test_name, test_func in all_tests.items():
            print(f"\nRunning test: {test_name}")
            try:
                result = test_func()
                results.append((test_name, result))
            except Exception as e:
                print(f"Error in test {test_name}: {e}")
                results.append((test_name, False))
        
        # Print summary
        print("\n=== Test Summary ===")
        success_count = sum(1 for _, r in results if r)
        total = len(results)
        for test_name, result in results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status} - {test_name}")
        
        print(f"\nResult: {success_count}/{total} tests passed")
        print(f"Time taken: {time.time() - start_time:.2f} seconds")
        
        if success_count < total:
            return 1
    else:
        if args.test in all_tests:
            success = all_tests[args.test]()
            return 0 if success else 1
        else:
            print(f"Unknown test: {args.test}")
            return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 