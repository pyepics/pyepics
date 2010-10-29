import time
import ftplib
from cStringIO import StringIO
from XPS_C8_drivers import  XPS

class config:
    host = '164.54.160.180'
    port = 5001
    timeout = 10
    user = 'Administrator'
    passwd = 'Administrator'
    traj_folder = 'Public/trajectories'
    group_name = 'FINE'
    positioners = 'X Y'
    gather_outputs = ['FINE.X.CurrentPosition',
                      'FINE.Y.CurrentPosition',
                      'FINE.X.SetpointPosition',
                      'FINE.Y.SetpointPosition' ]


xps = XPS()
socketID = xps.TCP_ConnectToServer(config.host, config.port, config.timeout)
xps.Login(socketID, config.user, config.passwd)
#         
# print socketID
# 
xps.CloseAllOtherSockets(socketID)
print 'Rebooting XPS....'
xps.Reboot(socketID)

time.sleep(2.0)

xps = XPS()
socketID = xps.TCP_ConnectToServer(config.host, config.port, config.timeout)
xps.Login(socketID, config.user, config.passwd)

print 'Reconnected with socketID = ', socketID

time.sleep(3.0)
groupNames = ('FINE', 'THETA', 'COARSEX', 'COARSEY', 'COARSEZ', 'DETX')
actions =  ('GroupInitialize', 'GroupHomeSearch', 'GroupStatusGet')
actions =  ('GroupInitialize', 'GroupStatusGet')

for group in groupNames:
    print '== GROUP:: ' , group
    for action in actions:
        meth = getattr(xps, action)
        err, msg = meth(socketID, group)
        time.sleep(1.0)
        if err < 0:
            err, msg = meth(socketID, group)
            time.sleep(1.0)

        if err < 0:
            print "Group %s has status %s " % (group, msg)
            
