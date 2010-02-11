"""
This module provides wxPython widgets specially designed to work as Epics Controls.
All these controls combine a wx widget with one Epics PV, and allow automatic updating
of the widget  when the associated PV changes.

"""
from MotorPanel import MotorPanel
from wxlib      import pvText, pvFloatCtrl, pvTextCtrl, pvEnumButtons, pvEnumChoice, pvAlarm
from wxlib      import catimer, closure, set_sizer, set_float, FloatCtrl

pvText        = pvText
pvAlarm       = pvAlarm
pvFloatCtrl   = pvFloatCtrl
pvTextCtrl    = pvTextCtrl
pvEnumButtons = pvEnumButtons
pvEnumChoice  = pvEnumChoice
catimer       = catimer

set_sizer = set_sizer
set_float = set_float

closure   = closure
FloatCtrl = FloatCtrl


MotorPanel = MotorPanel
