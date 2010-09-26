import sys
import time
import epics
import pvnames

pvnames.long_arr_pv   = '13IDC:str:mca1'
pvnames.char_arr_pv   = '13BMD:edb:dir'
pvnames.double_arr_pv = '13IDC:scan1.P1PA'
epics.ca.HAS_NUMPY = True
epics.ca.HAS_NUMPY = False

pvlist = (
    pvnames.double_arr_pv,
    pvnames.char_arr_pv,
    pvnames.double_pv,
    pvnames.float_pv,       
    pvnames.int_pv,
    pvnames.long_pv,
    pvnames.str_pv,
    pvnames.enum_pv,
    pvnames.long_arr_pv,       
    )
tforms = (#'native',
          # 'time',
          'ctrl',
          )

mypvs = []
for pvname in pvlist:
    for form in tforms: 
        pv = epics.PV(pvname, form=form)
        mypvs.append((form, pv))
        pv.connect()
        # epics.poll(1.e-3, 30.0)
        
for i in range(10):
    epics.poll(0.08, 5.0)


for form, pv in mypvs:
    print '=======' ,pv
    time.sleep(0.05)
    val = pv.get()
    cval = pv.get(as_string=True)    
    if pv.count > 1:
        val = val[:12]
    print val, cval
# 
# print '------------------------'
# for form, pv in mypvs:
#     print '=======' ,pv
#     time.sleep(0.25)
#     val = pv.get()
#     if pv.count > 1:
#         val = val[:20]
#     print val

# for p in pvs:
#     # print '==== PV : ' , p
#     for form in tforms: 
#         print '----PV / FORM ', p, form
#         x = epics.PV(p, form=form)
#         #callback=onChange,
#         #connection_callback=onConnect)
#         x.connect()
#         epics.poll(evt=0.025, iot=0.1)
#         val = x.get()
#         if x.count > 1:
#             val = val[:20]
#         print val
# 

        # print x.info
         
time.sleep(0.01)

#     p = epics.PV(pvnames.double_pv)
# 
# sys.stdout.write( 'PV    =  %s\n' % p)
# sys.stdout.write( 'Value = %s\n' % repr(p.value))
# sys.stdout.write('Info Paragraph:\n')
# sys.stdout.write('%s\n' %p.info)
