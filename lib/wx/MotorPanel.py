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
import types
import epics
import time
from wxlib import pvText, pvFloatCtrl, pvTextCtrl, pvTimerMixin, pvEnumButtons, pvEnumChoice
from wxlib import catimer, set_sizer, set_float


def xLabel(parent,label):
    return wx.StaticText(parent,label=label,style=wx.ALIGN_BOTTOM)

def xTitle(parent,label,fontsize=13,color='Blue'):
    u = wx.StaticText(parent,label=label,style=wx.ALIGN_BOTTOM)
    u.SetFont(wx.Font(fontsize,wx.SWISS,wx.NORMAL,wx.BOLD,False))
    u.SetForegroundColour(color)
    return u

    
class MotorDetailFrame(wx.Frame,pvTimerMixin):
    """ Detailed Motor Setup Frame"""
    __motor_fields = ('set','low_limit','high_limit','soft_limit','tweak_val',
                      'high_limit_set', 'low_limit_set')

    def __init__(self, motor=None, timer=None):
        
        wx.Frame.__init__(self, None, wx.ID_ANY, style=wx.DEFAULT_FRAME_STYLE,size=(500,750) )
        self.SetFont(wx.Font(11,wx.SWISS,wx.NORMAL,wx.BOLD,False))        

        pvTimerMixin.__init__(self,timer)
        
        self.motor = motor
        prec = motor.precision
       
        self.SetTitle("Motor Details: %s  | %s |" % (self.motor.pvname, self.motor.description))

        panel = wx.Panel(self)# outerpanel)
        sizer = wx.BoxSizer(wx.VERTICAL)

        devtype = motor.get_field('device_type',as_string=True)
        mlabel = "  %s: %s   (%s) units=%s" % (motor.pvname,
                                                  motor.description, devtype, motor.units)

        mlabel = "  %s:  (%s)" % (motor.pvname, devtype)

        _textstyle = wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL|wx.LEFT
        _textpadding = 5

        sizer.Add((5,5), 0, wx.EXPAND)
        sizer.Add(xLabel(panel, mlabel),   0,  wx.EXPAND|wx.ALIGN_CENTER)

        sizer.Add((5,5), 0, wx.EXPAND)

