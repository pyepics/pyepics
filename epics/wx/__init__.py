"""
This module provides wxPython widgets specially designed to work as
Epics Controls.  In general,  these controls combine a wx widget with
an Epics PV, and allow automatic updating of the widget when the
associated PV changes.
"""
from . import motorpanel, motordetailframe, wxlib, ogllib, utils

MotorPanel    = motorpanel.MotorPanel
MotorDetailPanel  = motordetailframe.MotorDetailPanel
MotorDetailFrame  = motordetailframe.MotorDetailFrame

PVText        = pvText        = wxlib.PVText
PVAlarm       = pvAlarm       = wxlib.PVAlarm
PVFloatCtrl   = pvFloatCtrl   = wxlib.PVFloatCtrl
PVTextCtrl    = pvTextCtrl    = wxlib.PVTextCtrl
PVStaticText  = pvStaticText  = wxlib.PVStaticText
PVEnumButtons = pvEnumButtons = wxlib.PVEnumButtons
PVEnumChoice  = pvEnumChoice  = wxlib.PVEnumChoice
PVBitmap      = pvBitmap      = wxlib.PVBitmap
PVCheckBox    = pvCheckBox    = wxlib.PVCheckBox
PVFloatSpin   = pvFloatSpin   = wxlib.PVFloatSpin
PVSpinCtrl    = pvSpinCtrl    = wxlib.PVSpinCtrl
PVButton      = pvButton      = wxlib.PVButton
PVRadioButton = pvRadioButton = wxlib.PVRadioButton
PVComboBox    = pvComboBox    = wxlib.PVComboBox
PVEnumComboBox = pvEnumComboBox = wxlib.PVEnumComboBox
PVCollapsiblePane = pvCollapsiblePane = wxlib.PVCollapsiblePane

# OGL shapes
PVRectangle   = pvRectangle   = ogllib.PVRectangle
PVCircle      = pvCircle      = ogllib.PVCircle

set_sizer = utils.set_sizer
set_float = utils.set_float

Closure   = utils.Closure
FloatCtrl = utils.FloatCtrl

DelayedEpicsCallback = wxlib.DelayedEpicsCallback
EpicsFunction  = wxlib.EpicsFunction
finalize_epics  = wxlib.finalize_epics
EpicsTimer      = wxlib.EpicsTimer

