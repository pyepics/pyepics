from epics import ca, dbr
import time
import debugtime

dt = debugtime.debugtime()
dt.add('test of fast connection to many PVs')
pvnames = []
values = []
pvlist = []
data   = {}

MAX_PVS = 10000
for line  in open('fastconn_pvlist.txt','r').readlines():
    pvnames.append(line[:-1])

if MAX_PVS is not None:
    pvnames = pvnames[:MAX_PVS]

dt.add('Read PV list:  Will connect to %i PVs' % len(pvnames))

libca = ca.initialize_libca()

for name in pvnames:
    chid = ca.create_channel(name, auto_cb=False)
    pvlist.append(chid)


dt.add("created PVs with ca_create_channel")

ca.pend_event(1.e-2)
ca.pend_io(1.0)

for chid in pvlist:
    name  = ca.name(chid)
    count = ca.element_count(chid)
    ftype = ca.field_type(chid)
    ca.get(chid, unpack=False)
    data[name] = chid, ftype, count

dt.add("did ca.get() for value references")
ca.pend_event(1.e-2)

dt.add("pend complete")
for name in pvnames:
    chid, ftype, count = data[name]
    val = ca.get_cached_value(chid, count=count, ftype=ftype)
    values.append(val)
dt.add("unpacked PV values")

f = open('fastconn_pvdata.sav', 'w')
for n,v in zip(pvnames, values):
    f.write("%s %s\n" % (n.strip(), v))
f.close()
dt.add("wrote values PVs")

dt.show()

time.sleep(0.1)
ca.poll()