#         lu_panel = wx.Panel(panel, -1, size=(500,-1))
#         lu_sizer = wx.BoxSizer(wx.HORIZONTAL)
# 
#         lu_sizer.AddMany([(xLabel(lu_panel,"Label"), 1, wx.ALIGN_LEFT), 
#                           (self.motor_textctrl(lu_panel,'description',size=(260,-1)),   0, wx.ALIGN_CENTER),
#                           (xLabel(lu_panel,'      units   '),    1, wx.ALIGN_CENTER),
#                           (self.motor_textctrl(lu_panel,'units',size=(50,-1)),  0, wx.ALIGN_RIGHT)])
#          
#         set_sizer(lu_panel,lu_sizer,fit=True)
# 
#         # lu_sizer.Fit(lu_panel)
#         
#         sizer.Add(lu_sizer, 0, wx.EXPAND)
               
        
        sizer.Add(wx.StaticLine(panel,size=(100,2)),  0, wx.EXPAND)


        ds = wx.GridBagSizer(6, 4)
        dp = wx.Panel(panel)
        nrow = 0
        
        nrow += 1

        ds.Add(xTitle(dp,"Drive"), (nrow,0), (1,1), _textstyle,_textpadding)
        ds.Add(xLabel(dp,"User" ), (nrow,1), (1,1), wx.ALIGN_CENTER)
        ds.Add(xLabel(dp,"Dial" ), (nrow,2), (1,1), wx.ALIGN_CENTER)
        ds.Add(xLabel(dp,"Raw"  ), (nrow,3), (1,1), wx.ALIGN_CENTER)

        ####
        nrow = nrow + 1
        ds.Add(xLabel(dp,"High Limit"),               (nrow,0), (1,1), _textstyle,_textpadding)
        ds.Add(self.motor_ctrl(dp,'high_limit'),      (nrow,1), (1,1), wx.ALIGN_CENTER)
        ds.Add(self.motor_ctrl(dp,'dial_high_limit'), (nrow,2), (1,1), wx.ALIGN_CENTER)        

        ####
        
        nrow = nrow + 1
        ds.Add(xLabel(dp,"Readback"),                (nrow,0), (1,1), _textstyle,_textpadding)
        ds.Add(self.motor_text(dp,'readback'),       (nrow,1), (1,1), wx.ALIGN_RIGHT,7)
        ds.Add(self.motor_text(dp,'dial_readback'),  (nrow,2), (1,1), wx.ALIGN_RIGHT,7)
        ds.Add(self.motor_text(dp,'raw_readback'),   (nrow,3), (1,1), wx.ALIGN_RIGHT,7)

        ####
        nrow = nrow + 1
        self.drives = [0,0,0]
        self.drives[0] = self.motor_ctrl(dp,'drive')
        self.drives[1] = self.motor_ctrl(dp,'dial_drive')
        self.drives[2] = self.motor_ctrl(dp,'raw_drive')

        ds.Add(xLabel(dp,"Move"),  (nrow,0), (1,1), _textstyle,_textpadding)
        ds.Add(self.drives[0],     (nrow,1), (1,1), wx.ALIGN_CENTER)
        ds.Add(self.drives[1],     (nrow,2), (1,1), wx.ALIGN_CENTER)
        ds.Add(self.drives[2],     (nrow,3), (1,1), wx.ALIGN_CENTER)        


        nrow = nrow + 1
        ds.Add(xLabel(dp,"Low Limit"),               (nrow,0), (1,1), _textstyle,_textpadding)
        ds.Add(self.motor_ctrl(dp,'low_limit'),      (nrow,1), (1,1), wx.ALIGN_CENTER)
        ds.Add(self.motor_ctrl(dp,'dial_low_limit'), (nrow,2), (1,1), wx.ALIGN_CENTER)

        ####

        twk_sizer = wx.BoxSizer(wx.HORIZONTAL)
        twk_panel = wx.Panel(dp)
        twk_val = pvFloatCtrl(twk_panel, size=(110,-1),precision=prec,timer=self.timer)
        twk_val.set_pv(self.motor.get_pv('tweak_val'))                
         
        twk_left = wx.Button(twk_panel, label='<',  size=(30,30))
        twk_right= wx.Button(twk_panel, label='>',  size=(30,30))
        twk_left.Bind(wx.EVT_BUTTON,  self.onLeftButton)
        twk_right.Bind(wx.EVT_BUTTON, self.onRightButton)
        twk_sizer.AddMany([(twk_left,   0, wx.ALIGN_CENTER),
                           (twk_val,    0, wx.ALIGN_CENTER),
                           (twk_right,  0, wx.ALIGN_CENTER)])
         
        set_sizer(twk_panel,twk_sizer)

        nrow = nrow + 1
        ds.Add(xLabel(dp,"Tweak"),    (nrow,0), (1,1), _textstyle,_textpadding)
        ds.Add(twk_panel,             (nrow,1), (1,2), wx.ALIGN_LEFT)
        
        able_btns = pvEnumButtons(dp, pvname=self.motor.pvname+'_able.VAL',
                                  orientation = wx.VERTICAL, 
                                  size=(110,-1),timer=self.timer)

        ds.Add(able_btns,             (nrow-1,3), (2,1), wx.ALIGN_CENTER)

        stop_btns = pvEnumButtons(dp, pvname=self.motor.get_pv('stop_go'),
                                  orientation = wx.VERTICAL, 
                                  size=(110,-1),timer=self.timer)

        ds.Add(stop_btns,             (2,4), (4,1), wx.ALIGN_RIGHT)

        for attr in ('low_limit','high_limit','dial_low_limit','dial_high_limit'):
            pv = epics.PV(self.motor.get_pv(attr))
            self.add_callback(pv, self.onLimitChange, 1224, attr=attr)
        # 
        set_sizer(dp,ds) # ,fit=True)
        sizer.Add(dp, 0)

        #### 
        sizer.Add(wx.StaticLine(panel,size=(100,2)),  0, wx.EXPAND)
        sizer.Add((5,5),0)
        sizer.Add(xTitle(panel,'Calibration'), 0,_textstyle,_textpadding)        

        ds = wx.GridBagSizer(6, 4)
        dp = wx.Panel(panel)
                   
        ds.Add(xLabel(dp, 'Mode: '),      (0,0),(1,1), _textstyle,_textpadding)
        

        
        ds.Add(pvEnumButtons(dp, pvname=self.motor.get_pv('set'),
                              orientation = wx.HORIZONTAL, 
                              size=(110,-1),timer=self.timer), (0,1), (1,1), wx.ALIGN_LEFT)

        ds.Add(xLabel(dp, 'Direction: '), (1,0),(1,1), _textstyle,_textpadding)
        ds.Add(pvEnumButtons(dp, pvname=self.motor.get_pv('direction'),
                              orientation = wx.HORIZONTAL, 
                              size=(110,-1),timer=self.timer), (1,1), (1,1), wx.ALIGN_LEFT)


        ds.Add(xLabel(dp, 'Freeze Offset: '), (0,2),(1,1), _textstyle,_textpadding)
        ds.Add(pvEnumChoice(dp, pvname=self.motor.get_pv('freeze_offset'),
                            size=(110,-1),timer=self.timer),  (0,3), (1,1), wx.ALIGN_CENTER)
        
        ds.Add(xLabel(dp, 'Offset Value: '), (1,2),(1,1), _textstyle,_textpadding)
        ds.Add(self.motor_ctrl(dp,'offset'), (1,3), (1,1), wx.ALIGN_CENTER)

        set_sizer(dp,ds)
        sizer.Add(dp,0)
        #####
        
        sizer.Add((5,5), 0)        
        sizer.Add(wx.StaticLine(panel,size=(100,2)),  0, wx.EXPAND)
        sizer.Add((5,5), 0)                
        #
        ds = wx.GridBagSizer(6, 3)
        dp = wx.Panel(panel)
        nrow = 0

        ds.Add(xTitle(dp,"Dynamics"),  (nrow,0), (1,1), _textstyle,_textpadding)
        ds.Add(xLabel(dp,"Normal" ),   (nrow,1), (1,1), wx.ALIGN_CENTER)
        ds.Add(xLabel(dp,"Backlash" ), (nrow,2), (1,1), wx.ALIGN_CENTER)

        ####
        nrow = nrow + 1
        ds.Add(xLabel(dp,"Max Speed"),           (nrow,0), (1,1), _textstyle,_textpadding)
        ds.Add(self.motor_ctrl(dp,'max_speed'), (nrow,1), (1,1), wx.ALIGN_CENTER)

        nrow = nrow + 1
        ds.Add(xLabel(dp,"Speed"),                 (nrow,0), (1,1), _textstyle,_textpadding)
        ds.Add(self.motor_ctrl(dp,'slew_speed'),   (nrow,1), (1,1), wx.ALIGN_CENTER)
        ds.Add(self.motor_ctrl(dp,'back_speed'),   (nrow,2), (1,1), wx.ALIGN_CENTER)

        nrow = nrow + 1
        ds.Add(xLabel(dp,"Base Speed"),                 (nrow,0), (1,1), _textstyle,_textpadding)
        ds.Add(self.motor_ctrl(dp,'base_speed'),   (nrow,1), (1,1), wx.ALIGN_CENTER)

        nrow = nrow + 1
        ds.Add(xLabel(dp,"Accel (s)"),              (nrow,0), (1,1), _textstyle,_textpadding)
        ds.Add(self.motor_ctrl(dp,'acceleration'),  (nrow,1), (1,1), wx.ALIGN_CENTER)
        ds.Add(self.motor_ctrl(dp,'back_accel'),    (nrow,2), (1,1), wx.ALIGN_CENTER)

        nrow = nrow + 1
        ds.Add(xLabel(dp,"Backslash Distance"),     (nrow,0), (1,2), _textstyle,_textpadding)
        ds.Add(self.motor_ctrl(dp,'backlash'),      (nrow,2), (1,1), wx.ALIGN_CENTER)

        nrow = nrow + 1
        ds.Add(xLabel(dp,"Move Fraction"),         (nrow,0), (1,2), _textstyle,_textpadding)
        ds.Add(self.motor_ctrl(dp,'move_fraction'),(nrow,2), (1,1), wx.ALIGN_CENTER)

        set_sizer(dp,ds) # ,fit=True)
        
        sizer.Add(dp,0)
        sizer.Add(wx.StaticLine(panel,size=(100,2)),  0, wx.EXPAND)

        sizer.Add((5,5), 0)                
        sizer.Add(xTitle(panel,'Resolution'), 0,_textstyle,_textpadding)

        ds = wx.GridBagSizer(4, 4)
        dp = wx.Panel(panel)

        nrow = 0
        ds.Add(xLabel(dp,"Motor Res"),             (nrow,0), (1,1), _textstyle,_textpadding)
        ds.Add(self.motor_ctrl(dp,'resolution'),   (nrow,1), (1,1), wx.ALIGN_CENTER)
        ds.Add(xLabel(dp,"Encoder Res"),            (nrow,2), (1,1), _textstyle,_textpadding)
        ds.Add(self.motor_ctrl(dp,'encoder_step'),  (nrow,3), (1,1), wx.ALIGN_CENTER)

        nrow = nrow + 1
        ds.Add(xLabel(dp,"Steps / Rev"),            (nrow,0), (1,1), _textstyle,_textpadding)
        ds.Add(self.motor_ctrl(dp,'s_revolutions'), (nrow,1), (1,1), wx.ALIGN_CENTER)
        ds.Add(xLabel(dp,"Units / Rev"),            (nrow,2), (1,1), _textstyle,_textpadding)
        ds.Add(self.motor_ctrl(dp,'u_revolutions'), (nrow,3), (1,1), wx.ALIGN_CENTER)        

        nrow = nrow + 1
        ds.Add(xLabel(dp,"Precision"),           (nrow,0), (1,1), _textstyle,_textpadding)
        ds.Add(self.motor_ctrl(dp,'precision'),  (nrow,1), (1,1), wx.ALIGN_CENTER)        

        set_sizer(dp,ds) 
        sizer.Add(dp,0)
        sizer.Add(wx.StaticLine(panel,size=(100,2)),  0, wx.EXPAND)        
        
        for i in self.__motor_fields:
            self.set_field_callback(i, self.onMotorEvent)

        ############
        set_sizer(panel,sizer,fit=True)
# 
#         outersizer = wx.BoxSizer(wx.HORIZONTAL)
#         outersizer.Add((34,10),0,wx.ALIGN_LEFT,30)
# 
#         outersizer.Add(panel,1,wx.ALIGN_CENTER,30)

        
        # set_sizer(self,outersizer,fit=True)
        
        self.Show()
        self.Raise()

    def set_field_callback(self, attr, callback):
        m = self.motor
        kw = {'field': attr, 'motor': m}
        m.store_attr(attr)
        self.add_callback(m._dat[attr], callback, -5, **kw)

    def onMotorEvent(self,pvname=None,field=None,motor=None,**kw):        
        print 'Motor event ' , pvname, field, motor
        if (pvname is None): return None
        
        field_val = motor.get_field(field)
        field_str = motor.get_field(field,as_string=1)

        if field in ('soft_limit', 'high_limit_set', 'low_limit_set'):
            s = 'Limit!'
            if (field_val == 0): s = ''

        elif field == 'set':
            label,color='Set:','Yellow'
            if field_val == 0: label,color='','White'
            # print 'on Motor Event ', self.drives
            for d in self.drives:
                d.SetBackgroundColour(color)
                d.Refresh()

    def motor_ctrl(self,panel,attr):
        return pvFloatCtrl(panel, size=(100,-1), timer=self.timer,
                           precision= self.motor.precision,
                           pvname = self.motor.get_pv(attr))

    def motor_text(self,panel,attr):
        return pvText(panel,  size=(100,-1), # style=wx.ALIGN_RIGHT,
                      timer=self.timer, as_string=True,
                      pvname=self.motor.get_pv(attr))

    def motor_textctrl(self,panel,attr,size=(100,-1)):
        return pvTextCtrl(panel,  size=size, # style=wx.ALIGN_RIGHT,
                          timer=self.timer, 
                          pvname=self.motor.get_pv(attr))        

