#!/usr/bin/python
#
#  Instruments GUI

import wx
import wx.lib.filebrowsebutton as filebrowse
from wx.lib.wordwrap import wordwrap
import wx.lib.agw.flatnotebook as flat_nb

import wx.lib.mixins.inspection

import sys
import time
import epics
from epics.wx import finalize_epics, EpicsFunction, \
     pvText, pvFloatCtrl, pvTextCtrl, pvEnumChoice

from epicscollect.gui import  empty_bitmap, add_button, add_menu, \
     Closure, NumericCombo, pack, popup, \
     FileSave, FileOpen, SelectWorkdir 

from MotorPanel import MotorPanel

from configfile import InstrumentConfig
from instrument import isInstrumentDB, InstrumentDB

FileBrowser = filebrowse.FileBrowseButtonWithHistory

ALL_EXP  = wx.ALL|wx.EXPAND

class SimpleText(wx.StaticText):
    "simple static text wrapper"
    def __init__(self, parent, label, minsize=None,
                 font=None, colour=None, bgcolour=None,
                 style=wx.ALIGN_CENTRE,  **kw):

        wx.StaticText.__init__(self, parent, wx.ID_ANY,
                               label=label, style=style, **kw)
        if minsize is not None:
            self.SetMinSize(minsize)
        if font is not None:
            self.SetFont(font)
        if colour is not None:
            self.SetForegroundColour(colour)
        if bgcolour is not None:
            self.SetBackgroundColour(bgcolour)

class ConnectDialog(wx.Dialog):
    """Connect to a recent or existing DB File, or create a new one"""

    msg = '''Select Recent Instrument File, create a new one'''
    
    def __init__(self, parent=None, filelist=None,
                 title='Select Instruments File'):

        wx.Dialog.__init__(self, parent, wx.ID_ANY, title=title)

        title = wx.StaticText(parent, label = self.msg)
        self.filebrowser = FileBrowser(self,  # label='Select File:',
                                       size=(450, -1))

        self.filebrowser.SetHistory(filelist)
        self.filebrowser.SetLabel('File:')
        if filelist is not None:
            self.filebrowser.SetValue(filelist[0])
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(wx.StaticText(self, label=self.msg), 0,
                  wx.ALIGN_CENTER|wx.ALL|wx.GROW, 3)
        sizer.Add(self.filebrowser, 1,
                  wx.ALIGN_CENTER|wx.ALL|wx.GROW, 3)

        sizer.Add(self.CreateButtonSizer(wx.OK| wx.CANCEL),
                 1, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 4)

        pack(self, sizer)
        
class InstrumentPanel(wx.Panel):
    """ create Panel for an instrument"""

    def __init__(self, parent, inst, size=(-1, -1)):
        self.inst = inst
        wx.Panel.__init__(self, parent, size=size)
        
        splitter = wx.SplitterWindow(self, style=wx.SP_LIVE_UPDATE)
        splitter.SetMinimumPaneSize(150)
       
        lpanel = wx.Panel(splitter, size=(550, 175))
        rpanel = wx.Panel(splitter, size=(150, 175))
        
        toprow = wx.Panel(lpanel)
        self.pos_name =  wx.TextCtrl(toprow, value="", size=(220, 25),
                                     style= wx.TE_PROCESS_ENTER)
        self.pos_name.Bind(wx.EVT_TEXT_ENTER, self.onSavePosition)

        topsizer = wx.BoxSizer(wx.HORIZONTAL)
        tfont = self.GetFont()
        tfont.PointSize += 3
        tfont.SetWeight(wx.BOLD)

        topsizer.Add(SimpleText(toprow, inst.name,
                                font=tfont, colour=(170, 0, 00),
                                minsize=(175, -1),
                                style=wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL), 0,
                     wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL, 2)

        topsizer.Add(SimpleText(toprow, 'Save Current Position:',
                                style=wx.ALIGN_RIGHT), 0,
                     wx.ALIGN_CENTER_VERTICAL|wx.ALL, 2)

        topsizer.Add(self.pos_name, 1,
                     wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL|wx.GROW|wx.ALL, 2)

        pack(toprow, topsizer)

        lsizer = wx.BoxSizer(wx.VERTICAL)
        lsizer.Add(toprow, 0,  wx.GROW|wx.ALIGN_LEFT|wx.TOP, 1)

        self.pvpanels = {}
        for x in inst.pvs:
            thispanel = wx.Panel(lpanel)
            thissizer = wx.BoxSizer(wx.HORIZONTAL)
            thissizer.Add(wx.StaticText(thispanel,
                                        label='Connecting %s' % x.name),
                          0, wx.ALL|wx.ALIGN_CENTER, 1)
            pack(thispanel, thissizer)
                           
            lsizer.Add(thispanel, 1, wx.TOP|wx.ALL, 2)
            self.PV_Panel(thispanel, thissizer, x.name)            
            
        time.sleep(0.05)
        
        pack(lpanel, lsizer)

        rsizer = wx.BoxSizer(wx.VERTICAL)
        btn_goto = add_button(rpanel, "Go To",  size=(70, -1),
                              action=self.onGo)
        btn_erase = add_button(rpanel, "Erase",  size=(70, -1),
                               action=self.onErase)
        
        brow = wx.BoxSizer(wx.HORIZONTAL)
        brow.Add(btn_goto,   0, ALL_EXP|wx.ALIGN_LEFT, 1)
        brow.Add(btn_erase,  0, ALL_EXP|wx.ALIGN_LEFT, 1)

        self.pos_list  = wx.ListBox(rpanel)
        self.pos_list.SetBackgroundColour(wx.WHITE)
        self.pos_list.Bind(wx.EVT_LISTBOX,    self.onSelectPosition)
        self.pos_list.Bind(wx.EVT_RIGHT_DOWN, self.onRightClick)

        self.pos_list.Clear()
        for pos in inst.positions:
            self.pos_list.Append(pos.name)

        rsizer.Add(brow,          0, wx.ALIGN_LEFT|wx.ALL)
        rsizer.Add(self.pos_list, 1, wx.ALL|wx.EXPAND|wx.ALIGN_CENTER, 1)
        pack(rpanel, rsizer)

        splitter.SplitVertically(lpanel, rpanel, 1)
            
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(splitter, 1, wx.ALIGN_LEFT|wx.GROW|wx.ALL, 3)
        pack(self, sizer)

    @EpicsFunction
    def PV_Panel(self, panel, sizer, pvname):
        pv = epics.PV(pvname)
        time.sleep(0.002)
        for control in panel.Children:
            control.Destroy()
        sizer.Clear()
            
        # check for motor
        pref = pvname
        if '.' in pvname:
            pref, suff = pvname.split('.')
        dtype  = epics.caget("%s.RTYP" % pref)
        if dtype.lower() == 'motor':
            sizer.Add(MotorPanel(panel, pvname, size=(450, 25)), 0,
                      wx.ALIGN_CENTER_VERTICAL|wx.ALL, 2)
            pack(panel, sizer)
            return
        
        label = SimpleText(panel, pvname, colour=wx.BLUE,
                           minsize=(100,-1),style=wx.ALIGN_LEFT)

        if pv.type in ('double', 'int', 'long', 'short'):
            control = pvFloatCtrl(panel, pv=pv)
        elif pv.type in ('string', 'unicode'):
            control = pvTextCtrl(panel, pv=pv)
        elif pv.type == 'enum':
            control = pvEnumChoice(panel, pv=pv)

        sizer.Add(label,   0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 2)
        sizer.Add(control, 1, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 2)
        pack(panel, sizer)
        sizer.Layout()
        self.Resize()
        self.Refresh()
        return
        
    def onSavePosition(self, evt=None):
        print 'save position', evt.GetString(), self.inst

    def onSelectPosition(self, evt=None):
        print 'select position', evt.GetString(), self.inst

    def onRightClick(self, evt=None):
        print 'right click ', evt.GetString(), self.inst        

    def onGo(self, evt=None):
        posname = self.pos_list.GetStringSelection()
        print 'on go ', evt.GetString(), self.inst, posname

    def onErase(self, evt=None):
        posname = self.pos_list.GetStringSelection()

        print 'on erase ', evt.GetString(), self.inst, posname
                  
    
