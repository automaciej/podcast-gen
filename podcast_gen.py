#!/usr/bin/env python
# coding: utf-8
#
# Podcast structure based on:
# http://www.podcast411.com/howto_1.html

from xml.etree import ElementTree as ET
import xml.dom.minidom
import StringIO
import optparse
import ConfigParser
import logging
import os
import tagpy
from email.utils import formatdate
import datetime
import urllib

class Podcast(object):

  CHANNEL_FIELDS = {
      "channel": ('title', 'description', 'link', 'language',
                  'webMaster', 'docs', ),
      "iTunes": ('author', 'subtitle', 'summary', 'explicit'),
  }
  def __init__(self, config_fn):
    config = ConfigParser.SafeConfigParser()
    config.read(config_fn)

    self.input_dir = config.get("general", "input_dir")
    self.output_file = config.get("general", "output_file")
    self.rss = ET.Element("rss")
    self.rss.set(
        "xmlns:itunes",
        "http://www.itunes.com/dtds/podcast-1.0.dtd")
    self.rss.set("version", "2.0")
    self.channel = ET.SubElement(self.rss, "channel")
    for section, prefix in (("channel", ""), ("iTunes", "itunes:")):
      for field in self.CHANNEL_FIELDS[section]:
        try:
          content = config.get(section, field)
          content = unicode(content, "utf-8")
          e = ET.SubElement(self.channel, "%s%s" % (prefix, field))
          e.text = content
        except ConfigParser.NoOptionError as e:
          logging.warning("Field %s.%s not found", section, field)

    pubDate = ET.SubElement(self.channel, "pubDate")
    pubDate.text = formatdate()

    # iTunes stuff
    self.image = ET.SubElement(self.channel, "itunes:image")
    self.image.set("href", config.get("iTunes", "image"))
    self.category = ET.SubElement(self.channel, "itunes:category")
    self.category.set("text", config.get("iTunes", "category"))
    self.owner = ET.SubElement(self.channel, "itunes:owner")
    self.owner_email = ET.SubElement(self.owner, "itunes:email")
    self.owner_email.text = config.get("iTunes", "owner_email")
    self.owner_name = ET.SubElement(self.owner, "itunes:name")
    self.owner_name.text = config.get("iTunes", "owner_name")
    
    audio_base_host = config.get("general", "base_host")
    audio_base_url = config.get("general", "base_url")

    # Episodes are traditionally sorted by date. In this case, we're
    # only interested in sorting them the way they are sorted in the
    # directory, and we're faking the dates. To making obvious that the
    # dates are fake, we're setting the year to 1970.
    base_time = datetime.datetime(1970, 1, 1)
    td = datetime.timedelta(1, 0, 0)
    count = 0
    for rel_f in sorted(os.listdir(self.input_dir)):
      f = os.path.join(self.input_dir, rel_f)
      # TODO: better support for file types
      if f.endswith(".mp3"):
        st = os.stat(f)
        basename = os.path.split(f)[1]
        fr = tagpy.FileRef(f)
        t = fr.tag()
        item = ET.SubElement(self.channel, "item")
        title = ET.SubElement(item, "title")
        title.text = t.title
        link = ET.SubElement(item, "link")
        audio_url = (
            "http://"
            + audio_base_host
            + urllib.quote(audio_base_url + "/" + basename))
        link.text = audio_url
        guid = ET.SubElement(item, "guid")
        guid.text = link.text
        desc = ET.SubElement(item, "description")
        desc.text = "by " + t.artist + " (%s)" % basename
        enc = ET.SubElement(item, "enclosure")
        enc.set("url", audio_url)
        enc.set("length", unicode(st.st_size))
        enc.set("type", "audio/mpeg")
        cat = ET.SubElement(item, "category")
        cat.text = "Podcasts"
        # pubDate is based on the last file change time.
        pubDate = ET.SubElement(item, "pubDate")
        pubDate.text = str(base_time + count * td)
        count += 1

  def Print(self, pretty=False):
    # This rewriting is a bit silly, but elementtree does not have a pretty
    # print function.
    s = ET.tostring(self.rss, encoding="UTF-8")
    if pretty:
      x = xml.dom.minidom.parseString(s)
      s = x.toprettyxml()
      s = s.encode("utf-8")
    with open(self.output_file, "w") as fd:
      fd.write(s)


def main():
  logging.basicConfig(level=logging.DEBUG)
  parser = optparse.OptionParser()
  parser.add_option("-c", "--config", dest="config_file")
  parser.add_option("-p", "--pretty", dest="pretty",
                    default=False, action="store_true",
                    help="Generate pretty XML")
  options, args = parser.parse_args()
  p = Podcast(options.config_file)
  p.Print(options.pretty)


if __name__ == '__main__':
  main()
