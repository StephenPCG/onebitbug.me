#!/usr/bin/env python
# -*- coding: utf-8 -*- #
from __future__ import unicode_literals

AUTHOR = u'Zhang Cheng'
#SITENAME = u'Bugs'
SITEURL = ''

SITENAME = u'May the #! be with you'
DISQUS_SITENAME = 'onebitbug'
GITHUB_URL = 'https://github.com/StephenPCG/'

TIMEZONE = 'Asia/Shanghai'
DEFAULT_LANG = u'zh'

# Uncomment following line if you want document-relative URLs when developing
RELATIVE_URLS = True

# Feed generation is usually not desired when developing
FEED_ALL_ATOM = None
CATEGORY_FEED_ATOM = None
TRANSLATION_FEED_ATOM = None

# Blogroll
#LINKS =  (('Pelican', 'http://getpelican.com/'),
#          ('Python.org', 'http://python.org/'),
#          ('Jinja2', 'http://jinja.pocoo.org/'),
#          ('You can modify those links in your config file', '#'),)

# Social widget
SOCIAL = (('https://github.com/StephenPCG/', 'Github'),)
MENUITEMS = (('Archives', '/archives.html'),
             ('Biography', '/biography/'),
             ('GuestBook', '/guest/'),
             )

DEFAULT_PAGINATION = 5

ARTICLE_URL = '{date:%Y}/{date:%m}/{date:%d}/{slug}/'
ARTICLE_SAVE_AS = '{date:%Y}/{date:%m}/{date:%d}/{slug}/index.html'
YEAR_ARCHIVE_SAVE_AS = '{date:%Y}/index.html'
MONTH_ARCHIVE_SAVE_AS = '{date:%Y}/{date:%m}/index.html'
DAY_ARCHIVE_SAVE_AS = '{date:%Y}/{date:%m}/{date:%d}/index.html'
CATEGORY_URL = 'categories/{slug}.html'
CATEGORY_SAVE_AS = 'categories/{slug}.html'
TAG_URL = 'tags/{slug}.html'
TAG_SAVE_AS = 'tags/{slug}.html'

DEFAULT_DATE_FORMAT = '%Y-%m-%d'

FEED_DOMAIN = SITEURL

