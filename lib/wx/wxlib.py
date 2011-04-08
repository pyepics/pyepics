"""
wx utility functions for Epics and wxPython interaction
"""
import wx
from wx._core import PyDeadObjectError
                   
import time
import sys
import epics
import wx.lib.buttons as buttons
import wx.lib.agw.floatspin as floatspin

from utils import Closure, FloatCtrl, set_float

def EpicsFunction(f):
    """decorator to wrap function in a wx.CallAfter() so that
    Epics calls can be made in a separate thread, and asynchronously.

    This decorator should be used for all code that mix calls to
    wx and epics    
    """
    def wrapper(*args, **kwargs):
        "callafter wrapper"
        wx.CallAfter(f, *args, **kwargs)
    return wrapper

def DelayedEpicsCallback(fcn):
    """decorator to wrap an Epics callback in a wx.CallAfter,
    so that the wx and epics ca threads do not clash
    This also checks for dead wxPython objects (say, from a
    closed window), and remove callbacks to them.
    """
    def wrapper(*args, **kw):
        "callafter wrapper"
        def cb():
            "default callback"
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
        "stop timer"
        self.timer.Stop()

    def StartTimer(self):
        "start timer"
        self.timer.Start(self.period)
        
    def pend(self, event=None):
        "pend/poll"
        epics.ca.poll()



class pvMixin:
    """ base class mixin for any class that needs PV wx callback
        support.
        
        If you're working with wxwidgets controls, see pvCtrlMixin.
        If you're working with wx OGL drawing, see ogllib.pvShapeMixin.

        Classes deriving directly from pvMixin must override OnPVChange()     
    """
    def __init__(self, pv=None, pvname=None):
        self.pv = None
        if pv is None and pvname is not None:
            pv = pvname
        if pv is not None:
            self.set_pv(pv)


    @EpicsFunction
    def set_pv(self, pv=None):
        if isinstance(pv, epics.PV):
            # or isinstance(pv, epics.PVTuple):
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
        
        self.OnPVChange(self.pv.get(as_string=True))
        self.pv.add_callback(self._pvEvent, wid=self.GetId() )


    @DelayedEpicsCallback
    def _pvEvent(self, pvname=None, value=None, wid=None,
                 char_value=None, **kws):
        # if pvname is None or id == 0: return
        # print 'generic pv event handler ', pvname, value
        if pvname is None or value is None or wid is None:
            return
        if char_value is None and value is not None:
            prec = kws.get('precision', None)
            if prec not in (None, 0):
                char_value = ("%%.%if" % prec) % value
            else:
                char_value = set_float(value)
        self.OnPVChange(char_value)


    @EpicsFunction
    def update(self, value=None):
        if value is None and self.pv is not None:
            value = self.pv.get(as_string=True)
        self.OnPVChange(value)

    @EpicsFunction
    def getValue(self, as_string=True):
        val = self.pv.get(as_string=as_string)
        result = self.translations.get(val, val)
        return result

    """ This method is called any time the PV value changes, via update() or via
        a PV callback
    """
    def OnPVChange(self, raw_value):        
        self._warn("Must override OnPVChange")

    def _warn(self, msg):
        sys.stderr.write("%s for pv='%s'\n" % (msg, self.pv.pvname))



