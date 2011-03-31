import sys
from epics import caget

import instrument

db = instrument.InstrumentDB('Test.einst')

pvlist = ['13XRM:m1.VAL','13XRM:m2.VAL','13XRM:m3.VAL']

iname = 'sample_stage'


inst = db.get_instrument(iname)
if inst is None:
    inst = db.add_instrument(iname, pvs=pvlist)

inst = db.get_instrument(iname)
print inst, inst.pvs
 
#values = {}
#for pv in pvlist:
#    values[pv] = 0
# # 
print '====== ', inst.positions

db.remove_position('p3', 'sample_stage')

# print a, a.pvs
# for p in a.pvs:
#     print p, p.pv.name, p.value
# ;# 
# values = {}
# for pv in pvlist:
#     values[pv] = caget(pv)
# 
# db.save_position('Current', inst, values)
# 
# 
# print '====='
# origin = db.get_position('Current')
# 
# print origin, origin.pvs
# ;
