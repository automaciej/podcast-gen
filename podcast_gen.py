#!/usr/bin/env python3
# coding: utf-8
# vim:set ts=2 sts=2 sw=2:
#
# Podcast feed structure based on:
# http://www.podcast411.com/howto_1.html

"""Podcast generator: Point it at a directory with MP3 files.

The tool is intended to generate podcasts in subdirectories of public_html and
it can be used with no configuration.

TODO: Better support for different file types: _IsThisAnAudioFile
"""

from email.utils import formatdate
from xml.etree import ElementTree as ET
import argparse
import datetime
import getpass
import logging
import mutagen.id3
import os
import socket
import time
import urllib.parse
import xml.dom.minidom

CHANNEL_FIELDS = {
    "channel": ('title', 'description', 'link', 'language',
                'webMaster', 'docs', ),
    "iTunes": ('author', 'subtitle', 'summary', 'explicit'),
}
DEFAULT_FEED_NAME = 'feed.xml'

def GenPubDate(dtime):
  tpl = dtime.timetuple()
  timestamp = time.mktime(tpl)
  return formatdate(timestamp)


def FormatDescription(tag):
  """The MP3 file might have a comment field and/or a description field."""
  description = None
  comment = None
  if 'TXXX:DESCRIPTION' in tag:
    description = '\n'.join(tag['TXXX:DESCRIPTION'].text)
  if 'TXXX:COMMENT' in tag:
    comment = '\n'.join(tag['TXXX:COMMENT'].text)
  if description and comment and description == comment:
    return description
  elif description:
    return description
  elif comment:
    return comment
  else:
    return ''


def _GetPathAfterPublicHtml(p):
  if 'public_html' not in p:
    return p
  accumulator = []
  while True:
    head, tail = os.path.split(p)
    if tail == 'public_html':
      break
    accumulator.insert(0, tail)
    p = head
  return os.path.join(*accumulator)


def ComposeConfig(local_path, base_host, username):
  """Returns a ConfigParser object with a guessed config.

  Ideally this function won't access the machine, but only compose
  a configuration based on a set of input fields.

  Args:
    directory: A directory on local disk with mp3 files.
  """
  base_dir_name = os.path.split(local_path)[1]
  under_public_html = _GetPathAfterPublicHtml(local_path)
  config = {'general': {}, 'channel': {}, 'iTunes': {}}
  config['general']['input_dir'] = local_path
  config['general']['output_file'] = os.path.join(local_path, DEFAULT_FEED_NAME)
  config['general']['base_host'] = base_host
  config['general']['base_url_path'] = '/~%s/%s' % (username, under_public_html)
  config['general']['base_url'] = 'http://%s/~%s/%s' % (
      base_host, username, under_public_html)
  config['general']['feed_url'] = (
      config['general']['base_url'] + '/' + DEFAULT_FEED_NAME)
  config['channel']['title'] = base_dir_name.title()
  config['channel']['description'] = 'Podcast generated from %r' % local_path
  # What if the file doesn't exist?
  config['iTunes']['image'] = 'http://%s/~%s/%s/cover.jpg' % (
      base_host, username, under_public_html)
  return config