class pvCtrlMixin(pvMixin):
    """ 
    mixin for wx Controls with epics PVs:  connects to PV,
    and manages callback events for the PV

    An overriding class must provide a method called _SetValue, which
    will set the contents of the corresponding widget.
    

    Optional Features for descendents
    =================================

    * Set a translation dictionary of PVValue->Python Value to be used
      whenever values are received via PV callbacks.

    * Set translation tables for setting particular foreground/background
      colours when the PV takes certain values.

    * Override foreground/background colours - without knowing what
      colour is currently set by the user, you can call
      OverrideForegroundColour()/OverrideBackGroundColor() to set a
      different colour on the control and then call the override again
      with None to go back to the original colour.
      
    """

    def __init__(self, pv=None, pvname=None, font=None, fg=None, bg=None):
        pvMixin.__init__(self, pv, pvname)

        self.translations = {}
        self.fgColourTranslations = None
        self.bgColourTranslations = None
        self.fgColourAlarms = {}
        self.bgColourAlarms = {}

        #if font is None:
        #    font = wx.Font(12, wx.SWISS, wx.NORMAL, wx.BOLD,False)
        
        try:
            if font is not None:  self.SetFont(font)
            if fg   is not None:  self.SetForegroundColour(fg)
            if bg   is not None:  self.SetBackgroundColour(fg)
        except:
            pass
        self.defaultFgColour = None
        self.defaultBgColour = None


    def SetTranslations(self, translations):
        """ 
        Pass a dictionary of value->value translations here if you want some PV values
        to automatically appear in the event callback as a different value.

        ie, to override PV value 0.0 to say "Disabled", call this method as
        control.SetTranslations({ 0.0 : "Disabled" })

        It is recommended that you use this function only when it is not possible to change
        the PV value in the database, or set a string value in the database.

        """
        self.translations = translations

    def SetForegroundColourTranslations(self, translations):
        """
        Pass a dictionary of value->colour translations here if you want the control
        to automatically set foreground colour based on PV value.

        Values used to lookup colours will be string values if available, but will otherwise
        be the raw PV value.

        Colour values in the dictionary may be strings or wx.Colour objects.

        """
        self.fgColourTranslations = translations

    def SetBackgroundColourTranslations(self, translations):
        """
        Pass a dictionary of value->colour translations here if you want the control
        to automatically set background colour based on PV value.

        Values used to lookup colours will be string values if available, but will otherwise
        be the raw PV value.

        Colour values in the dictionary may be strings or wx.Colour objects.

        """
        self.bgColourTranslations = translations
            

    def SetForegroundColour(self, colour):
        """ (Internal override) Needed to support OverrideForegroundColour() """
        if self.defaultFgColour is None:
            wx.Window.SetForegroundColour(self, colour)
        else:
            self.defaultFgColour = colour

    def GetForegroundColour(self):
        """ (Internal override) Needed to support OverrideForegroundColour()
        """
        return self.defaultFgColour if self.defaultFgColour is not None \
               else wx.Window.GetForegroundColour(self)
        
    def SetBackgroundColour(self, colour):
        """ (Internal override) Needed to support OverrideBackgroundColour()
        """
        if self.defaultBgColour is None:
            wx.Window.SetBackgroundColour(self, colour)
        else:
            self.defaultBgColour = colour

    def GetBackgroundColour(self):
        """ (Internal override) Needed to support OverrideBackgroundColour() """
        return self.defaultBgColour if self.defaultBgColour is not None \
               else wx.Window.GetBackgroundColour(self)

    def OverrideForegroundColour(self, colour):
        """
        Call this method to override the control's current set foreground colour,
        Call with colour=None to disable overriding and go back to whatever was set.

        Overriding allows SetForegroundColour() to still work as expected, except
        when the "override" is set.

        """
        if colour is None:
            if self.defaultFgColour is not None:
                wx.Window.SetForegroundColour(self, self.defaultFgColour)
                self.defaultFgColour = None
        else:
            if self.defaultFgColour is None:
                self.defaultFgColour = wx.Window.GetForegroundColour(self)
            wx.Window.SetForegroundColour(self, colour)      

    def OverrideBackgroundColour(self, colour):
        """
        Call this method to override the control's current set background colour,
        Call with colour=None to disable overriding and go back to whatever was set.

        Overriding allows SetForegroundColour() to still work as expected, except
        when the "override" is set.

        """
        if colour is None:
            if self.defaultBgColour is not None:
                wx.Window.SetBackgroundColour(self, self.defaultBgColour)
        else:
            if self.defaultBgColour is None:
                self.defaultBgColour = wx.Window.GetBackgroundColour(self)
            wx.Window.SetBackgroundColour(self, colour)

    def _SetValue(self, value):
        self._warn("must override _SetValue")

    def OnPVChange(self, raw_value):        
        if self.pv is None:
            return
        if len(self.fgColourAlarms) > 0 or len(self.bgColourAlarms) > 0:
            # load severity if we care about it
            # NB: this may be a performance problem
            self.pv.get_ctrlvars()

        colour = None
        if self.fgColourTranslations is not None and \
           raw_value in self.fgColourTranslations:
            colour = self.fgColourTranslations[raw_value]
        elif self.pv.severity in self.fgColourAlarms:
            colour = self.fgColourAlarms[self.pv.severity]        
        self.OverrideForegroundColour(colour)
            
        colour = None
        if self.bgColourTranslations is not None and \
           raw_value in self.bgColourTranslations:
            colour = self.bgColourTranslations[raw_value]
        elif self.pv.severity in self.bgColourAlarms:
            colour = self.bgColourAlarms[self.pv.severity]
        self.OverrideBackgroundColour(colour)
            
        self._SetValue(self.translations.get(raw_value, raw_value))



