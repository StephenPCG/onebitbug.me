#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals

# This file is only used if you use `make publish` or
# explicitly specify it as your config file.

import os
import sys
sys.path.append(os.curdir)
from pelicanconf import *
import yaml

try:
    with open("config.yml") as fp:
        PRIVATE_CONFIG = yaml.load(fp.read()).get("PUBLISH", dict())
except:
    PRIVATE_CONFIG = dict()

SITEURL = 'https://onebitbug.me'
RELATIVE_URLS = False

FEED_ATOM = 'feed/atom.xml'
FEED_ALL_ATOM = 'feed/all.atom.xml'
CATEGORY_FEED_ATOM = 'feed/%s.atom.xml'
FEED_RSS = None
FEED_ALL_RSS = None
CATEGORY_FEED_RSS = None
FEED_MAX_ITEMS = 5

GOOGLE_ANALYTICS = 'UA-21159450-1'

# vim:ai:et:sts=4:sw=4:
