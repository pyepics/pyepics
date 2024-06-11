import epics
import time
def onChanges(pvname=None, value=None, char_value=None, **kw):
    print('PV Changed! ', pvname, char_value, time.ctime())

mypv = epics.get_pv('PyTest:ao1.VAL', callback=onChanges)

print('Now wait for changes')
expire_time = time.time() + 60.
while time.time() < expire_time:
    time.sleep(0.01)
print('Done.')
