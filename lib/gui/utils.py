"""
wx utils
"""
import wx
import os
import array


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
    ID = wx.NewId()
    menu.Append(ID,label,text)
    if hasattr(action, '__call__'):
        wx.EVT_MENU(parent, ID, action)

def addtoMenu(parent,menu,label,text,action=None):
    ID = wx.NewId()
    menu.Append(ID,label,text)
    if callable(action): wx.EVT_MENU(parent, ID, action)

def popup(parent, message, title, style=None):
    "generic popup message dialog"
    if style is None:
        style = wx.OK | wx.ICON_INFORMATION
    dlg = wx.MessageDialog(parent, message, title, style)
    ret = dlg.ShowModal()
    dlg.Destroy()
    return ret    


def empty_bitmap(width, height, value=255):
    "return empty wx.BitMap"
    return wx.BitmapFromBuffer(width, height,
                               array.array('B',
                                           [value]*3*width*height))


def fix_filename(s):
    """fix string to be a 'good' filename. This may be a more
    restrictive than the OS, but avoids nasty cases."""
    bchars = '<>:"\'\\\t\r\n/|?* !%$'
    t = s.translate(string.maketrans(bchars, '_'*len(bchars)))
    if t[0] in '-,;[]{}()~`@#':
        t = '_%s' % t
    return t


def FileOpen(parent, message, default_dir=None,
             default_file=None, multiple=False, wildcard=None):
    "File Open dialog"
    out = None
    if default_dir is None:
        default_dir = os.getcwd()
    if wildcard is None:
        wildcard = 'All files (*.*)|*.*'

    style = wx.OPEN|wx.CHANGE_DIR
    if multiple:
        style = style| wx.MULTIPLE
    dlg = wx.FileDialog(parent, message=message,
                        defaultFile=default_file,
                        defaulDir=default_dir,
                        wildcard=wildcard,
                        style=style)

    out = []
    if dlg.ShowModal() == wx.ID_OK:
        out = os.path.abspath(dlg.GetPath())
    dlg.Destroy()
    return out


def FileSave(parent, message, default_file=None,
             wildcard=None):
    "File Save dialog"
    out = None
    if wildcard is None:
        wildcard = 'All files (*.*)|*.*'

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
            self.SetBackgroundColour(colour)
    
class HyperText(wx.StaticText):
    def  __init__(self, parent, label, action=None, colour=(50, 50, 180)):
        self.action = action
        wx.StaticText.__init__(self, parent, -1, label=label)
        font  = self.GetFont() # .Bold()
        font.SetUnderlined(True)
        self.SetFont(font)
        self.SetForegroundColour(colour)
        self.Bind(wx.EVT_LEFT_UP, self.onSelect)

    def onSelect(self, evt=None):
        if self.action is not None:
            self.action(evt=evt, label=self.GetLabel())
        evt.Skip()

class DateTimeCtrl(object):
    """combined date/time control"""
    def __init__(self, parent, name='datetimectrl', use_now=False):
        self.name = name
        panel = self.panel = wx.Panel(parent)
        bgcol = wx.Colour(250,250,250)

        datestyle = wx.DP_DROPDOWN|wx.DP_SHOWCENTURY|wx.DP_ALLOWNONE

        self.datectrl = wx.DatePickerCtrl(panel, size=(120,-1),
                                          style=datestyle)
        self.timectrl = masked.TimeCtrl(panel, -1, name=name,
                                        limited=False,
                                        fmt24hr=True, oob_color=bgcol)
        h = self.timectrl.GetSize().height
        spinner = wx.SpinButton(panel, -1, wx.DefaultPosition,
                                (-1, h), wx.SP_VERTICAL )
        self.timectrl.BindSpinButton(spinner)
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.datectrl, 0, wx.ALIGN_CENTER)
        sizer.Add(self.timectrl, 0, wx.ALIGN_CENTER)
        sizer.Add(spinner, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_LEFT)
        panel.SetSizer(sizer)
        sizer.Fit(panel)
        if use_now:
            self.timectrl.SetValue(wx.DateTime_Now())

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


def set_float(val, default=None):
    """ utility to set a floating value,
    useful for converting from strings """
    if val in (None, ''):
        return default
    try:
        return float(val)
    except ValueError:
        return default
        

