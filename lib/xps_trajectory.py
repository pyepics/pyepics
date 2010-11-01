#
import time
import sys
import ftplib
from cStringIO import StringIO
from string import printable

from XPS_C8_drivers import  XPS

##
## used methods for collector.py 
##    abortScan, clearabort
##    done ftp_connect 
##    done ftp_disconnect
##
## mapscan:   Build (twice!)
## linescan:  Build , clearabort
## ExecTraj;  Execute(),   building<attribute>, executing<attribute>
## WriteTrajData:  Read_FTP(), SaveGatheringData()
##
## need to have env and ROI written during traj scan:
##   use a separate thread for ROI and ENV, allow
##   XY trajectory to block.

class config:
    host = '164.54.160.180'
    port = 5001
    timeout = 10
    user = 'Administrator'
    passwd = 'Administrator'
    traj_folder = 'Public/trajectories'
    group_name = 'FINE'
    positioners = 'X Y'
    gather_titles = "# XPS Gathering Data\n#--------------\n#"
    # ('FINE.X.CurrentPosition', 'FINE.Y.CurrentPosition')
 
class XPSTrajectory(object):
    """XPS trajectory....
    """
    traj_text = """FirstTangent = 0
DiscontinuityAngle = 0.01

Line = %f, %f
"""    
    def __init__(self, host=None, user=None, passwd=None,
                 group=None, positioners=None):
        self.host = host or config.host
        self.user = user or config.user
        self.passwd = passwd or config.passwd
        self.group_name = group or config.group_name
        self.positioners = positioners or config.positioners
        self.positioners = tuple(self.positioners.replace(',', ' ').split())
        
        self.gather_outputs = ['%s.%s.CurrentPosition' % (self.group_name,i) for i in self.positioners]
        self.gather_outputs.extend(['%s.%s.SetpointPosition' % (self.group_name,i) for i in self.positioners])
        self.gather_titles = "%s %s\n" % (config.gather_titles,
                                          "  ".join(self.positioners))

        self.xps = XPS()
        self.ssid = self.xps.TCP_ConnectToServer(self.host, config.port, config.timeout)
        self.xps.Login(self.ssid, self.user, self.passwd)
        self.trajectories = {}

        self.ftpconn = ftplib.FTP()
    
        self.nlines_out = 0

        self.xps.GroupMotionDisable(self.ssid, self.group_name)
        time.sleep(0.1)
        self.xps.GroupMotionEnable(self.ssid, self.group_name)

        for i in range(64):
            self.xps.EventExtendedRemove(self.ssid,i)

        
    def ftp_connect(self):
        self.ftpconn.connect(self.host)
        self.ftpconn.login(self.user,self.passwd)
        self.FTP_connected = True
    
    def ftp_disconnect(self):
        "close ftp connnection"
        self.ftpconn.close()
        self.FTP_connected=False

    def upload_trajectoryFile(self,fname, data):
        self.ftp_connect()
        self.ftpconn.cwd(config.traj_folder)
        self.ftpconn.storbinary('STOR %s' %fname, StringIO(data))
        self.ftp_disconnect()
 
    def DefineTrajectory(self,name='Traj', **kw):
        traj_file = '%s.trj' % name
        tdata = dict(xstart=None, xstop=0, xstep=0.0,
                     ystart=None, ystop=0, ystep=0.0,
                     scantime=1.0, accel=1.0)
        tdata.update(kw)
        # could check if tdata in self.trajectories.... build up
        # store of used trajectories on the ftp server
        self.trajectories[name] = tdata
        
        xrange = yrange = 0
        if tdata['xstart'] is not None:
            xrange = tdata['xstop'] - tdata['xstart']

        if tdata['ystart'] is not None:            
            yrange = tdata['ystop'] - tdata['ystart']
        self.upload_trajectoryFile(traj_file, self.traj_text % (xrange, yrange))

    def abortScan(self):
        pass
    
    def RunTrajectory(self,name='Traj', verbose=False, save=True, outfile='Gather.dat', debug=False):

        traj = self.trajectories.get(name,None)
        if traj is None:
            print 'Cannot find trajectory named %s' %  name
            return

        traj_file = '%s.trj'  % name
        xstart = traj['xstart']
        xstop  = traj['xstop']
        xstep  = traj['xstep']
        ystart = traj['ystart']
        ystop  = traj['ystop']
        ystep  = traj['ystep']

        ret = xps.GatheringReset(socketID)
        ret = self.xps.XYLineArcVerification(self.ssid, self.group_name, traj_file)
        if debug: print 'XYLineArcVerification:: ', ret

        if xstep != 0 and xstart is not None:
            npulses = 1  + int( (abs(xstop-xstart) + abs(xstep)/10.0) / abs(xstep))
            xrange = abs(xstop-xstart)
            self.xps.XYLineArcPulseOutputSet(self.ssid, self.group_name,  0, xrange, xstep)
            speed = abs(xstop-xstart)/traj['scantime']
            if debug: 
                print 'XPS set pulseOutput to ', xrange, xstart, xstop, xstep, npulses
        elif ystep != 0 and ystart is not None:
            npulses = 1 + abs(ystop-ystart + ystep/10.0)/ abs(ystep)
            yrange = abs(ystop-ystart)            
            self.xps.XYLineArcPulseOutputSet(self.ssid, self.group_name, 0, yrange, ystep)
            speed = abs(ystop-ystart)/traj['scantime']            
        else:
            print "Cannot figure out number of pulses for trajectory"
            return -1

        o = self.xps.GatheringReset(self.ssid)
        if debug: print 'Gather reset: ', o

        o = self.xps.GatheringConfigurationSet(self.ssid, self.gather_outputs)
        if debug: print 'GatherConfSet: ', o

        buffer = ('Always', 'FINE.XYLineArc.TrajectoryPulse',)
        o = self.xps.EventExtendedConfigurationTriggerSet(self.ssid, buffer,
                                                          ('0','0'), ('0','0'),
                                                          ('0','0'), ('0','0'))
        
        if debug: print 'EventExtendedConf TriggerSet: ', o
        o = self.xps.EventExtendedConfigurationActionSet(self.ssid,  ('GatheringOneData',), 
                                                     ('',), ('',),('',),('',))
        if debug: print 'EventExtendedConf ActionSet: ', o
        eventID, m = self.xps.EventExtendedStart(self.ssid)

        if debug: print 'EventExtendedStart :  ', eventID, m
        accel   = traj['accel']

        ret = self.xps.XYLineArcExecution(self.ssid, self.group_name, traj_file, speed, accel, 1)

        if debug: print 'XYLineArcExecution :  ', ret
        o = self.xps.EventExtendedRemove(self.ssid, eventID)

        if debug: print 'EventExtendedRemove:  ', o

        time.sleep(0.05)
        o = self.xps.GatheringStop(self.ssid)
        if debug: print 'GatheringStop:  ', o
        time.sleep(0.05)
        ret, npulses, nx = self.xps.GatheringCurrentNumberGet(self.ssid)
        if debug: print 'GatheringCurrentNumberGet ', ret, npulses, nx

        ret,  buff = self.xps.GatheringDataMultipleLinesGet(self.ssid, 0, npulses)

        if debug: print 'GatheringMultipleLintGet  ', ret, len(buff) , 'bytes.'

        if save:
            self.SaveResults(outfile, verbose=verbose)
        return npulses

    def SaveResults(self,  fname, verbose=False):
        """read gathering data from XPS
        """
        t0 = time.time()
        # self.xps.GatheringStop(self.ssid)
        ret, npulses, nx = self.xps.GatheringCurrentNumberGet(self.ssid)
        time.sleep(0.002)

        t1 = time.time()
        ret,  buff = self.xps.GatheringDataMultipleLinesGet(self.ssid, 0, npulses)
        t2 =  time.time() 

        obuff = buff[:]
        for x in (';', '\r', '\t'):
            obuff = obuff.replace(x,' ')

        nlines = len(obuff.split('\n')) - 1
        
        f = open(fname, 'w')
        f.write(self.gather_titles)
        f.write(obuff)
        f.close()

        t3 =  time.time() 
        if verbose:
            msg = ' Wrote %i lines, %i bytes to %s  Times: GatherStop, GetData, WriteFile=(%.4f, %.4f, %.4f)'
            print msg % (nlines, len(buff), fname, t1-t0, t2-t1, t3-t2)
        self.nlines_out = nlines
        
        return nlines


