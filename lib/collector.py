import time
import os
import sys
import numpy
import epics 
from threading import Thread

from util import debugtime, new_filename, nativepath, winpath

from epics.devices  import Struck
from xmap_mca  import QuadVortex
from xps_trajectory import XPSTrajectory
from mapper import mapper

from configFile import FastMapConfig
from mca_rois import Write_MED_header
from mono_control import mono_control

USE_XMAP = True
USE_STRUCK = True
USE_MONO_CONTROL = False

# this should go into the configFile, but then again, 
# mono_control is highly specialized to a setup.....
MONO_PREFIX = '13IDA:'

def fix_range(start=0,stop=1,step=0.1, addstep=False):
    """returns (npoints,start,stop,step) for a trajectory
    so that the start and stop points are on the trajectory
    boundaries and will be included in the scan.
    """
    if stop < start:
        start, stop= stop, start
    step = abs(step)
    if addstep:
        start= start - step/2.0
        stop = stop  + step/2.0
    span = abs(stop-start)
    if abs(span) < 1.e-12:
        return (1, start, stop, 0)
    npts = 1 + int(0.25 + abs(span/step))
    stop = start + step * (npts-1)
    return (npts,start,stop,step)

class TrajectoryScan(epics.Device):
    subdir_fmt = 'scan%4.4i'
        
    def __init__(self, configfile=None):
        
        epics.Device.__init__(self,None)
        self.state = 'idle'
        conf = self.mapconf = FastMapConfig(configfile)
        
        struck      = conf.get('general', 'struck')
        scaler      = conf.get('general', 'scaler')
        xmappv      = conf.get('general', 'xmap')
        basedir     = conf.get('general', 'basedir')
        fileplugin  = conf.get('general', 'fileplugin')
        mapdb       = conf.get('general', 'mapdb')

        self.mapper = mapper(prefix=mapdb)
        self.mono_control = mono_control(MONO_PREFIX)

        self.subdir_index = 0
        self.scan_t0  = time.time()
        self.Connect_ENV_PVs()

        self.ROI_Written = False
        self.ENV_Written = False
        self.ROWS_Written = False

        self.traj = XPSTrajectory(**conf.get('xps'))
        self.dtime = debugtime()

        self.struck = None
        self.xmap = None
        if USE_STRUCK:
            self.struck = Struck(struck, scaler=scaler)
            
        if USE_XMAP:
            self.xmap = QuadVortex(xmappv,filesaver=fileplugin)
            self.xmap.SpectraMode()
       
        self.positioners = {}
        for pname in conf.get('slow_positioners'):
            self.positioners[pname] = self.PV(pname)

        self.mapper.PV('Start').add_callback(self.onStart)
        self.mapper.PV('Abort').add_callback(self.onAbort)
        self.mapper.PV('basedir').add_callback(self.onDirectoryChange)
            
        # self.mapper.basedir = basedir
        
    def onStart(self,pvname=None,value=None,**kw):
        if value == 1:
            self.state = 'start'

    def onAbort(self,pvname=None,value=None,**kw):
        if value == 1:
            self.traj.abortScan()
            self.state = 'abort'
        else:
            self.state = 'idle'

    def onDirectoryChange(self,value=None,char_value=None,**kw):
        if char_value is not None:
            os.chdir(os.path.abspath(nativepath(char_value)))
            
    def setWorkingDirectory(self):
        print ' ===Creating subfolder for this scan ',  os.getcwd(), self.mapper.basedir
        basedir = os.path.abspath(nativepath(self.mapper.basedir))
        print self.mapper.basedir , basedir
        try:
            os.chdir(basedir)
        except:
            print 'Cannot chdir to ', basedir

        subdir_fmt = 'Scan%5.5i'
        success = False
        i = self.subdir_index
        while i < 10000:
            i  = i + 1
            f = self.subdir_fmt % i
            if not os.path.exists(f):
                try:
                    os.mkdir(f)
                except:
                    print 'Cannot create dir ', f
                self.subdir_index = i
                subdir = f
                success = True
                break
        self.mapper.workdir = subdir
        self.workdir = os.path.abspath(os.path.join(basedir,subdir))

        if USE_XMAP:
            self.xmap.setFilePath(winpath(self.workdir))

        self.ROI_Written = False
        self.ENV_Written = False
        self.ROWS_Written = False
        return subdir

    def prescan(self,filename=None,filenumber=1,npulses=11,**kw):
        """ put all pieces (trajectory, struck, xmap) into
        the proper modes for trajectory scan"""
        if USE_STRUCK:
            self.struck.ExternalMode()

        if USE_XMAP:
            # self.xmap.setFileTemplate('%s%s_%4.4d.nc')
            self.xmap.setFileTemplate('%s%s.%4.4d')
            self.xmap.setFileWriteMode(2)
            self.xmap.MCAMode(filename='xmap', # filename,
                              npulses=npulses)
        self.ROI_Written = False
        self.ENV_Written = False
        self.dtime.add('prescan done %s %s' %(repr(USE_STRUCK), repr(USE_XMAP)))
        
    def postscan(self):
        """ put all pieces (trajectory, struck, xmap) into
        the non-trajectory scan mode"""
        if USE_XMAP:
            self.Wait_XMAPWrite(i=0)            
            self.xmap.SpectraMode()
        self.setIdle()
        self.dtime.add('postscan done')
        
    def save_positions(self, poslist=None):
        plist = self.positioners.keys()
        if poslist is not None:
            for p in poslist:
                if p not in plist:
                    plist.append(p)
                
        self.__savedpos={}
        for pvname in plist:
            self.__savedpos[pvname] = self.PV(pvname).get()
        self.dtime.add('save_positions done')
        
    def restore_positions(self):
        for pvname,val in self.__savedpos.items():
            self.PV(pvname).put(val)
        self.dtime.add('restore_positions done')            


    def Wait_XMAPWrite(self,i=0):
        """wait for XMAP to finish writing its data"""
        if USE_XMAP:
            # wait for previous netcdf file to be written
            t0 = time.time()
            time.sleep(0.05)
            while not self.xmap.FileWriteComplete():
                self.xmap.finish_pixels()
                time.sleep(0.05)
                if time.time()-t0 > 15:
                    self.mapper.message = 'XMAP File Writing Not Complete!'
                    # self.MasterFile.write('#WARN xmap write failed: row %i\n' % (irow-1))
                    break
            xmap_fname = nativepath(self.xmap.getLastFileName())[:-1]
            folder,xmap_fname = os.path.split(xmap_fname)
            prefix, suffix = os.path.splitext(xmap_fname)
            suffix = suffix.replace('.','')
            fnum = int(suffix)
            print 'XMAP file %s  / row %i (%3f sec)' % (xmap_fname, i, time.time()-t0)
            # print "xmap file ", xmap_fname, time.ctime(os.stat(xmap_fname).st_ctime)
        return fnum

    def mapscan(self, filename='TestMap',scantime=10, accel=1, 
                pos1='13XRM:m1',start1=0,stop1=1,step1=0.1, dimension=1,
                pos2=None,start2=0,stop2=1,step2=0.1, **kw):
        
        self.dtime.clear()
        if pos1 not in self.positioners:
            raise ValueError(' %s is not a trajectory positioner' % pos1)
 
        npts1,start1,stop1,step1 = fix_range(start1,stop1,step1, addstep=True)
        npts2,start2,stop2,step2 = fix_range(start2,stop2,step2, addstep=False)


        self.mapper.npts = npts1
        self.mapper.setNrow(0)
        self.mapper.maxrow  = npts2
        self.mapper.info    = 'Pending'
        self.mapper.message = "will execute %i points in %.2f sec" % (npts1,scantime)
        self.state = 'pending'
        
        self.save_positions()

        if pos2 is None:
            dimension = 1
            npts2 = 1

        self.scan_t0 = time.time()
        self.MasterFile.write('#SCAN started at %s\n' % time.ctime())
        self.MasterFile.write('#SCAN file name = %s\n' % filename)
        self.MasterFile.write('#SCAN dimension = %i\n' % dimension)            
        self.MasterFile.write('#SCAN nrows (expected) = %i\n' % npts2)
        self.MasterFile.write('#SCAN time per row (expected) [s] = %.2f\n' % scantime)
        self.MasterFile.write('#Y positioner = %s\n' %  str(pos2))
        self.MasterFile.write('#Y start, stop, step = %f, %f, %f \n' %  (start2, stop2, step2))
        self.MasterFile.write('#------------------------------------\n')
        self.MasterFile.write('# yposition  xmap_file  struck_file  xps_file    time\n')

        kw = dict(scantime=scantime, accel=accel,
                  filename=self.mapper.filename, filenumber=0,
                  dimension=dimension, npulses=npts1, scan_pt=1)

        fscan = dict(name='foreward', xstart=start1, xstop=stop1, xstep=step1)
        rscan = dict(name='backward', xstart=stop1,  xstop=start1, xstep=step1)
        if 'y' == self.mapconf.get('fast_positioners', pos1).lower():
            fscan = dict(name='foreward', ystart=start1, ystop=stop1, ystep=step1)
            rscan = dict(name='backward', ystart=stop1,  ystop=start1, ystep=step1)

        fscan.update(kw)
        rscan.update(kw)        

        self.traj.DefineTrajectory(**fscan)
        self.dtime.add('trajectory defined')
        if dimension > 1:
            self.traj.DefineTrajectory(**rscan)

        self.dtime.add('put pos1 %s %f' % (pos1, start1))
        self.PV(pos1).put(start1, wait=False)

        if dimension > 1:
            self.PV(pos2).put(start2, wait=False)
        self.dtime.add('put pos1/pos2 complete')

        self.prescan(**kw)

        irow = 0
        while irow < npts2:
            irow = irow + 1
            self.dtime.add('map row %i ' % irow)
            traj, p1_this, p1_next = [('backward', stop1, start1),
                                      ('foreward', start1, stop1)][irow%2]
            if dimension > 1:
                self.mapper.info =  'Row %i / %i (%s)' % (irow,npts2,traj)
            else:
                self.mapper.info =  'Scanning'
            self.mapper.setTime()

            self.PV(pos1).put(p1_this, wait=True)
            if dimension > 1:
                self.PV(pos2).put(start2 + (irow-1)*step2, wait=True)
            self.dtime.add('positioners ready %.5f' % p1_this)

            ## self.Wait_XMAPWrite()

            kw['filenumber'] = irow
            kw['scan_pt']    = irow
            if self.state == 'abort':
                self.mapper.message = 'Map aborted before starting!'
                break
            ypos = 0
            if dimension > 1:
                ypos = self.PV(pos2).get()

            self.ExecuteTrajectory(name=traj, **kw)

            if dimension > 1:
                self.PV(pos2).put(start2 + irow*step2, wait=False)            
            self.PV(pos1).put(p1_next, wait=False)

            if USE_MONO_CONTROL:
                self.mono_control.CheckMonoPitch()

            xmap_fnum = self.Wait_XMAPWrite(i = irow)
            # print ' row  ', irow, xmap_fnum
            if irow > xmap_fnum:
                print 'Missing XMAP File'
                irow = irow - 1
            else:
                # note: don't write xps/struck data if xmap file is missing!
                gather_lines, rowinfo = self.WriteRowData(ypos=ypos, npts=npts1, **kw)

                if gather_lines < npts1: 
                    print 'Bad XPS data !! ', gather_lines, npts1
                    # self.MasterFile.write('#WARN bad xps data: row %i\n' % (irow))
                    irow = irow - 1
                else:
                    self.MasterFile.write(rowinfo)
                    self.MasterFile.flush()

            # print 'set mapper.nrow : ', irow
            self.mapper.setNrow(irow)
            if self.state == 'abort':
                self.mapper.message = 'Map aborted!'
                break

        self.restore_positions()
        self.mapper.info = "Finished"
        self.dtime.add('after writing last row')
        self.postscan()
        self.dtime.add('map after postscan')

    def ExecuteTrajectory(self, name='line', filename='TestMap',
                          scan_pt=1, scantime=10, dimension=1,
                          npulses=11, wait=False, **kw):

        if USE_XMAP:
            t0 = time.time()
            self.xmap.setFileNumber(scan_pt)
            self.xmap.start()
            self.xmap.FileCaptureOn()

            while self.xmap.GetAcquire() != 1:
                if time.time() - t0 > 5.0 : 
                    break
                self.xmap.start()
                self.xmap.FileCaptureOn()
            self.dtime.add('exec: xmap armed? %s ' % (repr(1==self.xmap.GetAcquire())))

        if USE_STRUCK:
            self.struck.start()

        self.mapper.PV('Abort').put(0)
        # self.mapper.message = "scanning %s" % name
       
        scan_thread = Thread(target=self.traj.RunTrajectory, name='scanner',
                             kwargs=dict(name=name, save=False))
        scan_thread.start()
        self.state = 'scanning'        
        t0 = time.time()
        self.dtime.add('ExecTraj: traj thread begun')        

        if not self.ROI_Written:
            xmap_prefix = self.mapconf.get('general', 'xmap')
            fout    = os.path.join(self.workdir, 'ROI.dat')
            try:
                Write_MED_header(prefix=xmap_prefix,nmca=4,filename=fout)
                self.ROI_Written = True
                self.dtime.add('ExecTraj: ROI done')
            except:
                pass
        if not self.ENV_Written:
            fout    = os.path.join(self.workdir, 'Environ.dat')
            self.Write_EnvData(filename=fout)
            self.ENV_Written = True
            self.dtime.add('ExecTraj: Env done')

        # now wait for scanning thread to complete
        scan_thread.join()  # max(0.1, scantime-5.0))        
        while scan_thread.isAlive() and time.time()-t0 < scantime+5.0:
            time.sleep(0.001)
        self.dtime.add('ExecTraj: Scan Thread complete.')        
        time.sleep(0.002)


    def WriteRowData(self, filename='TestMap', scan_pt=1, ypos=0, npts=None, **kw):
        # NOTE:!!  should return here, write files separately.
        strk_fname = self.make_filename('struck', scan_pt)
        xmap_fname = self.make_filename('xmap', scan_pt)
        xps_fname  = self.make_filename('xps', scan_pt)
        # saver_thread = Thread(target=self.traj.SaveResults, name='saver',
        # args=(xps_fname,))
        # saver_thread.start()

        self.traj.SaveResults(xps_fname)

        if USE_XMAP:
            self.xmap.stop()
            xmap_fname = nativepath(self.xmap.getFileNameByIndex(scan_pt))[:-1]

        if USE_STRUCK:
            self.struck.stop()
            self.struck.saveMCAdata(fname=strk_fname, npts=npts, ignore_prefix='_')
        # wait for saving of gathering file to complete
        # saver_thread.join()            

        rowinfo = self.make_rowinfo(xmap_fname, strk_fname, xps_fname, ypos=ypos)
        self.dtime.add('Write Row Data: done')
        return (self.traj.nlines_out, rowinfo)

    def make_filename(self, name, number):
        fout = os.path.join(self.workdir, "%s.%4.4i" % (name,number))
        return  os.path.abspath(fout)

    def make_rowinfo(self, x_fname, s_fname, g_fname, ypos=0):
        x = os.path.split(x_fname)[1]
        s = os.path.split(s_fname)[1]
        g = os.path.split(g_fname)[1]
        dt = time.time() - self.scan_t0
        return '%.4f %s %s %s %9.2f\n' % (ypos,x,s,g,dt)

    def Write_EnvData(self,filename='Environ.dat'):
        fh = open(filename,'w')
        for pvname, title, pv in self.env_pvs:
            val = pv.get(as_string=True)
            fh.write("; %s (%s) = %s \n" % (title,pvname,val))
        fh.close()

    def Connect_ENV_PVs(self):
        self.env_pvs  = []
        envfile = self.mapconf.get('general', 'envfile')
        try:
            f = open(envfile,'r')
            lines = f.readlines()
            f.close()
        except:
            print 'ENV_FILE: could not read ', envfile
            return
        for line in lines:
            words = line.split(' ', 1)
            pvname =words[0].strip().rstrip()
            if len(pvname) < 2 or pvname.startswith('#'): continue
            title = pvname
            try:
                title = words[1][:-1].strip().rstrip()
            except:
                pass
            if pvname not in self.env_pvs:
                self.env_pvs.append((pvname, title, epics.PV(pvname)))
        return
           
    def setIdle(self):
        self.state = self.mapper.info = 'idle'
        self.mapper.ClearAbort()

    def StartScan(self):
        self.dtime.clear()
        self.setWorkingDirectory()

        self.mapconf.Read(os.path.abspath(self.mapper.scanfile) ) 
        self.mapper.message = 'preparing scan...'
        self.mapper.info  = 'Starting'

        self.MasterFile = open(os.path.join(self.workdir, 'Master.dat'), 'w')

        self.mapconf.Save(os.path.join(self.workdir, 'Scan.cnf'))

        scan = self.mapconf.get('scan')
        scan['scantime'] = scan['time1']
        if scan['dimension'] == 1:
            scan['pos2'] = None
            scan['start2'] = 0
            scan['stop2'] = 0

        self.mapscan(**scan)
        self.MasterFile.close()
        self.mapper.message = 'Scan finished: %s' % (scan['filename'])
        self.setIdle()
        # self.dtime.show()
        
    def mainloop(self):
        print 'FastMap collector starting up....'
        self.mapper.ClearAbort()
        self.mapper.setTime()
        self.mapper.message = 'Ready to Start Map'
        self.mapper.info = 'Ready'

        epics.poll()
        time.sleep(0.10)        
        t0 = time.time()
        self.state = 'idle'

        print 'FastMap collector ready.'
        while True:
            try:
                epics.poll()
                if time.time()-t0 > 0.2:
                    t0 = time.time()
                    self.mapper.setTime()                    
                if self.state  == 'start':
                    self.mapper.AbortScan()
                    self.StartScan()
                elif self.state  == 'abort':
                    print 'state abort! '
                    self.mapper.ClearAbort()
                    self.state = 'idle'
                elif self.state  == 'pending':
                    print 'state pending '  
                elif self.state  == 'reboot':
                    self.mapper.info = 'Rebooting'
                    sys.exit()
                elif self.state == 'waiting':
                    self.mapper.ClearAbort()
                elif self.state  != 'idle':
                    print 'state ', self.state
                time.sleep(0.025)
            except KeyboardInterrupt:
                break

if __name__ == '__main__':
    t = TrajectoryScan(configfile='default.scn')
    t.mainloop()
