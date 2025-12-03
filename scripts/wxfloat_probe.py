#!/usr/bin/python
#
# simple PV Probe application for Float PVs

import wx
import sys
import epics
from epics.wx import PVText, PVFloatCtrl, PVFloatSpin

class ProbeFrame(wx.Frame):
    def __init__(self, parent=None, **kwds):

        wx.Frame.__init__(self, parent, wx.ID_ANY, '',
                         wx.DefaultPosition,  size=(400, 400), **kwds)
        self.SetTitle("Connect to Float PV:")

        self.SetFont(wx.Font(12,wx.SWISS,wx.NORMAL,wx.BOLD,False))

        sizer = wx.GridBagSizer(3, 3)
        panel = wx.Panel(self)

        self.pvname = wx.TextCtrl(panel, value='', size=(150, -1),
                                      style=wx.TE_PROCESS_ENTER)
        self.pvname.Bind(wx.EVT_CHAR, self.onPVName)

        self.pvtext = PVText(panel, None, size=(100, -1))
        self.pvfloat = PVFloatCtrl(panel, None, size=(100, -1))
        self.pvfspin = PVFloatSpin(panel, None, size=(100, -1))

        pvname_label = wx.StaticText(panel, label='PV Name:', size=(150, -1))
        pvval_label = wx.StaticText(panel, label='PVText:', size=(150, -1))
        pvfloat_label = wx.StaticText(panel, label='PVFloatControl:', size=(150, -1))
        pvfspin_label = wx.StaticText(panel, label='PVFloatSpin:', size=(150, -1))

        sizer.Add(pvname_label,  (0, 0), (1, 1), wx.ALIGN_LEFT, 1)
        sizer.Add(self.pvname,   (0, 1), (1, 1), wx.ALIGN_LEFT, 1)
        sizer.Add(pvval_label,   (1, 0), (1, 1), wx.ALIGN_LEFT, 1)
        sizer.Add(self.pvtext,   (1, 1), (1, 1), wx.ALIGN_LEFT, 1)
        sizer.Add(pvfloat_label,  (2, 0), (1, 1), wx.ALIGN_LEFT, 1)
        sizer.Add(self.pvfloat,   (2, 1), (1, 1), wx.ALIGN_LEFT, 1)
        sizer.Add(pvfspin_label,  (3, 0), (1, 1), wx.ALIGN_LEFT, 1)
        sizer.Add(self.pvfspin,   (3, 1), (1, 1), wx.ALIGN_LEFT, 1)

        panel.SetSizer(sizer)
        sizer.Fit(panel)

        s = wx.BoxSizer(wx.VERTICAL)
        s.Add(panel)
        s.Fit(self)

        self.SetSize((400, 150))
        self.Refresh()

    def onPVName(self, event=None):
        if event.GetKeyCode() == wx.WXK_RETURN:
            pvname = self.pvname.GetValue().strip()
            if len(pvname) > 1:
                self.pvtext.SetPV(pvname)
                self.pvfloat.SetPV(pvname)
                self.pvfspin.SetPV(pvname)
        event.Skip()

if __name__ == '__main__':
    app = wx.App(redirect=False)
    ProbeFrame().Show()
    app.MainLoop()
