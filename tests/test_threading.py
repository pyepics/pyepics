#!/usr/bin/python
import sys
import time
import threading
import EpicsCA
from  urllib import urlopen

class PV_Thread(threading.Thread):
    def __init__(self, pvlist,delay=.5):
        threading.Thread.__init__(self)
        self.pvs = []
        for i in pvlist:
            x = EpicsCA.PV(i)
            self.pvs.append(x)
            x.set_monitor(callback=self.onChanges,kw={'pv':x})
            x.get()
        self.delay = delay
        self.count = 0
        
    def onChanges(self,pv=None, **kw):
        print "onchanges: ", time.ctime(), pv.pvname,pv.value
        
    def run(self):
        print 'starting PV thread  '
        while self.count <10:
            # Without this, onChanges is NEVER called.
            # With this, onChanges is ALWAYS called.
            # self.pv.search() 
            #
            try:
                for i in self.pvs:
                    x = EpicsCA.PV(i.pvname)
                    print '  --- ', i.pvname, i.check_monitor(),  x.value
                    
            except KeyboardInterrupt:
                print 'keyboard '
                sys.exit()
            time.sleep(self.delay)
            print 'mon: ',self.count
            self.count = self.count+1
        print 'ending PV thread '

class FetchURLThread(threading.Thread):
    def __init__(self, url, name,delay=5.0):
        threading.Thread.__init__(self)
        self.setName(name)
        self.url = url
        self.delay = delay
        self.count = 0
        print 'start collection thread for url: ', url
        
    def run(self):
        while self.count < 7:
            try:
                self.data = urlopen(self.url).read()
                delay = self.delay
                self.save_url_data("%s.html" % self.getName())
            except IOError:
                delay = self.archive_minutes * 60. * 2.0
                print self.url, ' not connected. waiting for reconnect. '
            except KeyboardInterrupt:
                print 'keyboard '                
                self.stop()
                sys.exit()                
            time.sleep(delay)
            self.count =self.count + 1

    def save_url_data(self,filename):
        out = open(filename, "wb")
        out.write(self.data)
        out.close()
        print ' fetch url wrote ', filename, len(self.data)
        

if __name__ == '__main__':
    pvlist = ('BL13:srCurrent', '13BMA:DMM1Ch3_calc') # , '13BMA:m1.VAL')
    url    = ('http://yahoo.com')
    t = PV_Thread(pvlist)
    t.start()
#     x = FetchURLThread(url, 'web')
#     x.start()
