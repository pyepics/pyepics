#!/usr/bin/env python
#
"""
provides two classes:
   MotorPanel: a wx panel for an Epics Motor, ala medm Motor row

 makes use of these modules
    wxlib:  extensions of wx.TextCtrl, etc for epics PVs
    Motor:  Epics Motor class
"""
#  Aug 21 2004 M Newville:  initial working version.
#
import wx
try:
    from wx._core import PyDeadObjectError
except:
    PyDeadObjectError = Exception

import epics
from epics.wx.wxlib import PVText, PVFloatCtrl, PVButton, PVComboBox, \
     DelayedEpicsCallback, EpicsFunction

from epics.wx.motordetailframe  import MotorDetailFrame

from epics.wx.utils import LCEN, RCEN, CEN, LTEXT, RIGHT, pack, add_button

class MotorPanel(wx.Panel):
    """ MotorPanel  a simple wx windows panel for controlling an Epics Motor

    use psize='full' (defaiult) for full capabilities, or
              'medium' or 'small' for minimal version
    """
    __motor_fields = ('SET', 'disabled', 'LLM', 'HLM',  'LVIO', 'TWV',
                      'HLS', 'LLS', 'SPMG', 'DESC')

    def __init__(self, parent,  motor=None,  psize='full',
                 messenger=None, prec=None, **kw):

        wx.Panel.__init__(self, parent, style=wx.TAB_TRAVERSAL)
        self.parent = parent

        if hasattr(messenger, '__call__'):
            self.__messenger = messenger

        self.format = None
        if prec is not None:
            self.format = "%%.%if" % prec

        self.motor = None
        self._size = 'full'
        if psize in ('medium', 'small'):
            self._size = psize
        self.__sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.CreatePanel()

        if motor is not None:
            try:
                self.SelectMotor(motor)
            except PyDeadObjectError:
                pass



    @EpicsFunction
    def SelectMotor(self, motor):
        " set motor to a named motor PV"
        if motor is None:
            return

        epics.poll()
        try:
            if self.motor is not None:
                for i in self.__motor_fields:
                    self.motor.clear_callback(attr=i)
        except PyDeadObjectError:
            return

        if isinstance(motor, (str, unicode)):
            self.motor = epics.Motor(motor)
        elif isinstance(motor, epics.Motor):
            self.motor = motor
        self.motor.get_info()


        if self.format is None:
            self.format = "%%.%if" % self.motor.PREC
        self.FillPanel()
        for attr in self.__motor_fields:
            self.motor.get_pv(attr).add_callback(self.OnMotorEvent,
                                                 wid=self.GetId(),
                                                 field=attr)
        if self._size == 'full':
            self.SetTweak(self.format % self.motor.TWV)

    @EpicsFunction
    def FillPanelComponents(self):
        epics.poll()
        try:
            if self.motor is None:
                return
        except PyDeadObjectError:
            return

        self.drive.SetPV(self.motor.PV('VAL'))
        self.rbv.SetPV(self.motor.PV('RBV'))
        self.desc.SetPV(self.motor.PV('DESC'))

        descpv = self.motor.PV('DESC').get()
        self.desc.Wrap(45)
        if self._size == 'full':
            self.twf.SetPV(self.motor.PV('TWF'))
            self.twr.SetPV(self.motor.PV('TWR'))
        elif len(descpv) > 20:
                font = self.desc.GetFont()
                font.PointSize -= 1
                self.desc.SetFont(font)

        self.info.SetLabel('')
        for f in ('SET', 'LVIO', 'SPMG', 'LLS', 'HLS', 'disabled'):
            uname = self.motor.PV(f).pvname
            wx.CallAfter(self.OnMotorEvent,
                         pvname=uname, field=f)

    def CreatePanel(self):
        " build (but do not fill in) panel components"
        wdesc, wrbv, winfo, wdrv = 200, 105, 90, 120
        if self._size == 'medium':
            wdesc, wrbv, winfo, wdrv = 140, 85, 80, 100
        elif self._size == 'small':
            wdesc, wrbv, winfo, wdrv = 50, 60, 25, 80

        self.desc = PVText(self, size=(wdesc, 25), style=LTEXT)
        self.desc.SetForegroundColour("Blue")
        font = self.desc.GetFont()
        font.PointSize -= 1
        self.desc.SetFont(font)

        self.rbv  = PVText(self, size=(wrbv, 25), fg='Blue', style=RCEN)
        self.info = wx.StaticText(self, label='',
                                  size=(winfo, 25), style=RCEN)
        self.info.SetForegroundColour("Red")

        self.drive = PVFloatCtrl(self, size=(wdrv, -1), style = wx.TE_RIGHT)

        try:
            self.FillPanelComponents()
        except PyDeadObjectError:
            return

        spacer = wx.StaticText(self, label=' ', size=(5, 5), style=RIGHT)
        if self._size != 'small':
            self.__sizer.AddMany([(spacer,      0, CEN)])

        self.__sizer.AddMany([ (self.desc,   1, LCEN),
                               (self.info,   0, CEN),
                               (self.rbv,    0, CEN),
                               (self.drive,  0, CEN)])

        if self._size == 'full':
            self.twk_list = ['','']
            self.__twkbox = wx.ComboBox(self, value='', size=(100, -1),
                                        choices=self.twk_list,
                                        style=wx.CB_DROPDOWN|wx.TE_PROCESS_ENTER)
            self.__twkbox.Bind(wx.EVT_COMBOBOX,    self.OnTweakBoxComboEvent)
            self.__twkbox.Bind(wx.EVT_TEXT_ENTER,  self.OnTweakBoxEnterEvent)

            self.twr = PVButton(self, label='<',  size=(30, 30))
            self.twf = PVButton(self, label='>',  size=(30, 30))

            self.stopbtn = add_button(self, label=' Stop ', action=self.OnStopButton)
            self.morebtn = add_button(self, label=' More ', action=self.OnMoreButton)

            self.__sizer.AddMany([(self.twr,      0, CEN),
                                  (self.__twkbox, 0, CEN),
                                  (self.twf,      0, CEN),
                                  (self.stopbtn,  0, CEN),
                                  (self.morebtn,  0, CEN)])

        self.SetAutoLayout(1)
        pack(self, self.__sizer)

    @EpicsFunction
    def FillPanel(self):
        " fill in panel components for motor "
        try:
            if self.motor is None:
                return
            self.FillPanelComponents()
            self.drive.Update()
            self.desc.Update()
            self.rbv.Update()
            if self._size == 'full':
                self.twk_list = self.make_step_list()
                self.UpdateStepList()
        except PyDeadObjectError:
            pass

    @EpicsFunction
    def OnStopButton(self, event=None):
        "stop button"
        if self.motor is None:
            return

        curstate = str(self.stopbtn.GetLabel()).lower().strip()
        if curstate == 'stop':
            self.motor.stop()
            epics.poll()
        else:
            self.motor.SPMG = 3

    @EpicsFunction
    def OnMoreButton(self, event=None):
        "more button"
        if self.motor is not None:
            MotorDetailFrame(parent=self, motor=self.motor)

    @DelayedEpicsCallback
    def OnTweakBoxEnterEvent(self, event=None):
        val = float(self.__twkbox.GetValue())
        wx.CallAfter(self.motor.PV('TWV').put, val)

    @DelayedEpicsCallback
    def OnTweakBoxComboEvent(self, event=None):
        val = float(self.__twkbox.GetValue())
        wx.CallAfter(self.motor.PV('TWV').put, val)

    @DelayedEpicsCallback
    def OnMotorEvent(self, pvname=None, field=None, event=None, **kws):
        if pvname is None:
            return None

        field_val = self.motor.get(field)
        field_str = self.motor.get(field, as_string=True)

        if field == 'LLM':
            self.drive.SetMin(self.motor.LLM)
        elif field == 'HLM':
            self.drive.SetMax(self.motor.HLM)

        elif field in ('LVIO', 'HLS', 'LLS'):
            s = 'Limit!'
            if field_val == 0:
                s = ''
            self.info.SetLabel(s)

        elif field == 'SET':
            label, color = 'Set:','Yellow'
            if field_val == 0:
                label, color = '','White'
            self.info.SetLabel(label)
            self.drive.bgcol_valid = color
            self.drive.SetBackgroundColour(color)
            self.drive.Refresh()

        elif field == 'disabled':
            label = ('','Disabled')[field_val]
            self.info.SetLabel(label)

        elif field == 'DESC':
            font = self.rbv.GetFont()
            if len(field_str) > 20:
                font.PointSize -= 1
            self.desc.SetFont(font)

        elif field == 'TWV' and self._size == 'full':
            self.SetTweak(field_str)

        elif field == 'SPMG' and self._size == 'full':
            label, info, color = 'Stop', '', 'White'
            if field_val == 0:
                label, info, color = ' Go ', 'Stopped', 'Yellow'
            elif field_val == 1:
                label, info, color = ' Resume ', 'Paused', 'Yellow'
            elif field_val == 2:
                label, info, color = ' Go ', 'Move Once', 'Yellow'
            self.stopbtn.SetLabel(label)
            self.info.SetLabel(info)
            self.stopbtn.SetBackgroundColour(color)
            self.stopbtn.Refresh()

        else:
            pass

    @EpicsFunction
    def SetTweak(self, val):
        if not isinstance(val, str):
            val = self.format % val
        try:
            if val not in self.twk_list:
                self.UpdateStepList(value=val)
            self.__twkbox.SetValue(val)
        except PyDeadObjectError:
            pass

    def make_step_list(self):
        """ create initial list of motor steps, based on motor range
        and precision"""
        if self.motor is None:
            return []
        return [self.format % i for i in self.motor.make_step_list()]

    def UpdateStepList(self, value=None):
        "add a value and re-sort the list of Step values"
        if value is not None:
            self.twk_list.append(value)
        x = [float(i) for i in self.twk_list]
        x.sort()
        self.twk_list = [self.format % i for i in x]
        # remake list in TweakBox
        self.__twkbox.Clear()
        self.__twkbox.AppendItems(self.twk_list)
