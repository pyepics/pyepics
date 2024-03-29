import time
import epics
import pvnames
import random
import numpy
import sys

def test_subarray():
    driver = epics.PV(pvnames.subarr_driver)
    sub1   = epics.PV(pvnames.subarr1)
    sub2   = epics.PV(pvnames.subarr2)
    sub3   = epics.PV(pvnames.subarr3)
    sub4   = epics.PV(pvnames.subarr4)
    s1_0 =  int(epics.caget("%s.INDX" % pvnames.subarr1))
    s2_0 =  int(epics.caget("%s.INDX" % pvnames.subarr2))
    s3_0 =  int(epics.caget("%s.INDX" % pvnames.subarr3))
    s4_0 =  int(epics.caget("%s.INDX" % pvnames.subarr4))

    s1_n =  int(epics.caget("%s.NELM" % pvnames.subarr1))
    s2_n =  int(epics.caget("%s.NELM" % pvnames.subarr2))
    s3_n =  int(epics.caget("%s.NELM" % pvnames.subarr3))
    s4_n =  int(epics.caget("%s.NELM" % pvnames.subarr4))

    npts = len(driver.get())

    for i in range(10):
        driver.put([100*random.random() for x in range(npts)])
        time.sleep(0.1)

        full = driver.get()
        sys.stdout.write("%s\n" % full)
        assert all( [all( sub1.get() == full[s1_0:s1_n+s1_0]),
                     all( sub2.get() == full[s2_0:s2_n+s2_0]),
                     all( sub3.get() == full[s3_0:s3_n+s3_0]),
                     all( sub4.get() == full[s4_0:s4_n+s4_0])
                     ])
