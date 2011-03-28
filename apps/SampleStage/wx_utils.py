"""
wx utils
"""
import wx
import os
import array

def add_btn(panel, label, size=(-1, -1), action=None):
    "add simple button with bound action"
    thisb = wx.Button(panel, label=label, size=size)
    if hasattr(action, '__call__'):
        panel.Bind(wx.EVT_BUTTON, action, thisb)
    return thisb

def add_menu(parent, menu, label='', text='', action=None):
    "add submenu"
    ID = wx.NewId()
    menu.Append(ID,label,text)
    if hasattr(action, '__call__'):
        wx.EVT_MENU(parent, ID, action)

def empty_bitmap(width, height, value=255):
    return wx.BitmapFromBuffer(width, height, array.array('B', [value]*3*width*height))

def savefile_dialog(parent,  message='Save File as ...',
                    defdir='', deffile='',
                    wildcard=None):
    "prompts for and returns a filename for a save"
    if defdir is None:
        defdir = os.getcwd()
    if wildcard is None:
        wildcard = 'All files (*.*)|*.*'
    dlg = wx.FileDialog(parent, message=message,
                        defaultDir=defdir,
                        defaultFile=deffile,
                        wildcard=wildcard, style=wx.SAVE)
    path = None
    if dlg.ShowModal() == wx.ID_OK:
        path = os.path.abspath(dlg.GetPath())
    dlg.Destroy()
    return path

def openfile_dialog(parent,  message='Open file ...',
                    defdir='', deffile='',
                    wildcard=None):
    "prompts for and return list of files to open"
    if defdir is None:
        defdir = os.getcwd()
    if wildcard is None:
        wildcard = 'All files (*.*)|*.*'
    dlg = wx.FileDialog(parent, message=message,
                        defaultDir=defdir,
                        defaultFile=deffile,
                        wildcard=wildcard,
                        style=wx.OPEN| wx.MULTIPLE|wx.CHANGE_DIR)

    paths = []
    if dlg.ShowModal() == wx.ID_OK:
        paths = os.path.abspath(dlg.GetPath())
    dlg.Destroy()
    return paths

def select_workdir(parent,  message='Select Working Folder...'):
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
                
def popup(parent, message, title, style=None):
    "generic popup message dialog"
    if style is None:
        style = wx.OK | wx.ICON_INFORMATION
    dlg = wx.MessageDialog(parent, message, title, style)
    ret = dlg.ShowModal()
    dlg.Destroy()
    return ret

class NumericCombo(wx.ComboBox):
    def __init__(self, parent, choices, precision=3,
                 init=0, width=80):

        self.fmt = "%%.%if" % precision
        self.choices  = choices
        schoices = [self.fmt % i for i in self.choices]
        wx.ComboBox.__init__(self, parent, -1, '', (-1, -1), (width, -1),
                             schoices, wx.CB_DROPDOWN|wx.TE_PROCESS_ENTER)
        
        init = min(init, len(self.choices))
        self.SetStringSelection(schoices[init])
        # self.Bind(wx.EVT_TEXT,    self.onText)
        self.Bind(wx.EVT_TEXT_ENTER, self.onEnter)

    def onText(self, evt): 
        evt.Skip()
        
    def onEnter(self, event=None):
        thisval = float(event.GetString())

        if thisval not in self.choices:
            self.choices.append(thisval)
            self.choices.sort()

        self.Clear()
        self.AppendItems([self.fmt % i for i in self.choices])
        self.SetSelection(self.choices.index(thisval))
    

class sText(wx.StaticText):
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
            self.SetBackgroundColour(colour)
    

class Closure:
    """A very simple callback class to emulate a closure (reference to
    a function with arguments) in python.

    This class holds a user-defined function to be executed when the
    class is invoked as a function.  This is useful in many situations,
    especially for 'callbacks' where lambda's are quite enough.
    Many Tkinter 'actions' can use such callbacks.

    >>>def my_action(x=None):
    ...        print 'my action: x = ', x
    >>>c = closure(my_action,x=1)
    ..... sometime later ...
    >>>c()
     my action: x = 1
    >>>c(x=2)
     my action: x = 2

    based on Command class from J. Grayson's Tkinter book.
    """
    def __init__(self,func=None,*args, **kw):
        self.func  = func
        self.kw    = kw
        self.args  = args
    def __call__(self,  *args, **kw):
        self.kw.update(kw)
        if self.func is None:
            return None
        self.args = args
        return self.func(*self.args, **self.kw)

