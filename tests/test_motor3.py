#!/usr/bin/env python

from EpicsCA import Motor, pend_event, pend_io, PV, cleanup
import time

import sys
def writeAndFlush(msg,stream=sys.stdout):
    stream.write(msg)
    stream.flush()

def cb(pv=None,**kw):
    print 'Drive PV changed ', pv.pvname, pv.value


motor_name = '13XRM:m1'
drive = PV("%s.VAL" % motor_name, callback=cb)


def main():
    writeAndFlush('creating motor ...')
    m = Motor(motor_name)
    writeAndFlush('OK.  Info:\n')

    m.show_info()
    
    writeAndFlush('tweak motor a few times..')
    for i in range(4):
        writeAndFlush('tweak, ')
        m.tweak(wait=True)

    writeAndFlush('OK.\n  Now move to low limit, wait 0.2 sec and stop:')

    m.move(m.low_limit)
    time.sleep(0.2)
    m.stop()
    pend_event(0.1)
   
    m.show_info()
    
main()
cleanup()

