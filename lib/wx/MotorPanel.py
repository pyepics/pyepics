#!/usr/bin/python
#
# wx panel widget for Epics Motor
#
# makes use of these modules
#    wxlib:  extensions of wx.TextCtrl, etc for epics PVs
#    Motor:  Epics Motor class
#
#  Aug 21 2004 MN
#         initial working version.
#----------------------------------------
import wx
import sys
import epics
from epics.wx.wxlib import pvText, pvFloatCtrl, pvTextCtrl, \
     DelayedEpicsCallback, EpicsFunction, set_float

from epics.wx.MotorDetailFrame  import MotorDetailFrame

class MotorPanel(wx.Panel):
    """ MotorPanel  a simple wx windows panel for controlling an Epics Motor
    """
    __motor_fields = ('SET', 'disabled', 'LLM', 'HLM',  'LVIO', 'TWV',
                      'HLS', 'LLS', 'SPMG')
    

    def __init__(self, parent,  motor=None,  
                 style='normal', messenger=None, *args, **kw):

        wx.Panel.__init__(self, parent, style=wx.TAB_TRAVERSAL)
        self.SetFont(wx.Font(13,wx.SWISS,wx.NORMAL,wx.BOLD))
        self.parent = parent
        # wx.Panel.SetBackgroundColour(self,(245,245,225))

        if hasattr(messenger,'__call__'):
            self.__messenger = messenger
        self.style = style
        self.format = "%.3f" 
        self.motor = None
        self.__sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.CreatePanel()

        self.SelectMotor(motor)

    @EpicsFunction
    def SelectMotor(self, motor):
        " set motor to a named motor PV"
        if motor is None:
            return

        if self.motor is not None:
            for i in self.__motor_fields:
                self.motor.clear_callback(attr=i)

        self.motor = epics.Motor(motor)
        self.motor.get_info()

        self.format = "%%.%if" % self.motor.PREC
        self.FillPanel()
        self.set_Tweak(self.format % self.motor.TWV)
        for attr in self.__motor_fields:
            self.motor.get_pv(attr).add_callback(self.onMotorEvent,
                                                 wid=self.GetId(),
                                                 field=attr)

    @EpicsFunction
    def fillPanelComponents(self):
        if self.motor is None: return
        try:
            odr = self.motor.PV('VAL')
            ord = self.motor.PV('RBV')
            ode = self.motor.PV('DESC')
        except:
            pass

        epics.poll()
        self.drive.set_pv(self.motor.PV('VAL'))
        self.rbv.set_pv(self.motor.PV('RBV'))

        descpv = self.motor.PV('DESC')
        if len(descpv.char_value) > 25:
            self.desc.Wrap(30)
            self.desc.SetFont(wx.Font(12, wx.SWISS, wx.NORMAL, wx.BOLD))
            self.desc.SetSize( (200, 40))
        else:
            self.desc.Wrap(45)
            self.desc.SetFont(wx.Font(13, wx.SWISS, wx.NORMAL, wx.BOLD))
            self.desc.SetSize( (200, -1))
            
        self.desc.set_pv(descpv)


        self.info.SetLabel('')
        for f in ('SET', 'LVIO', 'SPMG', 'LLS', 'HLS', 'disabled'):            
            uname = self.motor.PV(f).pvname
            wx.CallAfter(self.onMotorEvent,
                         pvname=uname, field=f)

            
    def CreatePanel(self,style='normal'):
        " build (but do not fill in) panel components"
        self.desc = pvText(self, size=(200, 25), 
                           font=wx.Font(13, wx.SWISS, wx.NORMAL, wx.BOLD),
                           style=  wx.ALIGN_LEFT| wx.ST_NO_AUTORESIZE )
        self.desc.SetForegroundColour("Blue")

        self.rbv  = pvText(self, size=(105, 25),
                           fg='Blue',style=wx.ALIGN_CENTRE_VERTICAL|wx.ALIGN_RIGHT)
        self.info = wx.StaticText(self, label='', size=(90, 25), style=wx.ALIGN_CENTRE_VERTICAL|wx.ALIGN_RIGHT)
        self.info.SetForegroundColour("Red")

        self.drive = pvFloatCtrl(self,  size=(120,-1), style = wx.TE_RIGHT)
        
        self.fillPanelComponents()
                
        self.twk_list = ['','']
        self.__twkbox = wx.ComboBox(self, value='', size=(100,-1), 
                                    choices=self.twk_list,
                                    style=wx.CB_DROPDOWN|wx.TE_PROCESS_ENTER)

        self.__twkbox.SetFont(wx.Font(13, wx.SWISS, wx.NORMAL, wx.BOLD))
        

        self.__twkbox.Bind(wx.EVT_COMBOBOX,    self.OnTweakBoxComboEvent)
        self.__twkbox.Bind(wx.EVT_TEXT_ENTER,  self.OnTweakBoxEnterEvent)        

        twkbtn1 = wx.Button(self, label='<',  size=(30,30))
        twkbtn2 = wx.Button(self, label='>',  size=(30,30))
        stopbtn = wx.Button(self, label=' Stop ')
        morebtn = wx.Button(self, label=' More ')
        
        twkbtn1.Bind(wx.EVT_BUTTON, self.onLeftButton)
        twkbtn2.Bind(wx.EVT_BUTTON, self.onRightButton)
        stopbtn.Bind(wx.EVT_BUTTON, self.onStopButton)
        morebtn.Bind(wx.EVT_BUTTON, self.onMoreButton)

        self.stopbtn = stopbtn
        
        for b in (twkbtn1, twkbtn2):
            b.SetFont(wx.Font(12,wx.SWISS,wx.NORMAL,wx.BOLD,False))

        spacer = wx.StaticText(self, label=' ', size=(10, 10), style=wx.ALIGN_RIGHT)            
        self.__sizer.AddMany([(spacer,      0, wx.ALIGN_CENTER),
                              (self.desc,   0, wx.ALIGN_CENTRE_VERTICAL|wx.ALIGN_LEFT),
                              (self.info,   0, wx.ALIGN_CENTER),
                              (self.rbv,    0, wx.ALIGN_CENTER),
                              (self.drive,  0, wx.ALIGN_CENTER),
                              (twkbtn1,       0, wx.ALIGN_CENTER),
                              (self.__twkbox, 0, wx.ALIGN_CENTER),
                              (twkbtn2,       0, wx.ALIGN_CENTER),
                              (stopbtn,       0, wx.ALIGN_CENTER),
                              (morebtn,       0, wx.ALIGN_CENTER)
                              ] )

        self.SetAutoLayout(1)
        self.SetSizer(self.__sizer)
        self.__sizer.Fit(self)

    @EpicsFunction
    def FillPanel(self):
        " fill in panel components for motor "
        if self.motor is None: return

        self.fillPanelComponents()

        self.drive.update()
        self.desc.update()
        self.rbv.update()

        self.twk_list = self.make_step_list()
        self.__Update_StepList()
        
    @EpicsFunction
    def onLeftButton(self,event=None):
        if self.motor is None: return        
        self.motor.tweak(direction='reverse')
        
    @EpicsFunction
    def onRightButton(self,event=None):
        if self.motor is None: return        
        self.motor.tweak(direction='foreward')

    @EpicsFunction
    def onStopButton(self,event=None):
        curstate = str(self.stopbtn.GetLabel()).lower().strip()
        
        if self.motor is None:
            return
        self.motor.StopNow()
        epics.poll()
        val = 3
        if curstate == 'stop':
            val = 0
        self.motor.put('SPMG', val)

    @EpicsFunction
    def onMoreButton(self,event=None):
        if self.motor is None:
            return        
        x = MotorDetailFrame(parent=self, motor=self.motor)
            
    @DelayedEpicsCallback
    def OnTweakBoxEnterEvent(self, event=None):
        val = float(self.__twkbox.GetValue())
        wx.CallAfter(self.motor.PV('TWV').put, val)

    @DelayedEpicsCallback
    def OnTweakBoxComboEvent(self, event=None):
        val = float(self.__twkbox.GetValue())
        wx.CallAfter(self.motor.PV('TWV').put, val)        

    @DelayedEpicsCallback
    def onMotorEvent(self, pvname=None, field=None, event=None, **kw):
        if pvname is None:
            return None
      
        field_val = self.motor.get(field)
        field_str = self.motor.get(field, as_string=True)
        
        sys.stdout.flush()
        
        if field == 'LLM':
            self.drive.SetMin(self.motor.LLM)
        elif field == 'HLM':
            self.drive.SetMax(self.motor.HLM)

        elif field in ('LVIO', 'HLS', 'LLS'):
            s = 'Limit!'
            if (field_val == 0): s = ''
            self.info.SetLabel(s)
            
        elif field == 'SET':
            label, color='Set:','Yellow'
            if field_val == 0:
                label,color='','White'
            self.info.SetLabel(label)
            self.drive.bgcol_valid = color
            self.drive.SetBackgroundColour(color)
            self.drive.Refresh()

        elif field == 'disabled':
            label = ('','Disabled')[field_val]
            self.info.SetLabel(label)
            
        elif field == 'TWV':
            self.set_Tweak(field_str)

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
    def set_Tweak(self,val):
        if not isinstance(val, str):
            val = self.format % val
        if val not in self.twk_list:
            self.__Update_StepList(value=val)
        self.__twkbox.SetValue(val)
            
    def make_step_list(self):
        """ create initial list of motor steps, based on motor range
        and precision"""
        if self.motor is None:
            return []
        return [self.format%i for i in self.motor.make_step_list()]

    def __Update_StepList(self,value=None):
        "add a value and re-sort the list of Step values"
        if value is not None:
            self.twk_list.append(value)
        x = [float(i) for i in self.twk_list]
        x.sort()
        self.twk_list = [self.format % i for i in x]
        # remake list in TweakBox
        self.__twkbox.Clear()
        self.__twkbox.AppendItems(self.twk_list)
        
