import pytest
import subprocess
import pkg_resources
import epics


# use yield_fixture() for compatibility with pytest < 2.10
@pytest.yield_fixture(scope='module')
def softioc():
    cas_rules = pkg_resources.resource_filename('rps',
                                                '../test/crit_sig_rules.cfg')
    cas_test_db = pkg_resources.resource_filename('rps', '../test/cas_test.db')
    proc = subprocess.Popen(['softIoc', '-m', 'P=test', '-a', cas_rules,
                             '-d', cas_test_db],
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
