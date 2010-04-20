import time
import epics 
p = epics.PV('13IDA:DMM2Ch9_calc.VAL', auto_monitor= False)
def onChange(pvname=None,char_value=None,value=None,**kw):
    print pvname, value, time.ctime()
p.add_callback(onChange)

t0 = time.time()
p.get()
while time.time()-t0 < 20:
    print p.get()
    time.sleep(0.1)
    
