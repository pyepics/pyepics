
from  EpicsCA import caget,pend_event

pvnames = ('13IDC:m1.VAL', '13IDC:m7.VAL', '13IDC:m12.VAL')

for p in pvnames:
    print p, caget(p)

print 'Waiting '
pend_event(0.4)

for p in pvnames:
    print p, caget(p)


