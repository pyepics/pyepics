#!/usr/bin/env python

import os
import sys

import time

os.environ['EPICS_CA_MAX_ARRAY_BYTES'] = '16777216'

import epics
from epics.wx import DelayedEpicsCallback, EpicsFunction

import numpy as np
import Image
import wx


class PlotFigure(wx.Frame):
    def __init__(self, prefix=None):

        if prefix is None:
            prefix = '13IDCPS1:image1'
        self.prefix = prefix
        print self.prefix
        self.nx = 1024
        self.ny = 1360
        wx.Frame.__init__(self, None, -1,
                          title="A PV Image Display: %s" % self.prefix)

        self.img_pv  = None
        self.frameno = None
        b = Image.open('AreaDetector_Display1.png')
        self.wximage = wx.EmptyImage(b.size[0], b.size[1])
        print b.size
        self.wximage.SetData(b.convert('RGB').tostring())
        self.bitmap = wx.StaticBitmap(self, -1, wx.BitmapFromImage(self.wximage), (400, 500))
        print self.bitmap
        self.tstamp = 0
        #         txtsizer = wx.BoxSizer(wx.HORIZONTAL)
        #         txtsizer.Add(wx.StaticText(self,wx.ID_ANY,'PV Name Prefix'),1,wx.LEFT)
        # 
        #         self.wid_pvname = wx.TextCtrl(self,wx.ID_ANY, self.prefix,
        #                                       size=(180,-1),
        #                                       style=wx.ALIGN_LEFT|wx.ST_NO_AUTORESIZE|wx.TE_PROCESS_ENTER)
        #         self.wid_pvname.Bind(wx.EVT_TEXT_ENTER, self.onPvName)
        #         txtsizer.Add(self.wid_pvname,1,wx.LEFT)
        # 
        #         sizer.Add(txtsizer, 0, wx.TOP)
        # ;
        sizer = wx.BoxSizer(wx.VERTICAL)
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

        
    @DelayedEpicsCallback
    def onNewImage(self, pvname=None, value=None, **kw):
        self.RefreshImage()

    @EpicsFunction
    def RefreshImage(self):
        t0 = time.time()
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
            t1 = time.time() - t0
            rawdata = self.img_pv.get(as_numpy=False, as_string=False)
            t2 = time.time() -t0

            print  '======== ', self.colormode, im_mode, im_size, len(rawdata), time.time()-self.tstamp
            self.tstamp= time.time()
            imbuff =  Image.frombuffer(im_mode, im_size, rawdata, 'raw', im_mode, 0, 1)
            t3 = time.time() -t0

            #             npbuff = np.array(imbuff)
            # 
            #             npbuff = 1.0 * npbuff / npbuff.max()
            # self.im.set_array(npbuff)
            if self.wximage.GetSize() != imbuff.size:
                self.wximage = wx.EmptyImage(imbuff.size[0], imbuff.size[1])

            # self.wximage.SetData(imbuff.transpose(Image.FLIP_TOP_BOTTOM).convert('RGB').tostring())
            self.wximage.SetData(imbuff.convert('RGB').tostring())            
            self.bitmap.SetBitmap(wx.BitmapFromImage(self.wximage))
            t4 = time.time() - t0
            print t1, t2, t3, t4
            # self.bitmap.SetBitmap(iwx.BitmapFromImage(self.wximage))            

if __name__ == '__main__':
    import sys
    prefix = '13PS1:image1:'
    if len(sys.argv) > 1:
        prefix = sys.argv[1]

    print sys.argv, prefix
    app = wx.PySimpleApp()
    frame = PlotFigure(prefix=prefix)
    
    frame.Show()
    app.MainLoop()

