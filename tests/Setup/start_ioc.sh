#!/bin/bash
# run softIoc, either on linux with procserv from conda-forge
# or on darwin with screen


export EPICS_CA_ADDR_LIST=localhost
export EPICS_CA_AUTO_ADDR_LIST=NO
export EPICS_CA_MAX_ARRAY_BYTES=20100300

PROCSERV=$CONDA_PREFIX/bin/procServ
PROCSERV_OPTS='-P 9230 -n pyepics_testioc -L pyepics_testioc.log --noautorestart'

uname=`uname`
if [ $uname == Darwin ]; then
    SOFTIOC=$CONDA_PREFIX/epics/bin/darwin-x86/softIoc
    /usr/bin/screen -d -m $SOFTIOC ./st.cmd

else
    SOFTIOC=$CONDA_PREFIX/epics/bin/linux-x86_64/softIoc
    $PROCSERV -e $PROCSERV_OPTS -e $SOFTIOC ./st.cmd
fi
