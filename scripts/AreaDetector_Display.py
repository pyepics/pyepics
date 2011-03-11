#!/usr/bin/env python

import os
import sys

import time
from debugtime import debugtime
os.environ['EPICS_CA_MAX_ARRAY_BYTES'] = '16777216'

import epics

from epics.wx import DelayedEpicsCallback, EpicsFunction, EpicsTimer

import numpy as np
import Image
import wx

class ImageView(wx.Window):
    def __init__(self, parent, id=-1, pos=wx.DefaultPosition,
                 size=wx.DefaultSize, **kw):
        wx.Window.__init__(self, parent, id, pos, size, **kw)
        
        self.image = None
        self.SetBackgroundColour('WHITE')

        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_SIZE, self.OnSize)

    def SetValue(self, image):
        self.image = image
        self.Refresh()
    
    def OnSize(self, event):
        self.DrawImage(size=event.GetSize())
        event.Skip()
        self.Refresh()

    def OnPaint(self, event):
        self.DrawImage()

    def DrawImage(self, dc=None, size=None):
        if not hasattr(self,'image') or self.image is None:
            return
        if size is None:
            size = self.GetSize()
        wwidth,wheight = size
        image = self.image
        bmp = None
        if image.IsOk():
            iwidth = image.GetWidth()   
            iheight = image.GetHeight()
        else:
            bmp = wx.ArtProvider.GetBitmap(wx.ART_MISSING_IMAGE,
                                           wx.ART_MESSAGE_BOX, (64,64))
            iwidth  = bmp.GetWidth()
            iheight = bmp.GetHeight()

        xfactor = float(wwidth) / iwidth
        yfactor = float(wheight) / iheight

        scale = 1.0
        if xfactor < 1.0 and xfactor < yfactor:
            scale = xfactor
        elif yfactor < 1.0 and yfactor < xfactor:
            scale = yfactor

        owidth = int(scale*iwidth)
        oheight = int(scale*iheight)
        diffx = (wwidth - owidth)/2   # center calc
        diffy = (wheight - oheight)/2   # center calc

        if bmp is None:
            if owidth!=iwidth or oheight!=iheight:
                image = image.Scale(owidth,oheight)
            bmp = image.ConvertToBitmap()

        if dc is None:
            try:
                dc = wx.PaintDC(self)
            except:
                pass
        if dc is not None:
            dc.DrawBitmap(bmp, diffx, diffy, useMask=True)

