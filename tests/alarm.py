import sys
import time
import epics
import pvnames

pvn = pvnames.alarm_pv
pvn = pvnames.alarm_comp
pvn = pvnames.alarm_trippoint

def alarmHandler(pvname=None,value=None,char_value=None,
                 comparison=None,trip_point=None,**kw):
    sys.stdout.write( 'Alarm! %s at %s ! \n' %( pvname,  time.ctime()))
    sys.stdout.write( 'Alarm  Comparison =%s  \n' %( comparison))
    sys.stdout.write( 'Alarm  TripPoint      =%s  \n' %( repr(trip_point)))
    sys.stdout.write( 'Current Value         =%s  \n' %(char_value))    

epics.Alarm(pvname = pvnames.alarm_pv,
            comparison = pvnames.alarm_comp,
            trip_point    =pvnames.alarm_trippoint,
            callback = alarmHandler,
            alert_delay=5.0)


t0 = time.time()

sys.stdout.write('Waiting for pv %s to change! \n' % pvnames.alarm_pv)
sys.stdout.write('Alarm settings:  comp=%s,  trip_point=%s\n' % (pvnames.alarm_comp,
                                                                 pvnames.alarm_trippoint))
sys.stdout.write('You may have to make this happen!!\n')

while time.time()-t0 < 30:
    try:
        epics.ca.poll()
    except KeyboardInterrupt:
        break
