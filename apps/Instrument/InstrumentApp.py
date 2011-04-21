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

from utils import GUIColors, ConnectDialog, set_font_with_children, EIN_WILDCARD
from instrumentpanel import InstrumentPanel

from settingsframe import SettingsFrame
from editframe import EditInstrumentFrame

FNB_STYLE = flat_nb.FNB_NO_X_BUTTON|flat_nb.FNB_X_ON_TAB|flat_nb.FNB_SMART_TABS
FNB_STYLE |= flat_nb.FNB_DROPDOWN_TABS_LIST|flat_nb.FNB_NO_NAV_BUTTONS
        
class InstrumentFrame(wx.Frame):
    def __init__(self, parent=None, conf=None, dbname=None, **kwds):

        self.config = InstrumentConfig(name=conf)

        self.connect_db(dbname)

        self.epics_pvs = {}
        wx.Frame.__init__(self, parent=parent, title='Epics Instruments',
                          size=(925, 400), **kwds)

        self.colors = GUIColors()
        self.SetBackgroundColour(self.colors.bg)

        wx.EVT_CLOSE(self, self.onClose)        
        self.create_Statusbar()
        self.create_Menus()
        self.create_Frame()

    def connect_db(self, dbname=None, new=False):
        """connects to a db, possibly creating a new one"""
        if dbname is None:
            filelist = self.config.get_dblist()
            if new:
                filelist = None
            dlg = ConnectDialog(filelist=filelist)
            dlg.Raise()
            if dlg.ShowModal() == wx.ID_OK:
                dbname = dlg.filebrowser.GetValue()
                if not dbname.endswith('.ein'):
                    dbname = "%s.ein" % dbname
            else:
                return
            dlg.Destroy()
            
        self.db = InstrumentDB()
        if isInstrumentDB(dbname):
            self.db.connect(dbname)
        else:
            self.db.create_newdb(dbname, connect=True)            
        self.config.set_current_db(dbname)
        self.dbname = dbname

    def create_Frame(self):
        self.nb = flat_nb.FlatNotebook(self, wx.ID_ANY, agwStyle=FNB_STYLE)

        colors = self.colors
        self.nb.SetActiveTabColour(colors.nb_active)
        self.nb.SetTabAreaColour(colors.nb_area)
        self.nb.SetNonActiveTabTextColour(colors.nb_text)
        self.nb.SetActiveTabTextColour(colors.nb_activetext)
        self.nb.SetBackgroundColour(colors.bg)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.nb, 1, wx.EXPAND)

        self.create_nbpages()
        self.SetMinSize((725, 300))
        
        pack(self, sizer)
        self.Refresh()

    def create_nbpages(self):
        self.Freeze()
        if self.nb.GetPageCount() > 0:
            self.nb.DeleteAllPages()

        for inst in self.db.get_all_instruments():
            if inst.show is None:
                inst.show = 1
            if int(inst.show) == 1:
                self.add_instrument_page(inst)
            
        self.Thaw()

    def add_instrument_page(self, inst):
        self.connect_pvs(inst, wait_time=1.0)
        panel = InstrumentPanel(self, inst, db=self.db,
                                size=(925, 300), 
                                writer = self.write_message)
        self.nb.AddPage(panel, inst.name, True)
        
    @EpicsFunction
    def connect_pvs(self, inst, wait_time=2.0):
        """connect to PVs for an instrument.."""
        self.connected = False
        for pv in inst.pvs:
            self.epics_pvs[pv.name]  = epics.PV(pv.name)
            time.sleep(0.002)
        t0 = time.time()
        while (time.time() - t0) < wait_time:
            time.sleep(0.002)
            if all(x.connected for x in self.epics_pvs.values()):
                break
        return
        
    def create_Menus(self):
        """create menus"""
        mbar = wx.MenuBar()
        file_menu = wx.Menu()
        opts_menu = wx.Menu()
        inst_menu = wx.Menu()
        help_menu = wx.Menu()

        add_menu(self, file_menu, "&New File", "Create New Instruments File",
                 action=self.onNew)
        add_menu(self, file_menu, "&Open File", "Open Instruments File",
                 action=self.onOpen)        
        add_menu(self, file_menu, "&Save As", "Save Instruments File",
                 action=self.onSave)        
        file_menu.AppendSeparator()
        add_menu(self, file_menu, "E&xit", "Terminate the program",
                 action=self.onClose)

        add_menu(self, inst_menu, "&Add New Instrument",
                 "Add New Instrument",
                 action=self.onAddInstrument)

        add_menu(self, inst_menu, "&Edit Current Instrument",
                 "Edit Current Instrument",
                 action=self.onEditInstrument)                 

        add_menu(self, opts_menu, "Settings",
                 "Change Settings for GUI behavior",
                 action=self.onSettings)
        
        add_menu(self, opts_menu, "Change Font", "Select Font",
                 action=self.onSelectFont)                         
        
        add_menu(self, help_menu, 'About',
                 "More information about this program", action=self.onAbout)

        mbar.Append(file_menu, "&File")
        mbar.Append(opts_menu, "&Options")
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

    def onAddInstrument(self, event=None):
        "add a new, empty instrument and start adding PVs"
        newname = basename = 'New Instrument'
        inst = self.db.get_instrument(newname)
        count = 1
        while inst is not None:
            count += 1
            newname = "%s(%i)" % (basename, count)
            inst = self.db.get_instrument(newname)

        inst = self.db.add_instrument(newname)

        panel = InstrumentPanel(self, inst, db=self.db,
                                size=(925, 300), 
                                writer = self.write_message)

        self.nb.AddPage(panel, inst.name, True)
        EditInstrumentFrame(parent=self, db=self.db, inst=inst,
                            epics_pvs=self.epics_pvs)
        
    def onEditInstrument(self, event=None):
        "edit the current instrument"
        inst = self.nb.GetCurrentPage().inst
        EditInstrumentFrame(parent=self, db=self.db, inst=inst,
                            epics_pvs=self.epics_pvs)

    def onSettings(self, event=None):
        try:
            self.settings_frame.Raise()
        except:
            self.settting_frame = SettingsFrame(parent=self, db=self.db)
        
    def onAbout(self, event=None):
        # First we create and fill the info object
        info = wx.AboutDialogInfo()
        info.Name = "Epics Instruments"
        info.Version = "0.2"
        info.Copyright = "2011, Matt Newville, University of Chicago"
        info.Description = """
        Epics Instruments is an application to save and restore Instrument Positions.
        An Instrument is defined as a collection of Epics Process Variable and a
        Position is defined as any named set of values for those Process Variables"""
        wx.AboutBox(info)

    def onOpen(self, event=None):
        fname = FileOpen(self, 'Open Instrument File',
                         wildcard=EIN_WILDCARD,
                         default_file=self.dbname)
        if fname is not None:
            self.db.close()
            time.sleep(1)
            self.dbname = fname
            self.config.set_current_db(fname)
            self.config.write()
            self.create_nbpages()

    def onNew(self, event=None):
        self.connect_db(dbname=self.dbname, new=True)
        self.create_nbpages()
                
    def onSave(self, event=None):
        outfile = FileSave(self, 'Save Instrument File As',
                           wildcard=EIN_WILDCARD,
                           default_file=self.dbname)

        # save current tab/instrument mapping
        if outfile not in (None, self.dbname):
            self.db.close()
            shutil.copy(self.dbname, outfile)
            time.sleep(1)
            self.dbname = outfile            
            self.config.set_current_db(outfile)
            self.config.write()
           
            self.db = InstrumentDB(outfile)

            # set current tabs to the new db
            insts = [(i, self.nb.GetPage(i).inst.name) for i in range(self.nb.GetPageCount())]
            
            for nbpage, name in insts:
                self.nb.GetPage(nbpage).db = self.db
                self.nb.GetPage(nbpage).inst = self.db.get_instrument(name)
                
            self.write_message("Saved Instrument File: %s" % outfile)

    def onSelectFont(self, evt=None):
        fontdata = wx.FontData()
        fontdata.SetInitialFont(self.GetFont())
        dlg = wx.FontDialog(self, fontdata)
        
        if dlg.ShowModal() == wx.ID_OK:
            font = dlg.GetFontData().GetChosenFont()
            set_font_with_children(self, font)
            self.Refresh()
            self.Layout()
        dlg.Destroy()

    def onClose(self, event):
        display_order = [self.nb.GetPage(i).inst.name for i in range(self.nb.GetPageCount())]

        for inst in self.db.get_all_instruments():
            inst.show = 0
            if inst.name in display_order:
                inst.show = 1
                inst.display_order = display_order.index(inst.name)
        self.db.commit()

        self.config.write()
        finalize_epics()
        self.Destroy()

## class InstrumentApp(wx.App):


class InstrumentApp(wx.App, wx.lib.mixins.inspection.InspectionMixin):
    def __init__(self, conf=None, dbname=None, **kws):
        self.conf  = conf
        self.dbname  = dbname
        wx.App.__init__(self)
        
    def OnInit(self):
        self.Init() 
        frame = InstrumentFrame(conf=self.conf, dbname=self.dbname)
        frame.Show()
        self.SetTopWindow(frame)
        return True

if __name__ == '__main__':
    conf = None
    dbname = None # 'Test.ein'
    inspect = False
    if inspect:
        app = InstrumentApp(dbname=dbname, conf=conf)
    else:
        app = wx.PySimpleApp()
        InstrumentFrame(conf=conf, dbname=dbname).Show()
        
    app.MainLoop()
