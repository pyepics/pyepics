"""
This module provides wxPython widgets specially designed to work as Epics Controls.
All these controls combine a wx widget with one Epics PV, and allow automatic updating
of the widget  when the associated PV changes.

"""
from . import MotorPanel
from . import wxlib

MotorPanel = MotorPanel.MotorPanel
pvText        = wxlib.pvText
pvAlarm       = wxlib.pvAlarm
pvFloatCtrl   = wxlib.pvFloatCtrl
pvTextCtrl    = wxlib.pvTextCtrl
pvEnumButtons = wxlib.pvEnumButtons
pvEnumChoice  = wxlib.pvEnumChoice

set_sizer = wxlib.set_sizer
set_float = wxlib.set_float

closure   = wxlib.closure
FloatCtrl = wxlib.FloatCtrl

DelayedEpicsCallback = wxlib.DelayedEpicsCallback
EpicsFunction  = wxlib.EpicsFunction
