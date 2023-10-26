import epics
import epics.ca
import epics.pv

import time
import subprocess
import pvnames
enabledpv = pvnames.clear_cache_enabled
beaconspv = pvnames.clear_cache_beacons


change_count = 0


def onChanges(pvname=None, value=None, **kw):
    global change_count
    change_count += 1


def run():
    for beaconpv in beaconspv:
        value = epics.caget(beaconpv)
        assert value is not None, \
            "PV {} is offline".format(beaconpv)
    time.sleep(0.2)
    epics.ca.clear_cache()


def test_use_monitor():
    # This test verifies that clear_cache clears subscriptions created by
    # use_monitor=True prior clearing channels.
    # Otherwise, EPICS will crash on an attempt to clear subscription
    # on a cleared channel.
    assert epics.caget(enabledpv, use_monitor=True) is not None, \
        "PV {} is offline".format(enabledpv)

    pv = epics.pv.get_pv(enabledpv)

    epics.ca.clear_cache()

    pv.disconnect()


def test_subscribe():
    # This test verifies that clear_cache does not
    # leave registered callbacks behind which may cause
    # a crash on shutdown on Linux randomly.
    # Therefore, the test runs itself
    # in a new process multiple times.
    # This test takes quite long time to complete.
    assert epics.caget(enabledpv) is not None, \
        "PV {} is offline".format(enabledpv)
    epics.caput(enabledpv, 1)
    for run in range(20):
        try:
            subprocess.run(['python', __file__], check=True)
        except subprocess.CalledProcessError as err:
            epics.caput(enabledpv, 0)
            if err.returncode > 0:
                error = 'the return code {}'.format(err.returncode)
            else:
                error = 'the signal {}'.format(-err.returncode)
            assert False, "Run {} failed due to {}".format(
                run,
                error)
    epics.caput(enabledpv, 0)


if (__name__ == '__main__'):
    run()