class FloatCtrl(wx.TextCtrl):
    """ Numerical Float Control::
    a wx.TextCtrl that allows only numerical input, can take a precision argument
    and optional upper / lower bounds
    Options:
      
    """
    def __init__(self, parent, value='', min='', max='', 
                 precision=3, bell_on_invalid = True,
                 action=None, action_kw={}, **kwargs):
        
        self.__digits = '0123456789.-'
        self.__prec   = precision
        if precision is None:
            self.__prec = 0
        self.format   = '%%.%if' % self.__prec
        
        self.__val = set_float(value)
        self.__max = set_float(max)
        self.__min = set_float(min)

        self.fgcol_valid   ="Black"
        self.bgcol_valid   ="White"
        self.fgcol_invalid ="Red"
        self.bgcol_invalid =(254, 254, 80)
        self.bell_on_invalid = bell_on_invalid
        
        # set up action 
        self.__action = Closure()  
        if hasattr(action, '__call__'):
            self.__action.func = action
        if len(list(action_kw.keys()))>0:
            self.__action.kw = action_kw

        this_sty =  wx.TE_PROCESS_ENTER|wx.TE_RIGHT
        kw = kwargs
        if 'style' in kw:
            this_sty = this_sty | kw['style']
        kw['style'] = this_sty
            
        wx.TextCtrl.__init__(self, parent, wx.ID_ANY, **kw)        

        self.__CheckValid(self.__val)
        self.SetValue(self.__val)
              
        self.Bind(wx.EVT_CHAR, self.onChar)
        self.Bind(wx.EVT_TEXT, self.onText)

        self.Bind(wx.EVT_SET_FOCUS,  self.onSetFocus)
        self.Bind(wx.EVT_KILL_FOCUS, self.onKillFocus)
        self.Bind(wx.EVT_SIZE, self.onResize)
        self.__GetMark()

    def DisableEntry(self):
        self.SetBackgroundColour((220,220,220))
        self.Disable()

    def EnableEntry(self):
        self.Enable()
        self.SetBackgroundColour(self.bgcol_valid)
        
    def SetAction(self, action, action_kw={}):
        self.__action = Closure()  
        if hasattr(action,'__call__'):
            self.__action.func = action
        if len(list(action_kw.keys()))>0:
            self.__action.kw = action_kw
        
    def SetPrecision(self, prec):
        if prec is None:
            prec = 0
        self.__prec = prec
        self.format = '%%.%if' % prec
        
    def __GetMark(self):
        " keep track of cursor position within text"
        try:
            self.__mark = min(wx.TextCtrl.GetSelection(self)[0],
                              len(wx.TextCtrl.GetValue(self).strip()))
        except:
            self.__mark = 0

    def __SetMark(self, mark=None):
        " "
        if mark is None:
            mark = self.__mark
        self.SetSelection(mark,mark)

    def SetValue(self, value=None, act=True):
        " main method to set value "
        if value == None:
            value = wx.TextCtrl.GetValue(self).strip()
        self.__CheckValid(value)
        self.__GetMark()
        if self.__valid:
            self.__Text_SetValue(self.__val)
            self.SetForegroundColour(self.fgcol_valid)
            self.SetBackgroundColour(self.bgcol_valid)
            if  hasattr(self.__action, '__call__') and act:
                self.__action(value=self.__val)
        else:
            self.__val = self.__bound_val
            self.__Text_SetValue(self.__val)
            self.__CheckValid(self.__val)
            self.SetForegroundColour(self.fgcol_invalid)
            self.SetBackgroundColour(self.bgcol_invalid)
            if self.bell_on_invalid:
                wx.Bell()
        self.__SetMark()
        
    def onKillFocus(self, event):
        self.__GetMark()
        event.Skip()

    def onResize(self, event):
        event.Skip()
        
    def onSetFocus(self, event=None):
        self.__SetMark()
        if event:
            event.Skip()
      
    def onChar(self, event):
        """ on Character event"""
        key   = event.GetKeyCode()
        entry = wx.TextCtrl.GetValue(self).strip()
        pos   = wx.TextCtrl.GetSelection(self)
        # really, the order here is important:
        # 1. return sends to ValidateEntry
        if key == wx.WXK_RETURN:
            self.SetValue(entry)
            return

        # 2. other non-text characters are passed without change
        if (key < wx.WXK_SPACE or key == wx.WXK_DELETE or key > 255):
            event.Skip()
            return
        
        # 3. check for multiple '.' and out of place '-' signs and ignore these
        #    note that chr(key) will now work due to return at #2
        
        has_minus = '-' in entry
        ckey = chr(key)
        if ((ckey == '.' and (self.__prec == 0 or '.' in entry) ) or
            (ckey == '-' and (has_minus or  pos[0] != 0)) or
            (ckey != '-' and  has_minus and pos[0] == 0)):
            return
        # 4. allow digits, but not other characters
        if chr(key) in self.__digits:
            event.Skip()
            return
        # return without event.Skip() : do not propagate event
        return
        
    def onText(self, event=None):
        try:
            if event.GetString() != '':
                self.__CheckValid(event.GetString())
        except:
            pass
        event.Skip()

    def GetValue(self):
        if self.__prec > 0:
            return set_float(fpformat.fix(self.__val, self.__prec))
        else:
            return int(self.__val)

    def GetMin(self):
        return self.__min
    def GetMax(self):
        return self.__max
    def SetMin(self,min):
        self.__min = set_float(min)
    def SetMax(self,max):
        self.__max = set_float(max)
    
    def __Text_SetValue(self, value):
        wx.TextCtrl.SetValue(self, self.format % set_float(value))
        self.Refresh()
    
    def __CheckValid(self, value):
        v = self.__val
        try:
            self.__valid = True
            v = set_float(value)
            if self.__min != None and (v < self.__min):
                self.__valid = False
                v = self.__min
            if self.__max != None and (v > self.__max):
                self.__valid = False
                v = self.__max
        except:
            self.__valid = False
        self.__bound_val = v
        if self.__valid:
            self.__bound_val = self.__val = v
            self.SetForegroundColour(self.fgcol_valid)
            self.SetBackgroundColour(self.bgcol_valid)
        else:
            self.SetForegroundColour(self.fgcol_invalid)
            self.SetBackgroundColour(self.bgcol_invalid)            
        self.Refresh()
