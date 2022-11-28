#!/bin/bash

export EPICS_CA_ADDR_LIST=localhost
export EPICS_CA_AUTO_ADDR_LIST=NO
export EPICS_CA_MAX_ARRAY_BYTES=20100300

PROCSERV=$CONDA/bin/procServ
PROCSERV_OPTS='-P 9230 -n pyepics_testioc -L pyepics_testioc.log --noautorestart'

if ! test -f ./st.cmd; then
    echo 'Error -- st.cmd not found at the current directory'
    echo 'Run the script with pwd at <repo>/tests/Setup/st.cmd'
    exit 1
fi

uname=`uname`
if [ $uname == Darwin ]; then
    SOFTIOC=$CONDA/epics/bin/darwin-x86/softIoc
    /usr/bin/screen -d -m $SOFTIOC ./st.cmd
else
    SOFTIOC=$CONDA/epics/bin/linux-x86_64/softIoc
    echo 'Running ioc with ' $PROCSERV $PROCSERV_OPTS -e $SOFTIOC ./st.cmd
    $PROCSERV $PROCSERV_OPTS -e $SOFTIOC ./st.cmd
fi
