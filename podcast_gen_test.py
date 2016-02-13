#!/usr/bin/env python3
# coding: utf-8
# vim:set ts=2 sts=2 sw=2:

import unittest
import podcast_gen

class PodcastGenUnitTest(unittest.TestCase):
  """A rudimentary unit test."""

  def testSubdirectoryOfPublicHtml(self):
    self.maxDiff = None
    config = {
        'general': {
            'input_dir': '/home/joe/public_html/bar',
            'output_file': '/home/joe/public_html/bar/feed.xml',
            'base_url': 'http://baz.com/~joe/bar',
            'feed_url': 'http://baz.com/~joe/bar/feed.xml',
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

  def testSubSubdirectoryOfPublicHtml(self):
    self.maxDiff = None
    config = {
        'general': {
            'input_dir': '/home/joe/public_html/foo/bar',
            'output_file': '/home/joe/public_html/foo/bar/feed.xml',
            'base_url': 'http://baz.com/~joe/foo/bar',
            'feed_url': 'http://baz.com/~joe/foo/bar/feed.xml',
            'base_host': 'baz.com',
            'base_url_path': '/~joe/foo/bar',
         },
        'channel': {
            'title': 'Bar',
            'description': "Podcast generated from '/home/joe/public_html/foo/bar'",
         },
        'iTunes': {
          'image': 'http://baz.com/~joe/foo/bar/cover.jpg'
         },
    }
    self.assertEqual(config,
                     podcast_gen.ComposeConfig(
                         "/home/joe/public_html/foo/bar", "baz.com", "joe"))

  def testGetPathAfterPublicHtml(self):
    self.assertEqual('foo/bar',
        podcast_gen._GetPathAfterPublicHtml('/home/joe/public_html/foo/bar'))


if __name__ == '__main__':
  unittest.main()
