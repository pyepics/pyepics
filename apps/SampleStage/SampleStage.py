#!/usr/bin/python
#
# Sample Stage Control
""" GSECARS Sample Stage Control Application

"""
import os
import time
import wx
import wx.lib.agw.pycollapsiblepane as CP
import wx.lib.mixins.inspection
from  cStringIO import StringIO
from  urllib import urlopen

from epics import Motor
from epics.wx import finalize_epics,  EpicsFunction, MotorPanel

from epics.wx.utils import  (empty_bitmap, add_button, add_menu, popup,
                             pack, Closure , NumericCombo,
                             FileSave, FileOpen,SelectWorkdir)

from StageConf import StageConfig
from Icons import images, app_icon

ALL_EXP  = wx.ALL|wx.EXPAND
CEN_ALL  = wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL
LEFT_CEN = wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL
LEFT_TOP = wx.ALIGN_LEFT|wx.ALIGN_TOP
LEFT_BOT = wx.ALIGN_LEFT|wx.ALIGN_BOTTOM
CEN_TOP  = wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_TOP
CEN_BOT  = wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_BOTTOM

IMG_W, IMG_H = 280, 210
CONFIG_DIR  = '//cars5/Data/xas_user/config/SampleStage/'
WORKDIR_FILE = os.path.join(CONFIG_DIR, 'workdir.txt')
ICON_FILE = os.path.join(CONFIG_DIR, 'micro.ico')

