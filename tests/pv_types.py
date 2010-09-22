import sys
import time
import epics
import pvnames

pvnames.long_arr_pv = '13IDC:str:mca1'
pvnames.char_arr_pv = '13BMD:edb:dir'
pvnames.double_arr_pv = '13IDC:scan1.P1PA'
pvnames.float_pv = '13XRM:m2.VERS'

pvs = (pvnames.double_pv,
       pvnames.float_pv,       
       pvnames.int_pv,
       pvnames.long_pv,
       pvnames.enum_pv,
       pvnames.str_pv,
       pvnames.double_arr_pv,
       pvnames.long_arr_pv,       
       pvnames.char_arr_pv,
       )

def onConnect(**kw):
    print 'onConnect : ', kw

def onChange(pvname=None, value=None, type=None, ftype=None,
             status='nostat', severity='nosev', timestamp=None,
             count=None, chid=None,  **kw):
    print 'onChange PV=  ', pvname, type, ftype, value
    print '   timestamp, chid, count, status, severity ',\
          timestamp, chid, count, status, severity

for p in pvs:
    print '==== PV : ' , p
    for form in ('native', 'time', 'ctrl'):
        x = epics.PV(p, form=form, callback=onChange,
                     connection_callback=onConnect)
        x.connect()
        epics.poll(evt=0.01, iot=0.1)
        time.sleep(0.05)
        # print x.get(), x
        print x.info
#         
#     p = epics.PV(pvnames.double_pv)
# 
# sys.stdout.write( 'PV    =  %s\n' % p)
# sys.stdout.write( 'Value = %s\n' % repr(p.value))
# sys.stdout.write('Info Paragraph:\n')
# sys.stdout.write('%s\n' %p.info)
