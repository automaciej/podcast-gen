#!/usr/bin/env python3
# coding: utf-8
# vim:set ts=2 sts=2 sw=2:

import unittest
import podcast_gen

class PodcastGenUnitTest(unittest.TestCase):
  """A rudimentary unit test."""

  def testBasicFunctionality(self):
    self.maxDiff = None
    config = {
        'general': {
            'input_dir': '/home/joe/public_html/bar',
            'output_file': '/home/joe/public_html/bar/feed.xml',
            'base_host': 'baz.com',
            'base_url_path': '/~joe/bar',
         },
        'channel': {
            'title': 'Bar',
            'description': "Podcast generated from '/home/joe/public_html/bar'",
         },
        'iTunes': {
          'image': 'http://baz.com/~joe/bar/cover.jpg'
         },
    }
    self.assertEqual(config,
                     podcast_gen.ComposeConfig(
                         "/home/joe/public_html/bar", "baz.com", "joe"))


if __name__ == '__main__':
  unittest.main()
