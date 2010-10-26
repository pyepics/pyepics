from mono_control import mono_control

m = mono_control('13IDA:')

print m.getVal('Shutter')
print m.getVal('PitchFB_ON')
print m.getVal('Roll_Tweakval')

print m.getVal('PreSlit_Sum'),  m.getVal('PreSlit_Diff')

# m.WaitForFeedbackLocked()
# m.WaitForShutterOpen()
m.CheckMonoPitch()
# m.OptimizeMonoPitch()
# m.OptimizeMonoRoll()
