#!/usr/bin/env python

import os
import sys

import time
from debugtime import debugtime

os.environ['EPICS_CA_MAX_ARRAY_BYTES'] = '16777216'

import epics

from epics.wx import DelayedEpicsCallback, EpicsFunction

import numpy as np
import Image
import wx


class PlotFigure(wx.Frame, epics.Device):
    attrs = ('ArrayData', 'UniqueId_RBV',
             'ArraySize0_RBV', 'ArraySize1_RBV', 'ArraySize2_RBV',
             'ColorMode_RBV')
    

    def __init__(self, prefix=None, nx=1024, ny=1360):

        self.prefix = prefix
        self.size = [ny, nx, 0]
        self.ny = ny
        self.nx = nx
        self.colormode = 0
        wx.Frame.__init__(self, None, -1)
        self.SetTitle("PV Image Display")

        sizer = wx.BoxSizer(wx.VERTICAL)

        self.wximage = wx.EmptyImage(self.ny, self.nx)
        self.bitmap = wx.StaticBitmap(self, -1, wx.BitmapFromImage(self.wximage),
                                      (self.ny, self.nx))

        txtsizer = wx.BoxSizer(wx.HORIZONTAL)
        txtsizer.Add(wx.StaticText(self,wx.ID_ANY,'PV Name Prefix'),1,wx.LEFT)
        
        self.wid_pvname = wx.TextCtrl(self,wx.ID_ANY, self.prefix,
                                      size=(180,-1),
                                      style=wx.ALIGN_LEFT|wx.ST_NO_AUTORESIZE|wx.TE_PROCESS_ENTER)
        self.wid_pvname.Bind(wx.EVT_TEXT_ENTER, self.onPvName)
        txtsizer.Add(self.wid_pvname,1,wx.LEFT)
         
        sizer.Add(txtsizer, 0, wx.TOP)

        sizer.Add(self.bitmap, 0, wx.LEFT|wx.TOP|wx.EXPAND)

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

        if s.endswith(':'):
            s = s[:-1]
        self.prefix = s
        self.connect_pvs()


    @EpicsFunction
    def connect_pvs(self):
        print 'Connect PVs ', self.prefix
        epics.Device.__init__(self, self.prefix,
                              attrs=self.attrs)
        self.SetTitle("PV Image Display: %s" % self.prefix)

        self.add_callback('UniqueId_RBV',   self.onNewImage)
        self.add_callback('ArraySize0_RBV', self.onProperty, dim=0)
        self.add_callback('ArraySize1_RBV', self.onProperty, dim=1)
        self.add_callback('ArraySize2_RBV', self.onProperty, dim=2)
        self.add_callback('ColorMode_RBV',  self.onProperty, dim='color')

        self.size = [1,1,1]
        self.size[0] = self.get('ArraySize0_RBV')
        self.size[1] = self.get('ArraySize1_RBV')
        self.size[2] = self.get('ArraySize2_RBV')
        self.colormode = self.get('ColorMode_RBV')

        self.nx = self.size[1]
        self.ny = self.size[0]
        if self.colormode == 2:
            self.nx = self.size[2]
            self.ny = self.size[1]
            
        epics.poll()
        
    @DelayedEpicsCallback
    def onProperty(self, pvname=None, value=None, dim=None, **kw):
        print 'on Property : ' , dim, value
        if dim=='color':
            self.colormode=value
        else:
            self.size[dim] = value            

    @DelayedEpicsCallback
    def onNewImage(self, pvname=None, value=None, **kw):
        self.RefreshImage()
        
    @EpicsFunction
    def RefreshImage(self):
        d = debugtime()
        if self.get('ArrayData') is None:
            return
        print 'Refresh image'
        im_mode = 'L'
        im_size = (self.size[0], self.size[1])
        if self.colormode == 2:
            im_mode = 'RGB'
            im_size = [self.size[1], self.size[2]]
        d.add('know image size/type')
        rawdata = self.get('ArrayData') # 
        d.add('have rawdata')

        imbuff =  Image.frombuffer(im_mode, im_size, rawdata, 'raw', im_mode, 0, 1)
        d.add('data to imbuff')
        
        if self.wximage.GetSize() != imbuff.size:
            print 'reset image??'
            self.wximage = wx.EmptyImage(imbuff.size[0], imbuff.size[1])
        d.add('have wximage')
        
        # self.wximage.SetData(imbuff.transpose(Image.FLIP_TOP_BOTTOM).convert('RGB').tostring())
        self.wximage.SetData(imbuff.convert('RGB').tostring())            
        d.add('wximage.SetData done')
            
        self.bitmap.SetBitmap(wx.BitmapFromImage(self.wximage))
        d.add('wx bitmap set')
        d.show()
        # self.bitmap.SetBitmap(iwx.BitmapFromImage(self.wximage))            

if __name__ == '__main__':
    import sys
    prefix = '13IDCPS1:image1:'
    if len(sys.argv) > 1:
        prefix = sys.argv[1]

    print sys.argv, prefix
    app = wx.PySimpleApp()
    frame = PlotFigure(prefix=prefix)
    
    frame.Show()
    app.MainLoop()

