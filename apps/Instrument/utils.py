import wx
import wx.lib.filebrowsebutton as filebrowse

import time
import epics
from epics.wx import EpicsFunction, pvText, pvFloatCtrl, pvTextCtrl, pvEnumChoice

from epicscollect.gui import  pack, popup, add_button, SimpleText

from MotorPanel import MotorPanel

FileBrowser = filebrowse.FileBrowseButtonWithHistory

ALL_EXP  = wx.ALL|wx.EXPAND


class GUIParams(object):
    def __init__(self, parent):
        class empty:
            pass
        self.colors = empty()
        self.colors.bg = wx.Colour(240,240,230)
        self.colors.nb_active = wx.Colour(254,254,195)
        self.colors.nb_area   = wx.Colour(250,250,245)
        self.colors.nb_text = wx.Colour(10,10,180)
        self.colors.nb_activetext = wx.Colour(80,10,10)
        self.colors.title  = wx.Colour(80,10,10)
        self.colors.pvname = wx.Colour(10,10,80)

        self.font       = parent.GetFont()
        self.titlefont  = parent.GetFont()
        self.titlefont.PointSize += 2
        self.titlefont.SetWeight(wx.BOLD)


class HideShow(wx.Choice):
    def __init__(self, parent, default=True, size=(100, -1)):
        wx.Choice.__init__(self, parent, -1, size=size)
        self.choices = ('Hide', 'Show')
        self.Clear()
        self.SetItems(self.choices)
        self.SetSelection({False:0, True:1}[default])

class YesNo(wx.Choice):
    def __init__(self, parent, defaultyes=True, size=(75, -1)):
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

class ConnectDialog(wx.Dialog):
    """Connect to a recent or existing DB File, or create a new one"""
    msg = '''Select Recent Instrument File, create a new one'''
    def __init__(self, parent=None, filelist=None,
                 title='Select Instruments File'):

        wx.Dialog.__init__(self, parent, wx.ID_ANY, title=title)

        panel = wx.Panel(self)
        self.guiparams = GUIParams(self)
        panel.SetBackgroundColour(self.guiparams.colors.bg)
        self.filebrowser = FileBrowser(panel, size=(450, -1))
        self.filebrowser.SetHistory(filelist)
        self.filebrowser.SetLabel('File:')
        

        if filelist is not None:
            self.filebrowser.SetValue(filelist[0])
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(wx.StaticText(panel, label=self.msg),
                  0, wx.ALIGN_CENTER|wx.ALL|wx.GROW, 1)
        sizer.Add(self.filebrowser, 1, wx.ALIGN_CENTER|wx.ALL|wx.GROW, 1)
        sizer.Add(self.CreateButtonSizer(wx.OK| wx.CANCEL),
                 1, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 1)
        pack(panel, sizer)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(panel, 0, 0, 0)
        pack(self, sizer)
        
