import wx
import sys
import time

from epics.wx import EpicsFunction

from epicscollect.gui import  empty_bitmap, add_button, add_menu, \
     Closure, NumericCombo, pack, popup, SimpleText, \
     FileSave, FileOpen, SelectWorkdir 

from utils import GUIColors, HideShow, YesNo, set_font_with_children

class pvNameCtrl(wx.TextCtrl):
    def __init__(self, parent,  value='', connecting_pvs=None, timer=None,  **kws):
        wx.TextCtrl.__init__(self, parent, wx.ID_ANY, value='', **kws)
        self.Bind(wx.EVT_CHAR, self.onChar)
        if connecting_pvs is None:
            connecting_pvs = {}
        self.connecting_pvs = connecting_pvs
        self.timer = timer
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

class EditFrame(wx.Frame) :
    """ Edit / Add Instrument"""
    def __init__(self, parent=None, pos=(-1, -1), inst=None, db=None):
        
        title = 'Add New Instrument'
        if inst is not None:
            title = 'Edit Instrument  %s ' % inst.name

        wx.Frame.__init__(self, None, -1, title,  size=(550, 550),  pos=pos)
        panel = wx.Panel(self, style=wx.GROW)
        self.colors = GUIColors()

        font = self.GetFont()
        if parent is not None:
            font = parent.GetFont()
            
        titlefont  = font
        titlefont.PointSize += 2
        titlefont.SetWeight(wx.BOLD)
        
        panel.SetBackgroundColour(self.colors.bg)

        self.parent = parent
        self.db = db
        self.inst = db.get_instrument(inst)
        self.connecting_pvs = {}

        labstyle  = wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL
        rlabstyle = wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL|wx.ALL
        tstyle    = wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL
        rtstyle   = wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL        

        self.etimer = wx.Timer(self)
        self.etimer_count = 0
        self.Bind(wx.EVT_TIMER, self.onTimer, self.etimer)

        sizer = wx.GridBagSizer(10, 5)
        # Name row
        label  = SimpleText(panel, 'Instrument Name',
                            minsize=(95, -1), style=labstyle)
        self.name =  wx.TextCtrl(panel, value='', size=(225, -1))

        sizer.Add(label,     (0, 0), (1, 1), labstyle, 1)
        sizer.Add(self.name, (0, 1), (1, 4), labstyle|wx.GROW|wx.ALL, 1)
        sizer.Add(wx.StaticLine(panel, size=(150, -1), style=wx.LI_HORIZONTAL),
                  (1, 0), (1, 5), wx.ALIGN_CENTER|wx.GROW|wx.ALL, 0)

        irow = 2
        self.delete_pvs = {}
        if inst is not None:
            self.name.SetValue(inst.name)
            i = 0
            for titleword in (' PV  ', 'Display Type', 'Remove?'):
                style = tstyle
                if titleword.startswith('Rem'):
                    style = rtstyle
                txt =SimpleText(panel, titleword,
                                font=titlefont,
                                minsize=(120, -1), 
                                colour=self.colors.title, style=style)
            
                sizer.Add(txt, (irow, i), (1, 1), labstyle, 1)
                i = i + 1

            irow += 1
            sizer.Add(wx.StaticLine(panel, size=(150, -1),
                                    style=wx.LI_HORIZONTAL),
                      (irow, 0), (1, 5), wx.ALIGN_CENTER|wx.GROW|wx.ALL, 0)

            for pv in inst.pvs:
                irow += 1
                label= SimpleText(panel, pv.name,  minsize=(120, -1),
                                  style=labstyle)
                pvtype = SimpleText(panel, pv.pvtype.name,  minsize=(120, -1),
                                   style=labstyle)
                del_pv = YesNo(panel, defaultyes=False)
                self.delete_pvs[pv.name] = del_pv

                sizer.Add(label,     (irow, 0), (1, 1), labstyle,  3)
                sizer.Add(pvtype,    (irow, 1), (1, 1), labstyle,  3)
                sizer.Add(del_pv,    (irow, 2), (1, 1), rlabstyle,  3)
 
            irow += 1
            sizer.Add(wx.StaticLine(panel, size=(150, -1),
                                    style=wx.LI_HORIZONTAL),
                      (irow, 0), (1, 4), wx.ALIGN_CENTER|wx.GROW|wx.ALL, 0)

        self.newpvs = []
        for newpvs in range(3):
            irow += 1
            name = pvNameCtrl(panel, value='',
                              connecting_pvs=self.connecting_pvs,
                              timer=self.etimer, size=(120, -1))
            status = SimpleText(panel, 'not connected',  minsize=(120, -1),
                                style=labstyle)
            sizer.Add(name,     (irow, 0), (1, 1), labstyle,  2)
            sizer.Add(status,   (irow, 1), (1, 1), labstyle,  2)
            
            self.newpvs.append((name, status))


        irow += 1
        sizer.Add(wx.StaticLine(panel, size=(150, -1), style=wx.LI_HORIZONTAL),
                  (irow, 0), (1, 5), wx.ALIGN_CENTER|wx.GROW|wx.ALL, 0)        

        btn_ok     = add_button(panel, 'OK',     size=(70, -1), action=self.onOK)
        btn_cancel = add_button(panel, 'Cancel', size=(70, -1), action=self.onCancel)
                            
        irow += 1
        sizer.Add(btn_ok,     (irow, 0), (1, 1), labstyle,  2)
        sizer.Add(btn_cancel, (irow, 1), (1, 1), labstyle,  2)
        pack(panel, sizer)

        mainsizer = wx.BoxSizer(wx.VERTICAL)
        mainsizer.Add(panel, 1, wx.GROW|wx.ALL, 1)
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
        
    def onOK(self, event=None):
        print 'onOK'
                
    def onCancel(self, event=None):
        self.Destroy()

