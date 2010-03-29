#!/usr/bin/env python

from EpicsCA import Motor, poll, pend_io

mname = '13XRM:m1'

motor = Motor(mname)

motor.show_info()


poll()

print 'Motor Acceleration: ', motor.acceleration
print 'done.'
