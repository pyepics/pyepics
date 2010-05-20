#!/usr/bin/python
#
# test the MotorPanel

import wx
import sys
import time
import epics

from epics.wx  import MotorPanel, closure, pvText, pvFloatCtrl

ID_ABOUT = wx.NewId()
ID_EXIT  = wx.NewId()
ID_FREAD = wx.NewId()
ID_FSAVE = wx.NewId()
ID_CONF  = wx.NewId()

def my_callback(value=None,**kw):
    print ">> my callback val = ", value
    for k,v in kw.items():
        print "my callback ", k, v

class MyFrame(wx.Frame):
    def __init__(self, parent, ID, *args,**kwds):

        ## kwds["style"] = wx.CAPTION|wx.MINIMIZE_BOX|wx.MAXIMIZE_BOX| wx.SYSTEM_MENU|wx.RESIZE_BORDER|wx.TAB_TRAVERSAL
        wx.Frame.__init__(self, parent, ID, '',
                         wx.DefaultPosition, wx.Size(-1,-1),**kwds)
        self.SetTitle(" Epics Motor example")

        wx.EVT_CLOSE(self, self.onClose)        

        self.CreateStatusBar(2,wx.CAPTION|wx.THICK_FRAME)
        self.SetStatusWidths([-5,-1])
        self.SetStatusText("This is the statusbar")
        self.SetFont(wx.Font(12,wx.SWISS,wx.NORMAL,wx.BOLD,False))
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
        menuBar.Append(cmenu, "&Configure");
        self.SetMenuBar(menuBar)

        wx.EVT_MENU(self, ID_ABOUT, self.onAbout)
        wx.EVT_MENU(self, ID_EXIT,  self.onClose)

        self.mainframe  = wx.BoxSizer(wx.VERTICAL)
        
        self.pane0 = wx.Panel(self, -1, size=(-1, -1))
        
        self.motors = {}
        motor_choices = []
        for i in range(10,15):
            m = "13IDC:m%i" % i
            j =  epics.caget("%s.DESC" % m)
            self.motors[j] =  m
            motor_choices.append(j)


        l1 = wx.StaticText(self.pane0, -1, "Motor 1:", size=(-1, -1),
                                     style=wx.RESIZE_BORDER)

        c1 = wx.Choice(self.pane0, -1, choices=motor_choices, size=(180, -1))
        c1.Bind(wx.EVT_CHOICE, closure(self.onMotorChoice,motor='1'))

        l1.SetFont(wx.Font(14,wx.SWISS,wx.NORMAL,wx.NORMAL,False))

        self.gs0 = wx.FlexGridSizer(1, 7, 5, 10)
        self.gs0.Add(l1, 0, wx.ALIGN_LEFT)
        self.gs0.Add(c1, 0, wx.ALIGN_LEFT)
        # self.gs0.Add(pvr, 0, wx.ALIGN_LEFT)
        # self.gs0.Add(pvc, 0, wx.ALIGN_LEFT)

        self.pane0.SetAutoLayout(1)
        self.pane0.SetSizer(self.gs0)
        self.gs0.Fit(self.pane0)

        self.mainframe.Add(self.pane0, 1, wx.EXPAND)

        self.motor1 = MotorPanel(self,
                                 messenger=self.write_message)

        self.motor2 = MotorPanel(self,
                                 messenger=self.write_message)

        
        self.mainframe.Add(self.motor1, 1,wx.ALIGN_LEFT|wx.EXPAND)

        self.mainframe.Add(self.motor2, 1,wx.ALIGN_LEFT|wx.EXPAND)

        self.SetSizer(self.mainframe)
        self.mainframe.Fit(self)
        self.Refresh()

        wx.CallAfter(self.motor1.SelectMotor,
                     self.motors[motor_choices[0]])

        wx.CallAfter(self.motor2.SelectMotor,
                     self.motors[motor_choices[3]])

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


    def onClose(self,event):
        self.Destroy()

if __name__ == '__main__':
    app = wx.App(redirect=False)
    f = MyFrame(None,-1)
    f.Show(True)
    # print ':: mainloop  ', app, f
    app.MainLoop()