class pvTextCtrl(wx.TextCtrl, pvCtrlMixin):
    """
    Text control (ie textbox) for PV display (as normal string), 
    with callback for automatic updates and option to write value
    back on input

    """
    def __init__(self, parent,  pv=None, 
                 font=None, fg=None, bg=None, **kws):

        wx.TextCtrl.__init__(self, parent, wx.ID_ANY, value='', **kws)
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
    """ Static text for displaying a PV value, 
        with callback for automatic updates
        
        By default the text colour will change on alarm states.
        This can be overriden or disabled as constructor
        parameters
        """
    def __init__(self, parent, pv=None, as_string=True,
                 font=None, fg=None, bg=None, style=None, 
                 minor_alarm="DARKRED", major_alarm="RED",
                 invalid_alarm="ORANGERED", units="", **kw):
        """
        Create a new pvText

        minor_alarm, major_alarm & invalid_alarm are all text colours
        that will be set depending no the alarm state of the target
        PV. Set to None if you want no highlighting in that alarm state.
        """

        wstyle = wx.ALIGN_LEFT
        if style is not None:
            wstyle = style

        wx.StaticText.__init__(self, parent, wx.ID_ANY, label='',
                               style=wstyle, **kw)
        pvCtrlMixin.__init__(self, pv=pv, font=font, fg=None, bg=None)
        
        self.as_string = as_string
        self.units = units

        self.fgColourAlarms = {
            1 : minor_alarm,
            2 : major_alarm,
            3 : invalid_alarm } #alarm severities do not have an enum
                                #in pyepics??
 
    def _SetValue(self, value):
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
        for i, label in enumerate(pv.enum_strs):
            b = buttons.GenToggleButton(self, -1, label)
            self.buttons.append(b)
            b.Bind(wx.EVT_BUTTON, Closure(self._onButton, index=i) )
            sizer.Add(b, flag = wx.ALL)
            b.SetToggle(0)

        self.buttons[pv.value].SetToggle(1)
                   
        self.SetAutoLayout(True)
        self.SetSizer(sizer)
        sizer.Fit(self)

    @EpicsFunction
    def _onButton(self, event=None, index=None, **kw):
        if self.pv is None:
            return
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
        if self.pv is None:
            return
        index = self.pv.enum_strs.index(event.GetString())
        self.pv.put(index)

    @DelayedEpicsCallback
    def _pvEvent(self, pvname=None, value=None, wid=None, **kw):
        if pvname is None or value is None:
            return
        self.SetSelection(value)

    def _SetValue(self,value):
        self.SetStringSelection(value)


class pvAlarm(wx.MessageDialog, pvCtrlMixin):
    """ Alarm Message for a PV: a MessageDialog will pop up when a
    PV trips some alarm level"""
   
    def __init__(self, parent,  pv=None, 
                 font=None, fg=None, bg=None, trip_point=None, **kw):

        pvCtrlMixin.__init__(self, pv=pv, font=font, fg=None, bg=None)
       
    def _SetValue(self,value): pass
    
        
