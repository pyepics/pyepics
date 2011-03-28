from xps_trajectory import XPSTrajectory
import time
print 'test:'
xps = XPSTrajectory()
xstop =  2.5
xstart = -xstop
xstep = 0.001
xps.DefineLineTrajectories(scantime=10,
                     start=xstart, stop=xstop, xstep=xstep)

for key,val in  xps.trajectories.items():
    print key, val

print '================'
xps.Move_XY(xstart, 0.1)

for i in range(2):
    print 'Foreward  # ', i
    xps.Move_XY(xstart, 0.1 + 0.005*(2*i))
    xps.RunLineTrajectory(name='foreward', outfile='Gathering.%3.3i' %(2*i+1))
    time.sleep(0.1)
    xps.Move_XY(xstop, 0.1 + 0.005*(2*i+1))
    xps.RunLineTrajectory(name='backward', outfile='Gathering.%3.3i' %(2*i+2))

