#!/bin/bash

pushd $(dirname $0) > /dev/null
__script_dir=$(pwd -P)
popd >/dev/null

logfile=$__script_dir/update.log
function log() {
    echo "[$(date +%Y/%m/%d:%H:%M:%S)] $@" >> $logfile
}

function log_echo() {
    log $@
    echo "[$(date +%Y/%m/%d:%H:%M:%S)] $@"
}

# must set this header, or fastcgi won't work
echo -e "Content-type: text/plain\n"

## parse http query args
#saveIFS=$IFS
#IFS='=&'
#param=($QUERY_STRING)
#IFS=$saveIFS
#
#declare -A args
#for ((i=0; i<${#param[@]}; i+=2)) do
#    args[${param[i]}]=${param[i+1]}
#done

echo >> $logfile
log "-------------------------------"
log "REMOTE_ADDR:     $REMOTE_ADDR"
log "REMOTE_PORT:     $REMOTE_PORT"
log "HTTP_USER_AGENT: $HTTP_USER_AGENT"
log "REQUEST_METHOD:  $REQUEST_METHOD"
log "HTTP_HOST:       $HTTP_HOST"
log "REQUEST_URI:     $REQUEST_URI"
if [ "$REQUEST_METHOD" == "POST" ]; then
    log "POST BODY:       \
$(</dev/stdin)"
fi

log_echo "updating..."
pushd $__script_dir/.. >> $logfile

log_echo "invoking: git pull"
git pull |& tee -a $logfile
log_echo "invoking: git submodule update"
git submodule update |& tee -a $logfile

# `make html` will first cleanup output/, if the web root directly point here,
# it will cause a short period of 404, and if make failed, things goes worse.
# so point let's make this structure:
# $code_root/
#    |- output/
#    |- webroot/
#    |-   output-$(date +%s)
#    |-   onebitbug.me --> output-%current%
# when a new `make html` succeed, copy output/ to webroot/output-$(date +%s)
# alter link target of onebitbug.me to output-%new%, remove output-%old%
log_echo "invoking: make html..."
if make html >> $logfile; then
    new="output-$(date +%s)"
    cp -ar output webroot/$new
    old=$(readlink webroot/onebitbug.me 2>/dev/null)
    ln -snf $new webroot/onebitbug.me
    if [ -e "webroot/$old" ]; then
        rm -rf webroot/$old
    fi
    echo "succeed!"
else
    echo "failed"
fi

popd >> $logfile

log_echo "done!"
