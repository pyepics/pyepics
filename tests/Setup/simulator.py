#!/usr/bin/env python
#
# test simulator for testing pyepics.
# 
# this script changes values definied in the pydebug.db, which all 
# the tests scripts use.  This script must be running (somewhere)
# for many of the tests (callbacks, etc) to work. 

# 
import epics
import time
import random
import numpy

prefix = 'Py:'

global NEEDS_INIT

NEEDS_INIT = True
SLEEP_TIME = 0.10

def onConnect(pvname=None, conn=None, **kws):
    global NEEDS_INIT
    NEEDS_INIT = conn

        
def make_pvs(*args, **kwds):
    # print "Make PVS '  ", prefix,  args
    # print  [("%s%s" % (prefix, name)) for name in args]
    pvlist = [epics.PV("%s%s" % (prefix, name)) for name in args]
    for pv in pvlist:
        pv.connect()
        pv.connection_callbacks.append(onConnect)
    return pvlist

mbbos    = make_pvs("mbbo1","mbbo2")
pause_pv = make_pvs("pause",)[0]
longs    = make_pvs("long1", "long2", "long3", "long4")
strs     = make_pvs("str1", "str2")
analogs  =  make_pvs("ao1", "ai1", "ao2", "ao3")
binaries = make_pvs("bo1", "bi1")

char_waves = make_pvs("char128", "char256", "char2k", "char64k")
double_waves = make_pvs("double128", "double2k", "double64k")
long_waves = make_pvs("long128", "long2k", "long64k")
str_waves = make_pvs("string128", "string2k", "string64k")

subarrays =  make_pvs("subArr1", "subArr2", "subArr3", "subArr4" )
subarray_driver = make_pvs("wave_test",)[0]


def initialize_data():
    subarray_driver.put(numpy.arange(64)/12.0)
    
    for p in mbbos:
        p.put(1)
        
    for i, p in enumerate(longs):    p.put((i+1))

    for i, p in enumerate(strs):     p.put("String %s" % (i+1))

    for i, p in enumerate(binaries):   p.put((i+1))

    for i, p in enumerate(analogs):   p.put((i+1)*1.7135000 )
    
    epics.caput('Py:ao1.EGU', 'microns')
    epics.caput('Py:ao1.PREC', 4)
    epics.caput('Py:ai1.PREC', 2)
    epics.caput('Py:ao2.PREC', 3)


        
    char_waves[0].put([60+random.randrange(30) for i in range(128)])
    char_waves[1].put([random.randrange(256) for i in range(256)])
    char_waves[2].put([random.randrange(256) for i in range(2048)])
    char_waves[3].put([random.randrange(256) for i in range(65536)])
    

    long_waves[0].put([i+random.randrange(2) for i in range(128)])
    long_waves[1].put([i+random.randrange(128) for i in range(2048)])
    long_waves[2].put([i  for i in range(65536)])
    
    double_waves[0].put([i+random.randrange(2) for i in range(128)])
    double_waves[1].put([random.random() for i in range(2048)])
    double_waves[2].put([random.random() for i in range(65536)])

    pause_pv.put(0)
    str_waves[0].put([" String %i" % (i+1) for i in range(128)])
    print 'Data initialized'

text = '''line 1
this is line 2
and line 3
here is another line
this is the 5th line
line 6
line 7
line 8
line 9
line 10
line 11
'''.split('\n')

start_time = time.time()
count = 0
long_update = 0
lcount =1

while True:
    if NEEDS_INIT:
        initialize_data()
        time.sleep(SLEEP_TIME)
        NEEDS_INIT = False
        
    time.sleep(SLEEP_TIME) 
        
    count = count + 1
    if count  == 3: print 'running'
    if count > 99999999: count = 1
        
    t0 = time.time()
    if pause_pv.get() == 1:
        # pause for up to 15 seconds if pause was selected
        t0 = time.time()
        while time.time()-t0 < 15:
            time.sleep(SLEEP_TIME)
            if pause_pv.get() == 0:
                break
        pause_pv.put(0)
    noise = numpy.random.normal

    analogs[0].put( 100*(random.random()-0.5))
    analogs[1].put( 76.54321*(time.time()-start_time))
    analogs[2].put( 0.3*numpy.sin(time.time() / 2.302) + noise(scale=0.4)  )
    char_waves[0].put([45+random.randrange(64) for i in range(128)])

    if count % 3 == 0:
        analogs[3].put( numpy.exp((max(0.001,  noise(scale=0.03)
                                       + numpy.sqrt((count/16.0) % 87.)))))

        long_waves[1].put([i+random.randrange(128) for i in range(2048)])
        str_waves[0].put(["Str%i_%.3f" % (i+1, 100*random.random()) for i in range(128)])
    
    if t0-long_update >= 1.0:
        long_update=t0
        lcount = (lcount + 1) % 10
        longs[0].put(lcount)
        char_waves[1].put(text[lcount])
        double_waves[2].put([random.random() for i in range(65536)])
        double_waves[1].put([random.random() for i in range(2048)])

