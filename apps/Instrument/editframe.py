import wx
import sys
import time

import epics
from epics.wx import EpicsFunction

from epicscollect.gui import  empty_bitmap, add_button, add_menu, \
     Closure, NumericCombo, pack, popup, SimpleText, \
     FileSave, FileOpen, SelectWorkdir 

from utils import GUIColors, HideShow, YesNo, set_font_with_children

class pvNameCtrl(wx.TextCtrl):
    def __init__(self, parent,  value='', connecting_pvs=None, timer=None,  **kws):
        wx.TextCtrl.__init__(self, parent, wx.ID_ANY, value='', **kws)
        self.Bind(wx.EVT_CHAR, self.onChar)
        self.Bind(wx.EVT_KILL_FOCUS, self.onFocus)
        #self.Bind(wx.EVT_SET_FOCUS,  self.onFocus)

        if connecting_pvs is None:
            connecting_pvs = {}
        self.connecting_pvs = connecting_pvs
        self.timer = timer

    def onFocus(self, evt=None):
        print 'Lose fOCUS Event: ', 
        print 'Value = ', self.Value
        #if (key == wx.WXK_RETURN):
        #    self.connect_pv(entry)

        evt.Skip()

    def onChar(self, event):
        key   = event.GetKeyCode()
        entry = wx.TextCtrl.GetValue(self).strip()
        pos   = wx.TextCtrl.GetSelection(self)
        if (key == wx.WXK_RETURN):
            self.connect_pv(entry)
        event.Skip()
            
    @EpicsFunction
    def connect_pv(self, pvname):
        if pvname not in self.connecting_pvs:
            self.connecting_pvs[pvname] = epics.PV(pvname)
            if self.timer is not None:
                if not self.timer.IsRunning():
                    self.timer.Start(100)


class FocusEventFrame(wx.Window):
    """mixin for Frames that all EVT_KILL_FOCUS/EVT_SET_FOCUS events"""
    def Handle_FocusEvents(self, closeEventHandler=None):
        self._closeHandler = closeEventHandler
        self.Bind(wx.EVT_CLOSE, self.closeFrame)
        
    def closeFrame(self, event):
        win = wx.Window_FindFocus()
        if win is not None:
            win.Disconnect(-1, -1, wx.wxEVT_KILL_FOCUS)
        if self._closeHandler is not None:
            self._closeHandler(event)
        else:
            event.Skip()
            
