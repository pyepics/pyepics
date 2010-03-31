import epics
import pvnames

p = epics.PV(pvnames.double_pv)
val = p.get()

print 'PV    = ', p
print 'Value = ', val
print 'Info Paragraph:'
print p.info

