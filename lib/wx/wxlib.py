"""
wx utility functions for Epics and wxPython interaction
"""
import wx
from wx._core import PyDeadObjectError
                   
import time
import sys
import fpformat
import epics
import wx.lib.buttons as buttons
import wx.lib.agw.floatspin as floatspin

def EpicsFunction(f):
    """decorator to wrap function in a wx.CallAfter() so that
    Epics calls can be made in a separate thread, and asynchronously.

    This decorator should be used for all code that mix calls to
    wx and epics    
    """
    def wrapper(*args, **kwargs):
        wx.CallAfter(f, *args, **kwargs)
    return wrapper

def DelayedEpicsCallback(fcn):
    """decorator to wrap an Epics callback in a wx.CallAfter,
    so that the wx and epics ca threads do not clash
    This also checks for dead wxPython objects (say, from a
    closed window), and remove callbacks to them.
    """
    def wrapper(*args, **kw):
        def cb():
            try:
                fcn(*args, **kw)
            except PyDeadObjectError:                    
                cb_index, pv =  kw.get('cb_info', (None, None))
                if hasattr(pv, 'remove_callback'):
                    try:
                        pv.remove_callback(index=cb_index)
                    except:
                        pass
        return wx.CallAfter(cb)
    return wrapper

@EpicsFunction
def finalize_epics():
    """explicitly finalize and cleanup epics so as to
    prevent core-dumps on exit.
    """
    epics.ca.finalize_libca()
    epics.ca.poll()
    
    
def set_sizer(panel, sizer=None, style=wx.VERTICAL, fit=False):
    """ utility for setting wx Sizer  """
    if sizer is None:  sizer = wx.BoxSizer(style)
    panel.SetAutoLayout(1)
    panel.SetSizer(sizer)
    if fit: sizer.Fit(panel)

def set_float(val, default=None):
    """ utility to set a floating value,
    useful for converting from strings """
    if val in (None, ''):
        return default
    try:
        return float(val)
    except ValueError:
        return default
        
class closure:
    """A very simple callback class to emulate a closure (reference to
    a function with arguments) in python.

    This class holds a user-defined function to be executed when the
    class is invoked as a function.  This is useful in many situations,
    especially for 'callbacks' where lambda's are quite enough.
    Many Tkinter 'actions' can use such callbacks.

    >>>def my_action(x=None):
    ...    print('my action: x = ', x)
    >>>c = closure(my_action,x=1)
    ..... sometime later ...
    >>>c()
     my action: x = 1
    >>>c(x=2)
     my action: x = 2

    based on Command class from J. Grayson's Tkinter book.
    """
    def __init__(self, func=None, *args, **kw):
        self.func  = func
        self.kw    = kw
        self.args  = args
    def __call__(self,  *args, **kw):
        self.kw.update(kw)
        if self.func is None:
            return None
        self.args = args
        return self.func(*self.args, **self.kw)

class EpicsTimer:
    """ Epics Event Timer:
    combines a wxTimer and epics.ca.pend_event to cause Epics Event Processing
    within a wx Application.

    >>> my_timer = EpicsTimer(parent, period=100)
    
    period is in milliseconds.  At each period, epics.ca.poll() will be run.
    
    """
    def __init__(self, parent, period=100, start = True, **kw):
        self.parent = parent
        self.period = period
        self.timer = wx.Timer(parent)
        self.parent.Bind(wx.EVT_TIMER, self.pend)
        if start:
            self.StartTimer()
        
    def StopTimer(self):
        self.timer.Stop()

    def StartTimer(self):
        self.timer.Start(self.period)
        
    def pend(self, event=None):
        epics.ca.poll()


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
        self.__action = closure()  
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

    def SetAction(self, action, action_kw={}):
        self.__action = closure()  
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