class pvFloatCtrl(FloatCtrl, pvCtrlMixin):
    """ Float control for PV display of numerical data,
    with callback for automatic updates, and
    automatic determination of string/float controls

    Options:
       parent     wx widget of parent
       pv         epics pv to use for value
       precision  number of digits past decimal point to display
                  (default to PV's precision)
       font       wx font
       fg         wx foreground colour
       bg         wx background colour 
       
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
    def _FloatpvEvent(self, pvname=None, value=None, wid=None,
                      char_value=None, **kw):
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
    """ 
    Static Bitmap where image is based on PV value,
    with callback for automatic updates

    """        
    def __init__(self, parent,  pv=None, bitmaps={},
                 defaultBitmap=None, **kw):
        """
        bitmaps - a dict of Value->Bitmap mappings, to automatically change
        the shown bitmap based on the PV value.

        defaultBitmap - the bitmap to show if the PV value doesn't match any
        of the values in the bitmaps dict.

        """
        wx.StaticBitmap.__init__(self, parent, wx.ID_ANY,
                                 bitmap=defaultBitmap, **kw)
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
    """ 
    Checkbox based on a binary PV value, both reads/writes the
    PV on changes.
   
    There are multiple options for translating PV values to checkbox
    settings (from least to most complex):

    * Use a PV with values 0 and 1
    * Use a PV with values that convert via Python's own bool(x)
    * Set on_value and off_value in the constructor
    * Use SetTranslations() to set a dictionary for converting various
      PV values to booleans.

    """
    def __init__(self, parent, pv=None, on_value=1, off_value=0, **kw):
        self.pv = None
        wx.CheckBox.__init__(self, parent, **kw)
        pvCtrlMixin.__init__(self, pv=pv, font="", fg=None, bg=None)
        wx.EVT_CHECKBOX(parent, self.GetId(), self._OnClicked)
        self.on_value = on_value
        self.off_value = off_value
        self.OnChange = None

    def _SetValue(self, value):
        if value in [ self.on_value, self.off_value ]:
            self.Value = (value == self.on_value)
        else:
            self.Value = bool(self.pv.get())

        if self.OnChange != None:
            self.OnChange(self)

    def _OnClicked(self, event):
        if self.pv is not None:
            self.pv.put(self.on_value if self.Value else self.off_value )

    def SetValue(self, new_value):
        old_value = self.Value
        wx.CheckBox.SetValue(self, new_value)
        if old_value != new_value:
            self._OnClicked(None)        

    # need to redefine the value Property as the old property refs old SetValue
    Value = property(wx.CheckBox.GetValue, SetValue)


class pvFloatSpin(floatspin.FloatSpin, pvCtrlMixin): 
    """ 
    A FloatSpin (floating-point-aware SpinCtrl) linked to a PV,
    both reads and writes the PV on changes.
        
    """
    def __init__(self, parent, pv=None, deadTime=500,
                 min_val=None, max_val=None, increment=1.0, digits=-1, **kw):
        """
        Most arguments are common with FloatSpin.

        Additional Arguments: 
        pv = pv to set 
        deadTime = delay (ms) between user typing a value into the field, 
        and it being set to the PV
        
        """
        floatspin.FloatSpin.__init__(self, parent,
                                     min_val=min_val, max_val=max_val,
                                     increment=increment, digits=digits, **kw)
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
            if self.pv.upper_ctrl_limit != 0 or self.pv.lower_ctrl_limit != 0:
                # both zero -> not set
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

    """
    def __init__(self, parent, pv=None, pushValue=1,
                 disablePV=None, disableValue=1, **kw):
        """
        pv = pv to write back to
        pushValue = value to write when button is pressed
        disablePV = read this PV in order to disable the button
        disableValue = disable the button if/when the disablePV has this value

        """
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
        if self.disablePV is not None and \
           (self.disablePV.get() == self.disableValue):
            enableValue = False
        if self.pv is not None and (self.pv.get() == self.pushValue):
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
    """A pvRadioButton is a radio button associated with a particular PV
    and one particular value.       
    Suggested for use in a group where all radio buttons are
    pvRadioButtons, and they all have a discrete value set.

    """
    def __init__(self, parent, pv=None, pvValue=None, **kw):
        """
        pvValue = This value will be written to the PV when the radiobutton is
        pushed, and the radiobutton will become select if/when the PV is set to
        this value.
           The value used is raw numeric, not "as string"
        """
        wx.RadioButton.__init__(self, parent, **kw)
        pvCtrlMixin.__init__(self, pv=pv, font="", fg=None, bg=None)
        self.pvValue = pvValue
        wx.EVT_RADIOBUTTON(self, self.GetId(), self.OnPress)

    def OnPress(self, event):
        self.pv.put(self.pvValue)
        
    def _SetValue(self, value):
        # uses raw PV val as is not string-converted
        if self.pv.get() == self.pvValue: 
            self.Value = True

        
class pvComboBox(wx.ComboBox, pvCtrlMixin):
    """ A ComboBox linked to a PV. Both reads/writes the combo value on changes

    """
    def __init__(self, parent, pv=None, **kw):
        wx.ComboBox.__init__(self, parent, **kw)
        pvCtrlMixin.__init__(self, pv=pv, font="", fg=None, bg=None)
        wx.EVT_TEXT(self, self.GetId(), self.OnText)
        
    def _SetValue(self, value):
        if value != self.Value:
            self.Value = value
    
    def OnText(self, event):
        self.pv.put(self.Value)
        
class pvToggleButton(wx.ToggleButton, pvCtrlMixin):
    """A ToggleButton that can be attached to a bi or bo Epics record."""
    
    def __init__(self, parent, pv=None, down=1, up_colour=None,
                 down_colour=None, **kwargs):
        """
        Create a ToggleButton and attach it to a bi or bo record.
        
        Toggling the button will toggle the bi/bo record (and vice versa.) The
        button label is the ONAM or ZNAM values of the record. Note the label
        displays the opposite state of the bi/bo record, i.e., it shows what
        will happen if the button is clicked.
        
        parent: Parent window of the ToggleButton.
        pv: Process variable attached to the ToggleButton. A bi/bo record.
        down: pv.value representing a down button. Default 1.
        up_colour: Background colour of button when it is up. Default None.
        down_colour: Background colour of button when it is down. Default None.
        """
        wx.ToggleButton.__init__(self, parent, wx.ID_ANY, label='', **kwargs)
        pvCtrlMixin.__init__(self, pv=pv)
        
        self.down = down
        self.up_colour = up_colour
        self.down_colour = down_colour
        self.Bind(wx.EVT_TOGGLEBUTTON, self._onButton)

    @EpicsFunction
    def _onButton(self, event=None):
        self.labels = self.pv.enum_strs
        if self.GetValue():
            self.SetLabel(self.labels[0])
            self.pv.put(self.down == 1)
            self.SetBackgroundColour(self.down_colour)
        else:
            self.SetLabel(self.labels[1])
            self.pv.put(self.down == 0)
            self.SetBackgroundColour(self.up_colour)

    def _SetValue(self, value):
        self.labels = self.pv.enum_strs
        if value==self.labels[1]:
            self.SetValue(self.down==1)
            self.SetBackgroundColour(self.down_colour if self.down==1 \
                                     else self.up_colour)
            self.SetLabel(self.labels[0])
        else:
            self.SetValue(self.down==0)
            self.SetBackgroundColour(self.down_colour if self.down==0 \
                                     else self.up_colour)
            self.SetLabel(self.labels[1])


class pvStatusBar(wx.StatusBar, pvMixin):
    """A status bar that displays a pv value
    
    To use in a wxFrame:
        self.SetStatusBar(pvStatusBar(prent=self, pv=PV(...), style=...)
    """
    
    def __init__(self, parent=None, pv=None, **kwargs):
        """
        Create a stsus bar that displays a pv value.
        """
        wx.StatusBar.__init__(self, parent, wx.ID_ANY, **kwargs)
        pvMixin.__init__(self, pv=pv)
    
    def OnPVChange(self, rawValue):
        self.SetStatusText(self.pv.get())

