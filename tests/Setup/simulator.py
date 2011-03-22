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
def make_pvs(*args, **kwds):
    print "Make PVS '  ", prefix,  args
    print  [("%s%s" % (prefix, name)) for name in args]
    s = [epics.PV("%s%s" % (prefix, name)) for name in args]
    for i in s: i.connect()
    return s

mbbos  = make_pvs("mbbo1","mbbo2")
pause_pv = make_pvs("pause",)[0]
longs = make_pvs("long1", "long2", "long3", "long4")
strs    = make_pvs("str1", "str2")
analogs =  make_pvs("ao1", "ai1", "ao2", "ao3")
binaries = make_pvs("bo1", "bi1")

char_waves = make_pvs("char128", "char256", "char2k", "char64k")
double_waves = make_pvs("double128", "double2k", "double64k")
long_waves = make_pvs("long128", "long2k", "long64k")
str_waves = make_pvs("string128", "string2k", "string64k")

subarrays =  make_pvs("subArr1", "subArr2", "subArr3", "subArr4" )
subarray_driver = make_pvs("wave_test",)[0]

subarray_driver.put(numpy.arange(64)/10.0)

# initialize data
for p in mbbos:    p.put(1)

for i, p in enumerate(longs):    p.put((i+1))

for i, p in enumerate(strs):     p.put("String %s" % (i+1))

for i, p in enumerate(analogs):   p.put((i+1)*1.7135000 )

epics.caput('Py:ao1.EGU', 'microns')
epics.caput('Py:ao1.PREC', 4)
epics.caput('Py:ai1.PREC', 2)

for i, p in enumerate(binaries):   p.put((i+1))

char_waves[0].put('a string')

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

t0 = time.time()
count = 0
long_update = 0
lcount =1

epics.ca.show_cache()
while True:
    time.sleep(0.1) 
    count = count + 1
    # pause for up to 15 seconds if pause was selected
    t0 = time.time()
    while pause_pv.get() == 1:
        time.sleep(0.5)
        if time.time() - t0 > 15:
            pause_pv.put(0)


    analogs[0].put(count/1000.0)
    analogs[1].put(1.2*(time.time()-t0))
    tx = time.time()
    if tx-long_update >= 1:
        long_update=tx
        lcount = (lcount + 1) % 10
        longs[0].put(lcount)
        print text[lcount]
        char_waves[1].put(text[lcount])