class pvCtrlMixin:
    """ mixin for wx Controls with epics PVs:  connects to PV,
    and manages callback events for the PV

    An overriding class must provide a method called _SetValue, which
    will set the contents of the corresponding widget.
    
    """

    def __init__(self, pv=None, pvname=None,
 font=None, fg=None, bg=None):
        self.translations = {}
        self.fgColourTranslations = None
        self.bgColourTranslations = None
        self.fgColourAlarms = {}
        self.bgColourAlarms = {}

        if font is None:
            font = wx.Font(12, wx.SWISS, wx.NORMAL, wx.BOLD,False)
        
        self.pv = None
        try:
            if font is not None:  self.SetFont(font)
            if fg   is not None:  self.SetForegroundColour(fg)
            if bg   is not None:  self.SetBackgroundColour(fg)
        except:
            pass
        self.defaultFgColour = None
        self.defaultBgColour = None

        if pv is None and pvname is not None:
            pv = pvname
        if pv is not None:
            self.set_pv(pv)

    def _SetValue(self,value):
        self._warn("must override _SetValue")

    def SetControlValue(self, raw_value):        
        if len(self.fgColourAlarms) > 0 or len(self.bgColourAlarms) > 0:
            self.pv.get_ctrlvars() # load severity if we care about it <-- NB: this may be a performance problem

        colour = None
        if self.fgColourTranslations is not None and raw_value in self.fgColourTranslations:
            colour = self.fgColourTranslations[raw_value]
        elif self.pv.severity in self.fgColourAlarms:
            colour = self.fgColourAlarms[self.pv.severity]        
        self.OverrideForegroundColour(colour)
            
        colour=None
        if self.bgColourTranslations is not None and raw_value in self.bgColourTranslations:
            colour = self.bgColourTranslations[raw_value]
        elif self.pv.severity in self.bgColourAlarms:
            colour = self.bgColourAlarms[self.pv.severity]
        self.OverrideBackgroundColour(colour)
            
        self._SetValue(self.translations.get(raw_value, raw_value))


    # Call this method to override the control's default foreground colour,
    # Call with color=None to disable overriding
    def OverrideForegroundColour(self, colour):
        if colour is None:
            if self.defaultFgColour is not None:
                wx.Window.SetForegroundColour(self, self.defaultFgColour)
                self.defaultFgColour = None
        else:
            if self.defaultFgColour is None:
                self.defaultFgColour = wx.Window.GetForegroundColour(self)
            wx.Window.SetForegroundColour(self, colour)      

    # Call this method to override the control's default background colour,
    # Call with color=None to disable overriding
    def OverrideBackgroundColour(self, color):
        if color is None:
            if self.defaultBgColour is not None:
                wx.Window.SetBackgroundColour(self, self.defaultBgColour)
        else:
            if self.defaultBgColour is None:
                self.defaultBgColour = wx.Window.GetBackgroundColour(self)
            wx.Window.SetBackgroundColour(self, color)


    # Override the standard set color methods so we can avoid
    # changing colour if it's currently being overriden

    def SetForegroundColour(self, color):
        if self.defaultFgColor is None:
            wx.Window.SetForegroundColour(self, color)
        else:
            self.defaultFgColor = color

    def GetForegroundColour(self):
        return self.defaultFgColor if self.defaultFgColor is not None else wx.Window.GetForegroundColour(self)
        
    def SetBackgroundColour(self, color):
        if self.defaultBgColour is None:
            wx.Window.SetBackgroundColour(self, color)
        else:
            self.defaultBgColor = color

    def GetBackgroundColour(self):
        return self.defaultBgColor if self.defaultBgColor is not None else wx.Window.GetBackgroundColour(self)



    # Setters for dicts to be used for text value or value->color automatic
    # translations

    def SetTranslations(self, translations):
        self.translations = translations

    def SetForegroundColourTranslations(self, translations):
        self.fgColourTranslations = translations

    def SetBackgroundColourTranslations(self, translations):
        self.bgColourTranslations = translations

    @EpicsFunction
    def update(self,value=None):
        if value is None and self.pv is not None:
            value = self.pv.get(as_string=True)
        self.SetControlValue(value)

    @EpicsFunction
    def getValue(self,as_string=True):
        val = self.pv.get(as_string=as_string)
        result = self.translations.get(val, val)
        return result
        
    def _warn(self,msg):
        sys.stderr.write("%s for pv='%s'\n" % (msg,self.pv.pvname))
    
    @DelayedEpicsCallback
    def _pvEvent(self,pvname=None,value=None,wid=None,char_value=None,**kw):
        # if pvname is None or id == 0: return
        # print 'generic pv event handler ', pvname, value
        if pvname is None or value is None or wid is None:  return
        if char_value is None and value is not None:
            prec = kw.get('precision',None)
            if prec not in (None,0):
                char_value = ("%%.%if" % prec) % value
            else:
                char_value = set_float(value)
        self.SetControlValue(char_value)

    @EpicsFunction
    def set_pv(self, pv=None):
        if isinstance(pv, epics.PV) or isinstance(pv, epics.PVTuple):
            self.pv = pv
        elif isinstance(pv, (str, unicode)):
            self.pv = epics.PV(pv)
            self.pv.connect()
        if self.pv is None:
            return

        epics.poll()
        self.pv.get_ctrlvars()
        if not self.pv.connected:
            return
        
        self.SetControlValue(self.pv.get(as_string=True))
        self.pv.add_callback(self._pvEvent, wid=self.GetId() )


