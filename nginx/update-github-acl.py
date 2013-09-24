#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Author:     Zhang Cheng <cheng.zhang@cloudacc-inc.com>
# Maintainer: Zhang Cheng <cheng.zhang@cloudacc-inc.com>

import urllib2
import simplejson as json
import shutil

req = urllib2.Request(url="https://api.github.com/meta")
f = urllib2.urlopen(req)
result = json.load(f)

with open("/tmp/github.acl", "w+") as fp:
    for cidr in result["hooks"]:
        print "allow %s;" % cidr
        fp.write("allow %s;\n" % cidr)
shutil.move("/tmp/github.acl", "global/github.acl")


# vim:ai:et:sts=4:sw=4:
