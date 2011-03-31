#!/usr/bin/python
#
#  Instruments GUI

import wx
import wx.lib.filebrowsebutton as filebrowse
from wx.lib.wordwrap import wordwrap
import wx.lib.agw.flatnotebook as flat_nb

import sys
import time
import epics
from epics.wx import finalize_epics, MotorPanel, EpicsFunction

from epicscollect.gui import  empty_bitmap, add_button, add_menu, \
     Closure, NumericCombo, pack, popup, \
     FileSave, FileOpen, SelectWorkdir \


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
        
        lpanel = wx.Panel(self, size=(350,200))
        rpanel = wx.Panel(self, size=(150,200))
        
        toprow = wx.Panel(lpanel)
        self.pos_name =  wx.TextCtrl(toprow, value="", size=(180, 25),
                                     style= wx.TE_PROCESS_ENTER)
        self.pos_name.Bind(wx.EVT_TEXT_ENTER, self.onSavePosition)

        topsizer = wx.BoxSizer(wx.HORIZONTAL)
        tfont  = self.GetFont() # .Bold()
        tfont.PointSize += 1
        tfont.SetWeight(wx.BOLD)

        topsizer.Add(SimpleText(toprow, inst.name,
                                font=tfont, colour=wx.BLUE,
                                minsize=(150,-1),
                                style=wx.ALIGN_LEFT), 1,
                     wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 2)

        topsizer.Add(SimpleText(toprow, 'Save Current Position:',
                                style=wx.ALIGN_RIGHT), 0,
                     wx.ALIGN_CENTER_VERTICAL|wx.ALL, 2)

        topsizer.Add(self.pos_name, 1,
                     wx.ALIGN_CENTER_VERTICAL|wx.GROW|wx.ALL, 2)

        pack(toprow, topsizer)

        lsizer = wx.BoxSizer(wx.VERTICAL)
        lsizer.Add(toprow, 0,  wx.ALIGN_LEFT|wx.TOP, 1)

        for x in inst.pvs:
            lsizer.Add(wx.StaticText(lpanel, label='pv: %s' % x,
                                     size=(220,-1)), 1, wx.GROW|wx.EXPAND|wx.ALL, 2)

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
        print 'Inst Positions: ', inst, inst.positions
        for pos in inst.positions:
            self.pos_list.Append(pos.name)

        
        rsizer.Add(brow,          0, wx.ALIGN_LEFT|wx.ALL)
        rsizer.Add(self.pos_list, 1, wx.ALL|wx.EXPAND|wx.ALIGN_CENTER, 1)
        pack(rpanel, rsizer)
            
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(lpanel, 0, wx.ALIGN_LEFT|wx.GROW|wx.ALL, 1)
        sizer.Add(rpanel, 1, wx.ALIGN_RIGHT|wx.GROW|wx.ALL, 1)
        pack(self, sizer)

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
                          size=(450, 550), **kwds)

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
        self.Bind(fnb.EVT_FLATNOTEBOOK_PAGE_DROPPED, self.onDrop)

        mainsizer = wx.BoxSizer(wx.VERTICAL)
        mainsizer.Add(self.nb, 1, wx.EXPAND)

        self.Freeze()
        for inst in self.db.get_all_instruments():
            self.nb.AddPage(InstrumentPanel(self, inst), inst.name, True)
        self.Thaw()
            
        pack(self, mainsizer)
        mainsizer.Layout()
        self.Refresh()
        self.SendSizeEvent()
        
    def create_Menus(self):
        """create menus"""
        mbar = wx.MenuBar()
        file_menu = wx.Menu()
        opts_menu = wx.Menu()
        help_menu = wx.Menu()

        add_menu(self, file_menu, "&Open", "Open Instruments File")
        add_menu(self, file_menu, "&Save", "Save Instruments File")        
        file_menu.AppendSeparator()
        add_menu(self, file_menu, "E&xit", "Terminate the program",
                 action=self.onClose)

        add_menu(self, opts_menu, "&Instruments","Add Instrument")

        add_menu(self, help_menu, '&About',
                 "More information about this program", action=self.onAbout)

        mbar.Append(file_menu, "&File")
        mbar.Append(opts_menu, "&Options")
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

    def onAbout(self, event):
        print 'Pages: ', [self.nb.GetPage(i).inst for i in range(self.nb.GetPageCount())]

        # First we create and fill the info object
        info = wx.AboutDialogInfo()
        info.Name = "Epics Instruments"
        info.Version = "0.1"
        info.Copyright = "2011, Matt Newville, University of Chicago"
        info.Description = """'Epics Instruments' is an application to save and restore Instrument Positions.  Here,an Instrument is defined as a collection of Epics Process Variable and a Position is defined as any named set of values for those Process Variables"""
        wx.AboutBox(info)


    def onDrop(self, event=None):
        print 'onDrop ', event.GetString(), event.GetSelection(), event.GetOldSelection()
        print event.GetClientData(), event.GetClientObject(), event.GetId()
        print dir(event)
        
    def onClose(self, event):
        finalize_epics()
        self.Destroy()

if __name__ == '__main__':
    dbname = 'Test.einst'
    conf = 'test.conf'
    if len(sys.argv)>1:
        motors = sys.argv[1:]
    
    app = wx.App(redirect=False)
    InstrumentFrame(conf=conf, dbname=dbname).Show()
    
    app.MainLoop()


