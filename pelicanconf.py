#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Configuration for pelican
"""

from __future__ import unicode_literals
import yaml

try:
    with open("config.yml") as fp:
        PRIVATE_CONFIG = yaml.load(fp.read()).get("DEVELOP", dict())
except:
    PRIVATE_CONFIG = dict()

### settings that may be different between developing and publishing
SITEURL = u'http://localhost:8000'
RELATIVE_URLS = True

PLUGIN_PATH = PRIVATE_CONFIG.get("PLUGIN_PATH", [])
PLUGIN_PATH.append("plugins")

### personal info
AUTHOR = u'Stephen Zhang'
SITENAME = u'May the #! be with you'

### blog arrangement
TIMEZONE = 'Asia/Shanghai'
DEFAULT_DATE_FORMAT = '%Y-%m-%d'
DEFAULT_LANG = u'zh'
DEFAULT_PAGINATION = 5

# url stuff
ARTICLE_URL = '{date:%Y}/{date:%m}/{date:%d}/{slug}/'
ARTICLE_SAVE_AS = '{date:%Y}/{date:%m}/{date:%d}/{slug}/index.html'
YEAR_ARCHIVE_SAVE_AS = '{date:%Y}/index.html'
MONTH_ARCHIVE_SAVE_AS = '{date:%Y}/{date:%m}/index.html'
DAY_ARCHIVE_SAVE_AS = '{date:%Y}/{date:%m}/{date:%d}/index.html'
CATEGORY_URL = 'categories/{slug}/'
CATEGORY_SAVE_AS = 'categories/{slug}/index.html'
TAG_URL = 'tags/{slug}/'
TAG_SAVE_AS = 'tags/{slug}/index.html'
TAGS_URL = 'tags/'
TAGS_SAVE_AS = 'tags/index.html'
PAGE_URL = '{slug}/'
PAGE_SAVE_AS = '{slug}/index.html'
SUBCATEGORY_SAVE_AS = 'subcategory/{savepath}/index.html'
SUBCATEGORY_URL = 'subcategory/{savepath}/'

USE_FOLDER_AS_CATEGORY = False
DISPLAY_PAGES_ON_MENU = False
DISPLAY_CATEGORIES_ON_MENU = False

STATIC_PATHS = ['images', 'upload', 'extra']
FILENAME_METADATA = r'(?P<date>\d{4}-\d{2}-\d{2})-(?P<slug>.*)'
EXTRA_PATH_METADATA = {
    'extra/robots.txt': {'path': 'robots.txt'},
    'extra/favicon.ico': {'path': 'favicon.ico'},
    }

# python-markdown extensions,
# see: http://pythonhosted.org/Markdown/extensions/index.html
MD_EXTENSIONS = ['codehilite', 'extra']

DELETE_OUTPUT_DIRECTORY = True

IGNORE_FILES = ['.*']

PAGINATION_PATTERNS = (
    (1, '{base_name}/', '{base_name}/index.html'),
    (2, '{base_name}/page/{number}/', '{base_name}/page/{number}/index.html'),
    )

### plugin settings
PLUGINS = [
    'cjk-auto-spacing',
    'custom_article_urls',
    #'github_activity',
    'gravatar',
    'liquid_tags.img',
    'multi_part',
    'neighbors',
    'read_more_link',
    'sitemap',
    'subcategory',
    'filetime_from_git',
    ]

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

### theme settings
THEME = 'octopress'
CSS_FILE = 'whitelake.css'
SEARCH_BOX = True

DISQUS_SITENAME = u'onebitbug'
GITHUB_USER = 'StephenPCG'

TAG_CLOUD_STEPS = 5

# Social widget
SOCIAL = (
    ('USTC LUG', 'http://lug.ustc.edu.cn/'),
    )

# Blogroll widget
LINKS = (
    ('Computing Life', 'http://grapeot.me/'),
    ('Code is Might', 'http://www.codeismight.com/'),
    ('Sigma', 'http://www.sigma.me'),
    )

MENUITEMS = (
    ('Home', '/'),
    ('Archives', '/archives.html'),
    ('Biography', '/biography/'),
    ('GuestBook', '/guest/'),
    )

SHOW_ARTICLE_NEIGHBORS = True
SHOW_DISQUS_COMMENT_COUNT = True

ARTICLE_ASIDES = ['recentpost', 'tags', 'categories', 'links']
PAGE_ASIDES = []
INDEX_ASIDES = ['github', 'recentpost', 'categories', 'social', 'links']

# vim:ai:et:sts=4:sw=4:
