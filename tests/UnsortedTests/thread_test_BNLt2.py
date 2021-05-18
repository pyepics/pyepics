
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


def onChanges(pvname=None, value=None, char_value=None, host=None, **kws):
    print('   %s = %s / %s ' % (pvname, char_value, host))

pvs = []
for pvname in pvlist_a + pvlist_b:
    pvs.append(epics.PV(pvname))

t0 = time.time()
while time.time()-t0 < 60:
    try:
        time.sleep(0.1)
        for pv in pvs:
            x = (pv.pvname, pv.get(as_string=True))
    except KeyboardInterrupt:
        break

print('Done')
