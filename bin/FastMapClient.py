#!/usr/bin/python
import sys
sys.path.insert(0,'lib')
import wx
from clientGUI import FastMapGUI

app  = wx.PySimpleApp(redirect=False,filename='fastmap.log')
frame= FastMapGUI()
app.SetTopWindow(frame)
frame.Show()        
app.MainLoop()