class Podcast(object):
  """Represents a podcast."""

  def __init__(self, config):
    self.config = config

    self.input_dir = self.config["general"]["input_dir"]
    self.output_file = self.config["general"]["output_file"]
    self.rss = None

  def _IsThisAnAudioFile(self, abs_path):
    return abs_path.endswith(".mp3")

  def GetBaseEtree(self, config):
    """Compose the base Etree with everything except the specific episodes."""
    rss = ET.Element("rss")
    rss.set(
        "xmlns:itunes",
        "http://www.itunes.com/dtds/podcast-1.0.dtd")
    rss.set("version", "2.0")
    channel = ET.SubElement(rss, "channel")
    for section, prefix in (("channel", ""), ("iTunes", "itunes:")):
      for field in CHANNEL_FIELDS[section]:
        content = config[section].get(field)
        if content is not None:
          e = ET.SubElement(channel, "%s%s" % (prefix, field))
          e.text = content
    pubDate = ET.SubElement(channel, "pubDate")
    pubDate.text = formatdate()

    # iTunes stuff
    image = ET.SubElement(channel, "itunes:image")
    image.set("href", config["iTunes"].get("image"))
    category = ET.SubElement(channel, "itunes:category")
    category.set("text", config["iTunes"].get("category") or 'Uncategorized')
    owner = ET.SubElement(channel, "itunes:owner")
    owner_email = ET.SubElement(owner, "itunes:email")
    owner_email.text = config["iTunes"].get("owner_email") or 'no email'
    owner_name = ET.SubElement(owner, "itunes:name")
    owner_name.text = config["iTunes"].get("owner_name") or 'no owner name'

    return rss

  def GetMetadata(self, abs_file_path):
    metadata = {
        'title': os.path.split(abs_file_path)[1],
        'description': None,
        'artist': None,
    }
    try:
      id3tag = mutagen.id3.Open(abs_file_path)
    except mutagen.id3._util.ID3NoHeaderError as exc:
      logging.warning("Couldn't read %r", abs_file_path)
      return metadata
    desc_from_tag = FormatDescription(id3tag)
    if desc_from_tag:
      metadata['description'] = desc_from_tag
    if 'TPE1' in id3tag:
      metadata['artist'] = ' '.join(id3tag['TPE1'].text)
    if 'TIT2' in id3tag:
      metadata['title'] = ' '.join(id3tag['TIT2'].text)
    return metadata

  def Process(self):
    self.rss = self.GetBaseEtree(self.config)
    channel = self.rss.find('channel')
    audio_base_host = self.config["general"]["base_host"]
    audio_base_url_path = self.config["general"]["base_url_path"]

    count = 0
    for rel_f in sorted(os.listdir(self.input_dir)):
      abs_file_path = os.path.join(self.input_dir, rel_f)
      if self._IsThisAnAudioFile(abs_file_path):
        logging.info('Adding %r to the feed', abs_file_path)
        metadata = self.GetMetadata(abs_file_path)
        basename = os.path.basename(abs_file_path)
        item = ET.SubElement(channel, "item")
        title = ET.SubElement(item, "title")
        if metadata['title']:
          title.text = metadata['title']
        audio_url = (
            "http://"
            + audio_base_host
            + urllib.parse.quote(audio_base_url_path + "/" + basename))
        # If we wanted to link to a page describing this file.
        # link = ET.SubElement(item, "link")
        # link.text = audio_url
        guid = ET.SubElement(item, "guid")
        guid.text = audio_url
        desc_tag = ET.SubElement(item, "description")
        description = []
        if metadata['description']:
          description.append(metadata['description'])
        if metadata['artist']:
          description.append('(by %s)' % metadata['artist'])
        description.append(u'(file name: %s)' % basename)
        desc_tag.text = '\n'.join(description)
        enc = ET.SubElement(item, "enclosure")
        enc.set("url", audio_url)
        stat_info = os.stat(abs_file_path)
        enc.set("length", str(stat_info.st_size))
        enc.set("type", "audio/mpeg")
        cat = ET.SubElement(item, "category")
        cat.text = "Podcasts"
        # pubDate is based on the last file modification time.
        pubDate = ET.SubElement(item, "pubDate")
        pubDate.text = GenPubDate(datetime.datetime.fromtimestamp(
            stat_info.st_mtime))
        count += 1

    if not count:
      logging.warning('No .mp3 files found.')

  def _PrettifyXmlString(self, xml_as_string):
    """Prettify an XML string."""
    # This rewriting is a bit silly, but elementtree does not have a pretty
    # print function.
    xml_tree = xml.dom.minidom.parseString(xml_as_string)
    xml_as_string = xml_tree.toprettyxml()
    xml_as_string = xml_as_string.encode("utf-8")
    return xml_as_string

  def Write(self, pretty=False):
    """Write podcast feed to disk."""
    serialized = ET.tostring(self.rss, encoding="UTF-8")

    if pretty:
      serialized = self._PrettifyXmlString(serialized)

    with open(self.output_file, "w") as file_descriptor:
      logging.info('Writing to %r', self.output_file)
      file_descriptor.write(str(serialized.decode('utf-8')))

  def GetFeedUrl(self):
    """Returns the external URL of the feed."""
    return self.config['general']['feed_url']


def main():
  logging.basicConfig(level=logging.DEBUG)
  parser = argparse.ArgumentParser()
  parser.add_argument("input_dir")
  parser.add_argument("-p", "--pretty",
                      default=False,
                      action='store_true',
                      help="Generate pretty XML")
  parser.add_argument("--title", help="Podcast title", default="")
  parser.add_argument("--base_url", default="",
                      help=("Base URL of the directory as viewed from the "
                            "Internet, like http://example.com/foo/bar. This "
                            "option is useful when the feed is generated on a "
                            "different host than the serving host."))
  args = parser.parse_args()
  username = getpass.getuser()
  input_dir = os.path.abspath(args.input_dir)
  host_name = socket.getfqdn()
  config = ComposeConfig(input_dir, host_name, username)
  if args.title:
    config['channel']['title'] = args.title
  if args.base_url:
    parsed_url = urllib.parse.urlparse(args.base_url)
    config['general']['base_url_path'] = parsed_url.path
    config['general']['base_url'] = args.base_url
    config['general']['feed_url'] = args.base_url + '/' + DEFAULT_FEED_NAME
    config['general']['base_host'] = parsed_url.netloc
    config['general']['image'] = args.base_url + '/cover.jpg'
  podcast = Podcast(config)
  podcast.Process()
  podcast.Write(args.pretty)
  feed_url = podcast.GetFeedUrl()
  logging.info('Feed URL: %r', feed_url)


if __name__ == '__main__':
  main()
