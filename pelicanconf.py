#!/usr/bin/env python
# -*- coding: utf-8 -*- #
from __future__ import unicode_literals

AUTHOR = u'Stephen Zhang'
SITEURL = ''

SITENAME = u'May the #! be with you'
DISQUS_SITENAME = 'onebitbug'
GITHUB_URL = 'https://github.com/StephenPCG/'
GITHUB_USER = 'StephenPCG'

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
SOCIAL = ( ('Computing Life', 'http://grapeot.me/'),
           ('Code is Might', 'http://www.codeismight.com/'),
           ('Sigma', 'http://www.sigma.me/'),
           ('USTC LUG', 'http://lug.ustc.edu.cn/'),
         )
MENUITEMS = (('Home', '/'),
             ('Archives', '/archives.html'),
             ('Biography', '/biography/'),
             ('GuestBook', '/guest/'),
             )

DEFAULT_PAGINATION = 5

ARTICLE_URL = '{date:%Y}/{date:%m}/{date:%d}/{slug}/'
ARTICLE_SAVE_AS = '{date:%Y}/{date:%m}/{date:%d}/{slug}/index.html'
YEAR_ARCHIVE_SAVE_AS = '{date:%Y}/index.html'
MONTH_ARCHIVE_SAVE_AS = '{date:%Y}/{date:%m}/index.html'
DAY_ARCHIVE_SAVE_AS = '{date:%Y}/{date:%m}/{date:%d}/index.html'
CATEGORY_URL = 'categories/{slug}/'
CATEGORY_SAVE_AS = 'categories/{slug}/index.html'
TAG_URL = 'tags/{slug}/'
TAG_SAVE_AS = 'tags/{slug}/index.html'

PAGE_URL = '{slug}/'
PAGE_SAVE_AS = '{slug}/index.html'

DEFAULT_DATE_FORMAT = '%Y-%m-%d'

FEED_DOMAIN = SITEURL

THEME = 'themes/octopress'
#USER_LOGO_URL = SITEURL + '/static/images/pages/snsface.png'
#TAGLINE = 'SA & OpsDev. <br />Proudly working @Cloudacc Inc.'
FAVICON_URL = 'images/blog/favicon2.png'
SEARCH_BOX = True

# don't guess category from folder name
USE_FOLDER_AS_CATEGORY = False

# don't display all pages on nav menu
DISPLAY_PAGES_ON_MENU = False

STATIC_PATHS = [ 'images', 'extra/robots.txt', 'upload']
EXTRA_PATH_METADATA = {
        'extra/robots.txt': {'path': 'robots.txt'},
        }

# don't display categories on nav menu
DISPLAY_CATEGORIES_ON_MENU = False

PLUGIN_PATH = "plugins"
PLUGINS = ['neighbors', 'sitemap', 'gravatar', 'liquid_tags.img']
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
