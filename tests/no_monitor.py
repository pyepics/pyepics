from __future__ import print_function
import time
import epics 
import pvnames

p = epics.PV(pvnames.updating_pv1, auto_monitor= False)

def onChange(pvname=None,char_value=None,value=None,**kw):
    print(pvname, value, time.ctime())
p.add_callback(onChange)

t0 = time.time()
p.get()
while time.time()-t0 < 20:
    print(p.get())
    time.sleep(0.1)
    
