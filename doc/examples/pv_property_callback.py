import epics
import time
def onChange(pvname, value, units='x', **kws):
    print(f'PV changed: {pvname}, value={value}, units={units}')

mypc = epics.get_pv('PyTest:ao1.VAL', form='ctrl',
                    auto_monitor=epics.ca.dbr.DBE_VALUE|epics.ca.dbr.DBE_PROPERTY,
                    callback=onChange)

print('Now wait for changes')
expire_time = time.time() + 60.
while time.time() < expire_time:
    time.sleep(0.01)
print('Done.')