class pvTextCtrl(wx.TextCtrl, pvCtrlMixin):
    """ text control for PV display (as normal string), with callback for automatic updates"""
    def __init__(self, parent,  pv=None, 
                 font=None, fg=None, bg=None, **kw):

        wx.TextCtrl.__init__(self,parent, wx.ID_ANY, value='', **kw)
        pvCtrlMixin.__init__(self, pv=pv, font=font, fg=None, bg=None)
        self.Bind(wx.EVT_CHAR, self.onChar)

    def onChar(self, event):
        key   = event.GetKeyCode()
        entry = wx.TextCtrl.GetValue(self).strip()
        pos   = wx.TextCtrl.GetSelection(self)
        if (key == wx.WXK_RETURN):
            self._caput(entry)
        event.Skip()
            

    @EpicsFunction
    def _caput(self, value):
        self.pv.put(value)
    
    def _SetValue(self, value):
        self.SetValue(value)

class pvText(wx.StaticText, pvCtrlMixin):
    """ static text for PV display, with callback for automatic updates"""
    def __init__(self, parent, pv=None, as_string=True,
                 font=None, fg=None, bg=None, style=None, 
                 minor_alarm="DARKRED", major_alarm="RED",
                 invalid_alarm="ORANGERED", units="", **kw):
        wstyle = wx.ALIGN_LEFT
        if style is not None:
            wstyle = style

        wx.StaticText.__init__(self, parent, wx.ID_ANY, label='',
                               style=wstyle, **kw)
        pvCtrlMixin.__init__(self, pv=pv, font=font,fg=None, bg=None)
        
        self.as_string = as_string
        self.units = units

        self.fgColourAlarms = {
            1 : minor_alarm,
            2 : major_alarm,
            3 : invalid_alarm } # alarm severities do not have an enum in pyepics
 
            

    def _SetValue(self,value):
        if value is not None:
            self.SetLabel("%s%s" % (value, self.units))

        
class pvEnumButtons(wx.Panel, pvCtrlMixin):
    """ a panel of buttons for Epics ENUM controls """
    def __init__(self, parent, pv=None, 
                 orientation=wx.HORIZONTAL,  **kw):

        wx.Panel.__init__(self, parent, wx.ID_ANY, **kw)
        pvCtrlMixin.__init__(self, pv=pv)

        time.sleep(0.001)
        if pv.type != 'enum':
            self._warn('pvEnumButtons needs an enum PV')
            return
        
        pv.get(as_string=True)
        
        sizer = wx.BoxSizer(orientation)
        self.buttons = []
        for i,label in enumerate(pv.enum_strs):
            b = buttons.GenToggleButton(self, -1, label)
            self.buttons.append(b)
            b.Bind(wx.EVT_BUTTON, closure(self._onButton, index=i) )
            sizer.Add(b, flag = wx.ALL)
            b.SetToggle(0)

        self.buttons[pv.value].SetToggle(1)
                   
        self.SetAutoLayout(True)
        self.SetSizer(sizer)
        sizer.Fit(self)

    @EpicsFunction
    def _onButton(self,event=None,index=None, **kw):
        if self.pv is None: return
        if index is not None:
            self.pv.put(index)

    @DelayedEpicsCallback
    def _pvEvent(self, pvname=None, value=None, wid=None, **kw):
        if pvname is None or value is None:
            return
        for i, btn in enumerate(self.buttons):
            btn.up =  (i != value)
            btn.Refresh()

    def _SetValue(self,value):
        pass

