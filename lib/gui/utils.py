"""
wx utils
"""
import os
import array
from string import maketrans

import wx
import wx.lib.masked as masked


def pack(window, sizer):
    "simple wxPython Pack"
    window.SetSizer(sizer)
    sizer.Fit(window)

def add_button(parent, label, size=(-1, -1), action=None):
    "add simple button with bound action"
    thisb = wx.Button(parent, label=label, size=size)
    if hasattr(action, '__call__'):
        parent.Bind(wx.EVT_BUTTON, action, thisb)
    return thisb

def add_menu(parent, menu, label='', text='', action=None):
    "add submenu"
    wid = wx.NewId()
    menu.Append(wid, label, text)
    if hasattr(action, '__call__'):
        wx.EVT_MENU(parent, wid, action)

def addtoMenu(parent, menu, label, longtext, action=None):
    "add label-with-action to menu"
    wid = wx.NewId()
    menu.Append(wid, label, longtext)
    if hasattr(action, '__call__'):
        wx.EVT_MENU(parent, wid, action)

def popup(parent, message, title, style=None):
    """generic popup message dialog, returns
    output of MessageDialog.ShowModal()
    """
    if style is None:
        style = wx.OK|wx.ICON_INFORMATION
    dlg = wx.MessageDialog(parent, message, title, style)
    ret = dlg.ShowModal()
    dlg.Destroy()
    return ret    

def empty_bitmap(width, height, value=255):
    "return empty wx.BitMap"
    data = array.array('B', [value]*3*width*height)
    return wx.BitmapFromBuffer(width, height, data)

def fix_filename(fname):
    """
    fix string to be a 'good' filename. This may be a more
    restrictive than the OS, but avoids nasty cases.
    """
    bchars = ' <>:"\'\\\t\r\n/|?*!%$'
    out = fname.translate(maketrans(bchars, '_'*len(bchars)))
    if out[0] in '-,;[]{}()~`@#':
        out = '_%s' % out
    return out


def FileOpen(parent, message, default_dir=None,
             default_file=None, multiple=False,
             wildcard=None):
    """File Open dialog wrapper.
    returns full path on OK or None on Cancel
    """
    out = None
    if default_dir is None:
        default_dir = os.getcwd()
    if wildcard is None:
        wildcard = 'All files (*.*)|*.*'

    style = wx.OPEN|wx.CHANGE_DIR
    if multiple:
        style = style|wx.MULTIPLE
    dlg = wx.FileDialog(parent, message=message,
                        defaultFile=default_file,
                        defaultDir=default_dir,
                        wildcard=wildcard,
                        style=style)

    out = None
    if dlg.ShowModal() == wx.ID_OK:
        out = os.path.abspath(dlg.GetPath())
    dlg.Destroy()
    return out


def FileSave(parent, message, default_file=None,
             default_dir=None,   wildcard=None):
    "File Save dialog"
    out = None
    if wildcard is None:
        wildcard = 'All files (*.*)|*.*'

    if default_dir is None:
        default_dir = os.getcwd()
        
    dlg = wx.FileDialog(parent, message=message,
                        defaultFile=default_file,
                        wildcard=wildcard,
                        style=wx.SAVE|wx.CHANGE_DIR)
    if dlg.ShowModal() == wx.ID_OK:
        out = os.path.abspath(dlg.GetPath())
    dlg.Destroy()
    return out


def SelectWorkdir(parent,  message='Select Working Folder...'):
    "prompt for and change into a working directory "
    dlg = wx.DirDialog(parent, message,
                       style=wx.DD_DEFAULT_STYLE|wx.DD_CHANGE_DIR)
    
    path = os.path.abspath(os.curdir)
    dlg.SetPath(path)
    if  dlg.ShowModal() == wx.ID_CANCEL:
        return None
    path = os.path.abspath(dlg.GetPath())
    dlg.Destroy()
    os.chdir(path)
    return path                        
                
class NumericCombo(wx.ComboBox):
    """
    Numeric Combo: ComboBox with numeric-only choices
    """
    def __init__(self, parent, choices, precision=3,
                 init=0, width=80):

        self.fmt = "%%.%if" % precision
        self.choices  = choices
        schoices = [self.fmt % i for i in self.choices]
        wx.ComboBox.__init__(self, parent, -1, '', (-1, -1), (width, -1),
                             schoices, wx.CB_DROPDOWN|wx.TE_PROCESS_ENTER)
        
        init = min(init, len(self.choices))
        self.SetStringSelection(schoices[init])
        self.Bind(wx.EVT_TEXT_ENTER, self.OnEnter)

    def OnEnter(self, event=None):
        "text enter event handler"
        thisval = float(event.GetString())

        if thisval not in self.choices:
            self.choices.append(thisval)
            self.choices.sort()

        self.Clear()
        self.AppendItems([self.fmt % i for i in self.choices])
        self.SetSelection(self.choices.index(thisval))
    
class SimpleText(wx.StaticText):
    "simple static text wrapper"
    def __init__(self, parent, label, minsize=None,
                 font=None, colour=None, bgcolour=None,
                 style=wx.ALIGN_CENTRE,  **kws):

        wx.StaticText.__init__(self, parent, -1,
                               label=label, style=style, **kws)

        if minsize is not None:
            self.SetMinSize(minsize)
        if font is not None:
            self.SetFont(font)
        if colour is not None:
            self.SetForegroundColour(colour)
        if bgcolour is not None:
            self.SetBackgroundColour(colour)
    
class HyperText(wx.StaticText):
    """HyperText is a simple extension of wx.StaticText that

       1. adds an underscore to the lable to appear to be a hyperlink
       2. performs the supplied action on Left-Up button events
    """
    def  __init__(self, parent, label, action=None, colour=(50, 50, 180)):
        self.action = action
        wx.StaticText.__init__(self, parent, -1, label=label)
        font  = self.GetFont() # .Bold()
        font.SetUnderlined(True)
        self.SetFont(font)
        self.SetForegroundColour(colour)
        self.Bind(wx.EVT_LEFT_UP, self.OnSelect)

    def OnSelect(self, evt=None):
        "Left-Up Event Handler"
        if self.action is not None:
            self.action(evt=evt, label=self.GetLabel())
        evt.Skip()

class DateTimeCtrl(object):
    """C
    ombined date/time control
    """
    def __init__(self, parent, name='datetimectrl', use_now=False):
        self.name = name
        panel = self.panel = wx.Panel(parent)
        bgcol = wx.Colour(250, 250, 250)

        datestyle = wx.DP_DROPDOWN|wx.DP_SHOWCENTURY|wx.DP_ALLOWNONE

        self.datectrl = wx.DatePickerCtrl(panel, size=(120, -1),
                                          style=datestyle)
        self.timectrl = masked.TimeCtrl(panel, -1, name=name,
                                        limited=False,
                                        fmt24hr=True, oob_color=bgcol)
        timerheight = self.timectrl.GetSize().height
        spinner = wx.SpinButton(panel, -1, wx.DefaultPosition,
                                (-1, timerheight), wx.SP_VERTICAL )
        self.timectrl.BindSpinButton(spinner)
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.datectrl, 0, wx.ALIGN_CENTER)
        sizer.Add(self.timectrl, 0, wx.ALIGN_CENTER)
        sizer.Add(spinner, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_LEFT)
        panel.SetSizer(sizer)
        sizer.Fit(panel)
        if use_now:
            self.timectrl.SetValue(wx.DateTime_Now())