class MoveToDialog(wx.Dialog):
    """Full Query for Move To for a Position"""
    msg = '''Select Recent Instrument File, create a new one'''
    def __init__(self,  posname, inst, db, pvs, pvdesc=None, **kws):

        self.posname = posname
        self.inst = inst
        self.db   = inst
        self.pvs  = pvs
        if pvdesc is None:
            pvdesc = {}
        
        thispos = db.get_position(posname, inst)
        if thispos is None:
            return
        
        title = "Move Instrument %s to Position '%s'?" % (inst.name, posname)
        wx.Dialog.__init__(self, None, wx.ID_ANY, title=title)
        panel = wx.Panel(self)
        self.guiparams = GUIParams(self)
        colors = self.guiparams.colors
        panel.SetBackgroundColour(self.guiparams.colors.bg)
        sizer = wx.GridBagSizer(10, 4)

        labstyle  = wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL|wx.ALL
        rlabstyle = wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL|wx.ALL
        tstyle    = wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL
        # title row
        i = 0
        for titleword in ('  PV', 'Current Value',
                          'Saved Value', 'Move?'):
            txt =SimpleText(self, titleword,
                            font=self.guiparams.titlefont,
                            minsize=(80, -1), 
                            colour=colors.title, 
                            style=tstyle)
            
            sizer.Add(txt, (0, i), (1, 1), labstyle, 1)
            i = i + 1

        sizer.Add(wx.StaticLine(self, size=(150, -1),
                                style=wx.LI_HORIZONTAL),
                  (1, 0), (1, 4), wx.ALIGN_CENTER|wx.GROW|wx.ALL, 0)

        self.checkboxes = {}
        for irow, pvpos in enumerate(thispos.pvs):
            pvname = desc = pvpos.pv.name
            curr_val = self.pvs[pvname].get(as_string=True)
            save_val = pvpos.value

            if pvname in pvdesc:
                desc = "%s (%s)" % (pvdesc[pvname], pvname)
            
            label = SimpleText(self, desc, style=tstyle,
                               colour=colors.pvname)
            curr  = SimpleText(self, curr_val, style=tstyle)
            saved = SimpleText(self, save_val, style=tstyle)
            cbox  = wx.CheckBox(self, -1, "Move")
            cbox.SetValue(True)
            self.checkboxes[pvname] = (cbox, save_val)

            sizer.Add(label, (irow+2, 0), (1, 1), labstyle,  2)
            sizer.Add(curr,  (irow+2, 1), (1, 1), rlabstyle, 2)
            sizer.Add(saved, (irow+2, 2), (1, 1), rlabstyle, 2)
            sizer.Add(cbox,  (irow+2, 3), (1, 1), rlabstyle, 2)

        sizer.Add(wx.StaticLine(self, size=(150, -1),
                                style=wx.LI_HORIZONTAL),
                  (irow+3, 0), (1, 4), wx.ALIGN_CENTER|wx.GROW|wx.ALL, 0)

        btnsizer = wx.StdDialogButtonSizer()
        btn = wx.Button(self, wx.ID_OK)
        btn.SetDefault()
        btnsizer.AddButton(btn)
        btnsizer.AddButton(wx.Button(self, wx.ID_CANCEL))

        btnsizer.Realize()
        sizer.Add(btnsizer, (irow+4, 2), (1, 2), wx.ALIGN_CENTER_VERTICAL|wx.ALL, 1)
        pack(self, sizer)

