import epics

p = epics.PV('13IDC:m1.VAL')
val = p.get()

print 'PV    = ', p
print 'Value = ', val
print 'Info Paragraph:'
print p.info