def read_long_gather():
    """ from playing with long trajectories"""
    
    ret,  buff = xps.GatheringDataMultipleLinesGet(socketID, 0, npulses_out)
    if ret < 0:
        Nchunks = 2
        nx    = int( (npulses_out-5) / Nchunks)
        ret = 1
        while True:
            ret, xbuff = xps.GatheringDataMultipleLinesGet(socketID, 0, nx)
            if ret == 0:
                break
            Nchunks = Nchunks + 1
            nx      = int( (npulses_out-5) / Nchunks)            
        buff = [xbuff]
        print ' need to read in %i chunks! ' % Nchunks
        for i in range(1, Nchunks):
            ret, xbuff = xps.GatheringDataMultipleLinesGet(socketID, i*nx, nx)
            buff.append(xbuff)
        ret, xbuff = xps.GatheringDataMultipleLinesGet(socketID, Nchunks*nx, npulses_out-Nchunks*nx)
        buff.append(xbuff)
        buff = '# break \n'.join(buff)
if __name__ == '__main__':
    print 'test:'
    xps = XPSTrajectory()
    xps.DefineTrajectory(name='foreward', 
                         dimension = 1,   accel=1, 
                         xstart=0, xstop=0.5, xstep=0.01,
                         npulses=51, 
                         scantime=10)

    xps.DefineTrajectory(name='backward', 
                         dimension = 1,   accel=1, 
                         xstart=0.5, xstop=0., xstep=0.01,
                         npulses=51, 
                         scantime=10)

    for i in range(10):
        xps.RunTrajectory(name='foreward')
        time.sleep(1.0)
        xps.RunTrajectory(name='backward')
