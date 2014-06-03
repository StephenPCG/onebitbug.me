#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Author:     Zhang Cheng <stephenpcg@gmail.com>
# Maintainer: Zhang Cheng <stephenpcg@gmail.com>

from bs4 import BeautifulSoup
import argparse
import urllib2
import os
import re
from datetime import datetime
from subprocess import Popen, PIPE
import errno

def makedirs(path):
    try:
        os.makedirs(path)
    except OSError as e:
        if e.errno == errno.EEXIST:
            pass
        else:
            raise

def read_input(infile):
    if infile.startswith("http://") or infile.startswith("https://"):
        content = urllib2.urlopen(infile).read()
    elif os.path.exists(infile):
        content = open(infile).read()
    else:
        raise Exception("input file not found")
    return content

def fetch_and_save_img(imgurl, save_path):
    print "fetching image:", imgurl
    imgcontent = urllib2.urlopen(imgurl).read()

    imgname = imgurl.split('/')[-1]
    filename = os.path.join(save_path, imgname)
    print "    saving to", filename

    makedirs(save_path)
    open(filename, "w+").write(imgcontent)

    return imgname

def parse_wordpress(args, content):
    # get slug
    url_ptn = re.compile(r'https?://.*/(?P<slug>.*)(.html|/|/index.html([#?].*)?)$')
    file_pth = re.compile(r'.*/(?P<slug>.*).html$')
    result = url_ptn.match(args.input)
    if result:
        slug = result.group('slug')
    else:
        result = file_pth.match(args.input)
        if result:
            slug = result.group('slug')
        else:
            slug = args.input
    slug.replace("/", '-')
    print "detected slug:", slug

    soup = BeautifulSoup(content, "html")

    # find title
    title_ = soup.html.body.find(itemprop="name")
    if title_:
        title = title_.text
    else:
        title = args.input
    print "detected title:", title.encode("utf8")

    # find publish date
    pubdate_ = soup.html.body.find(class_='entry-date')
    if pubdate_:
        pubdate = pubdate_.get('datetime').split("T")[0]
    else:
        pubdate = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print "detected publish date:", pubdate

    # find author
    author_ = soup.html.body.find('a', rel='author')
    if author_:
        href = author_['href'] if author_.has_attr('href') else None
        name = author_.text
        if href:
            author = '<a href=%s>%s</a>' % (href, name)
        else:
            author = name
    else:
        author = None
    print "detected author: %s" % author

    # find post content
    article_ = soup.html.body.find(itemprop="mainContentOfPage")

    # replace images
    for img in article_.find_all('img'):
        imgurl = img['src']
        imgpath = os.path.join(args.image_output_path, slug)
        imgname = fetch_and_save_img(imgurl, imgpath)
        imgnewurl = os.path.join(args.image_url_base, slug, imgname)
        img['src'] = imgnewurl
        if img.parent.has_attr('href') and img.parent['href'] == imgurl:
            img.parent['href'] = imgnewurl

        imgurl = '/%s/%s/%s' % (args.image_output_path, slug, imgname)
        img = '[{%% img center %s %%}](%s)' % (imgurl, imgurl)

    # strip <pre> css classes
    for pre in article_.find_all('pre'):
        if pre.has_attr('class'):
            del pre['class']

    # generate content
    cmd = ['pandoc', '-f', 'html', '-t', args.output_format]
    proc = Popen(cmd, stdin=PIPE, stdout=PIPE)
    (stdout, stderr) = proc.communicate(input=article_.decode_contents().encode('utf8'))

    # output filename
    if args.output_format == "markdown":
        ext = "md"
    elif args.output_format == "rst":
        ext = "rst"
    else:
        raise Exception("un-supported output format")
    output_filename = os.path.join(args.content_output_path, "%s.%s" % (slug, ext))
    makedirs(args.content_output_path)
    print "writing to", output_filename
    with open(output_filename, "w+") as fp:
        fp.write("Slug: %s\n" % slug)
        fp.write("Date: %s\n" % pubdate)
        fp.write("Title: %s\n" % title.encode("utf8"))
        fp.write("Category: %s\n" % args.category)
        fp.write("Author: %s\n" % author)
        if args.input.startswith("http://") or args.input.startswith("https://"):
            fp.write("ReproducedSource: %s\n" % args.input)
        for meta in args.metadata:
            fp.write("%s\n" % meta)
        fp.write("\n")
        fp.write(stdout)

def main():
    parser = argparse.ArgumentParser(
            description="Import a single wordpress page into pelican.",
            formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument(dest='input', help='The input file or url to read')
    parser.add_argument('-f', '--format', dest='format', default='wordpress',
            help='input page format, currently only support wordpress')
    parser.add_argument('-t', '--output-format', dest='output_format',
            default='markdown', help='output format, could be markdown, rst')
    parser.add_argument('--image-output-path', dest='image_output_path',
            default='content/images/', help='image save path')
    parser.add_argument('--image-url-base', dest="image_url_base",
            default='/images/', help='image url base')
    parser.add_argument('--content-output-path', dest='content_output_path',
            default='content/', help='content save path')
    parser.add_argument('--category', dest='category', default="Share",
            help='category of article for imported article')
    parser.add_argument('--metadata', action="append", dest="metadata", default=[],
            help='extra metadata for posts')

    args = parser.parse_args()

    content = read_input(args.input)
    if args.format == "wordpress":
        parse_wordpress(args, content)

if __name__ == "__main__":
    main()

# vim:ai:et:sts=4:sw=4:
