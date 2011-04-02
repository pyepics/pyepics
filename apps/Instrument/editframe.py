import wx
import sys
import time

from epics.wx import EpicsFunction

from epicscollect.gui import  empty_bitmap, add_button, add_menu, \
     Closure, NumericCombo, pack, popup, SimpleText, \
     FileSave, FileOpen, SelectWorkdir 

class HideShow(wx.Choice):
    def __init__(self, parent, default=True, size=(70,-1)):
        wx.Choice.__init__(self, parent, -1, size=size)
        self.choices = ('Hide', 'Show')
        self.Clear()
        self.SetItems(self.choices)
        self.SetSelection({False:0, True:1}[default])

class YesNo(wx.Choice):
    def __init__(self, parent, defaultyes=True, size=(70,-1)):
        wx.Choice.__init__(self, parent, -1, size=size)
        self.choices = ('No', 'Yes')
        self.Clear()
        self.SetItems(self.choices)
        self.SetSelection({False:0, True:1}[defaultyes])

    def SetChoices(self, choices):
        self.Clear()
        self.SetItems(choices)
        self.choices = choices
        
    def Select(self, choice):
        if isinstance(choice, int):
            self.SetSelection(0)
        elif choice in self.choices:
            self.SetSelection(self.choices.index(choice))


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

        self.parent = parent
        self.db = db
        self.inst = db.get_instrument(inst)
        self.connecting_pvs = {}
        
        style = wx.DEFAULT_FRAME_STYLE|wx.TAB_TRAVERSAL
        labstyle  = wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL
        rlabstyle = wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL|wx.ALL
        tstyle    = wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL
        tfont = self.GetFont()
        tfont.PointSize += 2
        tfont.SetWeight(wx.BOLD)

        self.etimer = wx.Timer(self)
        self.etimer_count = 0
        self.Bind(wx.EVT_TIMER, self.onTimer, self.etimer)

        sizer = wx.GridBagSizer(10, 5)
        panel = wx.Panel(self, style=wx.GROW)
        # Name row
        label  = SimpleText(panel, 'Instrument Name',  minsize=(95, -1), style=labstyle)
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
                txt =SimpleText(panel, titleword, font=tfont,
                                minsize=(120, -1), 
                                colour=(80, 10, 10), style=tstyle)
            
                sizer.Add(txt, (irow, i), (1, 1), labstyle, 1)
                i = i + 1

            irow += 1
            sizer.Add(wx.StaticLine(panel, size=(150, -1), style=wx.LI_HORIZONTAL),
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
            sizer.Add(wx.StaticLine(panel, size=(150, -1), style=wx.LI_HORIZONTAL),
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

                #         self.v_move  = YesNo(panel, defaultyes=True)
#         self.v_erase = YesNo(panel, defaultyes=True)
#         self.v_owrite = YesNo(panel, defaultyes=True)        
# 
#         sizer.Add(title, (0, 0), (1, 4), labstyle|wx.GROW|wx.ALL, 1)
#         sizer.Add(wx.StaticLine(panel, size=(150, -1), style=wx.LI_HORIZONTAL),
#                   (1, 0), (1, 4), wx.ALIGN_CENTER|wx.GROW|wx.ALL, 0)
# 
#         sizer.Add(lab_move,     (2, 0), (1, 1), labstyle,  2)
#         sizer.Add(self.v_move,  (2, 1), (1, 1), labstyle,  2)
#         sizer.Add(lab_erase,    (3, 0), (1, 1), labstyle,  2)
#         sizer.Add(self.v_erase, (3, 1), (1, 1), labstyle,  2)        
#         sizer.Add(lab_owrite,   (2, 2), (1, 1), labstyle,  2)
#         sizer.Add(self.v_owrite,(2, 3), (1, 1), labstyle,  2)
# 
#         irow = 4
#         sizer.Add(wx.StaticLine(panel, size=(150, -1), style=wx.LI_HORIZONTAL),
#                   (irow, 0), (1, 4), wx.ALIGN_CENTER|wx.GROW|wx.ALL, 0)        
# 
#         title = SimpleText(panel, 'Show / Hide Instruments',
#                            font=tfont,
#                            minsize=(130, -1), 
#                            colour=(80, 10, 10), style=tstyle)
#         irow += 1
#         sizer.Add(title, (irow, 0), (1, 4), labstyle|wx.GROW|wx.ALL, 1)
#         self.hideframes = {}
#         for inst in self.db.get_all_instruments():
#             irow += 1
#             isshown = inst.name in self.get_page_map()
#             hide_inst = HideShow(panel, default=isshown)
#             self.hideframes[inst.name] = hide_inst
#             label= SimpleText(panel, inst.name,  minsize=(120, -1),
#                               style=labstyle)
#             sizer.Add(label,     (irow, 0), (1, 1), labstyle,  3)
#             sizer.Add(hide_inst, (irow, 1), (1, 1), labstyle,  3)                        


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
#         self.db.set_info('verify_move',      str(self.v_move.GetSelection()))
#         self.db.set_info('verify_erase',     str(self.v_erase.GetSelection()))
#         self.db.set_info('verify_overwrite', str(self.v_owrite.GetSelection()))
# 
#         pagemap = self.get_page_map()
#         for pagename, wid in self.hideframes.items():
#             if wid.GetSelection() == 0 and pagename in pagemap:
#                 print 'Hide ', pagename, pagemap[pagename]
#                 self.parent.nb.DeletePage(pagemap[pagename])
#                 pagemap = self.get_page_map()
#                 
#             elif wid.GetSelection() == 1 and pagename not in pagemap:
#                 inst = self.db.get_instrument(pagename)
#                 self.parent.add_instrument_page(inst)
#                 pagemap = self.get_page_map()
#                 
#         self.Destroy()
#         
                
    def onCancel(self, event=None):
        self.Destroy()

