#!/usr/bin/env python
# -*- coding: utf-8 -*- #
from __future__ import unicode_literals

# This file is only used if you use `make publish` or
# explicitly specify it as your config file.

import os
import sys
sys.path.append(os.curdir)
from pelicanconf import *

SITEURL = 'http://onebitbug.me'
RELATIVE_URLS = False

USER_LOGO_URL = SITEURL + '/static/images/pages/snsface.png'

FEED_ATOM = 'feeds/atom.xml'
FEED_ALL_ATOM = 'feeds/all.atom.xml'
CATEGORY_FEED_ATOM = 'feeds/%s.atom.xml'
FEED_RSS = 'feeds/rss.xml'
FEED_ALL_RSS = 'feeds/all.rss.xml'
CATEGORY_FEED_RSS = 'feeds/%s.rss.xml'
FEED_MAX_ITEMS = 10
