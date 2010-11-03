#
import time
import sys
import ftplib
from cStringIO import StringIO
from string import printable

from debugtime import debugtime
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
    gather_titles = "# XPS Gathering Data\n#--------------"
    gather_outputs =  ('CurrentPosition', )
 
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
        
        gout = []
        gtit = []
        for pname in self.positioners:
            for out in config.gather_outputs:
                gout.append('%s.%s.%s' % (self.group_name, pname, out))
                gtit.append('%s.%s' % (pname, out))
        self.gather_outputs = gout
        self.gather_titles  = "%s\n#%s\n" % (config.gather_titles,
                                          "  ".join(gtit))
        
        # self.gather_titles  = "%s %s\n" % " ".join(gtit)

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
        
        print 'DEFINE TRAJ ', tdata
        xrange = yrange = 0
        if tdata['xstart'] is not None:
            xrange = tdata['xstop'] - tdata['xstart']

        if tdata['ystart'] is not None:            
            yrange = tdata['ystop'] - tdata['ystart']
        self.upload_trajectoryFile(traj_file, self.traj_text % (xrange, yrange))

    def abortScan(self):
        pass
    
    def Move_XY(self, xpos=0, ypos=0):
        "move XY positioner to supplied position"
        print 'Move XY ', xpos, ypos
        self.xps.GroupMoveAbsolute(self.ssid, 'FINE', (xpos, ypos))

    def RunTrajectory(self,name='Traj', verbose=False, save=True,
                      outfile='Gather.dat', debug=False):

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

        ret = self.xps.GatheringReset(self.ssid)

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

        print 'Execute',  traj_file, speed
        ret = self.xps.XYLineArcExecution(self.ssid, self.group_name, traj_file, speed, accel, 1)

        if debug: print 'XYLineArcExecution :  ', ret
        o = self.xps.EventExtendedRemove(self.ssid, eventID)

        if debug: print 'EventExtendedRemove:  ', o

        time.sleep(0.025)
        o = self.xps.GatheringStop(self.ssid)
        if debug: print 'GatheringStop:  ', o
        time.sleep(0.025)

        ret, npulses, nx = self.xps.GatheringCurrentNumberGet(self.ssid)
        if debug: print 'GatheringCurrentNumberGet ', ret, npulses, nx

        if debug: print 'GatheringMultipleLintGet  ', ret, len(buff) , 'bytes.'

        if save:
            self.SaveResults(outfile, verbose=verbose)
        return npulses

    def SaveResults(self,  fname, verbose=False):
        """read gathering data from XPS
        """
        # self.xps.GatheringStop(self.ssid)
        db = debugtime()
        ret, npulses, nx = self.xps.GatheringCurrentNumberGet(self.ssid)
        db.add(' Will Save %i pulses , ret=%i ' % (npulses, ret))
        ret, buff = self.xps.GatheringDataMultipleLinesGet(self.ssid, 0, npulses)
        db.add(' MLGet ret=%i, buff_len = %i ' % (ret, len(buff)))
        
        if ret < 0:  # gathering too long: need to read in chunks
            print 'Need to read Data in Chunks!!!'  # how many chunks are needed??
            Nchunks = 3
            nx    = int( (npulses-2) / Nchunks)
            ret = 1
            while True:
                print ' --> ', npulses, Nchunks, nx
                ret, xbuff = self.xps.GatheringDataMultipleLinesGet(self.ssid, 0, nx)
                print nx, ret, len(xbuff)                
                if ret == 0:
                    break
                Nchunks = Nchunks + 2
                nx      = int( (npulses-2) / Nchunks)
            print  ' -- wil use %i %i Chunks ' % (nx, Nchunks)
            db.add(' Will use %i chunks ' % (Nchunks))
            buff = [xbuff]
            for i in range(1, Nchunks):
                ret, xbuff = self.xps.GatheringDataMultipleLinesGet(self.ssid, i*nx, nx)
                print i*nx, nx, ret, len(xbuff)
                buff.append(xbuff)
                db.add('   chunk %i' % (i))
            ret, xbuff = self.xps.GatheringDataMultipleLinesGet(self.ssid, Nchunks*nx,
                                                                npulses-Nchunks*nx)
            buff.append(xbuff)
            buff = ''.join(buff)
            db.add('   chunk last')

        obuff = buff[:]
        for x in (';', '\r', '\t'):
            obuff = obuff.replace(x,' ')
        db.add('  data fixed')            
        f = open(fname, 'w')
        f.write(self.gather_titles)
        db.add('  file open')
        f.write(obuff)
        db.add('  file write')        
        f.close()
        db.add('  file closed')
        nlines = len(obuff.split('\n')) - 1
        if verbose:
            print 'Wrote %i lines, %i bytes to %s' % (nlines, len(buff), fname)
        self.nlines_out = nlines
        db.show()
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
    xps.DefineTrajectory(name='foreward', scantime=5,
                         xstart=0, xstop=2.50, xstep=0.001)

    xps.Move_XY(-1.00, 0.1)
    time.sleep(0.02)
    xps.RunTrajectory(name='foreward', outfile='BigFileOut.txt')

# 
#     for i in range(21):
#         xps.Move_XY(-0.25, 0.1 + 0.005*(2*i))
#         xps.RunTrajectory(name='foreward', outfile='Gathering.%3.3i' %(2*i+1))
#         time.sleep(0.25)
#         xps.Move_XY( 0.25, 0.1 + 0.005*(2*i+1))
#         xps.RunTrajectory(name='backward', outfile='Gathering.%3.3i' %(2*i+2))
# ;
