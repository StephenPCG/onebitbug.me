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

log_echo "get update request, updating..."
pushd $__script_dir/.. >> $logfile
log_echo "invoking: git pull"
git pull |& tee -a $logfile
log_echo "invoking: make html..."
if make html >> $logfile; then
    echo "succeed!"
else
    echo "failed"
fi
popd >> $logfile

log_echo "done!"
