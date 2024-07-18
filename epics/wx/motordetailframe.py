"""
wxFrame for Detailed Motor Settings, ala medm More (+Setup) screen
"""

import time
import wx
from wx.lib.scrolledpanel import ScrolledPanel

from .wxlib import (PVText, PVFloatCtrl, PVTextCtrl, PVEnumButtons,
                    PVEnumChoice, DelayedEpicsCallback, EpicsFunction)
from .wxutils import set_sizer, LCEN, RCEN, CEN, FileSave
from epics.utils import IOENCODING

TMPL_TOP = '''file "$(CARS)/CARSApp/Db/motor.db"
{
pattern
{P,       M,    DTYP,      C,  S,  DESC,               EGU,  DIR,  VELO, VBAS, ACCL, BDST,BVEL,BACC, SREV,UREV,PREC,DHLM,DLLM}
'''

def xLabel(parent, label):
    "simple label"
    return wx.StaticText(parent, label=" %s" % label, style=wx.ALIGN_BOTTOM)

def xTitle(parent, label, fontsize=13, color='Blue'):
    "simple title"
    wid = wx.StaticText(parent, label="  %s" % label, style=wx.ALIGN_BOTTOM)
    font = wid.GetFont()
    font.PointSize = fontsize
    wid.SetFont(font)
    wid.SetForegroundColour(color)
    return wid

MAINSIZE = (525, 750)
class MotorDetailFrame(wx.Frame):
    """ Detailed Motor Setup Frame"""
    __motor_fields = ('SET', 'LLM', 'HLM', 'LVIO', 'TWV', 'HLS', 'LLS')

    def __init__(self, parent=None, motor=None):
        wx.Frame.__init__(self, parent, wx.ID_ANY, size=MAINSIZE,
                          style=wx.DEFAULT_FRAME_STYLE|wx.TAB_TRAVERSAL)

        self.motor = motor
        devtype = motor.get('DTYP', as_string=True)
        motor_pvname = self.motor._prefix
        if motor_pvname.endswith('.'):
            motor_pvname = motor_pvname[:-1]

        self.SetTitle("Motor Details: %s  | %s | (%s)" % (motor_pvname,
                                                          self.motor.DESC,
                                                          devtype))

        sizer = wx.BoxSizer(wx.VERTICAL)
        panel = MotorDetailPanel(parent=self, motor=motor)

        sizer.Add(panel, 1, wx.EXPAND)

        # self.createMenu()
        set_sizer(self, sizer)

        self.Show()
        self.Raise()

    def createMenu(self, event=None):
        fmenu = wx.Menu()
        id_save = wx.NewId()
        id_copy = wx.NewId()
        fmenu.Append(id_save, "&Save Template File",
                     "Save Motor Template for this motor")
        fmenu.Append(id_copy, "&Copy Template"
                     "Copy Motor Template to Clipboard")

        menuBar = wx.MenuBar()
        menuBar.Append(fmenu, "&File");

        self.SetMenuBar(menuBar)
        self.Bind(wx.EVT_MENU,  self._onSaveTemplate, id=id_save)
        self.Bind(wx.EVT_MENU,  self._onCopyTemplate, id=id_copy)

    @EpicsFunction
    def MakeTemplate(self, event=None):
        out = TMPL_TOP
        return out

    @EpicsFunction
    def _onSaveTemplate(self, event=None):
        name = self.motor.pvname
        fname = FileSave(self, 'Save Template File',
                         wildcard='INI (*.template)|*.template|All files (*.*)|*.*',
                         default_file='Motor_%s.template' % name)
        if fname is not None:
            fout = open(fname, 'w+', encoding=IOENCODING)
            fout.write("%s\n" % self.MakeTemplate())
            fout.close()

    @EpicsFunction
    def _onCopyTemplate(self, event=None):
        dat = wx.TextDataObject()
        dat.SetText(self.MakeTemplate())
        wx.TheClipboard.Open()
        wx.TheClipboard.SetData(dat)
        wx.TheClipboard.Close()


class MotorDetailPanel(ScrolledPanel):
    """ Detailed Motor Setup Panel"""
    __motor_fields = ('SET', 'LLM', 'HLM', 'LVIO', 'TWV', 'HLS', 'LLS')

    def __init__(self, parent=None, motor=None):
        ScrolledPanel.__init__(self, parent, size=MAINSIZE, name='',
                               style=wx.EXPAND|wx.GROW|wx.TAB_TRAVERSAL)

        self.Freeze()
        self.motor = motor
        prec = motor.PREC

        sizer = wx.BoxSizer(wx.VERTICAL)


        ds = wx.GridBagSizer(1, 6)
        dp = wx.Panel(self)

        ds.Add(xLabel(dp, 'Label'), (0, 0), (1, 1), LCEN, 5)
        ds.Add(self.MotorTextCtrl(dp, 'DESC',  size=(180, -1)),
               (0, 1), (1, 1), LCEN, 5)

        ds.Add(xLabel(dp, 'units'), (0, 2), (1, 1), LCEN, 5)
        ds.Add(self.MotorTextCtrl(dp, 'EGU',  size=(90, -1)),
               (0, 3), (1, 1), LCEN, 5)
        ds.Add(xLabel(dp, "Precision"),      (0, 4), (1, 1), LCEN, 5)
        ds.Add(self.MotorCtrl(dp, 'PREC', size=(30, -1)),  (0, 5), (1, 1), CEN)

        set_sizer(dp, ds)
        sizer.Add(dp, 0)

        sizer.Add((3, 3), 0)
        sizer.Add(wx.StaticLine(self, size=(100, 2)),  0, wx.EXPAND)
        sizer.Add((3, 3), 0)

        ds = wx.GridBagSizer(6, 4)
        dp = wx.Panel(self)
        nrow = 0
        ds.Add(xTitle(dp,"Drive"), (nrow, 0), (1, 1), LCEN, 5)
        ds.Add(xLabel(dp,"User" ), (nrow, 1), (1, 1), CEN, 5)
        ds.Add(xLabel(dp,"Dial" ), (nrow, 2), (1, 1), CEN, 5)
        ds.Add(xLabel(dp,"Raw"  ), (nrow, 3), (1, 1), CEN, 5)

        ####
        nrow += 1
        self.info = wx.StaticText(dp, label='', size=(55, 20), style=CEN)
        self.info.SetForegroundColour("Red")

        ds.Add(xLabel(dp,"High Limit"),     (nrow, 0), (1, 1), LCEN, 5)
        ds.Add(self.MotorCtrl(dp,'HLM'),   (nrow, 1), (1, 1), CEN, 5)
        ds.Add(self.MotorCtrl(dp,'DHLM'),  (nrow, 2), (1, 1), CEN, 5)
        ds.Add(self.info,                   (nrow, 3), (1, 1), CEN, 5)

        ####
        nrow += 1
        ostyle = RCEN|wx.EXPAND
        ds.Add(xLabel(dp,"Readback"),       (nrow, 0),  (1, 1), LCEN, 5)
        ds.Add(self.MotorText(dp, 'RBV'),  (nrow, 1),  (1, 1), ostyle, 5)
        ds.Add(self.MotorText(dp, 'DRBV'), (nrow, 2),  (1, 1), ostyle, 5)
        ds.Add(self.MotorText(dp, 'RRBV'), (nrow, 3),  (1, 1), ostyle, 5)

        ####
        nrow += 1
        self.drives  = [self.MotorCtrl(dp, 'VAL'),
                        self.MotorCtrl(dp, 'DVAL'),
                        self.MotorCtrl(dp, 'RVAL')]

        ds.Add(xLabel(dp,"Move"),  (nrow, 0), (1, 1), LCEN, 5)
        ds.Add(self.drives[0],     (nrow, 1), (1, 1), CEN, 5)
        ds.Add(self.drives[1],     (nrow, 2), (1, 1), CEN, 5)
        ds.Add(self.drives[2],     (nrow, 3), (1, 1), CEN, 5)

        nrow += 1
        ds.Add(xLabel(dp,"Low Limit"),      (nrow, 0), (1, 1), LCEN, 5)
        ds.Add(self.MotorCtrl(dp, 'LLM'),  (nrow, 1), (1, 1), CEN, 5)
        ds.Add(self.MotorCtrl(dp, 'DLLM'), (nrow, 2), (1, 1), CEN, 5)

        ####

        twk_sizer = wx.BoxSizer(wx.HORIZONTAL)
        twk_panel = wx.Panel(dp)
        twk_val = PVFloatCtrl(twk_panel, size=(110, -1), precision=prec)
        twk_val.SetPV(self.motor.PV('TWV'))

        twk_left = wx.Button(twk_panel, label='<',  size=(35, 30))
        twk_right = wx.Button(twk_panel, label='>',  size=(35, 30))
        twk_left.Bind(wx.EVT_BUTTON,  self.OnLeftButton)
        twk_right.Bind(wx.EVT_BUTTON, self.OnRightButton)
        twk_sizer.AddMany([(twk_left,   0, CEN),
                           (twk_val,    0, CEN),
                           (twk_right,  0, CEN)])

        set_sizer(twk_panel, twk_sizer)

        nrow += 1
        ds.Add(xLabel(dp,"Tweak"),    (nrow, 0), (1, 1), LCEN, 5)
        ds.Add(twk_panel,             (nrow, 1), (1, 2), wx.ALIGN_LEFT, 5)

        epv = self.motor.PV('disabled')

        able_btns = PVEnumButtons(dp, pv=epv, orientation = wx.VERTICAL,
                                  size=(80, 60))

        ds.Add(able_btns,   (nrow-1, 3), (2, 1), CEN, 5)

        stop_btns = PVEnumButtons(dp, pv=self.motor.PV('SPMG'),
                                  orientation = wx.VERTICAL,
                                  size=(100, 125))

        ds.Add(stop_btns,     (2, 4), (4, 1), wx.ALIGN_RIGHT, 5)

        for attr in ('LLM', 'HLM', 'DLLM', 'DHLM'):
            pv = self.motor.PV(attr)
            pv.add_callback(self.OnLimitChange, wid=self.GetId(), attr=attr)

        #
        set_sizer(dp, ds) # ,fit=True)
        sizer.Add(dp, 0)

        ####
        sizer.Add((3, 3), 0)
        sizer.Add(wx.StaticLine(self, size=(100, 2)),  0, wx.EXPAND)
        sizer.Add((3, 3), 0)
        sizer.Add(xTitle(self, 'Calibration'), 0, LCEN, 25)

        ds = wx.GridBagSizer(6, 5)
        dp = wx.Panel(self)

        ds.Add(xLabel(dp, 'Mode: '),  (0, 0), (1, 1), LCEN, 5)

        ds.Add(PVEnumButtons(dp, pv=self.motor.PV('SET'),
                             orientation = wx.HORIZONTAL,
                             size=(175, 25)), (0, 1), (1, 2), wx.ALIGN_LEFT)

        ds.Add(xLabel(dp, 'Direction: '), (1, 0), (1, 1), LCEN, 5)
        ds.Add(PVEnumButtons(dp, pv=self.motor.PV('DIR'),
                             orientation=wx.HORIZONTAL,
                             size=(175, 25)), (1, 1), (1, 2), wx.ALIGN_LEFT)

        ds.Add(xLabel(dp, 'Freeze Offset: '), (0, 4), (1, 1), LCEN, 5)
        ds.Add(PVEnumChoice(dp, pv=self.motor.PV('FOFF'),
                            size=(110, -1)),  (0, 5), (1, 1), CEN)

        ds.Add(xLabel(dp, 'Offset Value: '), (1, 4), (1, 1), LCEN, 5)
        ds.Add(self.MotorCtrl(dp,'OFF'),    (1, 5), (1, 1), CEN)

        set_sizer(dp, ds)
        sizer.Add(dp, 0)
        #####

        sizer.Add((3, 3), 0)
        sizer.Add(wx.StaticLine(self, size=(100, 2)),  0, wx.EXPAND)
        sizer.Add((3, 3), 0)
        #
        ds = wx.GridBagSizer(6, 3)
        dp = wx.Panel(self)
        nrow = 0

        ds.Add(xTitle(dp, "Dynamics"),  (nrow, 0), (1, 1), LCEN, 55)
        ds.Add(xLabel(dp, "Normal" ),   (nrow, 1), (1, 1), CEN)
        ds.Add(xLabel(dp, "Backlash" ), (nrow, 2), (1, 1), CEN)

        ####
        nrow += 1
        ds.Add(xLabel(dp, "Max Speed"),      (nrow, 0), (1, 1), LCEN, 5)
        ds.Add(self.MotorCtrl(dp, 'VMAX'),  (nrow, 1), (1, 1), CEN)

        nrow += 1
        ds.Add(xLabel(dp, "Speed"),           (nrow, 0), (1, 1), LCEN, 5)
        ds.Add(self.MotorCtrl(dp, 'VELO'),   (nrow, 1), (1, 1), CEN)
        ds.Add(self.MotorCtrl(dp, 'BVEL'),   (nrow, 2), (1, 1), CEN)

        nrow += 1
        ds.Add(xLabel(dp, "Base Speed"),     (nrow, 0), (1, 1), LCEN, 5)
        ds.Add(self.MotorCtrl(dp, 'VBAS'),  (nrow, 1), (1, 1), CEN)

        nrow += 1
        ds.Add(xLabel(dp, "Accel (s)"),      (nrow, 0), (1, 1), LCEN, 5)
        ds.Add(self.MotorCtrl(dp, 'ACCL'),  (nrow, 1), (1, 1), CEN)
        ds.Add(self.MotorCtrl(dp, 'BACC'),  (nrow, 2), (1, 1), CEN)

        nrow += 1
        ds.Add(xLabel(dp, "Backslash Distance"), (nrow, 0), (1, 2), LCEN, 5)
        ds.Add(self.MotorCtrl(dp, 'BDST'),     (nrow, 2), (1, 1), CEN)

        nrow += 1
        ds.Add(xLabel(dp, "Move Fraction"),  (nrow, 0), (1, 2), LCEN, 5)
        ds.Add(self.MotorCtrl(dp, 'FRAC'),  (nrow, 2), (1, 1), CEN)

        set_sizer(dp, ds) # ,fit=True)

        sizer.Add(dp, 0)

        sizer.Add((3, 3), 0)
        sizer.Add(wx.StaticLine(self, size=(100, 2)),  0, wx.EXPAND)
        sizer.Add((3, 3), 0)
        sizer.Add(xTitle(self, 'Resolution, Readback, and Retries'), 0, LCEN, 5)

        ds = wx.GridBagSizer(4, 4)
        dp = wx.Panel(self)
        nrow = 0

        ds.Add(xLabel(dp, "Motor Res"),     (nrow, 0), (1, 1), LCEN, 5)
        ds.Add(self.MotorCtrl(dp, 'MRES'),  (nrow, 1), (1, 1), CEN)
        ds.Add(xLabel(dp, "Encoder Res"),   (nrow, 2), (1, 1), LCEN, 5)
        ds.Add(self.MotorCtrl(dp, 'ERES'),  (nrow, 3), (1, 1), CEN)

        nrow += 1
        ds.Add(xLabel(dp, "Steps / Rev"),    (nrow, 0), (1, 1), LCEN, 5)
        ds.Add(self.MotorCtrl(dp, 'SREV'),  (nrow, 1), (1, 1), CEN)
        ds.Add(xLabel(dp, "Units / Rev"),    (nrow, 2), (1, 1), LCEN, 5)
        ds.Add(self.MotorCtrl(dp, 'UREV'),  (nrow, 3), (1, 1), CEN)


        nrow += 1
        ds.Add(xLabel(dp, "Readback Res"),        (nrow, 0), (1, 1), LCEN, 5)
        ds.Add(self.MotorCtrl(dp, 'RRES'),        (nrow, 1), (1, 1), CEN)
        ds.Add(xLabel(dp, "Readback Delay (s)"),  (nrow, 2), (1, 1), LCEN, 5)
        ds.Add(self.MotorCtrl(dp, 'DLY'),         (nrow, 3), (1, 1), CEN)

        nrow += 1
        ds.Add(xLabel(dp, "Retry Deadband"),      (nrow, 0), (1, 1), LCEN, 5)
        ds.Add(self.MotorCtrl(dp, 'RDBD'),        (nrow, 1), (1, 1), CEN)
        ds.Add(xLabel(dp, "Max Retries"),         (nrow, 2), (1, 1), LCEN, 5)
        ds.Add(self.MotorCtrl(dp, 'RTRY'),        (nrow, 3), (1, 1), CEN)

        nrow += 1
        ds.Add(xLabel(dp, "Use Encoder"),      (nrow, 0), (1, 1), LCEN, 5)
        ds.Add(PVEnumChoice(dp, pv=self.motor.PV('UEIP'),
                            size=(110, -1)),  (nrow, 1), (1, 1), CEN)
        ds.Add(xLabel(dp, "Use Readback"),      (nrow, 2), (1, 1), LCEN, 5)
        ds.Add(PVEnumChoice(dp, pv=self.motor.PV('URIP'),
                            size=(110, -1)),  (nrow, 3), (1, 1), CEN)

        nrow += 1
        ds.Add(xLabel(dp, "Use NTM"),      (nrow, 0), (1, 1), LCEN, 5)
        ds.Add(PVEnumChoice(dp, pv=self.motor.PV('NTM'),
                            size=(110, -1)),  (nrow, 1), (1, 1), CEN)
        ds.Add(xLabel(dp, "NTM Factor"),      (nrow, 2), (1, 1), LCEN, 5)
        ds.Add(self.MotorCtrl(dp, 'NTMF'),    (nrow, 3), (1, 1), CEN)


        set_sizer(dp, ds)
        sizer.Add(dp, 0)
        sizer.Add(wx.StaticLine(self, size=(100, 2)),  0, wx.EXPAND)


        for attr in self.__motor_fields:
            self.motor.PV(attr).add_callback(self.OnMotorEvent,
                                             wid=self.GetId(), field=attr)

        self.info.SetLabel('')
        for f in ('HLS', 'LLS', 'LVIO', 'SET'):
            if self.motor.get(f):
                wx.CallAfter(self.OnMotorEvent,
                             pvname=self.motor.PV(f).pvname, field=f)

        set_sizer(self, sizer, fit=True)
        self.SetupScrolling()
        self.Thaw()

    @DelayedEpicsCallback
    def OnMotorEvent(self, pvname=None, field=None, **kws):
        "Motor event handler"
        if pvname is None:
            return None

        field_val = self.motor.get(field)
        if field in ('LVIO', 'HLS', 'LLS'):
            s = ''
            if field_val != 0:
                s = 'Limit!'
            self.info.SetLabel(s)

        elif field == 'SET':
            color = 'Yellow'
            if field_val == 0:
                color = 'White'
            for d in self.drives:
                d.SetBackgroundColour(color)
                d.Refresh()

    def MotorCtrl(self, panel, attr, size=(80, -1)):
        "PVFloatCtrl for a Motor attribute"
        return PVFloatCtrl(panel, size=size,
                           precision= self.motor.PREC,
                           pv=self.motor.PV(attr),
                           style = wx.TE_RIGHT)

    def MotorText(self, panel, attr, size=(80, -1)):
        "PVText for a Motor attribute"
        pv = self.motor.PV(attr)
        return PVText(panel,  pv=pv, as_string=True,
                      size=size, style=wx.CENTER)

    def MotorTextCtrl(self, panel, attr, size=(80, -1)):
        "PVTextCtrl for a Motor attribute"
        pv = self.motor.PV(attr)
        return PVTextCtrl(panel, pv=pv, size=size,
                          style=wx.ALIGN_LEFT|wx.TE_PROCESS_ENTER)

    @DelayedEpicsCallback
    def OnLimitChange(self, attr=None, value=None, **kws):
        "limit-change callback"
        funcs = {'low_limit':       self.drives[0].SetMin,
                 'high_limit':      self.drives[0].SetMax,
                 'dial_low_limit':  self.drives[1].SetMin,
                 'dial_high_limit': self.drives[1].SetMax}
        if attr in funcs:
            funcs[attr](value)

    @EpicsFunction
    def OnLeftButton(self, event=None):
        "left button event handler"
        if self.motor is not None:
            self.motor.tweak(direction='reverse')
        event.Skip()

    @EpicsFunction
    def OnRightButton(self, event=None):
        "right button event handler"
        if self.motor is not None:
            self.motor.tweak(direction='forward')
        event.Skip()
