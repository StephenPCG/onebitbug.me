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

FEED_ATOM = 'feed/atom.xml'
FEED_ALL_ATOM = 'feed/all.atom.xml'
CATEGORY_FEED_ATOM = 'feed/%s.atom.xml'
FEED_RSS = None
FEED_ALL_RSS = None
CATEGORY_FEED_RSS = None
FEED_MAX_ITEMS = 5
