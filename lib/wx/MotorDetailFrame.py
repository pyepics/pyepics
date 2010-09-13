import wx
import time
import sys
import epics
import wxlib

pvText = wxlib.pvText
pvFloatCtrl = wxlib.pvFloatCtrl
pvTextCtrl = wxlib.pvTextCtrl
pvEnumButtons = wxlib.pvEnumButtons
pvEnumChoice = wxlib.pvEnumChoice
set_sizer = wxlib.set_sizer
set_float = wxlib.set_float
DelayedEpicsCallback = wxlib.DelayedEpicsCallback
EpicsFunction = wxlib.EpicsFunction


def xLabel(parent,label):
    return wx.StaticText(parent,label=label,style=wx.ALIGN_BOTTOM)

def xTitle(parent,label,fontsize=13,color='Blue'):
    u = wx.StaticText(parent,label=label,style=wx.ALIGN_BOTTOM)
    u.SetFont(wx.Font(fontsize,wx.SWISS,wx.NORMAL,wx.BOLD,False))
    u.SetForegroundColour(color)
    return u

class MotorDetailFrame(wx.Frame):
    """ Detailed Motor Setup Frame"""
    __motor_fields = ('set', 'low_limit','high_limit','soft_limit','tweak_val',
                      'high_limit_set', 'low_limit_set')

    def __init__(self, parent=None, motor=None):
        
        wx.Frame.__init__(self, parent, wx.ID_ANY, style=wx.DEFAULT_FRAME_STYLE,size=(500,775) )
        self.SetFont(wx.Font(11,wx.SWISS,wx.NORMAL,wx.BOLD,False))        

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

        spanel = wx.Panel(panel, -1, size=(500,50))
        ssizer = wx.BoxSizer(wx.HORIZONTAL)
        ssizer.AddMany([(wx.StaticText(spanel,label=' Label ',size=(65,40)), 0, wx.ALIGN_BOTTOM|wx.ALIGN_CENTER|wx.ALIGN_RIGHT), 
                        (self.motor_textctrl(spanel,'description',size=(210,40)), 1, wx.ALIGN_TOP|wx.ALIGN_LEFT),
                        (wx.StaticText(spanel,label='  units ',size=(75,40)), 0, wx.ALIGN_BOTTOM|wx.ALIGN_RIGHT), 
                        (self.motor_textctrl(spanel,'units',size=(95,40)), 0, wx.ALIGN_TOP|wx.ALIGN_CENTER)
                        ])

        sizer.Add(ssizer, 0, wx.EXPAND)
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
        self.info = wx.StaticText(dp, label='', size=(55, 20), style=wx.ALIGN_CENTER)
        self.info.SetForegroundColour("Red")

        ds.Add(xLabel(dp,"High Limit"),               (nrow,0), (1,1), _textstyle,_textpadding)
        ds.Add(self.motor_ctrl(dp,'high_limit'),      (nrow,1), (1,1), wx.ALIGN_CENTER)
        ds.Add(self.motor_ctrl(dp,'dial_high_limit'), (nrow,2), (1,1), wx.ALIGN_CENTER)
        ds.Add(self.info,                             (nrow,3), (1,1), wx.ALIGN_CENTER)        

        ####
        
        nrow = nrow + 1
        ostyle = wx.ALIGN_CENTER|wx.ALIGN_CENTER_VERTICAL|wx.RIGHT|wx.EXPAND
        ds.Add(xLabel(dp,"Readback"),                (nrow,0),  (1,1), _textstyle,_textpadding)
        ds.Add(self.motor_text(dp,'readback'),       (nrow,1),  (1,1), ostyle, 5)
        ds.Add(self.motor_text(dp,'dial_readback'),  (nrow,2),  (1,1), ostyle, 5)
        ds.Add(self.motor_text(dp,'raw_readback'),   (nrow,3),  (1,1), ostyle, 5)

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
        twk_val = pvFloatCtrl(twk_panel, size=(110,-1),precision=prec)
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

        epv = self.motor.get_pv('enabled')


        able_btns = pvEnumButtons(dp, pv=self.motor.get_pv('enabled'),
                                  orientation = wx.VERTICAL, 
                                  size=(110,-1))

        ds.Add(able_btns,             (nrow-1,3), (2,1), wx.ALIGN_CENTER)

        stop_btns = pvEnumButtons(dp, pv=self.motor.get_pv('stop_go'),
                                  orientation = wx.VERTICAL, 
                                  size=(110,-1))

        ds.Add(stop_btns,             (2,4), (4,1), wx.ALIGN_RIGHT)

        for attr in ('low_limit','high_limit','dial_low_limit','dial_high_limit'):
            pv = self.motor.get_pv(attr)
            pv.add_callback(self.onLimitChange, wid=self.GetId(), attr=attr)
            
        # a
        set_sizer(dp,ds) # ,fit=True)
        sizer.Add(dp, 0)

        ####
        sizer.Add(wx.StaticLine(panel,size=(100,2)),  0, wx.EXPAND)
        sizer.Add((5,5),0)
        sizer.Add(xTitle(panel,'Calibration'), 0,_textstyle,_textpadding)        

        ds = wx.GridBagSizer(6, 4)
        dp = wx.Panel(panel)
                   
        ds.Add(xLabel(dp, 'Mode: '),      (0,0),(1,1), _textstyle,_textpadding)
        

        
        ds.Add(pvEnumButtons(dp, pv=self.motor.get_pv('set'),
                              orientation = wx.HORIZONTAL, 
                              size=(110,-1)), (0,1), (1,1), wx.ALIGN_LEFT)

        ds.Add(xLabel(dp, 'Direction: '), (1,0),(1,1), _textstyle,_textpadding)
        ds.Add(pvEnumButtons(dp, pv=self.motor.get_pv('direction'),
                              orientation = wx.HORIZONTAL, 
                              size=(110,-1)), (1,1), (1,1), wx.ALIGN_LEFT)


        ds.Add(xLabel(dp, 'Freeze Offset: '), (0,2),(1,1), _textstyle,_textpadding)
        ds.Add(pvEnumChoice(dp, pv=self.motor.get_pv('freeze_offset'),
                            size=(110,-1)),  (0,3), (1,1), wx.ALIGN_CENTER)
        
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
        
        for attr in self.__motor_fields:
            self.motor.get_pv(attr).add_callback(self.onMotorEvent, wid=self.GetId(),
                                                 field=attr)

        self.info.SetLabel('')
        if self.motor.get_field('set'):
            wx.CallAfter(self.onMotorEvent,
                         pvname=self.motor.get_pv('set').pvname,
                         field='set')
        for f in ('high_limit_set', 'low_limit_set', 'soft_limit'):
            if self.motor.get_field(f):
                wx.CallAfter(self.onMotorEvent,
                             pvname=self.motor.get_pv(f).pvname,
                             field=f,motor=self.motor)

        set_sizer(panel,sizer,fit=True)
        self.Show()
        self.Raise()

    @DelayedEpicsCallback
    def onMotorEvent(self, pvname=None, field=None, motor=None, **kw):
        if pvname is None:
            return None
        
        field_val = self.motor.get_field(field)
        field_str = self.motor.get_field(field,as_string=True)
        time.sleep(0.01)
        
        if field in ('soft_limit', 'high_limit_set', 'low_limit_set'):
            s = 'Limit!'
            if (field_val == 0): s = ''
            self.info.SetLabel(s)
            
        elif field == 'set':
            label,color='Set:','Yellow'
            if field_val == 0: label,color='','White'
            # print 'on Motor Event ', self.drives
            for d in self.drives:
                d.SetBackgroundColour(color)
                d.Refresh()

    def motor_ctrl(self,panel,attr):
        return pvFloatCtrl(panel, size=(100,-1), 
                           precision= self.motor.precision,
                           pv = self.motor.get_pv(attr),
                           style = wx.TE_RIGHT)

    def motor_text(self,panel,attr):
        return pvText(panel,  size=(100,-1), style=wx.ALIGN_RIGHT|wx.CENTER,
                      as_string=True, pv=self.motor.get_pv(attr))

    def motor_textctrl(self,panel,attr,size=(100,-1)):
        return pvTextCtrl(panel,  size=size, style=wx.ALIGN_LEFT|wx.TE_PROCESS_ENTER,
                          pv=self.motor.get_pv(attr))        

    @DelayedEpicsCallback
    def onLimitChange(self, pvname=None, attr=None, value=None, **kw):
        funcs = {'low_limit':       self.drives[0].SetMin,
                 'high_limit':      self.drives[0].SetMax,
                 'dial_low_limit':  self.drives[1].SetMin,
                 'dial_high_limit': self.drives[1].SetMax}
        if attr in funcs:
            funcs[attr](value)
            
    @EpicsFunction
    def onLeftButton(self,event=None):
        if (self.motor is None): return
        self.motor.tweak(dir='reverse')

    @EpicsFunction
    def onRightButton(self,event=None):
        if (self.motor is None): return        
        self.motor.tweak(dir='forward')