class MiniMotorPanel(wx.Panel):
    """ MiniMotorPanel:
     label (default taken from motor)
     info light
     readback
     drive
    """
    __motor_fields = ('SET', 'disabled', 'LLM', 'HLM',  'LVIO', 'TWV',
                      'HLS', 'LLS', 'SPMG')
    
    def __init__(self, parent,  motor=None,  label=None, prec=None,
                 style='normal', messenger=None, *args, **kw):

        wx.Panel.__init__(self, parent, style=wx.TAB_TRAVERSAL)
        self.SetFont(wx.Font(11, wx.SWISS,wx.NORMAL,wx.BOLD))
        self.parent = parent
        if hasattr(messenger,'__call__'):
            self.__messenger = messenger
        self.style = style
        self.label = label
        self.format =  None
        if prec is not None:
            self.format = "%%.%if" % prec
        self.motor = None
        self.font = wx.Font(11, wx.SWISS, wx.NORMAL, wx.BOLD)
        self.__sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.CreatePanel()
        if motor is not None:
            self.SelectMotor(motor)

    @EpicsFunction        
    def make_step_list(self):
        """ create initial list of motor steps, based on motor range
        and precision"""
        if self.motor is None:
            return []
        return [self.format%i for i in self.motor.make_step_list()]

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
            self.motor.get_pv(attr).add_callback(self.onMotorEvent,
                                                 wid=self.GetId(),
                                                 field=attr)

    @EpicsFunction
    def fillPanelComponents(self):
        if self.motor is None: return

        epics.poll()
        self.drive.set_pv(self.motor.PV('VAL'))
        self.rbv.set_pv(self.motor.PV('RBV'))

        self.motor.DESC
        if self.label is None:
            self.label = self.motor.PV('DESC').get()
        self.desc.SetFont(self.font)
        self.desc.SetLabel(self.label)
            
        self.info.SetLabel('')
        for f in ('SET', 'LVIO', 'SPMG', 'LLS', 'HLS', 'disabled'):            
            uname = self.motor.PV(f).pvname
            wx.CallAfter(self.onMotorEvent,
                         pvname=uname, field=f)

            
    def CreatePanel(self,style='normal'):
        " build (but do not fill in) panel components"
        self.desc = wx.StaticText(self, size=(40, -1), 
                                  style=  wx.ALIGN_LEFT| wx.ST_NO_AUTORESIZE )
        self.desc.SetForegroundColour("Blue")

        self.info = wx.StaticText(self, label='', size=(40, 10),
                                  style=wx.ALIGN_CENTRE_VERTICAL|wx.ALIGN_RIGHT)
        self.info.SetForegroundColour("Red")

        self.rbv  = pvText(self, size=(70, -1), font = self.font, 
                           fg='Blue',style=wx.ALIGN_CENTRE_VERTICAL|wx.ALIGN_CENTER)

        self.drive = pvFloatCtrl(self, size=(80, -1),
                                 font=self.font, style = wx.TE_RIGHT)
        
        self.fillPanelComponents()
        spacer = wx.StaticText(self, label=' ', size=(5, 5), style=wx.ALIGN_RIGHT)           
        self.__sizer.AddMany([(spacer,      0, wx.ALIGN_CENTER),
                              (self.desc,   0, wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_LEFT),
                              (self.info,   0, wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT),
                              (self.rbv,    0, wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_LEFT),
                              (self.drive,  0, wx.ALIGN_CENTER) ])

        self.SetAutoLayout(1)
        self.SetSizer(self.__sizer)
        self.__sizer.Fit(self)

    @EpicsFunction
    def FillPanel(self):
        " fill in panel components for motor "
        if self.motor is None: return
        self.fillPanelComponents()
        self.drive.update()
        self.rbv.update()

        
    @DelayedEpicsCallback
    def onMotorEvent(self, pvname=None, field=None, event=None, **kw):
        if pvname is None:
            return None
      
        field_val = self.motor.get(field)
        field_str = self.motor.get(field, as_string=True)
        
        sys.stdout.flush()
        
        if field == 'LLM':
            self.drive.SetMin(self.motor.LLM)
        elif field == 'HLM':
            self.drive.SetMax(self.motor.HLM)

        elif field in ('LVIO', 'HLS', 'LLS'):
            s = 'Limit!'
            if (field_val == 0): s = ''
            self.info.SetLabel(s)
            
        elif field == 'SET':
            label, color='Set:','Yellow'
            if field_val == 0:
                label,color='','White'
            self.info.SetLabel(label)
            self.drive.bgcol_valid = color
            self.drive.SetBackgroundColour(color)
            self.drive.Refresh()

        elif field == 'disabled':
            label = ('','Disabled')[field_val]
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
        else:
            pass