class InstrumentFrame(wx.Frame):
    def __init__(self, parent=None, conf=None, dbname=None, **kwds):

        self.config = InstrumentConfig(name=conf)

        if dbname is None:
            filelist = self.config.get_dblist()        
            dlg = ConnectDialog(filelist=filelist)
            dlg.Raise()
            if dlg.ShowModal() == wx.ID_OK:
                dbname = dlg.filebrowser.GetValue()
            else:
                return
            dlg.Destroy()

        self.db = InstrumentDB()
        if isInstrumentDB(dbname):
            self.db.connect(dbname)
        else:
            self.db.create_newdb(dbname)            

        self.config.set_current_db(dbname)

        wx.Frame.__init__(self, parent=parent, title='Epics Instruments',
                          size=(700, 350), **kwds)

        self.SetBackgroundColour(wx.Colour(245,245,235))
        
        wx.EVT_CLOSE(self, self.onClose)        
       
        self.create_Statusbar()
        self.create_Menus()
        self.create_Frame()

    def create_Frame(self):
        fnb = flat_nb
        style  = fnb.FNB_NODRAG|fnb.FNB_NO_X_BUTTON
        style |= fnb.FNB_DROPDOWN_TABS_LIST|fnb.FNB_NO_NAV_BUTTONS
        if style & fnb.FNB_NODRAG:
            style ^= fnb.FNB_NODRAG

        self.nb = flat_nb.FlatNotebook(self, wx.ID_ANY, agwStyle=style)

        self.nb.SetActiveTabColour(wx.Colour(250,250,105))
        self.nb.SetTabAreaColour(wx.Colour(250,250,245))
        self.nb.SetNonActiveTabTextColour(wx.Colour(10,10,80))
        self.nb.SetBackgroundColour(wx.Colour(235,235,225))

        mainsizer = wx.BoxSizer(wx.VERTICAL)
        mainsizer.Add(self.nb, 1, wx.EXPAND)

        self.Freeze()
        for inst in self.db.get_all_instruments():
            self.connect_pvs(inst, wait_time=1.0)

            self.nb.AddPage(InstrumentPanel(self, inst), inst.name, True)
        self.Thaw()
            
        pack(self, mainsizer)
        mainsizer.Layout()
        self.Refresh()
        self.SendSizeEvent()
        
    @EpicsFunction
    def connect_pvs(self, inst, wait_time=2.0):
        """connect to PVs for an instrument.."""
        self.connected = False
        pvobjs = []
        for pv in inst.pvs:
            pvobjs.append(epics.PV(pv.name))
            time.sleep(0.002)
        t0 = time.time()
        while (time.time() - t0) < wait_time:
            time.sleep(0.002)
            if all(x.connected for x in pvobjs):
                break
        return
        
    def create_Menus(self):
        """create menus"""
        mbar = wx.MenuBar()
        file_menu = wx.Menu()
        inst_menu = wx.Menu()
        help_menu = wx.Menu()

        add_menu(self, file_menu, "&Open", "Open Instruments File")
        add_menu(self, file_menu, "&Save", "Save Instruments File")        
        file_menu.AppendSeparator()
        add_menu(self, file_menu, "E&xit", "Terminate the program",
                 action=self.onClose)

        add_menu(self, inst_menu, "&Add Instrument","Add New Instrument",
                 action=self.onInstAdd)
        add_menu(self, inst_menu, "&Edit Current Instrument","Edit Current Instrument",
                 action=self.onInstEdit)                 
        inst_menu.AppendSeparator()
        add_menu(self, inst_menu, "General Stings","Edit Instrument List, etc",
                 action=self.onInstEdit)                 
        
        add_menu(self, help_menu, 'About',
                 "More information about this program", action=self.onAbout)

        mbar.Append(file_menu, "&File")
        mbar.Append(inst_menu, "&Instruments")
        mbar.Append(help_menu, "&Help")

        self.SetMenuBar(mbar)

    def create_Statusbar(self):
        "create status bar"
        self.statusbar = self.CreateStatusBar(2, wx.CAPTION|wx.THICK_FRAME)
        self.statusbar.SetStatusWidths([-4,-1])
        for index, name  in enumerate(("Messages", "Status")):
            self.statusbar.SetStatusText('', index)
            
    def write_message(self,text,status='normal'):
        self.SetStatusText(text)

    def onInstAdd(self, event=None):
        print 'add inst'

    def onInstEdit(self, event=None):
        print 'edit this inst ', self.nb.GetCurrentPage().inst

    def onInstEdit(self, event=None):
        print 'edit this inst ', self.nb.GetCurrentPage().inst

        
        

    def onAbout(self, event=None):
        # First we create and fill the info object
        info = wx.AboutDialogInfo()
        info.Name = "Epics Instruments"
        info.Version = "0.1"
        info.Copyright = "2011, Matt Newville, University of Chicago"
        info.Description = """'Epics Instruments' is an application to save and restore Instrument Positions.  Here,an Instrument is defined as a collection of Epics Process Variable and a Position is defined as any named set of values for those Process Variables"""
        wx.AboutBox(info)


    def onClose(self, event):
        print 'Should Get Page List: ',  [self.nb.GetPage(i).inst for i in range(self.nb.GetPageCount())]
        print 'Should save config file, with this info'
        finalize_epics()
        self.Destroy()

class TestApp(wx.App, wx.lib.mixins.inspection.InspectionMixin):
    def __init__(self, conf=None, dbname=None, **kws):
        self.conf  = conf
        self.dbname  = dbname
        wx.App.__init__(self)
        
    def OnInit(self):
        self.Init() 
        frame = InstrumentFrame(conf=conf, dbname=dbname)
        frame.Show()
        self.SetTopWindow(frame)
        return True

if __name__ == '__main__':
    dbname = 'Test.einst'
    conf = 'test.conf'
    TestApp(conf=conf, dbname=dbname).MainLoop()


