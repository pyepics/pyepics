#!/bin/sh

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

OPTS='-P 9230 -n pyepics_testioc -L pyepics_testioc.log --noautorestart'
$PROCSERV $OPTS -e $SOFTIOC ./st.cmd
