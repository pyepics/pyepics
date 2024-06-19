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

if [ -z ${EPICS_BASE+x} ] ; then
    if [ -z ${CONDA_PREFIX+x} ] ; then
        EPICS_BASE=/usr/local/epics/base
    else
        EPICS_BASE=$CONDA_PREFIX/epics
    fi
fi

PROCSERV_OPTS='-P 9230 -n pyepics_testioc -L pyepics_testioc.log --noautorestart'

uname=`uname`
if [ $uname == Darwin ]; then
    export EPICS_HOST_ARCH=darwin-x86
fi

export PATH=$EPICS_ROOT/bin/$EPICS_HOST_ARCH:$PATH

echo "#starting IOC with: $EPICS_BASE/bin/$EPICS_HOST_ARCH/softIoc ./st.cmd"
echo " using procServ opts: $PROCSERV_OPTS"

$EPICS_BASE/bin/$EPICS_HOST_ARCH/procServ $PROCSERV_OPTS $EPICS_BASE/bin/$EPICS_HOST_ARCH/softIoc ./st.cmd
