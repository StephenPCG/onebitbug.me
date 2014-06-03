#!/bin/bash

tools/import-post.py \
    --content-output-path content/Reproduced/ \
    --image-output-path content/images/reproduced/ \
    --image-url-base /images/reproduced/ \
    --category Reproduced \
    --metadata 'GitTime: Off' \
    $@

# vim:ai:et:sts=4:sw=4:
