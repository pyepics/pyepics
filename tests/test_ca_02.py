import _epics, time

pvname = '13IDA:DMM1Ch3_calc.VAL'
# pvname = '13IDA:mono_pid1.FBON'
# pvname = '13XRM:edb:file'

def get_callback(pvname=None, value=None, status=None, count=1, units=None,
                 precision=None, enumstrs=None, severity=0,
                 llim=None, hlim=None, disp_lo=None, disp_hi=None,*args,**kws):

    print 'get: ', pvname, value, status, count, units


chid = _epics.create_pv(pvname)
_epics.pend_event(1.e-3)

_epics.pend_io(1.e-1)

ctype = _epics.field_type(chid)
count = _epics.element_count(chid)

host  = _epics.host_name(chid)
rwacc = _epics.read_access(chid) + 2*_epics.write_access(chid)

_epics.pend_event(0.10)

print chid, ctype, count, rwacc, host

_epics.register_getcallback(chid, 0, get_callback)

# print 'Enum Strings: ', _epics.get_enum_strings(ctype,chid)
print ' Ready for action: '
print ' precision: ', _epics.get_precision(chid)

nx = 0
while nx < 100:
    _epics.pend_event(0.1)
    time.sleep(0.1)
    nx = nx + 1
    
