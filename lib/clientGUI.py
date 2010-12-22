#!/usr/bin/env python

import os
import wx
import wx.lib.newevent
import time

import epics
from epics.wx import DelayedEpicsCallback
from datetime import timedelta
from wx_utils import FloatCtrl, SText, addtoMenu, EpicsFunction
from util import new_filename, increment_filename, nativepath

from configFile import FastMapConfig, conf_files, default_conf

from mapper import mapper
MAX_POINTS = 2048

from EscanWriter import EscanWriter
DataSaverEvent, EVT_SAVE_DATA = wx.lib.newevent.NewEvent()

SAVE_ESCAN = False
SAVE_ESCAN = True

def Connect_Motors():
    conf = FastMapConfig().config
    pvs = {}
    for pvname, label in conf['slow_positioners'].items():
        pvs[label] = epics.PV(pvname)
    for  pv in pvs.values():
        x = pv.get()
        pv.get_ctrlvars()
    return pvs

class SetupFrame(wx.Frame):
    def __init__(self, conf=None, **kwds):
        self.config = conf

        kwds["style"] = wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, None, -1, **kwds)

        self.Font10=wx.Font(10, wx.SWISS, wx.NORMAL, wx.BOLD, 0, "")

        self.SetTitle("Setup For Fast Maps")
        self.SetSize((850, 550))
        self.SetFont(self.Font10)

        fmenu = wx.Menu()
        addtoMenu(self,fmenu, "&Quit", "Quit Setup",  self.onClose)

        mbar = wx.MenuBar()
        mbar.Append(fmenu, "&File")
        self.SetMenuBar(mbar)
        self.buildPanel()

    def buildPanel(self):
        panel = wx.Panel(self, -1)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(panel, 1, 0,0)
        self.SetSizer(sizer)
        sizer.Fit(self)
        self.Layout()
        self.Show()
        self.Raise()

    def onClose(self,evt=None):
        self.Destroy()

