
import os
import sys
import time
import wx
import Image
import numpy as np

from lib.imageframe import ImageFrame

os.environ['EPICS_CA_MAX_ARRAY_BYTES'] = '%i' % 2**24

import epics
from epics.wx import DelayedEpicsCallback, EpicsFunction

class PVImageFrame(ImageFrame):
    def __init__(self, prefix=None, parent=None, size=(500,500), **kw):
        self.title  = 'Image Display Frame" %s' % prefix
        self.size = size

        ImageFrame.__init__(self, parent=parent)

        self.prefix = prefix
        self.connect_pvs()
        self.RefreshImage()

    @EpicsFunction
    def connect_pvs(self):
        s = self.prefix
        print 'Connect PVs ', self.prefix
        self.img_pv     = epics.PV("%sArrayData" % s, auto_monitor=False)
        self.counter_pv = epics.PV("%sArrayCounter_RBV" % s)
        self.frame_pv   = epics.PV("%sUniqueId_RBV" % s)
        
        self.frame_pv.add_callback(self.onNewImage)
        self.size0 = epics.PV("%sArraySize0_RBV" % s).get()
        self.size1 = epics.PV("%sArraySize1_RBV" % s).get()
        self.size2 = epics.PV("%sArraySize2_RBV" % s).get()
        self.colormode = epics.PV("%sColorMode_RBV" % s).get()
        self.datatype  = epics.PV("%sDataType_RBV" % s).get()                
        self.nx = self.size1
        self.ny = self.size0
        print  ' Connect: ', self.size0, self.frame_pv,  self.colormode
        if self.colormode == 2:
            self.nx = self.size2
            self.ny = self.size1

    @DelayedEpicsCallback
    def onNewImage(self, pvname=None, value=None, **kw):
        print 'New Image! ', pvname, type(value)
        self.RefreshImage()

    @EpicsFunction
    def RefreshImage(self):
        if self.img_pv is not None:
            s = self.prefix
            tx = []
            tx.append( (time.time(), 'start'))
            self.size0 = epics.PV("%sArraySize0_RBV" % s).get()
            self.size1 = epics.PV("%sArraySize1_RBV" % s).get()
            self.size2 = epics.PV("%sArraySize2_RBV" % s).get()
            self.colormode = epics.PV("%sColorMode_RBV" % s).get()
            tx.append( (time.time(), 'got mode'))
            im_mode = 'L' 
            im_size = (self.size0, self.size1)
            if self.colormode == 2:
                im_mode = 'RGB'
                im_size = (self.size1, self.size2)
            tx.append( (time.time(), 'ready..'))
            rawdata = self.img_pv.get(as_numpy=False, as_string=False)
            tx.append( (time.time(), 'got raw'))
            imbuff =  Image.frombuffer(im_mode, im_size, rawdata)
            tx.append( (time.time(), 'as image'))
            tx.append( (time.time(), 'as numpy'))
            # npbuff = 1.0 * npbuff / npbuff.max()
            self.display(np.array(imbuff))
            tx.append( (time.time(), 'displayed'))
            for tf, msg in tx:
                print "%.4f %s" % (tf - tx[0][0], msg)

if __name__ == '__main__':
    import sys
    prefix = '13IDCPS1:image1:'
    if len(sys.argv) > 1:
        prefix = sys.argv[1]

    app = wx.PySimpleApp()
    frame =  PVImageFrame(prefix=prefix)
    frame.Show()
    app.MainLoop()