class EditInstrumentFrame(wx.Frame, FocusEventFrame) :
    """ Edit / Add Instrument"""
    def __init__(self, parent=None, pos=(-1, -1), inst=None, db=None):
        
        title = 'Add New Instrument'
        if inst is not None:
            title = 'Edit Instrument  %s ' % inst.name

        wx.Frame.__init__(self, None, -1, title,  size=(550, 550),  pos=pos)
        self.Handle_FocusEvents()
        
        panel = wx.Panel(self, style=wx.GROW)
        self.colors = GUIColors()

        font = self.GetFont()
        if parent is not None:
            font = parent.GetFont()
            
        titlefont  = font
        titlefont.PointSize += 1
        titlefont.SetWeight(wx.BOLD)
        
        panel.SetBackgroundColour(self.colors.bg)

        self.parent = parent
        self.db = db
        self.inst = db.get_instrument(inst)
        self.connecting_pvs = {}

        STY  = wx.GROW|wx.ALL|wx.ALIGN_CENTER_VERTICAL
        LSTY = wx.ALIGN_LEFT|STY
        RSTY = wx.ALIGN_RIGHT|STY
        CSTY = wx.ALIGN_CENTER|STY
        CEN  = wx.ALIGN_CENTER|wx.GROW|wx.ALL
        LEFT = wx.ALIGN_LEFT|wx.GROW|wx.ALL
        self.etimer = wx.Timer(self)
        self.etimer_count = 0
        self.Bind(wx.EVT_TIMER, self.onTimer, self.etimer)

        sizer = wx.GridBagSizer(12, 5)
        sizer.SetHGap(8),
        sizer.SetVGap(8)
        # Name row
        label  = SimpleText(panel, 'Instrument Name: ',
                            minsize=(150, -1), style=LSTY)
        self.name =  wx.TextCtrl(panel, value='', size=(250, -1))

        btn_remove = add_button(panel, 'Remove', size=(85, -1),
                                action=self.onRemoveInst)
        sizer.Add(label,      (0, 0), (1, 1), LSTY, 2)
        sizer.Add(self.name,  (0, 1), (1, 3), LSTY, 2)
        sizer.Add(btn_remove, (0, 4), (1, 1), RSTY, 2)
        sizer.Add(wx.StaticLine(panel, size=(195, -1), style=wx.LI_HORIZONTAL),
                  (1, 0), (1, 5), CEN, 2)

        irow = 2
        self.delete_pvs = {}
        if inst is not None:
            txt =SimpleText(panel, 'Current PVs:', font=titlefont,
                            colour=self.colors.title, style=LSTY)
            
            sizer.Add(txt, (irow, 0), (1, 5), LEFT, 3)
            irow += 1
            self.name.SetValue(inst.name)
            i = 0
            for titleword in (' PV  ', 'Display Type', 'Remove?'):
                style = LSTY
                wid = 1
                if titleword.startswith('Rem'):
                    style = RSTY
                elif titleword.startswith('Disp'):
                    wid = 3
                    style = CSTY
                txt =SimpleText(panel, titleword,  minsize=(120, -1), 
                                colour=self.colors.title, style=LSTY)
                
                sizer.Add(txt, (irow, i), (1, wid), style, 2)
                i = i + wid

            for pv in inst.pvs:
                irow += 1
                label= SimpleText(panel, pv.name,  minsize=(175, -1),
                                  style=LSTY)
                pvtype = SimpleText(panel, pv.pvtype.name,  minsize=(120, -1),
                                   style=LSTY)
                del_pv = YesNo(panel, defaultyes=False)
                self.delete_pvs[pv.name] = del_pv

                sizer.Add(label,     (irow, 0), (1, 1), LSTY,  3)
                sizer.Add(pvtype,    (irow, 1), (1, 3), CSTY,  3)
                sizer.Add(del_pv,    (irow, 4), (1, 1), RSTY,  3)
 
            irow += 1
            sizer.Add(wx.StaticLine(panel, size=(150, -1),
                                    style=wx.LI_HORIZONTAL),
                      (irow, 0), (1, 5), CEN, 0)
            irow += 1

            
        txt =SimpleText(panel, 'New PVs:', font=titlefont,
                        colour=self.colors.title, style=LSTY)
        
        sizer.Add(txt, (irow, 0), (1, 5), LEFT, 3)

        self.newpvs = []
        for newpvs in range(6):
            irow += 1
            name = pvNameCtrl(panel, value='',
                              connecting_pvs=self.connecting_pvs,
                              timer=self.etimer, size=(175, -1))
            status = SimpleText(panel, 'not connected',  minsize=(120, -1),
                                style=LSTY)
            sizer.Add(name,     (irow, 0), (1, 1), LSTY,  4)
            sizer.Add(status,   (irow, 1), (1, 1), LSTY,  4)
            
            self.newpvs.append((name, status))

        btn_panel = wx.Panel(panel)
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        btn_ok     = add_button(btn_panel, 'OK',     size=(70, -1), action=self.onOK)
        btn_cancel = add_button(btn_panel, 'Cancel', size=(70, -1), action=self.onCancel)
                            
        btn_sizer.Add(btn_ok,     0, wx.ALIGN_LEFT,  2)
        btn_sizer.Add(btn_cancel, 0, wx.ALIGN_RIGHT,  2)
        pack(btn_panel, btn_sizer)
        
        irow += 1
        sizer.Add(wx.StaticLine(panel, size=(150, -1), style=wx.LI_HORIZONTAL),
                  (irow, 0), (1, 5), CEN, 2)
        sizer.Add(btn_panel, (irow+1, 1), (1, 3), CEN, 2)

        pack(panel, sizer)

        mainsizer = wx.BoxSizer(wx.VERTICAL)
        mainsizer.Add(panel, 1, LSTY, 5)
        pack(self, mainsizer)

        set_font_with_children(self, font)

        self.Layout()
        self.Show()
        self.Raise()

    def get_page_map(self):
        out = {}
        for i in range(self.parent.nb.GetPageCount()):
            out[self.parent.nb.GetPageText(i)] = i
        return out
        
    def onTimer(self, event=None):
        print 'timer ' , len(self.connecting_pvs)
        if len(self.connecting_pvs) == 0:
            self.etimer.Stop()
        
    def onRemoveInst(self, event=None):
        print 'Remove Instrument -- verify'
        
    def onOK(self, event=None):
        print 'onOK'
                
    def onCancel(self, event=None):
        self.Destroy()

