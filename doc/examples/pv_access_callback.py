import epics
import time

def access_rights_callback(read_access, write_access, pv=None):
    print(f'{pv.pvname}: read={read_access}, write={write_access}')

mypv = epics.get_pv('PyTest:ao1.VAL', access_callback=access_rights_callback)

print('Now wait for changes')
expire_time = time.time() + 60.
while time.time() < expire_time:
    time.sleep(0.01)
print('Done.')