class pvEnumChoice(wx.Choice, pvCtrlMixin):
    """ a dropdown choice for Epics ENUM controls """
    
    def __init__(self, parent, pv=None, **kw):
        wx.Choice.__init__(self, parent, wx.ID_ANY, **kw)
        pvCtrlMixin.__init__(self, pv=pv)

        if pv.type != 'enum':
            self._warn('pvEnumChoice needs an enum PV')
            return

        self.Clear()
        pv.get(as_string=True)
        
        self.AppendItems(pv.enum_strs)
        self.SetSelection(pv.value)
        self.Bind(wx.EVT_CHOICE, self.onChoice)

    def onChoice(self,event=None, **kw):
        if self.pv is None: return
        index = self.pv.enum_strs.index(event.GetString())
        self.pv.put(index)

    @DelayedEpicsCallback
    def _pvEvent(self, pvname=None, value=None, wid=None, **kw):
        if pvname is None or value is None: return
        self.SetSelection(value)

    def _SetValue(self,value):
        self.SetStringSelection(value)


class pvAlarm(wx.MessageDialog, pvCtrlMixin):
    """ Alarm Message for a PV: a MessageDialog will pop up when a
    PV trips some alarm level"""
   
    def __init__(self, parent,  pv=None, 
                 font=None, fg=None, bg=None, trip_point=None, **kw):

        pvCtrlMixin.__init__(self,pv=pv,font=font,fg=None,bg=None)
       
    def _SetValue(self,value): pass
    
        
class pvFloatCtrl(FloatCtrl, pvCtrlMixin):
    """ float control for PV display of numerical data,
    with callback for automatic updates, and
    automatic determination of string/float controls

    Options:
       parent     wx widget of parent
       pv         epics pv to use for value
       precision  number of digits past decimal point to display (default to PV's precision)
       font       wx font
       fg         wx foreground color
       bg         wx background color 
       
       bell_on_invalid  ring bell when input is out of range

    """
    def __init__(self, parent, pv=None, 
                 font=None, fg=None, bg=None, precision=None, **kw):

        self.pv = None
        FloatCtrl.__init__(self, parent, value=0,
                           precision=precision, **kw)
        pvCtrlMixin.__init__(self,pv=pv,
                             font=font, fg=None, bg=None)

    def _SetValue(self,value):
        self.SetValue(value)
    
    @EpicsFunction
    def set_pv(self, pv=None):
        # print 'FloatCtrl: SET PV ', pvname, type(pvname), isinstance(pvname, epics.PV)
        if isinstance(pv, epics.PV):
            self.pv = pv
        elif isinstance(pv, (str, unicode)):
            self.pv = epics.PV(pv)
        if self.pv is None:
            return
        self.pv.get()
        self.pv.get_ctrlvars()
        # be sure to set precision before value!! or PV may be moved!!
        prec = self.pv.precision
        if prec is None: prec = 0
        self.SetPrecision(prec)

        self.SetValue(self.pv.char_value, act=False)

        if self.pv.type in ('string','char'):
            self._warn('pvFloatCtrl needs a double or float PV')
            
        self.SetMin(self.pv.lower_ctrl_limit)
        self.SetMax(self.pv.upper_ctrl_limit)
        self.pv.add_callback(self._FloatpvEvent, wid=self.GetId())
        self.SetAction(self._onEnter)

    @DelayedEpicsCallback
    def _FloatpvEvent(self,pvname=None,value=None,wid=None,char_value=None,**kw):
        # if pvname is None or id == 0: return
        # print 'FloatvEvent: ', pvname, value, char_value, wid

        if pvname is None or value is None or wid is None:  return
        if char_value is None and value is not None:
            prec = kw.get('precision',None)
            if prec not in (None,0):
                char_value = ("%%.%if" % prec) % value
            else:
                char_value = set_float(value)                

        self.SetValue(char_value, act=False)

    @EpicsFunction
    def _onEnter(self,value=None,**kw):
        if value in (None,'') or self.pv is None:
            return 
        try:
            if float(value) != self.pv.get():
                self.pv.put(float(value))
        except:
            pass


class pvBitmap(wx.StaticBitmap, pvCtrlMixin):
    """ Static Bitmap where image is based on PV value, with callback for automatic updates"""        
    def __init__(self, parent,  pv=None, bitmaps={},
                 defaultBitmap=None, **kw):
        wx.StaticBitmap.__init__(self,parent, wx.ID_ANY, bitmap=defaultBitmap, **kw)
        pvCtrlMixin.__init__(self, pv=pv)

        self.defaultBitmap = defaultBitmap
        self.bitmaps = bitmaps        

    def _SetValue(self, value):        
        if value in self.bitmaps:
            nextBitmap = self.bitmaps[value]
        else:
            nextBitmap = self.defaultBitmap        
        if nextBitmap != self.GetBitmap():
            self.SetBitmap(nextBitmap)

class pvCheckBox(wx.CheckBox, pvCtrlMixin):
    """ Checkbox based on a binary PV value, both reads/writes the
        PV on changes.
   
        If necessary, use the SetTranslations() option to write a
        dictionary for string value PVs to booleans
        
        If a PVTuple is assigned, the checkbox can act as a "master
        checkbox" (including with a 3-state value if the right style
        is set) that sets/clears all the PVs in the tuple as one.
        """
    def __init__(self, parent, pv=None, on_value=1, off_value=0, **kw):
        self.pv = None
        wx.CheckBox.__init__(self, parent, **kw)
        pvCtrlMixin.__init__(self, pv=pv, font="", fg=None, bg=None)
        wx.EVT_CHECKBOX(parent, self.GetId(), self._OnClicked)
        self.on_value = on_value
        self.off_value = off_value

    def _SetValue(self, value):
        if isinstance(self.pv, epics.PVTuple):
            rawValue = [ bool(r) for r in list(self.pv.get()) ]
            if all(rawValue):
                self.ThreeStateValue = wx.CHK_CHECKED
            elif self.Is3State() and any(rawValue):
                self.ThreeStateValue = wx.CHK_UNDETERMINED
            else:
                self.ThreeStateValue = wx.CHK_UNCHECKED
        else:
            self.Value = bool(self.pv.get())

    def _OnClicked(self, event):
        self.pv.put(self.on_value if self.Value else self.off_value )


class pvFloatSpin(floatspin.FloatSpin, pvCtrlMixin): 
    """ A FloatSpin (floating-point-aware SpinCtrl) linked to a PV,
        both reads and writes the PV on changes.
        
        Additional Arguments:
        pv = pv to set
        deadTime = delay between user typing a value into the field, and it being sent
    """
    def __init__(self, parent, pv=None, deadTime=500, **kw):
        floatspin.FloatSpin.__init__(self, parent, **kw)
        pvCtrlMixin.__init__(self, pv=pv, font="", fg=None, bg=None)
        floatspin.EVT_FLOATSPIN(parent, self.GetId(), self._OnChanged)
        
        self.deadTimer = wx.Timer(self)
        self.deadTime = deadTime
        wx.EVT_TIMER(self, self.deadTimer.GetId(), self._OnCharTimeout)
        
    def _SetValue(self, value):
        value = self.pv.get() # get a non-string value
        self.SetValue(float(value))

    def _OnChanged(self, event):
        if self.pv is not None:
            value = self.GetValue()
            if self.pv.upper_ctrl_limit <> 0 or self.pv.lower_ctrl_limit <> 0: # both zero -> not set
                if value > self.pv.upper_ctrl_limit:
                    value = self.pv.upper_ctrl_limit
                    self.SetValue(value)
                if value < self.pv.lower_ctrl_limit:
                    value = self.pv.lower_ctrl_limit
                    self.SetValue(value)            
            self.pv.put(value)

    def _OnCharTimeout(self, event):
        # save & restore insertion point before syncing control
        savePoint = self.GetTextCtrl().InsertionPoint
        self.SyncSpinToText()
        self.GetTextCtrl().InsertionPoint = savePoint  
        self._OnChanged(event)

    def OnChar(self, event):
        floatspin.FloatSpin.OnChar(self, event)
        # Timer will restart if it's already running
        self.deadTimer.Start(milliseconds=self.deadTime, oneShot=True)



       
