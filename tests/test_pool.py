from __future__ import print_function
from contextlib import contextmanager
import epics
import multiprocessing as mp

import pvnames
PVS = [pvnames.double_pv, pvnames.double_pv2]


@contextmanager
def pool_ctx():
    pool = epics.CAPool()
    yield pool
    pool.close()
    pool.join()

def test_caget():
    with pool_ctx() as pool:
        print('Using caget() in subprocess pools:')
        print('\tpool.process =', pool.Process)
        values = pool.map(epics.caget, PVS)

        for pv, value in zip(PVS, values):
            print('\t%s = %s' % (pv, value))


def _manager_test_fcn(pv_dict, pv):
    pv_dict[pv] = epics.caget(pv)


def test_manager():
    '''
    Fill up a shared dictionary using a manager
    '''
    with pool_ctx() as pool:
        print('Multiprocessing Manager test:')

        manager = mp.Manager()
        pv_dict = manager.dict()

        results = [pool.apply_async(_manager_test_fcn, [pv_dict, pv])
                   for pv in PVS]

    print('\tResulting pv dictionary: %s' % pv_dict)
