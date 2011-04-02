import wx
import sys
import time

from epicscollect.gui import  empty_bitmap, add_button, add_menu, \
     Closure, NumericCombo, pack, popup, SimpleText, \
     FileSave, FileOpen, SelectWorkdir 

from utils import GUIParams, HideShow, YesNo

class SettingsFrame(wx.Frame) :
    """ GUI Configure Frame"""
    def __init__(self, parent=None, pos=(-1, -1), db=None):
        
        self.parent = parent
        self.db = db

        style = wx.DEFAULT_FRAME_STYLE|wx.TAB_TRAVERSAL
        labstyle  = wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL
        rlabstyle = wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL|wx.ALL
        tstyle    = wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL
        
        wx.Frame.__init__(self, None, -1,
                          'Epics Instruments: General Settings',
                          size=(400, 350),  pos=pos)

        sizer = wx.GridBagSizer(10, 5)
        panel = wx.Panel(self, style=wx.GROW)
        # title row
        self.guiparams = GUIParams(self)
        self.colors = self.guiparams.colors
        panel.SetBackgroundColour(self.colors.bg)

        title = SimpleText(panel, 'General Settings',
                           font=self.guiparams.titlefont,
                           minsize=(130, -1), 
                           colour=self.colors.title, style=tstyle)

        lab_move = SimpleText(panel, 'Verify Move',  minsize=(95, -1), 
                              style=tstyle)
        lab_erase = SimpleText(panel, 'Verify Erase', minsize=(95, -1), 
                               style=tstyle)
        lab_owrite = SimpleText(panel, 'Verify Overwrite', minsize=(95, -1), 
                               style=tstyle)

        self.v_move  = YesNo(panel, defaultyes=True)
        self.v_erase = YesNo(panel, defaultyes=True)
        self.v_owrite = YesNo(panel, defaultyes=True)        

        sizer.Add(title, (0, 0), (1, 4), labstyle|wx.GROW|wx.ALL, 1)
        sizer.Add(wx.StaticLine(panel, size=(150, -1), style=wx.LI_HORIZONTAL),
                  (1, 0), (1, 4), wx.ALIGN_CENTER|wx.GROW|wx.ALL, 0)

        sizer.Add(lab_move,     (2, 0), (1, 1), labstyle,  2)
        sizer.Add(self.v_move,  (2, 1), (1, 1), labstyle,  2)
        sizer.Add(lab_erase,    (3, 0), (1, 1), labstyle,  2)
        sizer.Add(self.v_erase, (3, 1), (1, 1), labstyle,  2)        
        sizer.Add(lab_owrite,   (2, 2), (1, 1), labstyle,  2)
        sizer.Add(self.v_owrite,(2, 3), (1, 1), labstyle,  2)

        irow = 4
        sizer.Add(wx.StaticLine(panel, size=(150, -1), style=wx.LI_HORIZONTAL),
                  (irow, 0), (1, 4), wx.ALIGN_CENTER|wx.GROW|wx.ALL, 0)        

        title = SimpleText(panel, 'Show / Hide Instruments',
                           font=self.guiparams.titlefont,
                           minsize=(130, -1), 
                           colour=self.colors.title, style=tstyle)
        irow += 1
        sizer.Add(title, (irow, 0), (1, 4), labstyle|wx.GROW|wx.ALL, 1)
        self.hideframes = {}
        for inst in self.db.get_all_instruments():
            irow += 1
            isshown = inst.name in self.get_page_map()
            hide_inst = HideShow(panel, default=isshown)
            self.hideframes[inst.name] = hide_inst
            label= SimpleText(panel, inst.name,  minsize=(120, -1),
                              style=labstyle)
            sizer.Add(label,     (irow, 0), (1, 1), labstyle,  3)
            sizer.Add(hide_inst, (irow, 1), (1, 1), labstyle,  3)                        

        irow += 1
        sizer.Add(wx.StaticLine(panel, size=(150, -1), style=wx.LI_HORIZONTAL),
                  (irow, 0), (1, 4), wx.ALIGN_CENTER|wx.GROW|wx.ALL, 0)        

        btn_ok     = add_button(panel, 'OK',     size=(70, -1), action=self.onOK)
        btn_cancel = add_button(panel, 'Cancel', size=(70, -1), action=self.onCancel)
                            
        irow += 1
        sizer.Add(btn_ok,     (irow, 0), (1, 1), labstyle,  2)
        sizer.Add(btn_cancel, (irow, 1), (1, 1), labstyle,  2)
        pack(panel, sizer)

        mainsizer = wx.BoxSizer(wx.VERTICAL)
        mainsizer.Add(panel, 1, wx.GROW|wx.ALL, 1)
        pack(self, mainsizer)
        self.Layout()
        self.Show()
        self.Raise()

    def get_page_map(self):
        out = {}
        for i in range(self.parent.nb.GetPageCount()):
            out[self.parent.nb.GetPageText(i)] = i
        return out
        
    def onOK(self, event=None):
        self.db.set_info('verify_move',      str(self.v_move.GetSelection()))
        self.db.set_info('verify_erase',     str(self.v_erase.GetSelection()))
        self.db.set_info('verify_overwrite', str(self.v_owrite.GetSelection()))

        pagemap = self.get_page_map()
        for pagename, wid in self.hideframes.items():
            if wid.GetSelection() == 0 and pagename in pagemap:
                self.parent.nb.DeletePage(pagemap[pagename])
                pagemap = self.get_page_map()
                
            elif wid.GetSelection() == 1 and pagename not in pagemap:
                inst = self.db.get_instrument(pagename)
                self.parent.add_instrument_page(inst)
                pagemap = self.get_page_map()
        self.Destroy()
                
    def onCancel(self, event=None):
        self.Destroy()

