#!/usr/bin/python

import wx
from wx._core import PyDeadObjectError

import time
from threading import Thread

import epics
from epics.wx import (EpicsFunction, PVText, PVFloatCtrl, PVTextCtrl, PVEnumChoice, MotorPanel)
from epicscollect.gui import  pack, popup, add_button, SimpleText

from utils import ALL_EXP , GUIColors, get_pvtypes

class MoveToDialog(wx.Dialog):
    """Full Query for Move To for a Position"""
    msg = '''Select Recent Instrument File, create a new one'''
    def __init__(self, parent, posname, inst, db, pvs, pvdesc=None, **kws):
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
        wx.Dialog.__init__(self, parent, wx.ID_ANY, title=title)
        panel = wx.Panel(self)
        colors = GUIColors()

        self.SetFont(parent.GetFont())
        titlefont  = self.GetFont()
        titlefont.PointSize += 2
        titlefont.SetWeight(wx.BOLD)

        panel.SetBackgroundColour(colors.bg)
        sizer = wx.GridBagSizer(10, 4)

        labstyle  = wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL|wx.ALL
        rlabstyle = wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL|wx.ALL
        tstyle    = wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL
        # title row
        i = 0
        for titleword in ('  PV', 'Current Value',
                          'Saved Value', 'Move?'):
            txt =SimpleText(panel, titleword,
                            font=titlefont,
                            minsize=(80, -1),
                            colour=colors.title,
                            style=tstyle)

            sizer.Add(txt, (0, i), (1, 1), labstyle, 1)
            i = i + 1

        sizer.Add(wx.StaticLine(panel, size=(150, -1),
                                style=wx.LI_HORIZONTAL),
                  (1, 0), (1, 4), wx.ALIGN_CENTER|wx.GROW|wx.ALL, 0)

        self.checkboxes = {}
        for irow, pvpos in enumerate(thispos.pvs):
            pvname = desc = pvpos.pv.name
            curr_val = self.pvs[pvname].get(as_string=True)
            if curr_val is None:
                curr_val = 'Unknown'
            save_val = pvpos.value

            if pvname in pvdesc:
                desc = "%s (%s)" % (pvdesc[pvname], pvname)

            label = SimpleText(panel, desc, style=tstyle,
                               colour=colors.pvname)
            curr  = SimpleText(panel, curr_val, style=tstyle)
            saved = SimpleText(panel, save_val, style=tstyle)
            cbox  = wx.CheckBox(panel, -1, "Move")
            cbox.SetValue(True)
            self.checkboxes[pvname] = (cbox, save_val)

            sizer.Add(label, (irow+2, 0), (1, 1), labstyle,  2)
            sizer.Add(curr,  (irow+2, 1), (1, 1), rlabstyle, 2)
            sizer.Add(saved, (irow+2, 2), (1, 1), rlabstyle, 2)
            sizer.Add(cbox,  (irow+2, 3), (1, 1), rlabstyle, 2)

        sizer.Add(wx.StaticLine(panel, size=(150, -1),
                                style=wx.LI_HORIZONTAL),
                  (irow+3, 0), (1, 4), wx.ALIGN_CENTER|wx.GROW|wx.ALL, 0)

        btnsizer = wx.StdDialogButtonSizer()
        btn = wx.Button(panel, wx.ID_OK)
        btn.SetDefault()
        btnsizer.AddButton(btn)
        btnsizer.AddButton(wx.Button(panel, wx.ID_CANCEL))

        btnsizer.Realize()
        sizer.Add(btnsizer, (irow+4, 2), (1, 2),
                  wx.ALIGN_CENTER_VERTICAL|wx.ALL, 1)
        pack(panel, sizer)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(panel, 0, 0, 0)
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
        self.pv_components  = []
        wx.Panel.__init__(self, parent, size=size)

        colors = GUIColors()
        self.parent = parent
        self.SetFont(parent.GetFont())
        titlefont  = self.GetFont()
        titlefont.PointSize += 2
        titlefont.SetWeight(wx.BOLD)

        splitter = wx.SplitterWindow(self, -1,
                                     style=wx.SP_3D|wx.SP_BORDER|wx.SP_LIVE_UPDATE)

        lpanel = wx.Panel(splitter, style=wx.BORDER_SUNKEN, size=(-1, 175))
        rpanel = wx.Panel(splitter, style=wx.BORDER_SUNKEN, size=(-1, 175))

        splitter.SetMinimumPaneSize(150)

        toprow = wx.Panel(lpanel)
        self.pos_name =  wx.TextCtrl(toprow, value="", size=(250, 25),
                                     style= wx.TE_PROCESS_ENTER)
        self.pos_name.Bind(wx.EVT_TEXT_ENTER, self.onSavePosition)


        topsizer = wx.BoxSizer(wx.HORIZONTAL)
        topsizer.Add(SimpleText(toprow, '  %s  ' % inst.name,
                                font=titlefont,
                                colour=colors.title,
                                minsize=(125, -1),
                                style=wx.ALIGN_LEFT|wx.ALIGN_BOTTOM),
                     0, wx.ALIGN_CENTER|wx.ALIGN_CENTER_VERTICAL, 2)

        topsizer.Add(SimpleText(toprow, 'Save Current Position:',
                                minsize=(125, -1),
                                style=wx.ALIGN_RIGHT), 1,
                     wx.ALIGN_CENTER_VERTICAL|wx.ALL, 1)

        topsizer.Add(self.pos_name, 0,
                     wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, 1)

        pack(toprow, topsizer)
        self.toprow = toprow
        lsizer = wx.BoxSizer(wx.VERTICAL)

        # start a timer to check for when to fill in PV panels
        timer_id = wx.NewId()
        self.etimer = wx.Timer(self)
        self.puttimer = wx.Timer(self)
        self.etimer_count = 0
        self.etimer_poll = 50

        self.Bind(wx.EVT_TIMER, self.OnConnectTimer, self.etimer)
        self.Bind(wx.EVT_TIMER, self.OnPutTimer, self.puttimer)

        self.leftpanel = lpanel
        self.leftsizer = lsizer

        for ordered_pvs in self.db.get_ordered_instpvs(inst):
            self.add_pv(ordered_pvs.pv.name)

        rsizer = wx.BoxSizer(wx.VERTICAL)
        btn_goto = add_button(rpanel, "Go To",  size=(70, -1),
                              action=self.OnMove)
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


        splitter.SplitVertically(lpanel, rpanel, -1)

        lpanel.SetMinSize((625, 150))
        rpanel.SetMinSize((150, -1))

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(splitter, 1, wx.GROW|wx.ALL, 0)
        pack(self, sizer)

    def undisplay_pv(self, pvname):
        "remove pv from display"
        thisentry = None
        for entry in self.pv_components:
            if entry[0] == pvname:
                thisentry = entry
                break
        if thisentry is not None:
            self.pv_components.remove(thisentry)
            self.redraw_leftpanel()

    def redraw_leftpanel(self, announce=False):
        """ redraws the left panel """
        self.Freeze()
        self.Hide()
        self.leftsizer.Clear()
        self.leftsizer.Add(self.toprow, 0,  wx.GROW|wx.ALIGN_LEFT|wx.TOP, 1)

        current_comps = [self.toprow]
        for pvname, connected, wid in self.pv_components:
            self.leftsizer.Add(wid, 1, wx.TOP|wx.ALL|wx.GROW, 2)
            current_comps.append(wid)
        pack(self.leftpanel, self.leftsizer)

        for wid in self.leftpanel.Children:
            if wid not in current_comps and wid != self.toprow:
                try:
                    time.sleep(0.010)
                    wid.Destroy()
                except PyDeadObjectError:
                    pass

        self.Refresh()
        self.Layout()
        self.Thaw()
        self.Show()
        if announce:
            print 'Redraw Left Panel: %i components ' % (len(self.leftpanel.Children))

    def add_pv(self, pvname):
        """add a PV to the left panel"""
        wid = wx.StaticText(self.leftpanel,
                            label="Waiting for Connection for '%s'" % pvname)
        self.pv_components.append([pvname, False, wid])

        time.sleep(0.010)
        if not self.etimer.IsRunning():
            self.etimer.Start(self.etimer_poll)

    def write(self, msg, status='normal'):
        if self.write_message is None:
            return
        self.write_message(msg, status=status)

    def OnPutTimer(self, evt=None):
        """Timer Event for GoTo to look if move is complete."""
        if self.db.restore_complete():
            self.puttimer.Stop()
            # print 'would do inst post commands now!'

    def OnConnectTimer(self, evt=None):
        """Timer Event: look for uncompleted PV panels
        and try to create them ...
        """
        if all([comp[1] for comp in self.pv_components]): # "all connected"
            self.etimer.Stop()

        for component in self.pv_components:
            pvname, cnx, wid = component
            self.PV_Panel(pvname)

        # if we've done 20 rounds, there are probably
        # really unconnected PVs -- let's slow down.
        self.etimer_count += 1
        if self.etimer_count > 20:
            self.etimer.Stop()
            self.etimer_count = 0
            self.etimer_poll *=  2
            self.etimer_poll = min(self.etimer_poll, 5000)
            self.etimer.Start(self.etimer_poll)

    @EpicsFunction
    def PV_Panel(self, pvname): # , panel, sizer, current_wid=None):
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

        thiscomp = None
        for comp in self.pv_components:
            if comp[0] == pvname:
                comp[1] = True
                thiscomp = comp
                break
        if thiscomp is None:
            print("wait, can't find component for ", pnvame)
            return

        pv.get_ctrlvars()
        colors = GUIColors()
        pvtype = None
        db_pv = self.db.get_pv(pvname)
        try:
            pvtype = str(db_pv.pvtype.name)
        except AttributeError:
            pass

        if pvtype is None:
            pvtype  = get_pvtypes(pv)[0]

        self.db.set_pvtype(pvname, pvtype)

        panel = wx.Panel(self.leftpanel)
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        if pvtype == 'motor':
            sizer.Add(MotorPanel(panel, pvname, midsize=True),
                      1, wx.ALIGN_CENTER_VERTICAL|wx.ALL|wx.GROW, 0)
        else:

            label = SimpleText(panel, pvname,
                               colour=colors.pvname,
                               minsize=(125,-1),
                               style=wx.ALIGN_LEFT)
            if pvtype == 'enum':
                control = PVEnumChoice(panel, pv=pv, size=(250, -1))
            elif pvtype in ('string', 'unicode'):
                control = PTextCtrl(panel, pv=pv, size=(250, -1))
            else:
                control = PVFloatCtrl(panel, pv=pv, size=(250, -1))

            sizer.Add(label,   0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 2)
            sizer.Add(control, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 2)
        pack(panel, sizer)
        thiscomp[2] = panel
        self.redraw_leftpanel()


    @EpicsFunction
    def save_current_position(self, posname):
        values = {}
        for pv in self.pvs.values():
            values[pv.pvname] = pv.get(as_string=True)
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
    def restore_position(self, posname, exclude_pvs=None, timeout=60.0):
        self.db.restore_position(posname, self.inst,
                                 exclude_pvs=exclude_pvs)
        msg= "Moving to '%s' to position '%s'" % (self.inst.name, posname)
        if exclude_pvs is not None and len(exclude_pvs) > 0:
            msg = "%s (Partial: %i PVs not restored)" % (msg, len(exclude_pvs))
        self.write(msg)
        self.puttimer.Start(50)

    def OnMove(self, evt=None):
        """ on GoTo """
        posname = self.pos_list.GetStringSelection()
        thispos = self.db.get_position(posname, self.inst)
        if thispos is None:
            return

        verify = int(self.db.get_info('verify_move'))
        if verify == 0:
            self.restore_position(posname)
        elif verify == 1:
            dlg = MoveToDialog(self, posname, self.inst, self.db,
                               self.pvs, pvdesc=self.pvdesc)
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


