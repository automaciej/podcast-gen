#!/usr/bin/env python
# coding: utf-8
#
# Podcast feed structure based on:
# http://www.podcast411.com/howto_1.html

from email.utils import formatdate
from xml.etree import ElementTree as ET
import ConfigParser
import datetime
import logging
import mutagen.id3
import optparse
import os
import StringIO
import time
import urllib
import xml.dom.minidom


def GenPubDate(dtime):
  tpl = dtime.timetuple()
  ts = time.mktime(tpl)
  return formatdate(ts)


def FormatDescription(tag):
  """The MP3 file might have a comment field and/or a description field.
  """
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


class Podcast(object):

  CHANNEL_FIELDS = {
      "channel": ('title', 'description', 'link', 'language',
                  'webMaster', 'docs', ),
      "iTunes": ('author', 'subtitle', 'summary', 'explicit'),
  }
  def __init__(self, config_fn):
    self.config = ConfigParser.SafeConfigParser()
    self.config.read(config_fn)

    self.input_dir = self.config.get("general", "input_dir")
    self.output_file = self.config.get("general", "output_file")

  def _IsThisAnAudioFile(self, abs_path):
    return abs_path.endswith(".mp3")

  def Process(self):
    self.rss = ET.Element("rss")
    self.rss.set(
        "xmlns:itunes",
        "http://www.itunes.com/dtds/podcast-1.0.dtd")
    self.rss.set("version", "2.0")
    self.channel = ET.SubElement(self.rss, "channel")
    for section, prefix in (("channel", ""), ("iTunes", "itunes:")):
      for field in self.CHANNEL_FIELDS[section]:
        try:
          content = self.config.get(section, field)
          content = unicode(content, "utf-8")
          e = ET.SubElement(self.channel, "%s%s" % (prefix, field))
          e.text = content
        except ConfigParser.NoOptionError as e:
          logging.warning("Field %s.%s not found", section, field)

    pubDate = ET.SubElement(self.channel, "pubDate")
    pubDate.text = formatdate()

    # iTunes stuff
    self.image = ET.SubElement(self.channel, "itunes:image")
    self.image.set("href", self.config.get("iTunes", "image"))
    self.category = ET.SubElement(self.channel, "itunes:category")
    self.category.set("text", self.config.get("iTunes", "category"))
    self.owner = ET.SubElement(self.channel, "itunes:owner")
    self.owner_email = ET.SubElement(self.owner, "itunes:email")
    self.owner_email.text = self.config.get("iTunes", "owner_email")
    self.owner_name = ET.SubElement(self.owner, "itunes:name")
    self.owner_name.text = self.config.get("iTunes", "owner_name")

    audio_base_host = self.config.get("general", "base_host")
    audio_base_url = self.config.get("general", "base_url")

    count = 0
    for rel_f in sorted(os.listdir(self.input_dir)):
      abs_file_path = os.path.join(self.input_dir, rel_f)
      # TODO: better support for file types
      if self._IsThisAnAudioFile(abs_file_path):
        basename = os.path.basename(abs_file_path)
        basename_u = unicode(basename, 'utf-8')
        id3tag = mutagen.id3.Open(abs_file_path)
        item = ET.SubElement(self.channel, "item")
        title = ET.SubElement(item, "title")
        if 'TIT2' in id3tag:
          title.text = ' '.join(id3tag['TIT2'].text)
        audio_url = (
            "http://"
            + audio_base_host
            + urllib.quote(audio_base_url + "/" + basename))
        # If we wanted to link to a page describing this file.
        # link = ET.SubElement(item, "link")
        # link.text = audio_url
        guid = ET.SubElement(item, "guid")
        guid.text = audio_url
        desc_tag = ET.SubElement(item, "description")
        description = []
        desc_from_tag = FormatDescription(id3tag)
        if desc_from_tag:
          description.append(desc_from_tag)
        if 'TPE1' in id3tag:
          description.append('(by %s)' % ' '.join(id3tag['TPE1'].text))
        description.append(u'(file name: %s)' % basename_u)
        desc_tag.text = '\n'.join(description)
        enc = ET.SubElement(item, "enclosure")
        enc.set("url", audio_url)
        st = os.stat(abs_file_path)
        enc.set("length", unicode(st.st_size))
        enc.set("type", "audio/mpeg")
        cat = ET.SubElement(item, "category")
        cat.text = "Podcasts"
        # pubDate is based on the last file modification time.
        pubDate = ET.SubElement(item, "pubDate")
        pubDate.text = GenPubDate(datetime.datetime.fromtimestamp(st.st_mtime))
        count += 1

    if not count:
      logging.warning('No .mp3 files found.')

  def _PrettifyXmlString(self, xml_as_string):
    # This rewriting is a bit silly, but elementtree does not have a pretty
    # print function.
    x = xml.dom.minidom.parseString(xml_as_string)
    xml_as_string = x.toprettyxml()
    xml_as_string = xml_as_string.encode("utf-8")
    return xml_as_string

  def Write(self, pretty=False):
    serialized = ET.tostring(self.rss, encoding="UTF-8")

    if pretty:
      serialized = self._PrettifyXmlString(serialized)

    with open(self.output_file, "w") as fd:
      fd.write(serialized)


def main():
  logging.basicConfig(level=logging.DEBUG)
  parser = optparse.OptionParser()
  parser.add_option("-c", "--config", dest="config_file")
  parser.add_option("-p", "--pretty", dest="pretty",
                    default=False, action="store_true",
                    help="Generate pretty XML")
  options, args = parser.parse_args()
  p = Podcast(options.config_file)
  p.Process()
  p.Write(options.pretty)


if __name__ == '__main__':
  main()