class AD_Display(wx.Frame):
    """AreaDetector Display """
    attrs = ('ArrayData', 'UniqueId_RBV',
             'ArraySize0_RBV', 'ArraySize1_RBV', 'ArraySize2_RBV',
             'ColorMode_RBV')
    
    def __init__(self, prefix=None, scale=1.0, approx_height=600):

        self.ad_device = None
        self.prefix = prefix
        self.scale  = scale
        self.arrsize  = [0,0,0]
        self.imbuff = None
        self.colormode = 0
        wx.Frame.__init__(self, None, -1)
        self.SetTitle("Epics Area Detector Display")

        self.img_w = 0
        self.img_h = 0

        sizer = wx.BoxSizer(wx.VERTICAL)
        self.mainsizer = sizer
       
        self.wximage = wx.EmptyImage(approx_height, approx_height)
        
        txtsizer = wx.BoxSizer(wx.HORIZONTAL)
        txtsizer.Add(wx.StaticText(self,wx.ID_ANY,'PV Name Prefix'),1,wx.LEFT)
        
        self.wid_pvname = wx.TextCtrl(self,wx.ID_ANY, self.prefix,
                                      size=(180,-1),
                                      style=wx.ALIGN_LEFT|wx.ST_NO_AUTORESIZE|wx.TE_PROCESS_ENTER)
        self.wid_pvname.Bind(wx.EVT_TEXT_ENTER, self.onPvName)
        txtsizer.Add(self.wid_pvname,1,wx.LEFT)
         
        sizer.Add(txtsizer, 0, wx.TOP)

        self.image = ImageView(self, size=(100,100))

        sizer.Add(self.image, 1, wx.LEFT|wx.GROW|wx.ALL|wx.ALIGN_CENTER, 0)
        
        self.SetAutoLayout(True)
        self.SetSizer(sizer)
        wx.CallAfter( self.connect_pvs )
        self.Fit()

    def onPvName(self,evt=None, **kw):
        if evt is None:
            return
        s = evt.GetString()
        s = str(s).strip()

        if not s.endswith(':'):
            s = "%s:" % s
        self.prefix = s
        self.connect_pvs()


    @EpicsFunction
    def connect_pvs(self):
        print 'Connecting... ', self.prefix, self.attrs
        self.ad_dev = epics.Device(self.prefix, delim='',
                                   attrs=self.attrs)

        print self.ad_dev

        print self.attrs
        if not self.ad_dev.PV('UniqueId_RBV').connected:
            epics.ca.poll()
            if not self.ad_dev.PV('UniqueId_RBV').connected:
                return

        self.SetTitle("PV Image Display: %s" % self.prefix)

        self.ad_dev.add_callback('UniqueId_RBV',   self.onNewImage)
        self.ad_dev.add_callback('ArraySize0_RBV', self.onProperty, dim=0)
        self.ad_dev.add_callback('ArraySize1_RBV', self.onProperty, dim=1)
        self.ad_dev.add_callback('ArraySize2_RBV', self.onProperty, dim=2)
        self.ad_dev.add_callback('ColorMode_RBV',  self.onProperty, dim='color')

        self.GetImageSize()
        self.timer = EpicsTimer(self, period=100)
        epics.poll()
        print 'Connected... '
        self.RefreshImage()
        
    @EpicsFunction
    def GetImageSize(self):
        self.arrsize = [1,1,1]
        self.arrsize[0] = self.ad_dev.ArraySize0_RBV
        self.arrsize[1] = self.ad_dev.ArraySize1_RBV
        self.arrsize[2] = self.ad_dev.ArraySize2_RBV
        self.colormode = self.ad_dev.ColorMode_RBV

        self.img_w = self.arrsize[1]
        self.img_h = self.arrsize[0]
        if self.colormode == 2:
            self.img_w = self.arrsize[2]
            self.img_h = self.arrsize[1]
        
    @DelayedEpicsCallback
    def onProperty(self, pvname=None, value=None, dim=None, **kw):
        if dim=='color':
            self.colormode=value
        else:
            self.arrsize[dim] = value

    @DelayedEpicsCallback
    def onNewImage(self, pvname=None, value=None, **kw):
        self.RefreshImage()
        
    @EpicsFunction
    def RefreshImage(self):
        d = debugtime()
        if self.ad_dev.ArrayData is None:
            return
        im_mode = 'L'
        im_size = (self.arrsize[0], self.arrsize[1])
        
        if self.colormode == 2:
            im_mode = 'RGB'
            im_size = [self.arrsize[1], self.arrsize[2]]
        d.add('know image size/type')
        rawdata = self.ad_dev.ArrayData
        d.add('have rawdata')
        
        imbuff =  Image.frombuffer(im_mode, im_size, rawdata,
                                   'raw', im_mode, 0, 1)
        d.add('data to imbuff')
        self.GetImageSize()
        display_size = (int(self.img_h*self.scale), int(self.img_w*self.scale))

        if self.img_h < 1 or self.img_w < 1:
            return

        imbuff = imbuff.resize(display_size)

        d.add('imbuff resized')
        if self.wximage.GetSize() != imbuff.size:
             self.wximage = wx.EmptyImage(display_size[0], display_size[1])

        self.wximage.SetData(imbuff.convert('RGB').tostring())
        self.image.SetValue(self.wximage)

        d.add('wx bitmap set')
        d.show()
        
if __name__ == '__main__':
    import sys
    prefix = '13IDCPS1:image1:'
    if len(sys.argv) > 1:
        prefix = sys.argv[1]

    app = wx.PySimpleApp()
    frame = AD_Display(prefix=prefix)
    
    frame.Show()
    app.MainLoop()

