#!/usr/bin/python 
import epics
import time
import os

class mapper(epics.Device):
    """ 
    Fast Map Database
    """
    attrs = ('Start', 'Abort', 'scanfile', 'info', 'status', 'message',
             'filename', 'basedir', 'workdir',
             'nrow', 'maxrow', 'npts', 'TSTAMP','UNIXTS')
    
    def __init__(self,prefix,filename=None):
        self.prefix = prefix
        epics.Device.__init__(self, prefix, attrs=self.attrs)
        
    def StartScan(self,filename=None,scanfile=None):
        if filename is not None:
            self.filename=filename
        if scanfile is not None:
            self.scanfile=scanfile

        epics.poll()
        self.put('message','starting...')
        self.put('Start',1)

    def AbortScan(self,filename=None):
        self.put('Abort',1)

    def ClearAbort(self):
        self.put('Abort',0)
        self.put('Start',0)
        
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
        self.put('info',msg)
        
    def pv_property(attr, as_string=False,wait=False):
        return property(lambda self:     self.get(attr,as_string=as_string),
                        lambda self,val: self.put(attr,val,wait=wait),
                        None, None)

    basedir  = pv_property('basedir',  as_string=True)
    workdir  = pv_property('workdir',  as_string=True)    
    filename = pv_property('filename', as_string=True)
    scanfile = pv_property('scanfile', as_string=True)    
    message  = pv_property('message',  as_string=True)    
    info     = pv_property('info',     as_string=True)    
    status   = pv_property('status',   as_string=True)    
    npts     = pv_property('npts')
    # nrow     = pv_property('nrow')
    maxrow   = pv_property('maxrow')
    tstamp   = pv_property('TSTAMP')
    unixts   = pv_property('UNIXTS')
    start    = pv_property('Start')
    abort    = pv_property('Abort')
    


    
if __name__ == '__main__':

    m = mapper('13XRM:map:')
    
    print m.dir
    
