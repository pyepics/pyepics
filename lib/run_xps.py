import time
import epics
import debugtime

from XYTrajectory import XY_Trajectory
traj = XY_Trajectory()

dtimes = debugtime.debugtime()

xstart = -0.5
xstop = 0.5
xstep = 0.002
dwelltime = 5.0
accel = 10.0

traj.DefineTrajectory('Foreward', xstart=xstart, xstop=xstop, xstep=xstep,
                      dwelltime=dwelltime, accel=accel)
traj.DefineTrajectory('Backward', xstart=xstop, xstop=xstart, xstep=xstep,
                      dwelltime=dwelltime, accel=accel)

dtimes.add('trajectories defined')

traj.file_index = 0
traj.file_prefix = 'Scan1'

yPV = epics.PV('13XRM:m2.VAL')
xPV = epics.PV('13XRM:m1.VAL')
 
ystart = -0.5
ystop = 0.5
ystep = 0.002
ny    = 1 + int(0.1 + (ystop - ystart)/ystep)
ypositions = [ystart + iy*ystep for iy in range(ny)][:50]

print len(ypositions), len(ypositions)*5/3600.0
dtimes.add('move to start position')
print xstart, ystart

xPV.put(xstart)
yPV.put(ystart, wait=True)
xPV.put(xstart, wait=True)
time.sleep(0.01)

print 'At start position '
dtimes.add('Ready to begin:' )

for i, val in enumerate(ypositions):
    yPV.put(val, wait=True)
    xstart = xPV.get()
    time.sleep(0.05)
    
    trajName = 'Foreward'
    if i % 2 != 0:
        trajName = 'Backward'
    np_expected, np_read = traj.RunTrajectory(trajName, verbose=True, save=True)



    ntry = 0
    while np_read < np_expected:
        print 'Warning!!! read too few lines!! trying that trajectory again: '
        traj.file_index = traj.file_index-1
        time.sleep(0.1)
        xPV.put(xstart, wait=True)
        time.sleep(0.1)        
        np_expected, np_read = traj.RunTrajectory(trajName, verbose=True, save=True)
        ntry = ntry + 1
        if ntry > 3:
            print 'Cannot run this trajectory!!'
    
    dtimes.add('scan %i' % i)

dtimes.show()
