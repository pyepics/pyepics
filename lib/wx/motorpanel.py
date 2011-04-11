#!/usr/bin/python
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
import epics
from epics.wx.wxlib import pvText, pvFloatCtrl, \
     DelayedEpicsCallback, EpicsFunction

from epics.wx.motordetailframe  import MotorDetailFrame

from utils import LCEN, RCEN, CEN, LTEXT, RIGHT


class MotorPanel(wx.Panel):
    """ MotorPanel  a simple wx windows panel for controlling an Epics Motor

    use full=False for a minimal window (no tweak values, stop, or more)
    """
    __motor_fields = ('SET', 'disabled', 'LLM', 'HLM',  'LVIO', 'TWV',
                      'HLS', 'LLS', 'SPMG')
    

    def __init__(self, parent,  motor=None,  full=True,
                 messenger=None, prec=None, **kw):

        wx.Panel.__init__(self, parent, style=wx.TAB_TRAVERSAL)
        self.parent = parent

        if hasattr(messenger, '__call__'):
            self.__messenger = messenger

        self.format = None 
        if prec is not None:
            self.format = "%%.%if" % prec

        self.motor = None
        self.is_full = full
        self.__sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.CreatePanel()

        if motor is not None:
            self.SelectMotor(motor)

    @EpicsFunction
    def SelectMotor(self, motor):
        " set motor to a named motor PV"
        if motor is None:
            return

        # if self.motor already exists
        if self.motor is not None:
            for i in self.__motor_fields:
                self.motor.clear_callback(attr=i)

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
        if self.is_full:
            self.SetTweak(self.format % self.motor.TWV)

    @EpicsFunction
    def FillPanelComponents(self):
        if self.motor is None:
            return
        epics.poll()

        self.drive.SetPV(self.motor.PV('VAL'))
        self.rbv.SetPV(self.motor.PV('RBV'))
        self.desc.SetPV(self.motor.PV('DESC'))

        descpv = self.motor.PV('DESC').get()
        if not self.is_full:
            if len(descpv.char_value) > 25:
                self.desc.Wrap(30)
                self.desc.SetSize( (200, 40))
            else:
                self.desc.Wrap(45)
                self.desc.SetSize( (200, -1))

        self.info.SetLabel('')
        for f in ('SET', 'LVIO', 'SPMG', 'LLS', 'HLS', 'disabled'):            
            uname = self.motor.PV(f).pvname
            wx.CallAfter(self.OnMotorEvent,
                         pvname=uname, field=f)

    def CreatePanel(self):
        " build (but do not fill in) panel components"
        wdesc, wrbv, winfo, wdrv = 200, 105, 90, 120
        if not self.is_full:
            wdesc, wrbv, winfo, wdrv = 50, 50, 70, 80
            
        
        self.desc = pvText(self, size=(wdesc, 25), style=LTEXT)
        self.desc.SetForegroundColour("Blue")

        self.rbv  = pvText(self, size=(wrbv, 25), fg='Blue', style=RCEN)
        self.info = wx.StaticText(self, label='',
                                  size=(winfo, 25), style=RCEN)
        self.info.SetForegroundColour("Red")

        self.drive = pvFloatCtrl(self, size=(wdrv, -1), style = wx.TE_RIGHT)
        
        self.FillPanelComponents()
                
        if self.is_full:
            self.twk_list = ['','']
            self.__twkbox = wx.ComboBox(self, value='', size=(100, -1), 
                                        choices=self.twk_list,
                               style=wx.CB_DROPDOWN|wx.TE_PROCESS_ENTER)

            self.__twkbox.Bind(wx.EVT_COMBOBOX,    self.OnTweakBoxComboEvent)
            self.__twkbox.Bind(wx.EVT_TEXT_ENTER,  self.OnTweakBoxEnterEvent)

            twkbtn1 = wx.Button(self, label='<',  size=(30, 30))
            twkbtn2 = wx.Button(self, label='>',  size=(30, 30))
            stopbtn = wx.Button(self, label=' Stop ')
            morebtn = wx.Button(self, label=' More ')
            
            twkbtn1.Bind(wx.EVT_BUTTON, self.OnLeftButton)
            twkbtn2.Bind(wx.EVT_BUTTON, self.OnRightButton)
            stopbtn.Bind(wx.EVT_BUTTON, self.OnStopButton)
            morebtn.Bind(wx.EVT_BUTTON, self.OnMoreButton)

            self.stopbtn = stopbtn
        
        spacer = wx.StaticText(self, label=' ', size=(10, 10), style=RIGHT) 
        self.__sizer.AddMany([(spacer,      0, CEN),
                              (self.desc,   0, LCEN),
                              (self.info,   0, CEN),
                              (self.rbv,    0, CEN),
                              (self.drive,  0, CEN)])
        if self.is_full:
            self.__sizer.AddMany([(twkbtn1,       0, CEN),
                                  (self.__twkbox, 0, CEN),
                                  (twkbtn2,       0, CEN),
                                  (stopbtn,       0, CEN),
                                  (morebtn,       0, CEN)])
        
        self.SetAutoLayout(1)
        self.SetSizer(self.__sizer)
        self.__sizer.Fit(self)

    @EpicsFunction
    def FillPanel(self):
        " fill in panel components for motor "
        if self.motor is None:
            return

        self.FillPanelComponents()
        self.drive.Update()
        self.desc.Update()
        self.rbv.Update()
        if self.is_full:
            self.twk_list = self.make_step_list()
            self.UpdateStepList()
        
    @EpicsFunction
    def OnLeftButton(self, event=None):
        "left button"
        if self.motor is not None:
            self.motor.tweak(direction='reverse')
        
    @EpicsFunction
    def OnRightButton(self, event=None):
        "right button"
        if self.motor is not None:
            self.motor.tweak(direction='foreward')

    @EpicsFunction
    def OnStopButton(self, event=None):
        "stop button"
        if self.motor is None:
            return
        curstate = str(self.stopbtn.GetLabel()).lower().strip()

        self.motor.StopNow()
        epics.poll()
        val = 3
        if curstate == 'stop':
            val = 0
        self.motor.put('SPMG', val)

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
            
        elif field == 'TWV' and self.is_full:
            self.SetTweak(field_str)

        elif field == 'SPMG':
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
        if val not in self.twk_list:
            self.UpdateStepList(value=val)
        self.__twkbox.SetValue(val)
            
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
