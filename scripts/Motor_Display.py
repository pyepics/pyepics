#!/usr/bin/python
#
# test the MotorPanel

import wx
import sys
import time
import epics

from epics.wx import finalize_epics, MotorPanel

ID_ABOUT = wx.NewId()
ID_EXIT  = wx.NewId()
ID_FREAD = wx.NewId()
ID_FSAVE = wx.NewId()
ID_CONF  = wx.NewId()

class SimpleMotorFrame(wx.Frame):
    def __init__(self, parent=None, motors=None, *args,**kwds):

        wx.Frame.__init__(self, parent, wx.ID_ANY, '',
                         wx.DefaultPosition, wx.Size(-1,-1),**kwds)
        self.SetTitle(" Epics Motors Page")

        wx.EVT_CLOSE(self, self.onClose)        
        self.SetFont(wx.Font(12,wx.SWISS,wx.NORMAL,wx.BOLD,False))
        
        self.createSbar()
        self.createMenus()
        self.buildFrame(motors=motors)

    def buildFrame(self, motors=None):
        self.mainsizer = wx.BoxSizer(wx.VERTICAL)
        
        if motors is not None:
            self.motors= [MotorPanel(self, motor=m) for m in motors]
           
            for mpan in self.motors:
                self.mainsizer.Add(mpan, 1, wx.EXPAND)
                self.mainsizer.Add(wx.StaticLine(self, size=(100,3)),
                                   0, wx.EXPAND)
                 
        self.SetSizer(self.mainsizer)
        self.mainsizer.Fit(self)
        self.Refresh()

    def createMenus(self):
        fmenu = wx.Menu()
        fmenu.Append(ID_ABOUT, "&About",
                    "More information about this program")
        fmenu.Append(ID_FREAD, "&Read", "Read Configuration File")
        fmenu.Append(ID_FSAVE, "&Save", "Save Configuration File")        
        fmenu.AppendSeparator()
        fmenu.Append(ID_EXIT, "E&xit", "Terminate the program")

        cmenu = wx.Menu()
        cmenu.Append(ID_CONF, "&Configure",
                     "Setup Motors and options")

        menuBar = wx.MenuBar()
        menuBar.Append(fmenu, "&File");

        # menuBar.Append(cmenu, "&Configure");
        self.SetMenuBar(menuBar)

        wx.EVT_MENU(self, ID_ABOUT, self.onAbout)
        wx.EVT_MENU(self, ID_EXIT,  self.onClose)

    def createSbar(self):
        "create status bar"
        self.statusbar = self.CreateStatusBar(2, wx.CAPTION|wx.THICK_FRAME)
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
    motors =('13XRM:m2.VAL',)

    if len(sys.argv)>1:
        motors = sys.argv[1:]
    
    app = wx.App(redirect=False)
    SimpleMotorFrame(motors=motors).Show()
    
    app.MainLoop()


