
import time
from  sys import stdout
from threading import Thread
import epics
from epics.ca import CAThread


pvlist_a = ('S14A:P0:mswAve:x:AdjustedCC',
            'S14A:P0:ms:x:SetpointAO',
            'S13C:P0:mswAve:x:AdjustedCC', 
            'S13C:P0:ms:x:SetpointAO', 
            'S13C:P0:mswAve:x:ErrorCC', 
            'S13B:P0:mswAve:x:AdjustedCC',
            'S13B:P0:ms:x:SetpointAO',
            'S13B:P0:mswAve:x:ErrorCC')

pvlist_b = ('S13B:P0:mswAve:x:AdjustedCC',
            'S13B:P0:ms:x:SetpointAO',
            'S13B:P0:mswAve:x:ErrorCC',
            'S13ds:ID:SrcPt:xAngleM', 
            'S13ds:ID:SrcPt:xPositionM',
            'S13ds:ID:SrcPt:yAngleM',
            'S13ds:ID:SrcPt:yPositionM')


def run_test(runtime=1, pvnames=None,  run_name='thread c'):
    msg = '-> thread "%s" will run for %.3f sec, monitoring %s\n'
    stdout.write(msg % (run_name, runtime, pvnames))
    def onChanges(pvname=None, value=None, char_value=None, **kw):
        stdout.write('   %s = %s (%s)\n' % (pvname, char_value, run_name))
        stdout.flush()

    # epics.ca.use_initial_context()   #  epics.ca.create_context()
    start_time = time.time()
    pvs = [epics.PV(pvn, callback=onChanges) for pvn in pvnames]

    while time.time()-start_time < runtime:
        time.sleep(0.001)

    [p.clear_callbacks() for p in pvs]
    stdout.write( 'Completed Thread  %s\n' % ( run_name))

stdout.write( "First, create a PV in the main thread:\n")
for pvname in pvlist_a + pvlist_b:
    p = epics.PV(pvname)
    p.connect()
    p.get()
    print(p.info)

stdout.write("Run 2 Background Threads simultaneously:\n")
th1 = CAThread(target=run_test,args=(30, pvlist_a,  'A'))
th1.start()

th2 = CAThread(target=run_test,args=(60, pvlist_b, 'B'))
th2.start()

th2.join()
th1.join()
stdout.write('Done\n')
