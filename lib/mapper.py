#!/usr/bin/python 
import epics
import time
import os

class mapper(epics.Device):
    """ 
    Fast Map Database
    """
    _attrs = ('Start', 'Abort', 'scanfile', 'info', 'status', 'message',
             'filename', 'basedir', 'workdir',
             'nrow', 'maxrow', 'npts', 'TSTAMP','UNIXTS')
    
    def __init__(self,prefix,filename=None):
        self._prefix = prefix
        epics.Device.__init__(self, self._prefix,
                              attrs=self._attrs)
        
    def StartScan(self,filename=None,scanfile=None):
        if filename is not None:
            self.filename=filename
        if scanfile is not None:
            self.scanfile=scanfile

        epics.poll()
        self.put('message','starting...')
        self.put('Start',1)

    def AbortScan(self,filename=None):
        self.Abort = 1

    def ClearAbort(self):
        self.Abort = 0
        time.sleep(.025)
        self.Start = 0
        
    def setTime(self):
        "Set Time"
        self.put('UNIXTS',  time.time())
        self.put('TSTAMP',  time.strftime('%d-%b-%y %H:%M:%S'))

    def setMessage(self,msg):
        "Set message"
        self.put('message',  msg)

    def setNrow(self,nrow,maxrow=None):
        self.put('nrow', nrow)
        if maxrow is not None: self.put('maxrow', maxrow)

    def setNpoints(self,npts):
        self.put('npts', npts)
        
    def setInfo(self,msg):
        self.put('info',  msg)
        
    def __Fget(self, attr):
        return self.get(attr, as_string=True)

    def __Fput(self, attr, val):
        return self.put(attr, val)
    
    def pv_property(attr):
        return property(lambda self:     self.__Fget(attr), 
                        lambda self, val: self.__Fput(attr, val),
                        None, None)

    basedir  = pv_property('basedir')
    workdir  = pv_property('workdir')
    filename = pv_property('filename')
    scanfile = pv_property('scanfile')
    info     = pv_property('info')
    message  = pv_property('message')
     
if __name__ == '__main__':

    m = mapper('13XRM:map:')
 
    def as_string(carray):
        return ''.join([chr(i) for i in carray if i>0])
    
    print m
    print m.basedir
    print 'info= ', m.info
    print 'p_info ', m.info

    # print m.get('info', as_string=True)
    # print 'info= ', m.info, m.get('info'), m.get('info', as_string=True), as_string(m.info)
    
    print 'msg = ', m.message # , m.get('message', as_string=True)
    print 'unix ts: ', m.UNIXTS, '// ', m.TSTAMP
    
    print m.get('basedir', as_string=True)