#     def pv_text(self,panel,pvname):
#         return pvText(panel,  size=(100,-1), # style=wx.ALIGN_RIGHT,
#                       timer=self.timer, pvname=pvname)

    
    def onLimitChange(self,pv=None,attr=None,**kw):
        lim_val  = self.motor.get_field(attr)
        if   'low_limit' == attr:         self.drives[0].SetMin(lim_val)
        elif 'high_limit' == attr:        self.drives[0].SetMax(lim_val)
        elif 'dial_low_limit' == attr:    self.drives[1].SetMin(lim_val)
        elif 'dial_high_limit' == attr:   self.drives[1].SetMax(lim_val)
            

    def onLeftButton(self,event=None):
        if (self.motor is None): return
        self.motor.tweak_reverse = 1

    def onRightButton(self,event=None):
        if (self.motor is None): return        
        self.motor.tweak_forward = 1
        
class MotorPanel(wx.Panel,pvTimerMixin):
    """ MotorPanel  a simple wx windows panel for controlling an Epics Motor
    """
    __motor_fields = ('set','low_limit','high_limit','soft_limit','tweak_val',
                      'high_limit_set', 'low_limit_set')

    def __init__(self, parent,  motor=None,  timer=None,
                 style='normal', messenger=None, *args, **kw):

        wx.Panel.__init__(self, parent, style=wx.TAB_TRAVERSAL)
        self.SetFont(wx.Font(13,wx.SWISS,wx.NORMAL,wx.BOLD))
        self.parent = parent
        # wx.Panel.SetBackgroundColour(self,(245,245,225))

        pvTimerMixin.__init__(self,timer)

        if (callable(messenger)): self.__messenger = messenger
        self.style = style
        self.format = "%.3f" 
        self.motor = None
        self.__sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.CreatePanel()
        self.SelectMotor(motor)
        
    def SelectMotor(self, motor):
        " set motor to a named motor PV"
        if self.motor is not None:
            for i in self.__motor_fields:
                self.motor.clear_field_callback(i)
                
        if motor is None: return
        self.motor = epics.Motor(motor)
        
        self.format = "%%.%if" % self.motor.precision
        self.FillPanel()

        self.set_Tweak(self.format % self.motor.tweak_val)
        for i in self.__motor_fields:
            self.set_field_callback(i, self.onMotorEvent)

        self.info.SetLabel('')
        if (self.motor.get_field('set') == 1): self.info.SetLabel('Set:')
        for f in ('high_limit_set', 'low_limit_set', 'soft_limit'):
            if (self.motor.get_field(f) != 0):
                self.info.SetLabel('Limit!')

    def set_field_callback(self, attr, callback):
        m = self.motor
        kw = {'field': attr, 'motor': m}
        m.store_attr(attr)
        self.add_callback(m._dat[attr], callback, -6, **kw)

    def CreatePanel(self,style='normal'):
        " build (but do not fill in) panel components"
        print 'Create Panel !! '
        self.desc = pvText(self, timer= self.timer, size=(245, -1),
                           style=wx.ALIGN_RIGHT)
        self.rbv  = pvText(self, timer= self.timer, size=(125, -1),
                           fg='Blue',style=wx.ALIGN_CENTER)
        self.info = wx.StaticText(self, label='', size=(55, 20), style=wx.ALIGN_CENTER)
        self.info.SetForegroundColour("Red")

        self.drive = pvFloatCtrl(self,  size=(110,-1),
                                 timer=self.timer, style = wx.TE_RIGHT)
        
        try:
            self.drive.set_pv(self.motor.get_pv('drive'))
            self.rbv.set_pv(self.motor.get_pv('readback') )
            self.desc.set_pv(self.motor.get_pv('description') )
        except:
            pass
        
        self.twk_list = ['','']
        self.__twkbox = wx.ComboBox(self, value='', size=(120,-1), 
                                    choices=self.twk_list,
                                    style=wx.CB_DROPDOWN|wx.TE_PROCESS_ENTER)

        self.__twkbox.Bind(wx.EVT_COMBOBOX,    self.OnTweakBoxEvent)
        self.__twkbox.Bind(wx.EVT_TEXT_ENTER,  self.OnTweakBoxEvent)        

        twkbtn1 = wx.Button(self, label='<',  size=(30,30))
        twkbtn2 = wx.Button(self, label='>',  size=(30,30))
        stopbtn = wx.Button(self, label=' Stop ')
        morebtn = wx.Button(self, label=' More ')
        
        twkbtn1.Bind(wx.EVT_BUTTON, self.onLeftButton)
        twkbtn2.Bind(wx.EVT_BUTTON, self.onRightButton)
        stopbtn.Bind(wx.EVT_BUTTON, self.onStopButton)
        morebtn.Bind(wx.EVT_BUTTON, self.onMoreButton)

        for b in (twkbtn1, twkbtn2):
            b.SetFont(wx.Font(12,wx.SWISS,wx.NORMAL,wx.BOLD,False))
            
        self.__sizer.AddMany([(self.desc,   0, wx.ALIGN_CENTER),
                              (self.rbv,    0, wx.ALIGN_CENTER),
                              (self.info,   0, wx.ALIGN_CENTER),
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

    def FillPanel(self):
        " fill in panel components for motor "
        if self.motor is None: return

        

        self.desc.set_pv(self.motor.get_pv('description'))
        self.rbv.set_pv(self.motor.get_pv('readback'))
        self.drive.set_pv(self.motor.get_pv('drive'))


        self.drive.update()
        self.desc.update()
        self.rbv.update()

        self.twk_list = self.Create_StepList()
        self.__Update_StepList()
        
    def onLeftButton(self,event=None):
        if (self.motor is None): return        
        self.motor.tweak_reverse = 1

    def onRightButton(self,event=None):
        if (self.motor is None): return        
        self.motor.tweak_forward = 1

    def onStopButton(self,event=None):
        if (self.motor is None): return        
        self.motor.stop()
        epics.ca.poll()

    def onMoreButton(self,event=None):
        if (self.motor is None): return        
        x = MotorDetailFrame(motor=self.motor)
            
    def OnTweakBoxEvent(self,event):
        if (self.motor is None): return
        try:
            self.motor.tweak_val = set_float(event.GetString())
        except:
            pass

    def onMotorEvent(self,pvname=None,field=None,motor=None,**kw):        
        if (pvname is None): return None
        field_val = motor.get_field(field)
        field_str = motor.get_field(field,as_string=1)
        if field == 'low_limit':
            self.drive.SetMin(self.motor.low_limit)
        elif field == 'high_limit':
            self.drive.SetMax(self.motor.high_limit)

        elif field in ('soft_limit', 'high_limit_set', 'low_limit_set'):
            s = 'Limit!'
            if (field_val == 0): s = ''
            self.info.SetLabel(s)
            
        elif field == 'set':
            label,color='Set:','Yellow'
            if field_val == 0: label,color='','White'
            self.info.SetLabel(label)
            self.drive.bgcol_valid = color
            self.drive.SetBackgroundColour(color)
            self.drive.Refresh()
            
        elif field == 'tweak_val':
            self.set_Tweak(field_str)
        else:
            pass

    def set_Tweak(self,val):
        if type(val) is not types.StringType: val = self.format % val
        if val not in self.twk_list:  self.__Update_StepList(value=val)
        self.__twkbox.SetValue(val)
            
    def Create_StepList(self):
        """ create initial list of motor steps, based on motor range
        and precision"""

        print 'Create_StepList: ', self.motor

        if self.motor is None: return []
        smax = abs(self.motor.high_limit - self.motor.low_limit)*0.6

        p = self.motor.precision
        print self.motor.high_limit, self.motor.low_limit, smax, p

        l = []
        for i in range(6):
            x = 10**(i-p)
            for j in (1,2,5):
                if (j*x < smax):  l.append(j*x)
        return [self.format%i for i in l]

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
        
