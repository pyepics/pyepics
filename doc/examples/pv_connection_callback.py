import epics
import time

def onConnectionChange(pvname=None, conn= None, **kws):
    print(f'PV connection status changed: {pvname} {conn}')

def onValueChange(pvname=None, value=None, host=None, **kws):
    print(f'PV value changed: {pvname} ({host})  {value}')

mypv = epics.get_pv('PyTest:ao1.VAL',
                    connection_callback= onConnectionChange,
                    callback= onValueChange)

mypv.get()

print('Now wait for changes')
expire_time = time.time() + 60.
while time.time() < expire_time:
    time.sleep(0.01)
print('Done.')
