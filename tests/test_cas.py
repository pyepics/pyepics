import time
import pytest
import subprocess
from tempfile import NamedTemporaryFile as NTF
import epics


cas_test_db = '''
                record(ao, "test:ao") {
                    field(ASG, "rps_threshold")
                    field(DRVH, "10")
                    field(DRVL, "0")
                }

                record(bo, "test:bo") {
                    field(ASG, "rps_lock")
                    field(ZNAM, "OUT")
                    field(ONAM, "IN")
                }

                record(ao, "test:ao2") {
                    field(DRVH, "5")
                    field(DRVL, "1")
                }

                record(bo, "test:permit") {
                    field(VAL, "0")
                    field(PINI, "1")
                    field(ZNAM, "DISABLED")
                    field(ONAM, "ENABLED")
                }
            '''

cas_rules = '''
                ASG(DEFAULT) {
                    RULE(1,READ)
                    RULE(1,WRITE,TRAPWRITE)
                }

                ASG(rps_threshold) {
                    INPA("$(P):permit")
                    RULE(1, READ)
                    RULE(0, WRITE, TRAPWRITE) {
                        CALC("A=1")
                    }
                    RULE(1, WRITE, TRAPWRITE) {
                        CALC("A=0")
                    }
                }

                ASG(rps_lock) {
                    INPA("$(P):permit")
                    RULE(1, READ)
                    RULE(1, WRITE, TRAPWRITE) {
                        CALC("A=0")
                    }
                }
            '''

# use yield_fixture() for compatibility with pytest < 2.10
@pytest.yield_fixture(scope='module')
def softioc():
    with NTF(mode='w+') as cf, NTF(mode='w+') as df:
        cf.write(cas_rules)
        cf.flush()
        df.write(cas_test_db)
        df.flush()

        proc = subprocess.Popen(['softIoc', '-D',
                                 '/home/travis/mc/envs/testenv/epics/dbd/softIoc.dbd',
                                 '-m', 'P=test', '-a', cf.name,
                                 '-d', df.name],
                                 stdin=subprocess.PIPE,
                                 stdout=subprocess.PIPE)
        yield proc

        try:
            proc.kill()
            proc.wait()
        except OSError:
            pass


@pytest.yield_fixture(scope='module')
def pvs():
    pvlist = ['test:ao', 'test:ao.DRVH', 'test:bo', 'test:ao2',
              'test:permit']
    pvs = dict()
    for name in pvlist:
        pv = epics.get_pv(name)
        pv.wait_for_connection()
        pvs[pv.pvname] = pv

    yield pvs
    for pv in pvs.values():
        pv.disconnect()


def test_connected(softioc, pvs):
    for pv in pvs.values():
        assert pv.connected

def test_permit_disabled(softioc, pvs):
    # with the permit disabled, all test pvs should be readable/writable
    for pv in pvs.values():
        assert pv.read_access and pv.write_access

def test_permit_enabled(softioc, pvs):
    # set the run-permit
    pvs['test:permit'].put(1, wait=True)
    assert pvs['test:permit'].get(as_string=True, use_monitor=False) == 'ENABLED'

    # rps_lock rule should disable write access
    assert pvs['test:bo'].write_access is False
    with pytest.raises(epics.ca.CASeverityException):
        pvs['test:bo'].put(1, wait=True)

    # rps_threshold rule should disable write access to metadata, not VAL
    assert pvs['test:ao'].write_access is True
    assert pvs['test:ao.DRVH'].write_access is False
    with pytest.raises(epics.ca.CASeverityException):
        pvs['test:ao.DRVH'].put(100, wait=True)

def test_pv_access_event_callback(softioc, pvs):
    # clear the run-permit
    pvs['test:permit'].put(0, wait=True)
    assert pvs['test:permit'].get(as_string=True, use_monitor=False) == 'DISABLED'

    def lcb(read_access, write_access, pv=None):
        assert pv.read_access == read_access
        assert pv.write_access == write_access
        pv.flag = True

    bo = epics.get_pv('test:bo', access_callback=lcb)
    bo.flag = False

    # set the run-permit to trigger an access rights event
    pvs['test:permit'].put(1, wait=True)
    assert pvs['test:permit'].get(as_string=True, use_monitor=False) == 'ENABLED'

    assert bo.flag is True
    bo.access_callbacks = []


def test_ca_access_event_callback(softioc, pvs):
    # clear the run-permit
    pvs['test:permit'].put(0, wait=True)
    assert pvs['test:permit'].get(as_string=True, use_monitor=False) == 'DISABLED'

    bo_id = epics.ca.create_channel('test:bo')
    assert bo_id is not None

    def lcb(read_access, write_access):
        assert read_access and write_access
        lcb.sentinal = True

    lcb.sentinal = False
    epics.ca.replace_access_rights_event(bo_id, callback=lcb)

    assert lcb.sentinal is True
    epics.ca.clear_channel(bo_id)


def test_connection_callback(softioc, pvs):
    results = []

    def callback(conn, **kwargs):
        results.append(conn)

    pv = epics.PV('test:ao', connection_callback=callback)
    pv.wait_for_connection()
    softioc.kill()
    softioc.wait()

    t0 = time.time()
    while pv.connected and (time.time() - t0) < 5:
        time.sleep(0.1)

    assert True in results
    assert False in results
