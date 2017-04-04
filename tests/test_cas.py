import pytest
import subprocess
import tempfile
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
    with tempfile.NamedTemporaryFile() as cf, tempfile.NamedTemporaryFile() as df:
        cf.write(cas_rules)
        cf.flush()
        df.write(cas_test_db)
        df.flush()

        proc = subprocess.Popen(['softIoc', '-m', 'P=test', '-a', cf.name,
                                 '-d', df.name],
                                 stdin=subprocess.PIPE,
                                 stdout=subprocess.PIPE)
        yield proc

        proc.kill()
        proc.wait()

@pytest.yield_fixture(scope='module')
def pvs():
    pvlist = ['test:ao', 'test:ao.DRVH', 'test:bo', 'test:ao2',
              'test:permit']
    pvs = dict()
    for name in pvlist:
        pv = epics.PV(name)
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
    assert pvs['test:permit'].get(as_string=True) == 'ENABLED'

    # rps_lock rule should disable write access
    assert pvs['test:bo'].write_access is False
    with pytest.raises(epics.ca.CASeverityException):
        pvs['test:bo'].put(1, wait=True)

    # rps_threshold rule should disable write access to metadata, not VAL
    assert pvs['test:ao'].write_access is True
    assert pvs['test:ao.DRVH'].write_access is False
    with pytest.raises(epics.ca.CASeverityException):
        pvs['test:ao.DRVH'].put(100, wait=True)
