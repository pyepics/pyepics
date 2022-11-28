#!/bin/bash

SOFTIOC=softIoc
if ! command -v $SOFTIOC &> /dev/null ; then
    if [[ -z "${CONDA}" ]]; then
	echo 'Warning -- cannot find softIoc'
    else
	SOFTIOC=$CONDA/epics/bin/linux-x86_64/softIoc
    fi
fi

PROCSERV=procServ
if ! command -v $PROCSERV &> /dev/null ; then
    if [[ -z "${CONDA}" ]]; then
	echo 'Warning -- cannot find procServ'
    else
	SOFTIOC=$CONDA/bin/procServ
    fi
fi

if ! test -f ./st.cmd; then
    echo 'Error -- st.cmd not found at the current directory'
    echo 'Run the script with pwd at <repo>/tests/Setup/st.cmd'
    exit 1
fi

OPTS='-P 9230 -n pyepics_testioc -L pyepics_testioc.log --noautorestart'
$PROCSERV $OPTS -e $SOFTIOC ./st.cmd
