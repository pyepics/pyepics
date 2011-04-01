#!/usr/bin/python
#
#  Instruments GUI

import wx
from wx.lib.wordwrap import wordwrap
import wx.lib.agw.flatnotebook as flat_nb
import wx.lib.mixins.inspection

import sys
import time
import shutil

import epics
from epics.wx import finalize_epics, EpicsFunction

from epicscollect.gui import  empty_bitmap, add_button, add_menu, \
     Closure, NumericCombo, pack, popup, \
     FileSave, FileOpen, SelectWorkdir 

from configfile import InstrumentConfig
from instrument import isInstrumentDB, InstrumentDB

from utils import ConnectDialog, InstrumentPanel
    
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
        self.dbname = dbname

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

        self.nb.SetActiveTabColour(wx.Colour(254,254,195))
        self.nb.SetTabAreaColour(wx.Colour(250,250,245))
        self.nb.SetNonActiveTabTextColour(wx.Colour(10,10,180))
        self.nb.SetActiveTabTextColour(wx.Colour(80,10,10))
        self.nb.SetBackgroundColour(wx.Colour(235,235,225))

        mainsizer = wx.BoxSizer(wx.VERTICAL)
        mainsizer.Add(self.nb, 1, wx.EXPAND)

        self.Freeze()
        for inst in self.db.get_all_instruments():
            self.connect_pvs(inst, wait_time=1.0)

            self.nb.AddPage(InstrumentPanel(self, inst, db=self.db,
                                            writer = self.write_message),
                            inst.name, True)
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
        add_menu(self, file_menu, "&Save As", "Save Instruments File",
                 action=self.onSave)        
        file_menu.AppendSeparator()
        add_menu(self, file_menu, "E&xit", "Terminate the program",
                 action=self.onClose)

        add_menu(self, inst_menu, "&Add Instrument","Add New Instrument",
                 action=self.onInstAdd)
        add_menu(self, inst_menu, "&Edit Current Instrument","Edit Current Instrument",
                 action=self.onInstEdit)                 
        inst_menu.AppendSeparator()
        add_menu(self, inst_menu, "General Stings","Edit Instrument List, etc",
                 action=self.onSettings)                 
        
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

    def onSettings(self, event=None):
        print 'edit settings ', self.nb.GetCurrentPage().inst


    def onAbout(self, event=None):
        # First we create and fill the info object
        info = wx.AboutDialogInfo()
        info.Name = "Epics Instruments"
        info.Version = "0.1"
        info.Copyright = "2011, Matt Newville, University of Chicago"
        info.Description = """'Epics Instruments' is an application to save and restore Instrument Positions.  Here,an Instrument is defined as a collection of Epics Process Variable and a Position is defined as any named set of values for those Process Variables"""
        wx.AboutBox(info)


    def onSave(self, event=None):
        wildcard = 'Instrument Files (*.einst)|*.einst|All files (*.*)|*.*'
        outfile = FileSave(self, 'Save Instrument File As',
                           wildcard=wildcard,
                           default_file=self.dbname)

        # save current tab/instrument mapping
        insts = [(i, self.nb.GetPage(i).inst.name) for i in range(self.nb.GetPageCount())]
        if outfile is not None:
            self.db.close()
            shutil.copy(self.dbname, outfile)
            time.sleep(1)
            self.dbname = outfile            
            self.config.set_current_db(outfile)
            self.config.write()
           
            self.db = InstrumentDB(outfile)
            # set current tabs to the new db
            for nbpage, name in insts:
                self.nb.GetPage(nbpage).db = self.db
                self.nb.GetPage(nbpage).inst = self.db.get_instrument(name)

            self.message("Saved Instrument File: %s" % outfile)
                
        
    def onClose(self, event):
        print 'Should Get Page List: ',  [self.nb.GetPage(i).inst for i in range(self.nb.GetPageCount())]
        print 'Should save config file, with this info'
        finalize_epics()
        self.Destroy()

class InstrumentApp(wx.App, wx.lib.mixins.inspection.InspectionMixin):
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
    dbname = None # 'Test.einst'
    conf = 'test.conf'
    # app = wx.PySimpleApp()
    # InstrumentFrame(conf=conf, dbname=dbname).Show()
    app = InstrumentApp(conf=conf, dbname=dbname)
    app.MainLoop()


