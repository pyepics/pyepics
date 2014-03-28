from __future__ import print_function
import epics
import multiprocessing as mp

import pvnames
PVS = [pvnames.double_pv, pvnames.double_pv2]


class CAPoolTest(object):
    def __enter__(self):
        self.pool = epics.CAPool()
        return self.pool

    def __exit__(self, type_, value, traceback):
        if type_ is None:
            self.pool.close()
            self.pool.join()


def caget_test():
    with CAPoolTest() as pool:
        print('Using caget() in subprocess pools:')
        print('\tpool.process =', pool.Process)
        values = pool.map(epics.caget, PVS)

        for pv, value in zip(PVS, values):
            print('\t%s = %s' % (pv, value))


def _manager_test_fcn(pv_dict, pv):
    pv_dict[pv] = epics.caget(pv)


def manager_test():
    '''
    Fill up a shared dictionary using a manager
    '''
    with CAPoolTest() as pool:
        print('Multiprocessing Manager test:')

        manager = mp.Manager()
        pv_dict = manager.dict()

        results = [pool.apply_async(_manager_test_fcn, [pv_dict, pv])
                   for pv in PVS]

    print('\tResulting pv dictionary: %s' % pv_dict)


def main():
    print('Initializing ca context in main process...')
    value = epics.caget(PVS[0])
    print('\t%s = %s' % (PVS[0], value))

    caget_test()
    manager_test()


if __name__ == '__main__':
    main()
