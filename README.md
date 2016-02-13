Podcast Generator
=================

A utility generating a podcast feed based on a config file and a directory with
audio files.

Usage instructions
------------------

1. Get your '.mp3' and 'cover.jpg' files into a directory such as
   `/home/joe/public_html/PodcastName`.  It must be a subdirectory of
   `~/public_html/`
2. This must be on a machine which is also a web server and which serves
   `public_html` under `example.com/~username/...`
3. Run the tool, passing the directory as an argument.
   `podcast_gen.py input_dir`

See `--help` for more instructions.

License
-------

This file is part of podcast-gen.

podcast-gen is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Foobar is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Foobar.  If not, see <http://www.gnu.org/licenses/>.

Dependencies
------------

* Python 3
* python3-mutagen

TODO
----

- use libmagic to determine file formats
- support more file formats
