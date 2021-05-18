# tests caget (and so pv.get() and ca.get()) for "large arrays"
# especially for "slow networks".  
# the 3 pvs listed here are:   
#   13GEXMAP:mca1:                2048 ints (simple MCA record)
#   GSE-PIL1:image1:ArrayData    94965 longs (Pilatus 100k) 
#   13MARCCD1:image1:ArrayData  420000 ints  (MAR165)
# obviously, you'll need to alter these names
#
# TIMEOUT sets the pend_io() time.  If working with large
# arrays and/or slow networks, you may want to test for a
# suitable safe timeout.
import epics
import time
pvnames = ('13GEXMAP:mca1',
           'GSE-PIL1:image1:ArrayData',
           '13MARCCD2:image1:ArrayData',
           )

TIMEOUT = 15.0  # Timeout in seconds

for name in pvnames:
    t0 = time.time()
    value = epics.caget(name, timeout=TIMEOUT)
    dt = time.time()-t0
    if value is None:
        print( 'cannot get value for ', name)
    else:
        print( "%s: npts=%i, sum=%i, max=%i, time=%.3fs" % (name,
                                                           len(value),
                                                           value.sum(),
                                                           value.max(), dt))

print( 'done.')


