#!/bin/bash

# install pip and python-dev
sudo apt-get install --no-install-recommends python-pip python-dev

pip install --pre pelican
pip install Markdown
pip install typogrify

# vim:ai:et:sts=4:sw=4:
