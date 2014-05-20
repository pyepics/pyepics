from __future__ import print_function

import time
import threading
import epics
import pvnames
def threaded_pvput(pv, value):
    "put-with-wait for calling in a thread"
    t0 = time.time()
    print(' - threaded_pvput starting at ', pv.get())
    pv.put(value, wait=True, timeout=10.0)
    print(' - threaded_pvput done (%.3f sec)' % (time.time()-t0))
   
if __name__ == '__main__':
    pvname = pvnames.motor2
    target = 0.55
    
    pv = epics.PV(pvname)
    pv.put(-target, wait=True)
    time.sleep(0.5)
    
    th = threading.Thread(target=threaded_pvput,
                          args=(pv, target))
    th.start()
    th.join()
    print('All Done.')
        
 