class SampleStage(wx.Frame):
    """Main Sample Stage Class
    """
    motorgroups = {'fine': ('fineX', 'fineY'),
                   'coarse': ('X', 'Y'),
                   'focus': ('Z', None),
                   'theta': ('theta', None)}
    htmllog  = 'SampleStage.html'
    html_header = """<html><head><title>Sample Stage Log</title></head>
<meta http-equiv='Pragma'  content='no-cache'>
<meta http-equiv='Refresh' content='300'>
<body>
    """

    def __init__(self, configfile=None,  *args, **kwds):
        wx.Frame.__init__(self, None, wx.ID_ANY, '',
                         wx.DefaultPosition, wx.Size(-1,-1),**kwds)
        self.SetFont(wx.Font(11, wx.SWISS, wx.NORMAL, wx.BOLD, False))
        self.SetSize((900, 575))
        self.positions = None
        self.read_config(configfile=configfile, get_dir=False) # True)
        self.SetTitle("XRM Sample Stage")
        wx.EVT_CLOSE(self, self.onClose)

        self.tweaks = {}
        self.motors = None
        self.motorwids = {}
        self.create_frame()
        self.connect_motors()
        self.set_position_list()

    #@EpicsFunction
    def connect_motors(self):
        "connect to epics motors"
        self.motors = {}
        self.sign = {}
        for pvname, val in self.config['stages'].items():
            pvname = pvname.strip()
            label = val['label']
            self.motors[label] = Motor(name=pvname)
            self.sign[label] = val['sign']

        for mname in self.motorwids:
            self.motorwids[mname].SelectMotor(self.motors[mname])

    def begin_htmllog(self):
        "initialize log file"
        fout = open(self.htmllog, 'w')
        fout.write(self.html_header)
        fout.close()

    def read_config(self, configfile=None, get_dir=False):
        "open/read ini config file"
        if get_dir:
            try:
                workdir = open(WORKDIR_FILE, 'r').readline()[:-1]
                os.chdir(workdir)
            except:
                pass
            ret = SelectWorkdir(self)
            if ret is None:
                self.Destroy()

        self.cnf = StageConfig(configfile)
        self.config = self.cnf.config
        self.positions = self.config['positions']
        self.stages    = self.config['stages']
        self.v_move    = self.config['setup']['verify_move']
        self.v_erase   = self.config['setup']['verify_erase']
        self.v_replace = self.config['setup']['verify_overwrite']
        self.finex_dir = self.config['setup']['finex_dir']
        self.finey_dir = self.config['setup']['finey_dir']
        self.imgdir    = self.config['setup']['imgdir']
        self.webcam    = self.config['setup']['webcam']
        if not os.path.exists(self.imgdir):
            os.makedirs(self.imgdir)
        if not os.path.exists(self.htmllog):
            self.begin_htmllog()

        self.get_tweakvalues()

    def get_tweakvalues(self):
        "get settings for tweak values for combo boxes"
        def maketweak(prec=3, tmin=0, tmax=10,
                      decades=7, steps=(1,2,5)):
            steplist = []
            for i in range(decades):
                for step in (j* 10**(i - prec) for j in steps):
                    if (step <= tmax and step > 0.98*tmin):
                        steplist.append(step)
            return steplist
        self.tweaklist = {}
        self.tweaklist['fine']   = maketweak(prec=4, tmax=2.0)
        self.tweaklist['coarse'] = maketweak(tmax=70.0)
        self.tweaklist['focus']  = maketweak(tmax=70.0)
        self.tweaklist['theta']  = maketweak(tmax=9.0)
        self.tweaklist['theta'].extend([10, 20, 30, 45, 90, 180])

    def write_message(self, msg='', index=0):
        "write to status bar"
        self.statusbar.SetStatusText(msg, index)

    def create_menus(self):
        "Create the menubar"
        mbar = wx.MenuBar()
        fmenu   = wx.Menu()
        omenu   = wx.Menu()
        add_menu(self, fmenu, label="&Save", text="Save Configuration",
                 action = self.onSave)
        add_menu(self, fmenu, label="&Read", text="Read Configuration",
                 action = self.onRead)

        fmenu.AppendSeparator()
        add_menu(self, fmenu, label="E&xit",  text="Quit Program",
                 action = self.onClose)

        vmove  = wx.NewId()
        verase = wx.NewId()
        vreplace = wx.NewId()
        self.menu_opts = {vmove: 'v_move',
                          verase: 'v_erase',
                          vreplace: 'v_replace'}

        mitem = omenu.Append(vmove, "Verify Go To ",
                             "Prompt to Verify Moving with 'Go To'",
                             wx.ITEM_CHECK)
        mitem.Check()
        self.Bind(wx.EVT_MENU, self.onMenuOption, mitem)

        mitem = omenu.Append(verase, "Verify Erase",
                     "Prompt to Verify Erasing Positions", wx.ITEM_CHECK)
        mitem.Check()
        self.Bind(wx.EVT_MENU, self.onMenuOption, mitem)

        mitem = omenu.Append(vreplace, "Verify Overwrite",
                     "Prompt to Verify Overwriting Positions",  wx.ITEM_CHECK)
        mitem.Check()
        self.Bind(wx.EVT_MENU, self.onMenuOption, mitem)

        mbar.Append(fmenu, '&File')
        mbar.Append(omenu, '&Options')
        self.SetMenuBar(mbar)

        self.popup_up1 = wx.NewId()
        self.popup_dn1 = wx.NewId()
        self.popup_upall = wx.NewId()
        self.popup_dnall = wx.NewId()

    def onMenuOption(self, evt=None):
        """events for options menu: move, erase, overwrite """
        setattr(self, self.menu_opts[evt.GetId()], evt.Checked())

    def create_frame(self):
        "build main frame"
        self.create_menus()
        # status bars
        self.statusbar = self.CreateStatusBar(2, wx.CAPTION|wx.THICK_FRAME)
        self.statusbar.SetStatusWidths([-4, -1])
        for index in range(2):
            self.statusbar.SetStatusText('', index)

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.AddMany([
            (self.make_mainpanel(self), 0, ALL_EXP|wx.ALIGN_LEFT, 1),
            (self.make_imgpanel(self),  0, ALL_EXP|LEFT_CEN,  1),
            (self.make_pospanel(self),  1, ALL_EXP|wx.ALIGN_RIGHT, 1)])

        pack(self, sizer)

        icon = wx.Icon(ICON_FILE, wx.BITMAP_TYPE_ICO)
        self.SetIcon(icon)

    def make_pospanel(self, parent):
        """panel of position lists, with buttons"""
        panel = wx.Panel(parent, size=(145, 200))
        btn_goto  = add_button(panel, "Go To",  size=(70, -1), action=self.onGo)
        btn_erase = add_button(panel, "Erase",  size=(70, -1),
                            action=self.onErasePosition)

        brow = wx.BoxSizer(wx.HORIZONTAL)
        brow.Add(btn_goto,   0, ALL_EXP|wx.ALIGN_LEFT, 1)
        brow.Add(btn_erase,  0, ALL_EXP|wx.ALIGN_LEFT, 1)

        self.pos_list  = wx.ListBox(panel)
        self.pos_list.SetBackgroundColour(wx.Colour(253, 253, 250))
        self.pos_list.Bind(wx.EVT_LISTBOX, self.onSelectPosition)
        self.pos_list.Bind(wx.EVT_RIGHT_DOWN, self.onPosRightClick)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(brow,          0, wx.ALIGN_LEFT|wx.ALL)
        sizer.Add(self.pos_list, 1, ALL_EXP|wx.ALIGN_CENTER, 3)

        pack(panel, sizer)
        panel.SetAutoLayout(1)
        return panel

    def make_imgpanel(self, parent):
        panel = wx.Panel(parent)

        wlabel = wx.StaticText(panel, label="Save Position: ")
        self.pos_name =  wx.TextCtrl(panel, value="", size=(180, 25),
                                     style= wx.TE_PROCESS_ENTER)
        self.pos_name.Bind(wx.EVT_TEXT_ENTER, self.onSavePosition)

        imglabel  = "Select a position...\n  "
        self.info = wx.StaticText(panel,  label=imglabel)
        self.img  = wx.StaticBitmap(panel, -1,
                                    empty_bitmap(IMG_W, IMG_H, value=200))
        self.info.SetSize((IMG_W, 36))
        savebox = wx.BoxSizer(wx.HORIZONTAL)
        savebox.Add(wlabel,        1, LEFT_CEN, 1)
        savebox.Add(self.pos_name, 0, wx.EXPAND|LEFT_CEN, 1)

        sizer  = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(savebox,      0, CEN_TOP,  2)
        sizer.Add((3, 5))
        sizer.Add(self.img,     0, CEN_ALL,  5)
        sizer.Add(self.info,    0, LEFT_TOP, 2)
        sizer.Add((3, 5))

        pack(panel, sizer)
        return panel

    def group_panel(self, parent, label='Fine Stages',
                    precision=3, collapseable=False,
                    add_buttons=None,  group='fine'):
        """make motor group panel """
        motors = self.motorgroups[group]

        is_xy = motors[1] is not None

        if collapseable:
            cpane = CP.PyCollapsiblePane(parent,
                                         agwStyle=wx.CP_GTK_EXPANDER)
            cpane.Bind(wx.EVT_COLLAPSIBLEPANE_CHANGED,
                    Closure(self.onCollapse, panel=cpane, label=label))
            cpane.Collapse(True)
            cpane.SetFont(wx.Font(11, wx.SWISS, wx.NORMAL, wx.BOLD, False))
            cpane.SetLabel('Show %s' % label)
            panel = cpane.GetPane()
        else:
            panel  = wx.Panel(parent)

        self.tweaks[group] = NumericCombo(panel, self.tweaklist[group],
                                          precision=precision, init=3)

        slabel = wx.BoxSizer(wx.HORIZONTAL)
        slabel.Add(wx.StaticText(panel, label=" %s: " % label),
                   1,  ALL_EXP|LEFT_BOT)
        slabel.Add(self.tweaks[group], 0,  ALL_EXP|LEFT_TOP)

        smotor = wx.BoxSizer(wx.VERTICAL)
        smotor.Add(slabel, 0, ALL_EXP)

        for mname in motors:
            if mname is None: continue
            self.motorwids[mname] = MotorPanel(panel, label=mname, full=False)
            self.motorwids[mname].desc.SetLabel(mname)
            smotor.Add(self.motorwids[mname], 1, ALL_EXP|LEFT_TOP)

        if add_buttons is not None:
            for label, action in add_buttons:
                smotor.Add(add_button(panel, label, action=action))

        btnbox = self.make_button_panel(panel, full=is_xy, group=group)
        btnbox_style = CEN_BOT
        if is_xy:
            btnbox_style = CEN_TOP

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(smotor, 0, ALL_EXP|LEFT_TOP)
        sizer.Add(btnbox, 0, btnbox_style, 1)

        pack(panel, sizer)
        if collapseable:
            return cpane
        return panel

    def make_mainpanel(self, parent):
        "create right hand panel"
        panel = wx.Panel(parent)
        sizer =  wx.BoxSizer(wx.VERTICAL)

        fine_panel = self.group_panel(panel, label='Fine Stages',
                                      group='fine', precision=4,
                                      collapseable=True,
                                      add_buttons=[('Zero Fine Motors',
                                                   self.onZeroFineMotors)])

        sizer.Add(fine_panel,   0, ALL_EXP|LEFT_TOP)
        sizer.Add((2, 2))
        sizer.Add(wx.StaticLine(panel, size=(300, 3)), 0, CEN_TOP)
        sizer.Add(self.group_panel(panel, label='Coarse Stages',
                                   group='coarse'),  0, ALL_EXP|LEFT_TOP)
        sizer.Add((2, 2))
        sizer.Add(wx.StaticLine(panel, size=(300, 3)), 0, CEN_TOP)
        sizer.Add(self.group_panel(panel, label='Focus',
                                   group='focus'),   0, ALL_EXP|LEFT_TOP)
        sizer.Add((2, 2))
        sizer.Add(wx.StaticLine(panel, size=(300, 3)), 0, CEN_TOP)
        sizer.Add(self.group_panel(panel, label='Theta', collapseable=True,
                                   group='theta'),
                  0, ALL_EXP|LEFT_TOP)
        pack(panel, sizer)
        return panel

    def make_button_panel(self, parent, group='', full=True):
        panel = wx.Panel(parent)
        if full:
            sizer = wx.GridSizer(3, 3, 1, 1)
        else:
            sizer = wx.GridSizer(1, 3)
        def _btn(name):
            img = images[name].GetImage()
            btn = wx.BitmapButton(panel, -1, wx.BitmapFromImage(img),
                                style = wx.NO_BORDER)
            btn.Bind(wx.EVT_BUTTON, Closure(self.onMove,
                                          group=group, name=name))
            return btn
        if full:
            sizer.Add(_btn('nw'),     0, wx.ALL)
            sizer.Add(_btn('nn'),     0, wx.ALL)
            sizer.Add(_btn('ne'),     0, wx.ALL)
            sizer.Add(_btn('ww'),     0, wx.ALL)
            sizer.Add(_btn('camera'), 0, wx.ALL)
            sizer.Add(_btn('ee'),     0, wx.ALL)
            sizer.Add(_btn('sw'),     0, wx.ALL)
            sizer.Add(_btn('ss'),     0, wx.ALL)
            sizer.Add(_btn('se'),     0, wx.ALL)
        else:
            sizer.Add(_btn('ww'),     0, wx.ALL, 0)
            sizer.Add(wx.StaticText(panel, label='', size=(1, 1)))
            sizer.Add(_btn('ee'),     0, wx.ALL, 0)

        pack(panel, sizer)
        return panel

    def set_position_list(self):
        "set the list of position on the left-side panel"
        self.pos_list.Clear()
        # print self.positions, self.config
        if self.positions is None:
            self.positions = self.config['positions']
        for name in self.positions:
            self.pos_list.Append(name)

    def onClose(self, event=None):
        ret = popup(self, "Really Quit?", "Exit Sample Stage?",
                    style=wx.YES_NO|wx.NO_DEFAULT|wx.ICON_QUESTION)
        if ret == wx.ID_YES:
            finalize_epics()
            try:
                fout = open(WORKDIR_FILE, 'w')
                fout.write("%s\n" % os.path.abspath(os.curdir))
                fout.close()
            except:
                pass
            self.Destroy()

    def onSave(self, event=None):
        fname = FileSave(self, 'Save Configuration File',
                         wildcard='INI (*.ini)|*.ini|All files (*.*)|*.*',
                         default_file='SampleStage.ini')
        if fname is not None:
            self.cnf.Save(fname)
        self.write_message('Saved Configuration File %s' % fname)

    def onRead(self, event=None):
        fname = FileOpen(self, 'Read Configuration File',
                         wildcard='INI (*.ini)|*.ini|All files (*.*)|*.*',
                         default_file='SampleStage.ini')
        if fname is not None:
            self.read_config(fname)
            self.connect_motors()
            self.set_position_list()
        self.write_message('Read Configuration File %s' % fname)

    def onPosRightClick(self, event=None):
        menu = wx.Menu()
        # make basic widgets for popup menu
        for item, name in (('popup_up1', 'Move up'),
                           ('popup_dn1', 'Move down'),
                           ('popup_upall', 'Move to top'),
                           ('popup_dnall', 'Move to bottom')):
            setattr(self, item,  wx.NewId())
            wid = getattr(self, item)
            self.Bind(wx.EVT_MENU, self.onPosRightEvent, wid)
            menu.Append(wid, name)
        self.PopupMenu(menu)
        menu.Destroy()

    def onPosRightEvent(self, event=None):
        "popup box event handler"
        idx = self.pos_list.GetSelection()
        if idx < 0: # no item selected
            return
        wid = event.GetId()
        namelist = list(self.positions.keys())[:]
        stmp = {}
        for name in namelist:
            stmp[name] = self.positions[name]

        if wid == self.popup_up1 and idx > 0:
            namelist.insert(idx-1, namelist.pop(idx))
        elif wid == self.popup_dn1 and idx < len(namelist):
            namelist.insert(idx+1, namelist.pop(idx))
        elif wid == self.popup_upall:
            namelist.insert(0, namelist.pop(idx))
        elif wid == self.popup_dnall:
            namelist.append( namelist.pop(idx))

        self.positions.clear()
        for name in namelist:
            self.positions[name]  = stmp[name]
        self.set_position_list()
        self.autosave()

    def onSelectPosition(self, event=None, name=None):
        "Event handler for selecting a named position"
        if name is None:
            name = str(event.GetString().strip())
        if name is None or name not in self.positions:
            return
        self.pos_name.SetValue(name)
        thispos = self.positions[name]
        imgfile = os.path.join(self.imgdir, thispos['image'])
        tstamp =  thispos.get('timestamp', None)
        if tstamp is None:
            try:
                img_time = time.localtime(os.stat(imgfile).st_mtime)
                tstamp =  time.strftime('%b %d %H:%M:%S', img_time)
            except:
                tstamp = ''
        self.display_imagefile(fname=imgfile, name=name, tstamp=tstamp)

    def onErasePosition(self, event):
        posname = self.pos_list.GetStringSelection()
        ipos  =  self.pos_list.GetSelection()
        if posname is None or len(posname) < 1:
            return
        if self.v_erase:
            ret = popup(self, "Erase  %s?" % (posname),
                        'Verify Erase',
                        style=wx.YES_NO|wx.ICON_QUESTION)
            if ret != wx.ID_YES:
                return
        self.positions.pop(posname)
        self.pos_list.Delete(ipos)
        self.pos_name.Clear()
        self.display_imagefile(fname=None)
        self.write_message('Erased Position %s' % posname)

    def onSavePosition(self, event=None):
        name = event.GetString().strip()

        if self.v_replace and name in self.config['positions']:
            ret = popup(self, "Overwrite Position %s?" %name,
                        "Veriry Overwrite Position",
                    style=wx.YES_NO|wx.NO_DEFAULT|wx.ICON_QUESTION)

            if ret != wx.ID_YES:
                return
        imgfile = '%s.jpg' % time.strftime('%b%d_%H%M%S')
        self.save_image(fname=os.path.join(self.imgdir, imgfile))

        tmp_pos = []
        for v in self.config['stages'].values():
            tmp_pos.append(float(self.motors[v['label']].VAL))

        self.positions[name] = {'image': imgfile,
                                'timestamp': time.strftime('%b %d %H:%M:%S'),
                                'position': tmp_pos}

        if name not in self.pos_list.GetItems():
            self.pos_list.Append(name)

        self.pos_name.Clear()
        self.onSelectPosition(event=None, name=name)
        self.pos_list.SetStringSelection(name)
        # auto-save file
        self.config['positions'] = self.positions
        self.autosave()
        self.write_htmllog(name)
        self.write_message('Saved Position %s,  autosave file written.' % name)

    def autosave(self):
        self.cnf.Save('SampleStage_autosave.ini')

    def write_htmllog(self, name):
        thispos = self.positions.get(name, None)
        if thispos is None: return
        imgfile = thispos['image']
        tstamp  = thispos['timestamp']
        pos     = ', '.join([str(i) for i in thispos['position']])
        pvnames = ', '.join([i.strip() for i in self.stages.keys()])
        labels  = ', '.join([i['label'].strip() for i in self.stages.values()])
        fout = open(self.htmllog, 'a')
        fout.write("""<hr>
<table><tr><td><a href='Sample_Images/%s'>
    <img src='Sample_Images/%s' width=200></a></td>
    <td><table><tr><td>Position:</td><td>%s</td></tr>
    <tr><td>Saved:</td><td>%s</td></tr>
    <tr><td>Motor Names:</td><td>%s</td></tr>
    <tr><td>Motor PVs:</td><td>%s</td></tr>
    <tr><td>Motor Values:</td><td>%s</td></tr>
    </table></td></tr>
</table>""" % (imgfile, imgfile, name, tstamp, labels, pvnames, pos))
        fout.close()

    def save_image(self, fname=None):
        "save image to file"
        try:
            img = urlopen(self.webcam).read()
        except:
            self.write_message('could not open webcam %s')
        if fname is None:
            fname = FileSave(self, 'Save Image File',
                             wildcard='JPEG (*.jpg)|*.jpg|All files (*.*)|*.*',
                             default_file='sample.jpg')
        if fname is not None:
            out = open(fname,"wb")
            out.write(img)
            out.close()
            self.write_message('saved image to %s' % fname)
        return fname

    def onGo(self, event):
        posname = self.pos_list.GetStringSelection()
        if posname is None or len(posname) < 1:
            return
        pos_vals = self.positions[posname]['position']
        stage_names = self.config['stages'].values()
        postext = []
        for name, val in zip(stage_names, pos_vals):
            postext.append('  %s\t= %.4f' % (name['label'], val))
        postext = '\n'.join(postext)

        if self.v_move:
            ret = popup(self, "Move to %s?: \n%s" % (posname, postext),
                        'Verify Move',
                        style=wx.YES_NO|wx.ICON_QUESTION)
            if ret != wx.ID_YES:
                return
        for name, val in zip(stage_names, pos_vals):
            self.motorwids[name['label']].drive.SetValue("%f" % val)
        self.write_message('moved to %s' % posname)

    #@EpicsFunction
    def onMove(self, event, name=None, group=None):
        if name == 'camera':
            return self.save_image()

        twkval = float(self.tweaks[group].GetStringSelection())
        ysign = {'n':1, 's':-1}.get(name[0], 0)
        xsign = {'e':1, 'w':-1}.get(name[1], 0)

        x, y = self.motorgroups[group]

        val = float(self.motorwids[x].drive.GetValue())
        self.motorwids[x].drive.SetValue("%f" % (val + xsign*twkval))
        if y is not None:
            val = float(self.motorwids[y].drive.GetValue())
            self.motorwids[y].drive.SetValue("%f" % (val + ysign*twkval))
        try:
            self.motors[x].TWV = twkval
            if y is not None:
                self.motors[y].TWV = twkval
        except:
            pass

    def onZeroFineMotors(self, event=None):
        "event handler for Zero Fine Motors"
        mot = self.motors
        mot['X'].VAL +=  self.finex_dir * mot['fineX'].VAL
        mot['Y'].VAL +=  self.finey_dir * mot['fineY'].VAL
        time.sleep(0.1)
        mot['fineX'].VAL = 0
        mot['fineY'].VAL = 0

    def display_imagefile(self, fname=None, name='', tstamp=''):
        "display raw jpeg image as wx bitmap"
        bmp = empty_bitmap(IMG_W, IMG_H, value=200)
        if fname is not None and os.path.exists(fname):
            stream = StringIO(open(fname, "rb").read())
            bmp = wx.BitmapFromImage( wx.ImageFromStream(
                (stream)).Rescale(IMG_W, IMG_H))

        self.img.SetBitmap(bmp)
        if tstamp != '':
            tstamp = 'Saved:     %s\n' % tstamp
        self.info.SetLabel("%s\n%s" % (name, tstamp))
        self.info.SetSize((IMG_W, 36))

    def onCollapse(self, event=None, panel=None, label=''):
        # change the label of 'Show/Hide'
        if panel is None:
            return
        txt = 'Show'
        if panel.IsExpanded():
            txt = 'Hide'
        panel.SetLabel('%s %s' % (txt, label))
        self.Refresh()

class StageApp(wx.App, wx.lib.mixins.inspection.InspectionMixin):
    def OnInit(self):
        self.Init()
        frame = SampleStage()
        frame.Show()
        self.SetTopWindow(frame)
        time.sleep(3.5)
        return True

if __name__ == '__main__':
    app = wx.PySimpleApp()
    f = SampleStage(configfile='SampleStage.ini')
    f.Show()
    app.MainLoop()