class InstrumentPanel(wx.Panel):
    """ create Panel for an instrument"""

    def __init__(self, parent, inst, db=None, writer=None,
                 size=(-1, -1)):
        self.inst = inst
        self.db   = db
        self.write_message = writer
        self.pvs  = {}
        self.pvdesc = {}
        wx.Panel.__init__(self, parent, size=size)

        self.guiparams = GUIParams(self)
        colors = self.guiparams.colors

        splitter = wx.SplitterWindow(self,
                                     style=wx.SP_3DSASH|wx.SP_LIVE_UPDATE)
        splitter.SetMinimumPaneSize(150)
       
        lpanel = wx.Panel(splitter, size=(550, 175))
        rpanel = wx.Panel(splitter, size=(150, 175))
        
        toprow = wx.Panel(lpanel, size=(425,-1))
        self.pos_name =  wx.TextCtrl(toprow, value="", size=(220, 25),
                                     style= wx.TE_PROCESS_ENTER)
        self.pos_name.Bind(wx.EVT_TEXT_ENTER, self.onSavePosition)


        topsizer = wx.BoxSizer(wx.HORIZONTAL)
        topsizer.Add(SimpleText(toprow, inst.name,
                                font=self.guiparams.titlefont,
                                colour=colors.title,
                                minsize=(125, -1),
                                style=wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL),
                     0, wx.ALIGN_LEFT, 1)

        topsizer.Add(SimpleText(toprow, 'Save Current Position:',
                                style=wx.ALIGN_RIGHT), 1,
                     wx.ALIGN_CENTER_VERTICAL|wx.ALL, 1)

        topsizer.Add(self.pos_name, 1,
                     wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL|wx.GROW|wx.ALL, 1)

        pack(toprow, topsizer)

        lsizer = wx.BoxSizer(wx.VERTICAL)
        lsizer.Add(toprow, 0,  wx.GROW|wx.ALIGN_LEFT|wx.TOP, 1)

        # start a timer to check for when to fill in PV panels
        self.pvpanels = {}
        timer_id = wx.NewId()
        self.etimer = wx.Timer(self)
        self.etimer_count = 0
        self.Bind(wx.EVT_TIMER, self.onTimer, self.etimer)

        for x in inst.pvs:
            ppanel = wx.Panel(lpanel, size=(425, -1))
            psizer = wx.BoxSizer(wx.HORIZONTAL)
            init_msg = wx.StaticText(ppanel,
                                     label='Connecting %s' % x.name)
            
            self.pvpanels[x.name] = (ppanel, psizer, init_msg)
            
            psizer.Add(init_msg, 0, wx.ALL|wx.ALIGN_CENTER, 1)
            pack(ppanel, psizer)
            lsizer.Add(ppanel, 1, wx.TOP|wx.ALL, 2)

        time.sleep(0.010)
        pack(lpanel, lsizer)
        self.etimer.Start(100)

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
        self.pos_list.Bind(wx.EVT_RIGHT_DOWN, self.onRightClick)

        self.pos_list.Clear()
        for pos in inst.positions:
            self.pos_list.Append(pos.name)

        rsizer.Add(brow,          0, wx.ALIGN_LEFT|wx.ALL)
        rsizer.Add(self.pos_list, 1, wx.EXPAND|wx.ALIGN_CENTER, 1)
        pack(rpanel, rsizer)

        splitter.SplitVertically(lpanel, rpanel, 1)
        lpanel.SetMinSize((350, 150))
        rpanel.SetMaxSize((500, -1))
        rpanel.SetMinSize((100, -1))

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(splitter, 1, wx.GROW|wx.ALL, 0)
        # wx.ALIGN_LEFT|wx.GROW|wx.ALL, 3)
        pack(self, sizer)

    def write(self, msg, status='normal'):
        if self.write_message is None:
            return
        self.write_message(msg, status=status)
        
    def onTimer(self, evt=None):
        """Timer Event: look for uncompleted PV panels
        and try to create them ...
        """
        self.etimer_count += 1
        if len(self.pvpanels) == 0:
            self.etimer.Stop()
        for pvname in self.pvpanels:
            pnl, szr, wid = self.pvpanels[pvname]
            self.PV_Panel(pvname, pnl, szr, wid)
        # if we've done 100 rounds, there are probably
        # really unconnected PVs -- let's slow down.
        if self.etimer_count > 100:
            self.etimer.Stop()
            self.etimer.Start(5000)
            
    @EpicsFunction
    def PV_Panel(self, pvname, panel, sizer, current_wid=None):
        """ try to create a PV Panel for the given pv
        returns quickly for an unconnected PV, to be tried later
        by the timer"""
        if pvname not in self.pvs:
            pv = epics.PV(pvname)
            self.pvs[pvname] = pv
        else:
            pv = self.pvs[pvname]
            
        # return if not connected
        if pv.connected == False:
            return

        if current_wid is not None:
            current_wid.Destroy()
            sizer.Clear()

        self.pvpanels.pop(pvname)
        pv.get_ctrlvars()

        instrument_pvs = [i.name for i in self.inst.pvs]
        # check if pv is a motor
        pref = pvname
        if '.' in pvname:
            pref, suff = pvname.split('.')
        desc  = epics.caget("%s.DESC" % pref)
        if desc is not None:
            self.pvdesc[pvname] = desc
        dtype = epics.caget("%s.RTYP" % pref)
        if dtype.lower() == 'motor':
            self.db.set_pvtype(pvname, 'motor')
            sizer.Add(MotorPanel(panel, pvname, size=(450, 25)), 1,
                      wx.ALIGN_CENTER_VERTICAL|wx.ALL, 2)
            pack(panel, sizer)
            return

        label = SimpleText(panel, pvname,
                           colour=self.guiparams.colors.pvname,
                           minsize=(100,-1),style=wx.ALIGN_LEFT)

        if pv.type in ('double', 'int', 'long', 'short'):
            control = pvFloatCtrl(panel, pv=pv)
            self.db.set_pvtype(pvname, 'numeric')
        elif pv.type in ('string', 'unicode'):
            control = pvTextCtrl(panel, pv=pv)
            self.db.set_pvtype(pvname, 'string')
        elif pv.type == 'enum': 
            self.db.set_pvtype(pvname, 'enum')
            control = pvEnumChoice(panel, pv=pv)

        sizer.Add(label,   0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 2)
        sizer.Add(control, 1, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 2)
        pack(panel, sizer)
        sizer.Layout()
        return
        
    @EpicsFunction
    def save_current_position(self, posname):
        values = {}
        for p in self.pvs:
            values[p.pvname] = p.get(as_string=True)
        self.db.save_position(posname, self.inst, values)
        self.write("Saved position '%s' for '%s'" % (posname, self.inst.name))
        
    def onSavePosition(self, evt=None):
        posname = evt.GetString()
        verify = int(self.db.get_info('verify_overwrite'))
        if verify and posname in self.pos_list.GetItems():

            thispos = self.db.get_position(posname, self.inst)
            postext = ["\nSaved Values were:\n"]
            for pvpos in thispos.pvs:
                postext.append('  %s= %s' % (pvpos.pv.name, pvpos.value))
            postext = '\n'.join(postext)

            ret = popup(self, "Overwrite %s?: \n%s" % (posname, postext),
                        'Verify Overwrite',
                        style=wx.YES_NO|wx.ICON_QUESTION)
            if ret != wx.ID_YES:
                return

        self.save_current_position(posname)
        if posname not in self.pos_list.GetItems():
            self.pos_list.Append(posname)

    @EpicsFunction
    def restore_position(self, posname, exclude_pvs=None, timeout=5.0):
        self.db.restore_position(posname, self.inst,
                                 wait=True, timeout=timeout,
                                 exclude_pvs=exclude_pvs)

        msg= "Moved '%s' to position '%s'" % (self.inst.name, posname)
        if exclude_pvs is not None and len(exclude_pvs) > 0:
            msg = "%s (Partial: %i PVs not restored)" % (msg, len(exclude_pvs))
        self.write(msg)
        
    def onGo(self, evt=None):
        """ on GoTo"""
        posname = self.pos_list.GetStringSelection()
        thispos = self.db.get_position(posname, self.inst)
        if thispos is None:
            return

        verify = int(self.db.get_info('verify_move'))
        if verify == 0:
            self.restore_position(posname)
        elif verify == 1:
            dlg = MoveToDialog(posname, self.inst, self.db, self.pvs,
                               pvdesc=self.pvdesc)
            dlg.Raise()
            if dlg.ShowModal() == wx.ID_OK:
                exclude_pvs = []
                for pvname, data, in dlg.checkboxes.items():
                    if not data[0].IsChecked():
                        exclude_pvs.append(pvname)
                self.restore_position(posname, exclude_pvs=exclude_pvs)
            else:
                return
            dlg.Destroy()
        
    def onRightClick(self, evt=None):
        menu = wx.Menu()
        if not hasattr(self, 'popup_up1'):
            for item in ('popup_up1', 'popup_dn1',
                         'popup_upall', 'popup_dnall',
                         'popup_rename'):
                setattr(self, item,  wx.NewId())
                self.Bind(wx.EVT_MENU, self.onPosRightEvent,
                          id=getattr(self, item))
            
        menu.Append(self.popup_up1, "Move up")
        menu.Append(self.popup_dn1, "Move down")
        menu.Append(self.popup_upall, "Move to top")
        menu.Append(self.popup_dnall, "Move to bottom")
        self.PopupMenu(menu)
        menu.Destroy()

    def onPosRightEvent(self, event=None, posname=None):
        idx = self.pos_list.GetSelection()
        if idx < 0: # no item selected
            return
        
        wid = event.GetId()
        namelist = self.pos_list.GetItems()
        if wid == self.popup_up1 and idx > 0:
            namelist.insert(idx-1, namelist.pop(idx))
        elif wid == self.popup_dn1 and idx < len(namelist):
            namelist.insert(idx+1, namelist.pop(idx))
        elif wid == self.popup_upall:
            namelist.insert(0, namelist.pop(idx))            
        elif wid == self.popup_dnall:
            namelist.append( namelist.pop(idx))

        self.pos_list.Clear()
        for posname in namelist:
            self.pos_list.Append(posname)

    def onErase(self, evt=None):
        posname = self.pos_list.GetStringSelection()
        verify = int(self.db.get_info('verify_erase'))

        if verify:
            ret = popup(self, "Erase  %s?" % (posname),
                        'Verify Erase',
                        style=wx.YES_NO|wx.ICON_QUESTION)
            if ret != wx.ID_YES:
                return

        self.db.remove_position(posname, self.inst)
        ipos  =  self.pos_list.GetSelection()
        self.pos_list.Delete(ipos)
        self.write("Erased position '%s' for '%s'" % (posname, self.inst.name))
