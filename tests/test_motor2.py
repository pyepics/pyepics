#!/usr/bin/env python

from EpicsCA import Motor, poll, pend_io

mname = '13XRM:m1'

motor = Motor(mname)

motor.show_info()


print motor.drive
print 'limits [%f : %f]', motor.low_limit, motor.high_limit

range =  motor.high_limit - motor.low_limit


print 'move (with wait) close to low limit:'

motor.move(motor.low_limit + range*0.001, wait=True)

print 'OK, now move (with wait) close to high limit:'
motor.move(motor.high_limit - range*0.001, wait=True)


print 'done.'


