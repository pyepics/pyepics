from __future__ import print_function
import epics
import time
import multiprocessing as mp
import threading

import pvnames
PVN1 = pvnames.double_pv # 'Py:ao2'
PVN2 = pvnames.double_pv2 # 'Py:ao3'

def subprocess(*args):
    print('==subprocess==', args)
    mypvs = [epics.PV(pvname) for pvname in args]

    for i in range(10):
        time.sleep(0.750)
        out = [(p.pvname, p.get(as_string=True)) for p in mypvs]
        out = ', '.join(["%s=%s" % o for o in out])
        print('==sub (%d): %s' % (i, out))

def main_process():
    def monitor(pvname=None, char_value=None, **kwargs):
        print('--main:monitor %s=%s' % (pvname, char_value))

    print('--main:')
    pv1 = epics.PV(PVN1)
    print('--main:init %s=%s' % (PVN1, pv1.get()))
    pv1.add_callback(callback=monitor)

    try:
        proc1 = epics.CAProcess(target=subprocess,
                                args=(PVN1, PVN2))
        proc1.start()
        proc1.join()
    except KeyboardInterrupt:
        print('--main: killing subprocess')
        proc1.terminate()

    print('--main: subprocess complete')
    time.sleep(0.9)
    print('--main:final %s=%s' % (PVN1, pv1.get()))

if __name__ == '__main__':
    main_process()
