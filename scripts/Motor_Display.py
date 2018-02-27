#!/usr/bin/python
#
# test the MotorPanel

import wx
import sys
import time
import epics
from mpanel import MotorPanel
from epics import Motor
from epics.wx import finalize_epics
from epics.wx.utils import add_menu

class SimpleMotorFrame(wx.Frame):
    def __init__(self, parent=None, motors=None, *args,**kwds):

        wx.Frame.__init__(self, parent, wx.ID_ANY, '',
                         wx.DefaultPosition, wx.Size(-1,-1),**kwds)
        self.SetTitle(" Epics Motors Page")

        self.Bind(wx.EVT_CLOSE, self.onClose)
        self.SetFont(wx.Font(12,wx.SWISS,wx.NORMAL,wx.BOLD,False))
        self.xtimer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.onTimer, self.xtimer)
        self.createSbar()
        self.createMenus()
        motorlist = None
        if motors is not None:
            motorlist = [Motor(mname) for mname in motors]
        self.buildFrame(motors=motorlist)
        self.xtimer.Start(250)

    def onTimer(self, evt=None):
        pass # print(" tick ", time.ctime())

    def buildFrame(self, motors=None):
        self.mainsizer = wx.BoxSizer(wx.VERTICAL)
        if motors is not None:
            self.motors = [MotorPanel(self, motor=m) for m in motors]

        for mpan in self.motors:
            self.mainsizer.Add(mpan, 1, wx.EXPAND)
            self.mainsizer.Add(wx.StaticLine(self, size=(100,3)),
                               0, wx.EXPAND)

        self.SetSizer(self.mainsizer)
        self.mainsizer.Fit(self)
        self.Refresh()

    def createMenus(self):
        mbar = wx.MenuBar()
        fmenu = wx.Menu()
        add_menu(self, fmenu, "E&xit", "Terminate the program",
                 action=self.onClose)
        mbar.Append(fmenu, "&File")
        self.SetMenuBar(mbar)

    def createSbar(self):
        "create status bar"
        self.statusbar = self.CreateStatusBar(2, wx.CAPTION)
        self.statusbar.SetStatusWidths([-4,-1])
        for index, name  in enumerate(("Messages", "Status")):
            self.statusbar.SetStatusText('', index)

    def write_message(self,text,status='normal'):
        self.SetStatusText(text)

    def onAbout(self, event):
        dlg = wx.MessageDialog(self, "WX Motor is was written by \n"
                               "Matt Newville <newville @ cars.uchicago.edu>\n"
                               "About Me", wx.OK | wx.ICON_INFORMATION)
        dlg.ShowModal()
        dlg.Destroy()

    def onMotorChoice(self,event,motor=None):
        self.motor1.SelectMotor(self.motors[event.GetString()])

    def onClose(self, event):
        finalize_epics()
        self.Destroy()

if __name__ == '__main__':
    motors =('13XRM:m1.VAL',
             '13XRM:m2.VAL',
             '13XRM:m3.VAL',
             '13XRM:m4.VAL',
             '13XRM:m5.VAL',
             '13XRM:m6.VAL')

    if len(sys.argv)>1:
        motors = sys.argv[1:]

    app = wx.App(redirect=False)
    SimpleMotorFrame(motors=motors).Show()
    print("App  ", time.ctime())

    app.MainLoop()
