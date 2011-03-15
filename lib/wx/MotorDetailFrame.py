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
    __motor_fields = ('SET', 'LLM','HLM','LVIO','TWV', 'HLS', 'LLS')

    def __init__(self, parent=None, motor=None):
        
        wx.Frame.__init__(self, parent, wx.ID_ANY, style=wx.DEFAULT_FRAME_STYLE,size=(500,775) )
        self.SetFont(wx.Font(11,wx.SWISS,wx.NORMAL,wx.BOLD,False))        

        self.motor = motor
        prec = motor.PREC
        motor_pvname = self.motor._prefix
        devtype = motor.get('DTYP',as_string=True)

        if motor_pvname.endswith('.'):
            motor_pvname = motor_pvname[:-1]
            
        self.SetTitle("Motor Details: %s  | %s | (%s)" % (motor_pvname, self.motor.DESC, devtype))

        panel = wx.Panel(self) 
        sizer = wx.BoxSizer(wx.VERTICAL)

        
        _textstyle = wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL|wx.LEFT
        _textpadding = 5

        spanel = wx.Panel(panel, -1, size=(500,50))


        ssizer = wx.BoxSizer(wx.HORIZONTAL)
        ssizer.AddMany([(wx.StaticText(spanel,label=' Label ', size=(65,40)), 0,  wx.ALIGN_BOTTOM|wx.ALIGN_CENTER|wx.ALIGN_RIGHT), 
                        (self.motor_textctrl(spanel, 'DESC',   size=(210,40)), 1, wx.ALIGN_TOP|wx.ALIGN_LEFT),
                        (wx.StaticText(spanel,label='  units ',size=(75,40)), 0,  wx.ALIGN_BOTTOM|wx.ALIGN_RIGHT), 
                        (self.motor_textctrl(spanel, 'EGU',    size=(95,40)), 0,  wx.ALIGN_TOP|wx.ALIGN_CENTER)
                        ])

        set_sizer(spanel, ssizer)
        sizer.Add(spanel, 0, wx.EXPAND)
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
        ds.Add(self.motor_ctrl(dp,'HLM'),      (nrow,1), (1,1), wx.ALIGN_CENTER)
        ds.Add(self.motor_ctrl(dp,'DHLM'), (nrow,2), (1,1), wx.ALIGN_CENTER)
        ds.Add(self.info,                             (nrow,3), (1,1), wx.ALIGN_CENTER)        

        ####
        
        nrow = nrow + 1
        ostyle = wx.ALIGN_CENTER|wx.ALIGN_CENTER_VERTICAL|wx.RIGHT|wx.EXPAND
        ds.Add(xLabel(dp,"Readback"),        (nrow,0),  (1,1), _textstyle,_textpadding)
        ds.Add(self.motor_text(dp, 'RBV'),    (nrow,1),  (1,1), ostyle, 5)
        ds.Add(self.motor_text(dp, 'DRBV'),   (nrow,2),  (1,1), ostyle, 5)
        ds.Add(self.motor_text(dp, 'RRBV'),   (nrow,3),  (1,1), ostyle, 5)

        ####
        nrow = nrow + 1
        self.drives = [0,0,0]
        self.drives[0] = self.motor_ctrl(dp, 'VAL')
        self.drives[1] = self.motor_ctrl(dp, 'DVAL')
        self.drives[2] = self.motor_ctrl(dp, 'RVAL')

        ds.Add(xLabel(dp,"Move"),  (nrow,0), (1,1), _textstyle,_textpadding)
        ds.Add(self.drives[0],     (nrow,1), (1,1), wx.ALIGN_CENTER)
        ds.Add(self.drives[1],     (nrow,2), (1,1), wx.ALIGN_CENTER)
        ds.Add(self.drives[2],     (nrow,3), (1,1), wx.ALIGN_CENTER)        


        nrow = nrow + 1
        ds.Add(xLabel(dp,"Low Limit"),               (nrow,0), (1,1), _textstyle,_textpadding)
        ds.Add(self.motor_ctrl(dp, 'LLM'),      (nrow,1), (1,1), wx.ALIGN_CENTER)
        ds.Add(self.motor_ctrl(dp, 'DLLM'), (nrow,2), (1,1), wx.ALIGN_CENTER)

        ####

        twk_sizer = wx.BoxSizer(wx.HORIZONTAL)
        twk_panel = wx.Panel(dp)
        twk_val = pvFloatCtrl(twk_panel, size=(110,-1),precision=prec)
        twk_val.set_pv(self.motor.PV('TWV'))                
         
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

        epv = self.motor.PV('disabled')

        able_btns = pvEnumButtons(dp, pv=epv, orientation = wx.VERTICAL, 
                                  size=(110,-1))

        ds.Add(able_btns,             (nrow-1,3), (2,1), wx.ALIGN_CENTER)

        stop_btns = pvEnumButtons(dp, pv=self.motor.PV('SPMG'),
                                  orientation = wx.VERTICAL, 
                                  size=(110,-1))

        ds.Add(stop_btns,             (2,4), (4,1), wx.ALIGN_RIGHT)

        for attr in ('LLM','HLM','DLLM','DHLM'):
            pv = self.motor.PV(attr)
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
        

        
        ds.Add(pvEnumButtons(dp, pv=self.motor.PV('SET'),
                              orientation = wx.HORIZONTAL, 
                              size=(110,-1)), (0,1), (1,1), wx.ALIGN_LEFT)

        ds.Add(xLabel(dp, 'Direction: '), (1,0),(1,1), _textstyle,_textpadding)
        ds.Add(pvEnumButtons(dp, pv=self.motor.PV('DIR'),
                              orientation = wx.HORIZONTAL, 
                              size=(110,-1)), (1,1), (1,1), wx.ALIGN_LEFT)


        ds.Add(xLabel(dp, 'Freeze Offset: '), (0,2),(1,1), _textstyle,_textpadding)
        ds.Add(pvEnumChoice(dp, pv=self.motor.PV('FOFF'),
                            size=(110,-1)),  (0,3), (1,1), wx.ALIGN_CENTER)
        
        ds.Add(xLabel(dp, 'Offset Value: '), (1,2),(1,1), _textstyle,_textpadding)
        ds.Add(self.motor_ctrl(dp,'OFF'), (1,3), (1,1), wx.ALIGN_CENTER)

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
        ds.Add(xLabel(dp,"Max Speed"),      (nrow,0), (1,1), _textstyle,_textpadding)
        ds.Add(self.motor_ctrl(dp,'SMAX'),  (nrow,1), (1,1), wx.ALIGN_CENTER)

        nrow = nrow + 1
        ds.Add(xLabel(dp,"Speed"),           (nrow,0), (1,1), _textstyle,_textpadding)
        ds.Add(self.motor_ctrl(dp,'VELO'),   (nrow,1), (1,1), wx.ALIGN_CENTER)
        ds.Add(self.motor_ctrl(dp,'BVEL'),   (nrow,2), (1,1), wx.ALIGN_CENTER)

        nrow = nrow + 1
        ds.Add(xLabel(dp,"Base Speed"),     (nrow,0), (1,1), _textstyle,_textpadding)
        ds.Add(self.motor_ctrl(dp,'VBAS'),  (nrow,1), (1,1), wx.ALIGN_CENTER)

        nrow = nrow + 1
        ds.Add(xLabel(dp,"Accel (s)"),      (nrow,0), (1,1), _textstyle,_textpadding)
        ds.Add(self.motor_ctrl(dp,'ACCL'),  (nrow,1), (1,1), wx.ALIGN_CENTER)
        ds.Add(self.motor_ctrl(dp,'BACC'),  (nrow,2), (1,1), wx.ALIGN_CENTER)

        nrow = nrow + 1
        ds.Add(xLabel(dp,"Backslash Distance"),     (nrow,0), (1,2), _textstyle,_textpadding)
        ds.Add(self.motor_ctrl(dp,'BDST'),      (nrow,2), (1,1), wx.ALIGN_CENTER)

        nrow = nrow + 1
        ds.Add(xLabel(dp,"Move Fraction"),         (nrow,0), (1,2), _textstyle,_textpadding)
        ds.Add(self.motor_ctrl(dp,'FRAC'),(nrow,2), (1,1), wx.ALIGN_CENTER)

        set_sizer(dp,ds) # ,fit=True)
        
        sizer.Add(dp,0)
        sizer.Add(wx.StaticLine(panel,size=(100,2)),  0, wx.EXPAND)

        sizer.Add((5,5), 0)                
        sizer.Add(xTitle(panel,'Resolution'), 0,_textstyle,_textpadding)

        ds = wx.GridBagSizer(4, 4)
        dp = wx.Panel(panel)

        nrow = 0
        ds.Add(xLabel(dp,"Motor Res"),      (nrow,0), (1,1), _textstyle,_textpadding)
        ds.Add(self.motor_ctrl(dp,'MRES'),  (nrow,1), (1,1), wx.ALIGN_CENTER)
        ds.Add(xLabel(dp,"Encoder Res"),    (nrow,2), (1,1), _textstyle,_textpadding)
        ds.Add(self.motor_ctrl(dp,'ERES'),  (nrow,3), (1,1), wx.ALIGN_CENTER)

        nrow = nrow + 1
        ds.Add(xLabel(dp,"Steps / Rev"),    (nrow,0), (1,1), _textstyle,_textpadding)
        ds.Add(self.motor_ctrl(dp,'SREV'),  (nrow,1), (1,1), wx.ALIGN_CENTER)
        ds.Add(xLabel(dp,"Units / Rev"),    (nrow,2), (1,1), _textstyle,_textpadding)
        ds.Add(self.motor_ctrl(dp,'UREV'),  (nrow,3), (1,1), wx.ALIGN_CENTER)        

        nrow = nrow + 1
        ds.Add(xLabel(dp,"Precision"),      (nrow,0), (1,1), _textstyle,_textpadding)
        ds.Add(self.motor_ctrl(dp,'PREC'),  (nrow,1), (1,1), wx.ALIGN_CENTER)        

        set_sizer(dp,ds) 
        sizer.Add(dp,0)
        sizer.Add(wx.StaticLine(panel,size=(100,2)),  0, wx.EXPAND)        
        
        for attr in self.__motor_fields:
            self.motor.PV(attr).add_callback(self.onMotorEvent, wid=self.GetId(),
                                                 field=attr)

        self.info.SetLabel('')
        if self.motor.get('SET'):
            wx.CallAfter(self.onMotorEvent,
                         pvname=self.motor.PV('SET').pvname,
                         field='SET')
        for f in ('HLS', 'LLS', 'LVIO'):
            if self.motor.get(f):
                wx.CallAfter(self.onMotorEvent,
                             pvname=self.motor.PV(f).pvname,
                             field=f,motor=self.motor)

        set_sizer(panel,sizer,fit=True)
        self.Show()
        self.Raise()

    @DelayedEpicsCallback
    def onMotorEvent(self, pvname=None, field=None, motor=None, **kw):
        if pvname is None:
            return None
        
        field_val = self.motor.get(field)
        field_str = self.motor.get(field,as_string=True)
        
        if field in ('LVIO', 'HLS', 'LLS'):
            s = 'Limit!'
            if (field_val == 0): s = ''
            self.info.SetLabel(s)
            
        elif field == 'SET':
            label,color='Set:','Yellow'
            if field_val == 0: label,color='','White'
            # print 'on Motor Event ', self.drives
            for d in self.drives:
                d.SetBackgroundColour(color)
                d.Refresh()

    def motor_ctrl(self, panel, attr):
        return pvFloatCtrl(panel, size=(100,-1), 
                           precision= self.motor.PREC,
                           pv = self.motor.PV(attr),
                           style = wx.TE_RIGHT)

    def motor_text(self, panel, attr):
        return pvText(panel,  size=(100,-1), style=wx.ALIGN_RIGHT|wx.CENTER,
                      as_string=True, pv=self.motor.PV(attr))

    def motor_textctrl(self,panel,attr,size=(100,-1)):
        return pvTextCtrl(panel,  size=size, style=wx.ALIGN_LEFT|wx.TE_PROCESS_ENTER,
                          pv=self.motor.PV(attr))        

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
        self.motor.tweak(direction='reverse')

    @EpicsFunction
    def onRightButton(self,event=None):
        if (self.motor is None): return        
        self.motor.tweak(direction='forward')
