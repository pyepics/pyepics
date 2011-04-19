import sys
from epics import caget
import time
import instrument

db = instrument.InstrumentDB('Test.ein')

pvlist = ['13XRM:m1.VAL','13XRM:m2.VAL','13XRM:m3.VAL']

iname = 'Sample Stage'

inst = db.get_instrument(iname)
if inst is None:
    inst = db.add_instrument(iname, pvs=pvlist)

inst = db.get_instrument(iname)
print inst, inst.pvs, inst.positions

for p in inst.pvs:
    print p, p.pvtype


x = db.add_pv('13XRM:m4.VAL')
print 'Add PV ', x

print inst.pvs

print '==  And now =='
for p in inst.pvs:
    print p, p.pvtype
    
print 'Instid = ', inst.id
IPV = instrument.Instrument_PV
pvs_ordered = db.query(IPV).filter(IPV.instrument_id==inst.id
                                   ).order_by(IPV.display_order
                                              ).all()
for i, pv in enumerate(inst.pvs):
    print pv, pv.id
    for o in pvs_ordered:
        if o.pv == pv:
            o.display_order = i+1
            
db.commit()    
    
# 
# for ix, entry in enumerate(pvs_ordered):
#     print entry.pv, entry.display_order
#     # entry.display_order = ix
# ;
# db.commit()


# db.close()
# time.sleep(0.1)
# print '=------------------------------------'
# db = instrument.InstrumentDB('Bob.einst')
# inst = db.get_instrument(iname)
# print inst, inst.pvs
# print inst.positions
# ;
#values = {}
#for pv in pvlist:
#    values[pv] = 0
# # 
#print '====== ', inst.positions
#db.remove_position('p3', 'sample_stage')

#print db.get_info('modify_date')

#db.set_info('verify_erase', '1')
#db.set_info('verify_move', '1')

print db.get_info('verify_erase')

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
