#!/usr/bin/python
#
# simple PV Probe application

import wx
import sys
import epics
from epics.wx import EpicsFunction, DelayedEpicsCallback

class PVDisplay(wx.Frame):
    def __init__(self, pvname, parent=None, **kwds):
        wx.Frame.__init__(self, parent, wx.ID_ANY, '',
                         wx.DefaultPosition, wx.Size(-1,-1),**kwds)
        self.SetFont(wx.Font(11,wx.SWISS,wx.NORMAL,wx.BOLD,False))
        self.pvname = pvname

        self.SetTitle("%s" % pvname)
        
        self.sizer = wx.GridBagSizer(3, 2)
        panel = wx.Panel(self)
        name      = wx.StaticText(panel, label=pvname,        size=(120, -1))
        self.val  = wx.StaticText(panel, label='unconnected', size=(200, -1))
        self.info = wx.StaticText(panel, label='-- ' ,        size=(400,300))
        self.info.SetFont(wx.Font(9,wx.SWISS,wx.NORMAL,wx.BOLD,False))
        
        self.sizer.Add(wx.StaticText(panel, label='PV: ',    size=(60, -1)),
                       (0, 0), (1, 1), wx.EXPAND, 1)
        self.sizer.Add(wx.StaticText(panel, label='Value: ',  size=(60, -1)),
                       (1, 0), (1, 1), wx.EXPAND, 1)
        self.sizer.Add(wx.StaticText(panel, label='Info: ',   size=(60, -1)),
                       (2, 0), (1, 1), wx.EXPAND, 1)
        self.sizer.Add(name,      (0, 1), (1, 1), wx.EXPAND, 1)
        self.sizer.Add(self.val,  (1, 1), (1, 1), wx.ALIGN_RIGHT|wx.EXPAND, 1)
        self.sizer.Add(self.info, (2, 1), (2, 2), wx.ALIGN_LEFT|wx.EXPAND, 1)

        panel.SetSizer(self.sizer)

        self.needs_info = None
        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.onTimer, self.timer)

        self.s1 = wx.BoxSizer(wx.VERTICAL)
        self.s1.Add(panel, 1, wx.EXPAND, 2)
        self.s1.Fit(self)
        self.Refresh()
        self.connect_pv()
        
    @EpicsFunction
    def connect_pv(self):
        self.pv = epics.PV(self.pvname, connection_callback=self.onConnect,
                           callback=self.onPV_value)

    @EpicsFunction
    def onTimer(self, evt):
        if self.need_info and self.pv.connected:
            self.info.SetLabel(self.pv.info)
            self.timer.Stop()
            self.needs_info = False
        
    @DelayedEpicsCallback
    def onConnect(self, **kws):
        self.need_info = True
        self.timer.Start(25)
                
    @DelayedEpicsCallback
    def onPV_value(self, name=None, char_value=None, **kws):
        if len(char_value) > 90:
            char_value = char_value[:90]
        self.val.SetLabel('   %s' % char_value)
        self.need_info = True
        self.timer.Start(25)

        
class NameCtrl(wx.TextCtrl):
    def __init__(self, panel, value='', action=None, **kws):
        self.action = action
        wx.TextCtrl.__init__(self, panel, wx.ID_ANY, value='',
                             style=wx.TE_PROCESS_ENTER, **kws)
        self.Bind(wx.EVT_CHAR, self.onChar)

    def onChar(self, event):
        if event.GetKeyCode() == wx.WXK_RETURN and \
           self.action is not None:
            self.action(wx.TextCtrl.GetValue(self).strip())
        event.Skip()
        

class ProbeFrame(wx.Frame):
    def __init__(self, parent=None, **kwds):

        wx.Frame.__init__(self, parent, wx.ID_ANY, '',
                         wx.DefaultPosition, wx.Size(-1,-1),**kwds)
        self.SetTitle("Connect to Epics Records:")

        self.SetFont(wx.Font(11,wx.SWISS,wx.NORMAL,wx.BOLD,False))

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        panel = wx.Panel(self)
        label = wx.StaticText(panel, label='PV Name:')
        self.pvname = NameCtrl(panel, value='', size=(175,-1),
                               action=self.onName)

        sizer.Add(label,       0, wx.ALIGN_LEFT, 1)
        sizer.Add(self.pvname, 1, wx.EXPAND, 1)
        panel.SetSizer(sizer)
        sizer.Fit(panel)
        s = wx.BoxSizer(wx.VERTICAL)
        s.Add(panel)
        s.Fit(self)
        self.Refresh()

    def onName(self, value, wid=None, **kws):
        PVDisplay(value, parent=self).Show()

if __name__ == '__main__':
    app = wx.App(redirect=False)
    ProbeFrame().Show()
    app.MainLoop()
