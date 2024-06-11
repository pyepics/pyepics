#!/bin/bash

if ! test -f ./st.cmd; then
    echo 'Error -- st.cmd not found at the current directory'
    echo 'Run the script with pwd at <repo>/tests/Setup/st.cmd'
    exit 1
fi

export EPICS_CA_ADDR_LIST=localhost
export EPICS_CA_AUTO_ADDR_LIST=NO
export EPICS_CA_MAX_ARRAY_BYTES=20100300
export EPICS_HOST_ARCH=linux-x86_64

PROCSERV=$CONDA/bin/procServ
PROCSERV_OPTS='-P 9230 -n pyepics_testioc -L pyepics_testioc.log --noautorestart'

uname=`uname`
if [ $uname == Darwin ]; then
    export EPICS_HOST_ARCH=darwin-x86
fi

export PATH=$CONDA/epics/bin/$EPICS_HOST_ARCH/softIoc:$PATH

$PROCSERV $PROCSERV_OPTS softIoc ./st.cmd
