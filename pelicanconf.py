#!/usr/bin/env python
# -*- coding: utf-8 -*- #
from __future__ import unicode_literals

AUTHOR = u'Stephen Zhang'
SITEURL = ''

SITENAME = u'May the #! be with you'
DISQUS_SITENAME = 'onebitbug'
GITHUB_URL = 'https://github.com/StephenPCG/'

TIMEZONE = 'Asia/Shanghai'
DEFAULT_LANG = u'zh'

# Uncomment following line if you want document-relative URLs when developing
RELATIVE_URLS = True

# Blogroll
#LINKS =  (('Pelican', 'http://getpelican.com/'),
#          ('Python.org', 'http://python.org/'),
#          ('Jinja2', 'http://jinja.pocoo.org/'),
#          ('You can modify those links in your config file', '#'),)

# Social widget
SOCIAL = (('https://github.com/StephenPCG/', 'Github'),)
MENUITEMS = (('Archives', '/archives.html'),
             ('Biography', '/pages/biography/'),
             ('GuestBook', '/pages/guest/'),
             )

DEFAULT_PAGINATION = 5

ARTICLE_URL = 'posts/{date:%Y}/{date:%m}/{date:%d}/{slug}/'
ARTICLE_SAVE_AS = 'posts/{date:%Y}/{date:%m}/{date:%d}/{slug}/index.html'
YEAR_ARCHIVE_SAVE_AS = 'posts/{date:%Y}/index.html'
MONTH_ARCHIVE_SAVE_AS = 'posts/{date:%Y}/{date:%m}/index.html'
DAY_ARCHIVE_SAVE_AS = 'posts/{date:%Y}/{date:%m}/{date:%d}/index.html'
CATEGORY_URL = 'categories/{slug}/'
CATEGORY_SAVE_AS = 'categories/{slug}/index.html'
TAG_URL = 'tags/{slug}/'
TAG_SAVE_AS = 'tags/{slug}/index.html'

PAGE_URL = 'pages/{slug}/'
PAGE_SAVE_AS = 'pages/{slug}/index.html'

DEFAULT_DATE_FORMAT = '%Y-%m-%d'

FEED_DOMAIN = SITEURL

THEME = 'themes/svbhack'
USER_LOGO_URL = SITEURL + '/static/images/pages/snsface.png'
TAGLINE = 'SA & OpsDev. <br />Proudly working @Cloudacc Inc.'
FAVICON_URL = '/static/images/blog/favicon.ico'

# don't guess category from folder name
USE_FOLDER_AS_CATEGORY = False

# don't display all pages on nav menu
DISPLAY_PAGES_ON_MENU = False

STATIC_PATHS = [ 'images' ]
FILES_TO_COPY = (
        ('extra/robots.txt', 'robots.txt'),
        )

# don't display categories on nav menu
DISPLAY_CATEGORIES_ON_MENU = False

PLUGIN_PATH = "plugins"
PLUGINS = ['neighbors', 'sitemap', 'gravatar']
SITEMAP = {
    'format': 'xml',
    'priorities': {
        'articles': 0.5,
        'indexes': 0.5,
        'pages': 0.5
    },
    'changefreqs': {
        'articles': 'monthly',
        'indexes': 'daily',
        'pages': 'monthly'
    }
}

# python-markdown extensions, see: http://pythonhosted.org/Markdown/extensions/index.html
MD_EXTENSIONS = ['codehilite','extra']

DELETE_OUTPUT_DIRECTORY = True
