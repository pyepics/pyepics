#!/usr/bin/env python

import os
import sys

import time

os.environ['EPICS_CA_MAX_ARRAY_BYTES'] = '90000000'

import epics
from epics.wx import DelayedEpicsCallback, EpicsFunction

import matplotlib
matplotlib.use('WXAgg')

import numpy as np
import Image
import wx

import matplotlib.cm as cm
from matplotlib.figure import Figure
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg


class PlotFigure(wx.Frame):
    def __init__(self, prefix=None):

        if prefix is None:
            prefix = '13IDCPS1:image1'
        self.prefix = prefix
        print self.prefix
        self.nx = 1024
        self.ny = 1360
        wx.Frame.__init__(self, None, -1,
                          title="PV Image Display: %s" % self.prefix)

        self.img_pv  = None
        self.frameno = None
        self.fig = Figure((4,6), 100)
        self.axes = self.fig.add_axes([0.05, 0.05, 0.9, 0.9])
        self.axes.set_axis_off()
        self.canvas = FigureCanvasWxAgg(self, wx.ID_ANY, self.fig)        


        txtsizer = wx.BoxSizer(wx.HORIZONTAL)
        txtsizer.Add(wx.StaticText(self,wx.ID_ANY,'PV Name Prefix'),1,wx.LEFT)

        self.wid_pvname = wx.TextCtrl(self,wx.ID_ANY, self.prefix,
                                      size=(180,-1),
                                      style=wx.ALIGN_LEFT|wx.ST_NO_AUTORESIZE|wx.TE_PROCESS_ENTER)
        self.wid_pvname.Bind(wx.EVT_TEXT_ENTER, self.onPvName)
        txtsizer.Add(self.wid_pvname,1,wx.LEFT)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(txtsizer, 0, wx.TOP)
        sizer.Add(self.canvas, 2, wx.LEFT|wx.TOP|wx.EXPAND, 0)

        self.SetAutoLayout(True)
        self.SetSizer(sizer)
        self.connect_pvs()
        self.Fit()
        self.RefreshImage()


    def onPvName(self,evt=None, **kw):
        if evt is None:
            return
        s = evt.GetString()
        s = str(s).strip()

        if s.endswith(':'): s = s[:-1]
        s = self.prefix
        self.SetTitle('Image display: %s' % s)
        self.connect_pvs()

    @EpicsFunction
    def connect_pvs(self):
        s = self.prefix
        print 'Connect PVs ', self.prefix
        self.img_pv   = epics.PV("%sArrayData" % s, auto_monitor=False)
        self.frame_pv = epics.PV("%sUniqueId_RBV" % s)
        
        self.frame_pv.add_callback(self.onNewImage)
        self.size0 = epics.PV("%sArraySize0_RBV" % s).get()
        self.size1 = epics.PV("%sArraySize1_RBV" % s).get()
        self.size2 = epics.PV("%sArraySize2_RBV" % s).get()
        self.colormode = epics.PV("%sColorMode_RBV" % s).get()
        self.datatype  = epics.PV("%sDataType_RBV" % s).get()                
        self.nx = self.size1
        self.ny = self.size0
        print self.size0, self.frame_pv,  self.colormode
        if self.colormode == 2:
            self.nx = self.size2
            self.ny = self.size1
            
        time.sleep(0.01)

    def init_plot_data(self):
        axes    = self.fig.add_axes([0.075,0.1,0.75,0.85])
        self.x = np.empty((self.nx, self.ny))
        self.x.flat = np.arange(self.nx )*2*np.pi/1060.0
        self.y = np.empty((self.nx, self.ny))
        self.y.flat = np.arange(self.ny)*2*np.pi/800.0

        z = abs(np.sin(self.x)/2. + np.cos(self.x)/2.)

        self.im = axes.imshow( z, cmap=cm.gray, interpolation='bilinear', origin='lower')
        axes.set_axis_off()
        
    @DelayedEpicsCallback
    def onNewImage(self, pvname=None, value=None, **kw):
        self.RefreshImage()

    @EpicsFunction
    def RefreshImage(self):
        if self.img_pv is not None:
            s = self.prefix
            self.size0 = epics.PV("%sArraySize0_RBV" % s).get()
            self.size1 = epics.PV("%sArraySize1_RBV" % s).get()
            self.size2 = epics.PV("%sArraySize2_RBV" % s).get()
            self.colormode = epics.PV("%sColorMode_RBV" % s).get()

            im_mode = 'L'
            im_size = (self.size0, self.size1)
            if self.colormode == 2:
                im_mode = 'RGB'
                im_size = (self.size1, self.size2)
            rawdata = self.img_pv.get(as_numpy=False, as_string=False)

            print  '======== ', self.colormode, im_mode, im_size, len(rawdata)
            imbuff =  Image.frombuffer(im_mode, im_size, rawdata)
            npbuff = np.array(imbuff)

            npbuff = 1.0 * npbuff / npbuff.max()
            self.im.set_array(npbuff)
            self.canvas.draw()

if __name__ == '__main__':
    import sys
    prefix = '13PS1:image1:'
    if len(sys.argv) > 1:
        prefix = sys.argv[1]

    print sys.argv, prefix
    app = wx.PySimpleApp()
    frame = PlotFigure(prefix=prefix)
    frame.init_plot_data()

    frame.Show()
    app.MainLoop()