class FastMapGUI(wx.Frame):
    _about = """ Fast Maps documentation is at
  http://cars.uchicago.edu/gsecars/software/PyDataCollection
  Matt Newville <newville @ cars.uchicago.edu>
  """
    _scantypes = ('Line Scan', 'Map')
    _cnf_wildcard = "Scan Definition Files(*.cnf)|*.cnf|All files (*.*)|*.*"

    def __init__(self, configfile=None, motorpvs=None,  **kwds):

        kwds["style"] = wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, None, -1, **kwds)

        self.Font16=wx.Font(16, wx.SWISS, wx.NORMAL, wx.BOLD, 0, "")
        self.Font10=wx.Font(10, wx.SWISS, wx.NORMAL, wx.BOLD, 0, "")

        self.SetTitle("X-ray Microprobe Fast Maps")
        self.SetSize((850, 475))
        self.SetFont(self.Font10)
        self.statusbar = self.CreateStatusBar(2, 0)
        self.statusbar.SetStatusWidths([-4, -1])

        self.createMenus()
        self.buildFrame()
        self.ReadyForSave = False
        
        statusbar_fields = ["Messages", "Status"]
        for i in range(len(statusbar_fields)):
            self.statusbar.SetStatusText(statusbar_fields[i], i)

        self.dimchoice.Clear()
        self.dimchoice.AppendItems(self._scantypes)
        self.dimchoice.SetSelection(1)
        self.m1time.SetAction(self.onM1time)
        self.m1start.SetAction(self.onM1step)
        self.m1stop.SetAction(self.onM1step)
        self.m1step.SetAction(self.onM1step)
        self.m2start.SetAction(self.onM2step)        
        self.m2stop.SetAction(self.onM2step)        
        self.m2step.SetAction(self.onM2step)

        self.mapconf = None
        self._pvs = motorpvs
        self.start_time = time.time() - 100.0
        self.configfile = configfile
        self.ReadConfigFile()
        
    def buildFrame(self):
        pane = wx.Panel(self, -1)

        self.dimchoice = wx.Choice(pane, size=(120,30))
        self.m1choice = wx.Choice(pane,  size=(120,30))
        self.m1units  = SText(pane, "",minsize=(50,20))
        self.m1start  = FloatCtrl(pane, precision=4,value=0)
        self.m1stop   = FloatCtrl(pane, precision=4,value=1)
        self.m1step   = FloatCtrl(pane, precision=4,value=0.1)

        self.m1npts   = SText(pane, "0",minsize=(55,20))
        self.m1time   = FloatCtrl(pane, precision=1,value=10.,min=0.)

        self.m2choice = wx.Choice(pane, size=(120,30),choices=[])
        self.m2units  = SText(pane, "",minsize=(50,20))
        self.m2start  = FloatCtrl(pane, precision=4,value=0)
        self.m2stop   = FloatCtrl(pane, precision=4,value=1)
        self.m2step   = FloatCtrl(pane, precision=4,value=0.1)
        self.m2npts   = SText(pane, "0",minsize=(60,20))
        
        self.maptime  = SText(pane, "0")
        self.pixtime  = SText(pane, "0")

        self.filename = wx.TextCtrl(pane, -1, "")
        self.filename.SetMinSize((350, 25))
        
        self.usertitles = wx.TextCtrl(pane, -1, "",
                                      style=wx.TE_MULTILINE)
        self.usertitles.SetMinSize((350, 75))        
        self.startbutton = wx.Button(pane, -1, "Start")
        self.abortbutton = wx.Button(pane, -1, "Abort")

        self.startbutton.Bind(wx.EVT_BUTTON, self.onStartScan)
        self.abortbutton.Bind(wx.EVT_BUTTON, self.onAbortScan)

        self.m1choice.Bind(wx.EVT_CHOICE, self.onM1Select)
        self.m2choice.Bind(wx.EVT_CHOICE, self.onM2Select)
        self.dimchoice.Bind(wx.EVT_CHOICE, self.onDimension)

        # ties DataSaverEvent to run SaveEscanData
        # self.Bind(EVT_SAVE_DATA, self.SaveEscanData)


        self.m1choice.SetBackgroundColour(wx.Colour(255, 255, 255))
        self.m2choice.SetBackgroundColour(wx.Colour(255, 255, 255))
        self.abortbutton.SetBackgroundColour(wx.Colour(255, 72, 31))

        gs = wx.GridBagSizer(8, 8)
        all_cvert = wx.ALL|wx.ALIGN_CENTER_VERTICAL
        all_bot   = wx.ALL|wx.ALIGN_BOTTOM|wx.ALIGN_CENTER_HORIZONTAL
        all_cen   = wx.ALL|wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL

        # Title row
        nr = 0
        gs.Add(SText(pane, "XRF Map Setup",
                     minsize=(200, 30),
                     font=self.Font16, colour=(120,0,0)), 
               (nr,0), (1,4),all_cen)
        gs.Add(SText(pane, "Scan Type",
                     minsize=(80,20),style=wx.ALIGN_RIGHT),
               (nr,5), (1,1), all_cvert)
        gs.Add(self.dimchoice, (nr,6), (1,2),
               wx.ALIGN_LEFT)
        nr +=1
        gs.Add(wx.StaticLine(pane, size=(650,3)),
               (nr,0), (1,8),all_cen)
        # title
        nr +=1
        gs.Add(SText(pane, "Stage"),  (nr,1), (1,1), all_bot)
        gs.Add(SText(pane, "Units",minsize=(50,20)),  (nr,2), (1,1), all_bot)
        gs.Add(SText(pane, "Start"),  (nr,3), (1,1), all_bot)
        gs.Add(SText(pane, "Stop"),   (nr,4), (1,1), all_bot)
        gs.Add(SText(pane, "Step"),   (nr,5), (1,1), all_bot)
        gs.Add(SText(pane, "Npoints"),(nr,6), (1,1), all_bot)
        gs.Add(SText(pane, "Time for Line (s)",
                         minsize=(140,20)),(nr,7), (1,1), all_cvert|wx.ALIGN_LEFT)
        # fast motor row
        nr +=1
        gs.Add(SText(pane, "Fast Motor", minsize=(90,20)),
               (nr,0),(1,1), all_cvert )
        gs.Add(self.m1choice, (nr,1))
        gs.Add(self.m1units,  (nr,2))
        gs.Add(self.m1start,  (nr,3))
        gs.Add(self.m1stop,   (nr,4)) # 0, all_cen)
        gs.Add(self.m1step,   (nr,5))
        gs.Add(self.m1npts,   (nr,6),(1,1),wx.ALIGN_CENTER_HORIZONTAL)
        gs.Add(self.m1time,   (nr,7))

        # slow motor row
        nr +=1
        gs.Add(SText(pane, "Slow Motor", minsize=(90,20)),
               (nr,0),(1,1), all_cvert )
        gs.Add(self.m2choice, (nr,1))
        gs.Add(self.m2units,  (nr,2))        
        gs.Add(self.m2start,  (nr,3))
        gs.Add(self.m2stop,   (nr,4)) # 0, all_cen)
        gs.Add(self.m2step,   (nr,5))
        gs.Add(self.m2npts,   (nr,6),(1,1),wx.ALIGN_CENTER_HORIZONTAL)
        # 
        nr +=1
        gs.Add(wx.StaticLine(pane, size=(650,3)),(nr,0), (1,8),all_cen)

        # filename row 
        nr +=1
        gs.Add(SText(pane, "File Name", minsize=(90,20)), (nr,0))
        gs.Add(self.filename, (nr,1), (1,4))

        gs.Add(SText(pane, "Time per pixel:",
                     minsize=(160,20),style=wx.ALIGN_RIGHT),
               (nr,5), (1,2), wx.ALIGN_RIGHT)
        gs.Add(self.pixtime, (nr,7))

        # title row 
        nr +=1
        gs.Add(SText(pane, "Comments ",
                     minsize=(80,50)), (nr,0))
        gs.Add(self.usertitles,        (nr,1),(1,4))
        gs.Add(SText(pane, "Time for map:",
                         minsize=(160,20),style=wx.ALIGN_RIGHT),
               (nr,5), (1,2), wx.ALIGN_RIGHT)
        gs.Add(self.maptime, (nr,7))

        # button row 
        nr +=1        
        gs.Add(SText(pane, " ", minsize=(90,35)), (nr,0))
        gs.Add(self.startbutton, (nr,1))
        gs.Add(self.abortbutton, (nr,3))
        # 
        # nr +=1
        #gs.Add(wx.StaticLine(pane, size=(650,3)),(nr,0), (1,7),all_cen)

        pane.SetSizer(gs)


        MainSizer = wx.BoxSizer(wx.VERTICAL)
        MainSizer.Add(pane, 1, 0,0)
        self.SetSizer(MainSizer)
        MainSizer.SetSizeHints(self)
        MainSizer.Fit(self)
        self.Layout()

    def createMenus(self):
        self.menubar = wx.MenuBar()
        # file
        fmenu = wx.Menu()
        addtoMenu(self,fmenu, "&Read Scan File",
                  "Read Scan Parameter or Configuration File",
                  self.onReadConfigFile)
                    
        addtoMenu(self,fmenu,"&Save Scan File",
                  "Save Scan Parameters File", self.onSaveScanFile)
                    
        addtoMenu(self,fmenu, "Save Full Configuration",
                  "Save Configuration File", self.onSaveConfigFile)

        fmenu.AppendSeparator()
        addtoMenu(self,fmenu,'Change &Working Folder',
                  "Choose working directory",
                  self.onFolderSelect)
        fmenu.AppendSeparator()        
        addtoMenu(self,fmenu, "E&xit",
                  "Terminate the program", self.onClose)

        # options
        omenu = wx.Menu()
        addtoMenu(self,omenu, "&Options",
                  "Setup Motors, Detectors, other Options",
                  self.onSetup)
        # help
        hmenu = wx.Menu()
        addtoMenu(self,hmenu, "&About",
                  "More information about this program",  self.onAbout)

        self.menubar.Append(fmenu, "&File")
        self.menubar.Append(omenu, "Edit")
        self.menubar.Append(hmenu, "&Help")
        self.SetMenuBar(self.menubar)
        
    def onAbout(self,evt):
        dlg = wx.MessageDialog(self, self._about,"About Me",
                               wx.OK | wx.ICON_INFORMATION)
        dlg.ShowModal()
        dlg.Destroy()

    def onClose(self,evt):
        self.Destroy()

    def onSetup(self,evt=None):
        SetupFrame(self.config)
        
    @EpicsFunction
    def onFolderSelect(self,evt):
        style = wx.DD_DIR_MUST_EXIST|wx.DD_DEFAULT_STYLE
        
        dlg = wx.DirDialog(self, "Select Working Directory:", os.getcwd(),
                           style=style)

        if dlg.ShowModal() == wx.ID_OK:
            basedir = os.path.abspath(str(dlg.GetPath()))
            try:
                os.chdir(nativepath(basedir))
                self.mapper.basedir = basedir
            except OSError:
                pass
        dlg.Destroy()

    def onSaveScanFile(self,evt=None):
        self.onSaveConfigFile(evt=evt,scan_only=True)

    def onSaveConfigFile(self,evt=None,scan_only=False):
        fout=self.configfile
        if fout is None: fout = 'config.cnf'
        dlg = wx.FileDialog(self,
                            message="Save Scan Definition File",
                            defaultDir=os.getcwd(), 
                            defaultFile=fout, 
                            wildcard=self._cnf_wildcard,
                            style=wx.SAVE|wx.CHANGE_DIR)
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            self.SaveConfigFile(path,scan_only=scan_only)
        dlg.Destroy()
        
    def onReadConfigFile(self,evt=None):
        fname = self.configfile
        if fname is None: fname = ''
        dlg = wx.FileDialog(self, message="Read Scan Definition File",
                            defaultDir=os.getcwd(), 
                            defaultFile='',  wildcard=self._cnf_wildcard,
                            style=wx.OPEN | wx.CHANGE_DIR)
        if dlg.ShowModal() == wx.ID_OK:
            paths = dlg.GetPaths()
            self.ReadConfigFile(paths[0])
        dlg.Destroy()
 

    def SaveConfigFile(self,fname,scan_only=False):
        cnf = self.config
        dim = cnf['scan']['dimension'] = self.dimchoice.GetSelection() + 1

        cnf['general']['basedir']  = self.mapper.basedir
        cnf['general']['scandir']  = self.mapper.workdir

        cnf['scan']['filename']  = self.filename.GetValue()
        cnf['scan']['comments']  = self.usertitles.GetValue().replace('\n','\\n')

        fm_keys   = cnf['fast_positioners'].keys()
        cnf['scan']['pos1']   = fm_keys[self.m1choice.GetSelection()]
        cnf['scan']['start1'] = str(self.m1start.GetValue())
        cnf['scan']['stop1']  = str(self.m1stop.GetValue())
        cnf['scan']['step1']  = str(self.m1step.GetValue())
        cnf['scan']['time1']  = str(self.m1time.GetValue())        

        if dim > 1:
            sm_values = cnf['slow_positioners'].values()
            im2 = sm_values.index(self.m2choice.GetStringSelection())
            cnf['scan']['pos2'] = cnf['slow_positioners'].keys()[im2]
            cnf['scan']['start2'] = str(self.m2start.GetValue())
            cnf['scan']['stop2']  = str(self.m2stop.GetValue())
            cnf['scan']['step2']  = str(self.m2step.GetValue())
            
        self.mapconf.config = cnf
        save = self.mapconf.Save
        if scan_only:
            save = self.mapconf.SaveScanParams
        save(fname)
        
    def ReadConfigFile(self,filename=None):
        "read configuration file "
        if self.mapconf is None:
            self.mapconf = FastMapConfig(filename=filename)
        else:
            try:
                self.mapconf.Read(filename)
            except IOError:
                print "Cannot read %s" % fileanme
                return
        
        self.configfile = filename
        cnf = self.config = self.mapconf.config

        fm_labels = cnf['fast_positioners'].values()
        m1label   = cnf['fast_positioners'].get(cnf['scan']['pos1'],None)
        if m1label is None:  m1label = fm_labels[0]

        sm_labels = cnf['slow_positioners'].values()
        m2label   = cnf['slow_positioners'].get(cnf['scan']['pos2'],None)
        if m2label is None:  m2label = sm_labels[0]

        sm_labels.remove(m1label)

        self.m1choice.Clear()
        self.m1choice.AppendItems(fm_labels)
        self.m1choice.SetStringSelection(m1label)

        self.m2choice.Clear()
        self.m2choice.AppendItems(sm_labels)
        self.m2choice.SetStringSelection(m2label)

        self.dimchoice.Clear()
        self.dimchoice.AppendItems(self._scantypes)
        self.dimchoice.SetSelection(cnf['scan']['dimension']-1)

        self.m1start.SetValue(cnf['scan']['start1'])
        self.m1stop.SetValue(cnf['scan']['stop1'])
        self.m1step.SetValue(cnf['scan']['step1'])
        self.m1time.SetValue(cnf['scan']['time1'])

        self.m2start.SetValue(cnf['scan']['start2'])
        self.m2stop.SetValue(cnf['scan']['stop2'])
        self.m2step.SetValue(cnf['scan']['step2'])
        self.filename.SetValue(new_filename(cnf['scan']['filename']))

        self.connect_mapper()
        self.onM1step()
        self.onDimension()
        
    @EpicsFunction
    def connect_mapper(self):
        "setup epics callbacks for PVs from mapper "
        mapper_pv = self.config['general']['mapdb']
        self.mapper = mapper(mapper_pv)
        self.mapper.add_callback('Start',self.onMapStart)
        self.mapper.add_callback('Abort',self.onMapAbort)
        self.mapper.add_callback('message',self.onMapMessage)
        self.mapper.add_callback('info',self.onMapInfo)
        self.mapper.add_callback('nrow',self.onMapRow)
        if self._pvs is None:
            self._pvs = {}
            for pvname,label in self.config['slow_positioners'].items():
                self._pvs[label] = epics.PV(pvname)

        os.chdir(nativepath(self.mapper.basedir))
        self.SetMotorLimits()

    @EpicsFunction
    def SaveEscanData(self, **kw):
        """here we run the escan_saver.process() method,
        which looks for new lines to save to the escan data file"""
        if not SAVE_ESCAN:
            return
        new_lines = 0
        # print 'Save Escan Data ', self.data_fname
        if (time.time() - self.start_time < 5.0):
            return
        
        self.escan_saver.folder =self.mapper.workdir
        
        new_lines = self.escan_saver.process()

        if new_lines > 0:
            f = open(self.data_fname, self.data_mode)
            f.write("%s\n" % '\n'.join(self.escan_saver.buff))
            f.close()
            self.data_mode  = 'a'
            print 'Wrote %i lines to %s ' % (new_lines, self.data_fname)
        try:
            self.escan_saver.clear()
        except:
            pass
    
    @DelayedEpicsCallback
    def onMapRow(self,pvname=None,value=0,**kw):
        " the map row changed -- another row is finished"
        rowtime  = 0.5 + float(self.m1time.GetValue())
        nrows    = float(self.m2npts.GetLabel().strip())
        time_left = int(0.5+ rowtime * max(0, nrows - value))
        message = "Estimated Time remaining: %s" % timedelta(seconds=time_left)       
        self.statusbar.SetStatusText(message, 0)
        # note that we generate an event here so that
        # SaveEscanData will be called shortly
        # (we don't call it directly here because this
        # is still 'inside' an Epics callback
        if value > 0 and SAVE_ESCAN:
            self.SaveEscanData()
        
    @DelayedEpicsCallback
    def onMapInfo(self,pvname=None,char_value=None,**kw):
        self.statusbar.SetStatusText(char_value,1)
        
    @DelayedEpicsCallback
    def onMapMessage(self,pvname=None,char_value=None,**kw):
        self.statusbar.SetStatusText(char_value,0)
        
    @DelayedEpicsCallback
    def onMapStart(self,pvname=None,value=None,**kw):
        if value == 0: # stop of map
            self.startbutton.Enable()
            self.abortbutton.Disable()           

            self.usertitles.Enable()
            self.filename.Enable()        

            if SAVE_ESCAN:
                self.SaveEscanData()

            fname = str(self.filename.GetValue())

            nfile = new_filename(os.path.abspath(fname))
            self.filename.SetValue(os.path.split(nfile)[1])            
        else: # start of map
            self.startbutton.Disable()
            self.abortbutton.Enable()

    @DelayedEpicsCallback
    def onMapAbort(self,pvname=None,value=None,**kw):
        if value == 0:
            self.abortbutton.Enable()
            self.startbutton.Disable()
        else:
            self.abortbutton.Disable()            
            self.startbutton.Enable()
            
    def epics_CtrlVars(self,posname):
        posname = str(posname)
        ctrlvars = {'lower_ctrl_limit':-0.001,
                    'upper_ctrl_limit':0.001,
                    'units': 'mm'}

        if posname not in self._pvs:
            labels = self.config['slow_positioners'].values()
            if posname in labels:
                keys   = self.config['slow_positioners'].keys()
                pvname = keys[labels.index(posname)]
                self._pvs[posname] = epics.PV(pvname)

        if (posname in self._pvs and
            self._pvs[posname] is not None and
            self._pvs[posname].connected):            
            self._pvs[posname].get() # make sure PV is connected
            c  = self._pvs[posname].get_ctrlvars()
            if c is not None: ctrlvars = c
        return ctrlvars
    
    @EpicsFunction
    def SetMotorLimits(self):
        m1name = self.m1choice.GetStringSelection()
        m1 = self._pvs[m1name]
        if m1.lower_ctrl_limit is None:
            m1.get_ctrlvars()
        xmin,xmax =  m1.lower_ctrl_limit, m1.upper_ctrl_limit
        self.m1units.SetLabel(m1.units)
        self.m1step.SetMinMax(-abs(xmax-xmin), abs(xmax-xmin))
        self.m1start.SetMinMax(xmin, xmax)
        self.m1stop.SetMinMax(xmin, xmax)
            
        m2name = self.m2choice.GetStringSelection()
        if not self.m2choice.IsEnabled() or len(m2name) < 1:
            return
        
        m2 = self._pvs[m2name]
        if m2.lower_ctrl_limit is None:
            m2.get_ctrlvars()
        
        xmin,xmax =  m2.lower_ctrl_limit, m2.upper_ctrl_limit
        self.m2units.SetLabel( m2.units)
        self.m2step.SetMinMax(-abs(xmax-xmin),abs(xmax-xmin))
        self.m2start.SetMinMax(xmin,xmax)
        self.m2stop.SetMinMax(xmin,xmax)
           
    def onDimension(self,evt=None):
        cnf = self.config
        dim = self.dimchoice.GetSelection() + 1
        cnf['scan']['dimension'] = dim
        if dim == 1:
            self.m2npts.SetLabel("1")
            self.m2choice.Disable()
            for m in (self.m2start,self.m2units,self.m2stop,self.m2step):
                m.Disable()
        else:
            self.m2choice.Enable()            
            for m in (self.m2start,self.m2units,self.m2stop,self.m2step):
                m.Enable() 
        self.onM2step()
        
    def onM1Select(self,evt=None):
        m1name = evt.GetString()
        m2name = self.m2choice.GetStringSelection()

        sm_labels = self.config['slow_positioners'].values()[:]
        sm_labels.remove(m1name)
        if m1name == m2name:
            m2name = sm_labels[0]
           
        self.m2choice.Clear()
        self.m2choice.AppendItems(sm_labels)
        self.m2choice.SetStringSelection(m2name)
        self.SetMotorLimits()
        
    def onM2Select(self,evt=None):
        self.SetMotorLimits()
        
    def onM2step(self,value=None,**kw):
        try:
            s1 = self.m2start.GetValue()
            s2 = self.m2stop.GetValue()
            ds = self.m2step.GetValue()
            t  = self.m1time.GetValue()
            npts = 1 + int(0.5  + abs(s2-s1)/(max(ds,1.e-10)))
            if npts > MAX_POINTS: npts = MAX_POINTS
            if self.config['scan']['dimension'] == 1:
                npts = 1
            self.m2npts.SetLabel("  %i" % npts)
            total = 2 + int( (t + 0.5) * max(1,npts))
            self.maptime.SetLabel("%s" % timedelta(seconds=total))
        except AttributeError:
            pass            
        
    def onM1step(self,value=None,**kw):
        try:
            s1 = self.m1start.GetValue()
            s2 = self.m1stop.GetValue()
            ds = self.m1step.GetValue()
            t  = self.m1time.GetValue()
            npts = 1 + int(0.5  + abs(s2-s1)/(max(ds,1.e-10)))
            if npts > MAX_POINTS: npts = MAX_POINTS
            self.m1npts.SetLabel("  %i" % npts)
            self.pixtime.SetLabel("%.3f s" % (t/max(1,(npts-1))))
        except AttributeError:
            pass
            
    def onM1time(self,value=None,**kw):
        try:
            npts1 = float(self.m1npts.GetLabel().strip())
            npts2 = float(self.m2npts.GetLabel().strip())
            total = int((value + 1.25) * max(1,npts2))
            self.maptime.SetLabel("%s" % timedelta(seconds=total))
            self.pixtime.SetLabel("%.3f s" % (value/max(1,(npts1-1))))
        except AttributeError:
            pass       

    @EpicsFunction
    def onStartScan(self,evt=None):
        fname = str(self.filename.GetValue())
        if os.path.exists(fname):
            fname = increment_filename(fname)
            self.filename.SetValue(fname)

        sname = fname + '.cnf'
        self.SaveConfigFile(sname, scan_only=True)
        self.mapper.StartScan(fname, sname)            

        # setup escan saver 
        self.data_mode   = 'w'

        self.data_fname  = os.path.abspath(os.path.join(nativepath(self.mapper.basedir), self.mapper.filename))

        self.usertitles.Disable()
        self.filename.Disable()        
        self.abortbutton.Enable()        
        self.start_time = time.time()
        self.escan_saver = EscanWriter(folder=self.mapper.workdir)
        
    @EpicsFunction
    def onAbortScan(self,evt=None):
        self.mapper.AbortScan()


if __name__ == "__main__":
    motorpvs = Connect_Motors()

    app  = wx.PySimpleApp(redirect=False,
                          filename='fastmap.log')
                          
    frame= FastMapGUI(motorpvs=motorpvs)
    app.SetTopWindow(frame)
    frame.Show()        
    app.MainLoop()
