#!/usr/bin/env python
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring
import unittest

from mdscraper.cli import create_cli_parser
from mdscraper.core.scraper import scraper_cli

class CliTests(unittest.TestCase):

    def test_config_param(self):
        """Testing the CLI parser"""
        parser = create_cli_parser()
        with self.assertRaises(SystemExit) as cm:
            parser.parse_args(['-h'])
        self.assertEqual(cm.exception.code, 0)

    def test_cli_basic(self):
        """Testing the CLI with basic options"""
        parser = create_cli_parser()
        args = parser.parse_args(['--url', 'https://example.com', '--output', 'cli_basic.md'])
        scraper_cli(**vars(args))
