#!/usr/bin/python
"""
Miniature Motor Panel, consisting of
  label (default taken from motor), info light, readback, drive
"""
import wx
import epics

from epics.wx.wxlib import pvText, pvFloatCtrl, \
     DelayedEpicsCallback, EpicsFunction

LCEN = wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_LEFT
RCEN = wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT
CCEN = wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER

class MiniMotorPanel(wx.Panel):
    """ MiniMotorPanel:
    Miniature Version of a Motor Panel
     label (default taken from motor)
     info light
     readback
     drive
    """
    __motor_fields = ('SET', 'disabled', 'LLM', 'HLM',  'LVIO',
                      'TWV', 'HLS', 'LLS', 'SPMG')
    
    def __init__(self, parent,  motor=None,  label=None, prec=None,
                 style='normal', messenger=None):

        wx.Panel.__init__(self, parent, style=wx.TAB_TRAVERSAL)

        self.parent = parent
        if hasattr(messenger,'__call__'):
            self.__messenger = messenger
        self.style = style
        self.label = label
        self.format =  None
        if prec is not None:
            self.format = "%%.%if" % prec
        self.motor = None
        self.__sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.CreatePanel()
        if motor is not None:
            self.SelectMotor(motor)

    @EpicsFunction
    def SelectMotor(self, motor):
        " set motor to a named motor PV"
        if motor is None:
            return
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

    @EpicsFunction
    def FillPanelComponents(self):
        "enter values into Panel Componets from PVs"
        if self.motor is None:
            return

        epics.poll()
        self.drive.set_pv(self.motor.PV('VAL'))
        self.rbv.set_pv(self.motor.PV('RBV'))

        if self.label is None:
            self.label = self.motor.PV('DESC').get()

        self.desc.SetLabel(self.label)
            
        self.info.SetLabel('')
        for f in ('SET', 'LVIO', 'SPMG', 'LLS', 'HLS', 'disabled'):            
            uname = self.motor.PV(f).pvname
            wx.CallAfter(self.OnMotorEvent,
                         pvname=uname, field=f)

    def CreatePanel(self):
        " build (but do not fill in) panel components"
        self.desc = wx.StaticText(self, size=(40, -1), 
                                  style= wx.ALIGN_LEFT|wx.ST_NO_AUTORESIZE)
        self.desc.SetForegroundColour("Blue")
        
        self.info = wx.StaticText(self, label='', size=(40, 10), style=RCEN)
        self.info.SetForegroundColour("Red")

        self.rbv  = pvText(self, size=(70, -1), fg='Blue', style=CCEN)

        self.drive = pvFloatCtrl(self, size=(80, -1), style = wx.TE_RIGHT)
        
        self.FillPanelComponents()
        spacer = wx.StaticText(self, label=' ', size=(5, 5),
                               style=wx.ALIGN_RIGHT)
        
        self.__sizer.AddMany([(spacer,      0, CCEN),
                              (self.desc,   0, LCEN),
                              (self.info,   0, RCEN),
                              (self.rbv,    0, LCEN), 
                              (self.drive,  0, CCEN)])

        self.SetAutoLayout(1)
        self.SetSizer(self.__sizer)
        self.__sizer.Fit(self)

    @EpicsFunction
    def FillPanel(self):
        " fill in panel components for motor "
        if self.motor is None:
            return
        self.FillPanelComponents()
        self.drive.update()
        self.rbv.update()

        
    @DelayedEpicsCallback
    def OnMotorEvent(self, pvname=None, field=None, event=None):
        "General Purpose Motor Event Handler"
        if pvname is None:
            return None
      
        field_val = self.motor.get(field)
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
            label, color = 'Set:', 'Yellow'
            if field_val == 0:
                label, color = '', 'White'
            self.info.SetLabel(label)
            self.drive.bgcol_valid = color
            self.drive.SetBackgroundColour(color)
            self.drive.Refresh()

        elif field == 'disabled':
            label = ('', 'Disabled')[field_val]
            self.info.SetLabel(label)
            
        elif field == 'SPMG':
            label, info, color = 'Stop', '', 'White'
            if field_val == 0:
                label, info, color = ' Go ', 'Stopped', 'Yellow'
            elif field_val == 1:
                label, info, color = ' Resume ', 'Paused', 'Yellow'
            elif field_val == 2:
                label, info, color = ' Go ', 'Move Once', 'Yellow'
            self.info.SetLabel(info)
