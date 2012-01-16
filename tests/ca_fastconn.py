from epics import ca, dbr
import time
import debugtime
try:
    from collections import OrderedDict
except:
    from ordereddict import OrderedDict
dt = debugtime.debugtime()
dt.add('test of fast connection to many PVs')
pvnames = []

results = OrderedDict()

MAX_PVS = 20000


for line  in open('fastconn_pvlist.txt','r').readlines():
    pvnames.append(line[:-1])

if MAX_PVS is not None:
    pvnames = pvnames[:MAX_PVS]


dt.add('Read PV list:  Will connect to %i PVs' % len(pvnames))
libca = ca.initialize_libca()

for name in pvnames:
    chid = ca.create_channel(name, connect=False, auto_cb=False)
    results[name] = {'chid': chid}

time.sleep(0.001)

dt.add("created PVs with ca_create_channel")

for name in pvnames:
    ca.connect_channel(results[name]['chid'])

time.sleep(0.001)

dt.add("connected to PVs with connect_channel")

ca.pend_event(1.e-2)

for name in pvnames:
    chid = results[name]['chid']
    val = ca.get(chid, wait=False)
    results[name]['value'] =  val

dt.add("did ca.get(wait=False)")
ca.pend_event(1.e-2)
dt.add("pend complete")

for name in pvnames:
    chid = results[name]['chid']    
    val = ca.get_complete(chid)
    results[name]['value'] =  val
    

dt.add("unpacked PV values")
 
f = open('fastconn_pvdata.sav', 'w')
for name, val in results.items():
    f.write("%s %s\n" % (name.strip(), val['value']))
f.close()
dt.add("wrote values PVs")

dt.show()

time.sleep(0.01)
ca.poll()