class pvButton(wx.Button, pvCtrlMixin):
    """ A Button linked to a PV. When the button is pressed, a certain value
        is written to the PV (useful for momentary PVs with HIGH= set.)

        Additional Arguments:
        pv = pv to write back to
        pushValue = value to write when button is pressed
        disablePV = read this PV in order to disable the button
        disableValue = disable the button if/when the disablePV has this value
        
    """
    def __init__(self, parent, pv=None, pushValue=1, disablePV=None, disableValue=1, **kw):
        wx.Button.__init__(self, parent, **kw)
        pvCtrlMixin.__init__(self, pv=pv, font="", fg=None, bg=None)
        self.pushValue = pushValue
        wx.EVT_BUTTON(self, self.GetId(), self.OnPress)

        self.disablePV = disablePV
        self.disableValue = disableValue            
        if disablePV is not None:
            self.disablePV.add_callback(self._disableEvent, wid=self.GetId())     
        self.maskedEnabled = True
            

    def Enable(self, value):
        self.maskedEnabled = value
        self._UpdateEnabled()

    def _UpdateEnabled(self):
        enableValue = self.maskedEnabled
        if self.disablePV is not None and (self.disablePV.get() == self.disableValue):
            enableValue = False
        if self.pv is not None and ( self.pv.get() == self.pushValue ):
            enableValue = False
        wx.Button.Enable(self, enableValue)
        
    @DelayedEpicsCallback
    def _disableEvent(self, **kw):
        self._UpdateEnabled()

    def _SetValue(self, event):
        self._UpdateEnabled()

    def OnPress(self, event):
        self.pv.put(self.pushValue)

    

class pvRadioButton(wx.RadioButton, pvCtrlMixin):
    """A pvRadioButton is a radio button associated with a particular PV and one particular value.
       
       Suggested for use in a group where all radio buttons are pvRadioButtons, and they all have a
       discrete value set.
    """
    def __init__(self, parent, pv=None, pvValue=None, **kw):
        wx.RadioButton.__init__(self, parent, **kw)
        pvCtrlMixin.__init__(self, pv=pv, font="", fg=None, bg=None)
        self.pvValue = pvValue
        wx.EVT_RADIOBUTTON(self, self.GetId(), self.OnPress)

    def OnPress(self, event):
        self.pv.put(self.pvValue)
        
    def _SetValue(self, value):
        if self.pv.get() == self.pvValue: # use raw PV val as is not string-converted
            self.Value = True

        
class pvComboBox(wx.ComboBox, pvCtrlMixin):
    """ A ComboBox linked to a PV. Both reads/writes the combo value on changes
    """
    def __init__(self, parent, pv=None, **kw):
        wx.ComboBox.__init__(self, parent, **kw)
        pvCtrlMixin.__init__(self, pv=pv, font="", fg=None, bg=None)
        wx.EVT_TEXT(self, self.GetId(), self.OnText)
        
    def _SetValue(self, value):
        # print "pvComboBox %s _SetValue %s" % (self, self.pv.get(as_string=True))
        if value != self.Value:
            self.Value = value
    
    def OnText(self, event):
        self.pv.put(self.Value)
