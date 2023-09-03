"""
wx utility functions for Epics and wxPython interaction
"""
import wx

import time
import sys
import epics
import wx.lib.buttons as buttons
import wx.lib.agw.floatspin as floatspin

PyDeadObjectError = Exception

from .wxutils import Closure, FloatCtrl, set_float

def EpicsFunction(f):
    """decorator to wrap function in a wx.CallAfter() so that
    Epics calls can be made in a separate thread, and asynchronously.

    This decorator should be used for all code that mix calls to
    wx and epics
    """
    def wrapper(*args, **kwargs):
        "callafter wrapper"
        try:
            wx.CallAfter(f, *args, **kwargs)
        except PyDeadObjectError:
            pass
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
                    except RuntimeError:
                        pass
        if wx.GetApp() is not None:
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
    def __init__(self, parent, period=100, start=True):
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

    @EpicsFunction
    def pend(self, event=None):
        "pend/poll"
        epics.ca.poll()
        event.Skip()

class PVMixin(object):
    """ base class mixin for any class that needs PV wx callback
        support.

        If you're working with wxwidgets controls, see PVCtrlMixin.
        If you're working with wx OGL drawing, see ogllib.pvShapeMixin.

        Classes deriving directly from PVMixin must override OnPVChange()
    """
    def __init__(self, pv=None, pvname=None):
        self.pv = None
        if pv is None and pvname is not None:
            pv = pvname
        if pv is not None:
            self.SetPV(pv)

        self._popupmenu = None
        self.Bind(wx.EVT_RIGHT_DOWN, self._onRightDown)

    def _onRightDown(self, event=None):
        """right button down: show pop-up"""
        if event is None:
            return
        if self._popupmenu is None:
            self.build_popupmenu()
        wx.CallAfter(self.PopupMenu, self._popupmenu, event.GetPosition())
        event.Skip()

    def build_popupmenu(self, event=None):
        self._copy_name = wx.NewId()
        self._copy_val  = wx.NewId()
        self._show_info = wx.NewId()
        self._popupmenu = wx.Menu()
        self._popupmenu.Append(self._copy_name, 'Copy PV Name to Clipboard')
        self._popupmenu.Append(self._copy_val,  'Copy PV Value to Clipboard')
        self._popupmenu.AppendSeparator()
        self._popupmenu.Append(self._show_info, 'Show PV Info')

        self.Bind(wx.EVT_MENU, self.copy_name,  id=self._copy_name)
        self.Bind(wx.EVT_MENU, self.copy_val,   id=self._copy_val)
        self.Bind(wx.EVT_MENU, self.show_info,  id=self._show_info)

    @EpicsFunction
    def copy_name(self, event=None):
        dat = wx.TextDataObject()
        dat.SetText(self.pv.pvname)
        wx.TheClipboard.Open()
        wx.TheClipboard.SetData(dat)
        wx.TheClipboard.Close()

    @EpicsFunction
    def copy_val(self, event=None):
        dat = wx.TextDataObject()
        dat.SetText(self.pv.get(as_string=True))
        wx.TheClipboard.Open()
        wx.TheClipboard.SetData(dat)
        wx.TheClipboard.Close()

    @EpicsFunction
    def show_info(self, event=None):
        dlg = wx.MessageDialog(self, self.pv.info,
                               'Info for %s' % self.pv.pvname,
                               wx.OK|wx.ICON_INFORMATION)
        dlg.ShowModal()
        dlg.Destroy()

    @EpicsFunction
    def SetPV(self, pv=None):
        "set pv, either an epics.PV object or a pvname"
        if pv is None:
            return
        if isinstance(pv, epics.PV):
            self.pv = pv
        elif isinstance(pv, str):
            form = "ctrl" if len(self._fg_colour_alarms) > 0 or len(self._bg_colour_alarms) > 0 else "native"
            self.pv = epics.get_pv(pv, form=form)
            self.pv.connect()

        epics.poll()
        self.pv.connection_callbacks.append(self.OnEpicsConnect)
        if self.pv.connected:
            self.OnEpicsConnect(pvname=self.pv.pvname, conn=True, pv=self.pv)

        self.pv.get_ctrlvars()

        self.OnPVChange(self.pv.get(as_string=True))
        ncback = len(self.pv.callbacks) + 1
        self.pv.add_callback(self._pvEvent, wid=self.GetId(), cb_info=ncback)
        # print " PVMixin add callback for ", self.pv, self.pv.chid, len(self.pv.callbacks)

    @DelayedEpicsCallback
    def OnEpicsConnect(self, pvname=None, conn=None, pv=None):
        """Connect Callback:
             Enable/Disable widget on change in connection status
        """
        pass

    @DelayedEpicsCallback
    def _pvEvent(self, pvname=None, value=None, wid=None,
                 char_value=None, **kws):
        "epics PV callback function"
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
    def Update(self, value=None):
        "update value"
        if value is None and self.pv is not None:
            value = self.pv.get(as_string=True)
        self.OnPVChange(value)

    @EpicsFunction
    def GetValue(self, as_string=True):
        "return value"
        val = self.pv.get(as_string=as_string)
        result = self.translations.get(val, val)
        return result

    def OnPVChange(self, str_value):
        """method is called any time the PV value changes, via
        Update() or via a PV callback
        """
        self._warn("Must override OnPVChange")

    def _warn(self, msg):
        "write warning"
        sys.stderr.write("%s for pv='%s'\n" % (msg, self.pv.pvname))

    @EpicsFunction
    def GetEnumStrings(self):
        """try to get list of enum strings,
        returns enum strings or None"""
        epics.poll()
        out = None
        if isinstance(self.pv, epics.PV):
            self.pv.get_ctrlvars()
            if self.pv.type == 'enum':
                out =list(self.pv.enum_strs)
        return out

class PVCtrlMixin(PVMixin):
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
        PVMixin.__init__(self, pv, pvname)

        self._translations = {}
        self._fg_colour_translations = None
        self._bg_colour_translations = None
        self._fg_colour_alarms = {}
        self._bg_colour_alarms = {}
        self._default_fg_colour = None
        self._default_bg_colour = None

        try:
            if font is not None:
                self.SetFont(font)
            if fg   is not None:
                self.SetForegroundColour(fg)
            if bg   is not None:
                self.SetBackgroundColour(fg)
        except:
            pass
        self._connect_bgcol = self.GetBackgroundColour()
        self._connect_fgcol = self.GetForegroundColour()

    @DelayedEpicsCallback
    def OnEpicsConnect(self, pvname=None, conn=None, pv=None):
        """Connect Callback:
             Enable/Disable widget on change in connection status
        """
        PVMixin.OnEpicsConnect(self, pvname, conn, pv)
        action = getattr(self, 'Enable', None)
        bgcol = self._connect_bgcol
        fgcol = self._connect_fgcol
        if not conn:
            action = getattr(self, 'Disable', None)
            self._connect_bgcol = self.GetBackgroundColour()
            self._connect_fgcol = self.GetForegroundColour()
            bgcol = wx.Colour(240, 240, 210)
            fgcol = wx.Colour(200, 100, 100)
        if action is not None:
            self.SetBackgroundColour(bgcol)
            self.SetForegroundColour(fgcol)
            action()



    def SetTranslations(self, translations):
        """
        Pass a dictionary of value->value translations here if you want some P
        PV values to automatically appear in the event callback as a different
        value.

        ie, to override PV value 0.0 to say "Disabled", call this method as
        control.SetTranslations({ 0.0 : "Disabled" })

        It is recommended that you use this function only when it is not
        possible to change the PV value in the database, or set a string
        value in the database.
        """
        self._translations = translations

    def SetForegroundColourTranslations(self, translations):
        """
        Pass a dictionary of value->colour translations here if you want the
        control to automatically set foreground colour based on PV value.

        Values used to lookup colours will be string values if available,
        but will otherwise be the raw PV value.

        Colour values in the dictionary may be strings or wx.Colour objects.
        """
        self._fg_colour_translations = translations

    def SetBackgroundColourTranslations(self, translations):
        """
        Pass a dictionary of value->colour translations here if you want the
        control to automatically set background colour based on PV value.

        Values used to lookup colours will be string values if available,
        but will otherwise be the raw PV value.

        Colour values in the dictionary may be strings or wx.Colour objects.

        """
        self._bg_colour_translations = translations

    def SetForegroundColour(self, colour):
        """ (Internal override) Needed to support OverrideForegroundColour()
        """
        if self._default_fg_colour is None:
            wx.Window.SetForegroundColour(self, colour)
        else:
            self._default_fg_colour = colour

    def GetForegroundColour(self):
        """ (Internal override) Needed to support OverrideForegroundColour()
        """
        return self._default_fg_colour if self._default_fg_colour is not None \
               else wx.Window.GetForegroundColour(self)

    def SetBackgroundColour(self, colour):
        """ (Internal override) Needed to support OverrideBackgroundColour()
        """
        if self._default_bg_colour is None:
            wx.Window.SetBackgroundColour(self, colour)
        else:
            self._default_bg_colour = colour

    def GetBackgroundColour(self):
        """ (Internal override) Needed to support OverrideBackgroundColour()
        """
        return self._default_bg_colour if self._default_bg_colour is not None \
               else wx.Window.GetBackgroundColour(self)

    def OverrideForegroundColour(self, colour):
        """
        Call this method to override the control's current set foreground
        colour.  Call with colour=None to disable overriding and go back to
        whatever was set.

        Overriding allows SetForegroundColour() to still work as expected,
        except when the "override" is set.
        """
        if colour is None:
            if self._default_fg_colour is not None:
                wx.Window.SetForegroundColour(self, self._default_fg_colour)
                self._default_fg_colour = None
        else:
            if self._default_fg_colour is None:
                self._default_fg_colour = wx.Window.GetForegroundColour(self)
            wx.Window.SetForegroundColour(self, colour)

    def OverrideBackgroundColour(self, colour):
        """
        Call this method to override the control's current set background
        colour, Call with colour=None to disable overriding and go back to
        whatever was set.

        Overriding allows SetForegroundColour() to still work as expected,
        except when the "override" is set.
        """
        if colour is None:
            if self._default_bg_colour is not None:
                wx.Window.SetBackgroundColour(self, self._default_bg_colour)
        else:
            if self._default_bg_colour is None:
                self._default_bg_colour = wx.Window.GetBackgroundColour(self)
            wx.Window.SetBackgroundColour(self, colour)

    def _SetValue(self, value):
        "set value -- must override"
        self._warn("must override _SetValue")

    @EpicsFunction
    def OnPVChange(self, raw_value):
        "called by PV callback"
        try:
            if self.pv is None:
                return
            if self.pv.form == "native" \
               and ( len(self._fg_colour_alarms) > 0 or
                     len(self._bg_colour_alarms) > 0 ):
                # native PVs don't update severity on callback,
                # so we need to do the same manually
                self.pv.get_ctrlvars()

            colour = None
            if self._fg_colour_translations is not None and \
               raw_value in self._fg_colour_translations:
                colour = self._fg_colour_translations[raw_value]
            elif self.pv.severity in self._fg_colour_alarms:
                colour = self._fg_colour_alarms[self.pv.severity]
            self.OverrideForegroundColour(colour)

            colour = None
            if self._bg_colour_translations is not None and \
               raw_value in self._bg_colour_translations:
                colour = self._bg_colour_translations[raw_value]
            elif self.pv.severity in self._bg_colour_alarms:
                colour = self._bg_colour_alarms[self.pv.severity]
            self.OverrideBackgroundColour(colour)
            try:
                self._SetValue(self._translations.get(raw_value, raw_value))
            except TypeError:
                pass
        except PyDeadObjectError:
            pass


class PVTextCtrl(wx.TextCtrl, PVCtrlMixin):
    """
    Text control (ie textbox) for PV display (as normal string),
    with callback for automatic updates and option to write value
    back on input
    """
    def __init__(self, parent,  pv=None,
                 font=None, fg=None, bg=None, dirty_timeout=2500, **kws):

        if 'style' not in kws:
            kws['style'] = wx.TE_PROCESS_ENTER
        else:
            kws['style'] |= wx.TE_PROCESS_ENTER

        wx.TextCtrl.__init__(self, parent, wx.ID_ANY, value='', **kws)
        PVCtrlMixin.__init__(self, pv=pv, font=font, fg=fg, bg=bg)
        self.Bind(wx.EVT_CHAR, self.OnChar)
        self.dirty_timeout = dirty_timeout
        self.dirty_writeback_timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.OnWriteback)
        self.Bind(wx.EVT_KILL_FOCUS, self.OnWriteback)
        self.Bind(wx.EVT_CHAR, self.OnChar)


    @EpicsFunction
    def _caput(self, value):
        "epics pv.put wrapper"
        self.pv.put(str(value))

    def SetValue(self, value):
        "override all setvalue"
        self._caput(value)

    def _SetValue(self, value):
        "set widget value"
        wx.TextCtrl.SetValue(self, value)

    def OnChar(self, event):
        "char event handler"
        if event.KeyCode == wx.WXK_RETURN:
            self.OnWriteback()
        else:
            if self.dirty_timeout is not None:
                self.dirty_writeback_timer.Start(self.dirty_timeout)
            event.Skip()

    def OnWriteback(self, event=None):
        """ writeback the currently displayed value to the PV """
        self.dirty_writeback_timer.Stop()
        entry = str(self.GetValue().strip())
        self.SetValue(entry)

class PVText(wx.StaticText, PVCtrlMixin):
    """ Static text for displaying a PV value,
        with callback for automatic updates

        By default the text colour will change on alarm states.
        This can be overriden or disabled as constructor
        parameters
        """
    def __init__(self, parent, pv=None, as_string=True,
                 font=None, fg=None, bg=None, style=None,
                 minor_alarm="DARKRED", major_alarm="RED",
                 invalid_alarm="ORANGERED", auto_units=False, units="", **kw):
        """
        Create a new pvText

        minor_alarm, major_alarm & invalid_alarm are all text colours
        that will be set depending no the alarm state of the target
        PV. Set to None if you want no highlighting in that alarm state.

        auto_units means the PV value will be displayed with the EGU
        "engineering units" as a suffix. Alternately, you can specify
        an explicit unit string.
        """

        wstyle = wx.ALIGN_LEFT
        if style is not None:
            wstyle = style

        wx.StaticText.__init__(self, parent, wx.ID_ANY, label='',
                               style=wstyle, **kw)
        PVCtrlMixin.__init__(self, pv=pv, font=font, fg=fg, bg=bg)

        self.as_string = as_string
        self.auto_units = auto_units
        self.units = units

        self._fg_colour_alarms = {
            epics.MINOR_ALARM : minor_alarm,
            epics.MAJOR_ALARM : major_alarm,
            epics.INVALID_ALARM : invalid_alarm }

    def _SetValue(self, value):
        "set widget label"
        if self.auto_units and self.pv.units:
            self.units = " " + self.pv.units
        if value is not None:
            self.SetLabel("%s%s" % (value, self.units))


class PVStaticText(wx.StaticText, PVMixin):
    """ Static text for displaying a PV value,
        with callback for automatic updates

        By default the text colour will change on alarm states.
        This can be overriden or disabled as constructor
        parameters
        """
    def __init__(self, parent, pv=None, style=None,
                 minor_alarm="DARKRED", major_alarm="RED",
                 invalid_alarm="ORANGERED", **kw):
        wstyle = wx.ALIGN_LEFT
        if style is not None:
            wstyle = style

        wx.StaticText.__init__(self, parent, wx.ID_ANY, label='',
                               style=wstyle, **kw)
        PVMixin.__init__(self, pv=pv)
        self._fg_colour_alarms = {
            epics.MINOR_ALARM : minor_alarm,
            epics.MAJOR_ALARM : major_alarm,
            epics.INVALID_ALARM : invalid_alarm }


    def _SetValue(self, value):
        "set widget label"
        if value is not None:
            self.SetLabel("%s" % value)

    @EpicsFunction
    def OnPVChange(self, value):
        "called by PV callback"
        try:
            if self.pv is None:
                return
            self.SetLabel(value)
        except:
            pass

class PVEnumButtons(wx.Panel, PVCtrlMixin):
    """ a panel of buttons for Epics ENUM controls """
    def __init__(self, parent, pv=None,
                 orientation=wx.HORIZONTAL,  **kw):

        self.orientation = orientation
        wx.Panel.__init__(self, parent, wx.ID_ANY, **kw)
        PVCtrlMixin.__init__(self, pv=pv)

    @EpicsFunction
    def SetPV(self, pv=None):
        "set pv, either an epics.PV object or a pvname"
        if pv is None:
            return
        if isinstance(pv, epics.PV):
            self.pv = pv
        elif isinstance(pv, str):
            self.pv = epics.get_pv(pv)
            self.pv.connect()

        epics.poll()
        self.pv.connection_callbacks.append(self.OnEpicsConnect)

        self.pv.get_ctrlvars()

        self.OnPVChange(self.pv.get(as_string=True))
        ncback = len(self.pv.callbacks) + 1
        self.pv.add_callback(self._pvEvent, wid=self.GetId(), cb_info=ncback)

        pv_value = pv.get(as_string=True)
        enum_strings = pv.enum_strs

        sizer = wx.BoxSizer(self.orientation)
        self.buttons = []
        if enum_strings is not None:
            for i, label in enumerate(enum_strings):
                b = buttons.GenToggleButton(self, -1, label)
                self.buttons.append(b)
                b.Bind(wx.EVT_BUTTON, Closure(self._onButton, index=i) )
                b.Bind(wx.EVT_RIGHT_DOWN, self._onRightDown)
                sizer.Add(b, flag = wx.ALL)
                b.SetToggle(label==pv_value)

        self.SetAutoLayout(True)
        self.SetSizer(sizer)
        sizer.Fit(self)


    @EpicsFunction
    def _onButton(self, event=None, index=None, **kw):
        "button event handler"
        if self.pv is not None and index is not None:
            self.pv.put(index)

    @DelayedEpicsCallback
    def _pvEvent(self, pvname=None, value=None, wid=None, **kw):
        "pv event handler"
        if pvname is None or value is None:
            return
        for i, btn in enumerate(self.buttons):
            btn.up = (i != value)
            btn.Refresh()

    def _SetValue(self, value):
        "not implemented"
        pass

class PVEnumChoice(wx.Choice, PVCtrlMixin):
    """ a dropdown choice for Epics ENUM controls """

    def __init__(self, parent, pv=None, **kw):
        wx.Choice.__init__(self, parent, wx.ID_ANY, **kw)
        PVCtrlMixin.__init__(self, pv=pv)

    @EpicsFunction
    def SetPV(self, pv=None):
        "set pv, either an epics.PV object or a pvname"
        if pv is None:
            return
        if isinstance(pv, epics.PV):
            self.pv = pv
        elif isinstance(pv, str):
            self.pv = epics.get_pv(pv)
            self.pv.connect()

        epics.poll()
        self.pv.connection_callbacks.append(self.OnEpicsConnect)

        self.pv.get_ctrlvars()

        self.OnPVChange(self.pv.get(as_string=True))
        ncback = len(self.pv.callbacks) + 1
        self.pv.add_callback(self._pvEvent, wid=self.GetId(), cb_info=ncback)

        self.Bind(wx.EVT_CHOICE, self._onChoice)

        pv_value = self.pv.get(as_string=True)
        enum_strings = self.pv.enum_strs

        self.Clear()
        self.AppendItems(enum_strings)
        self.SetStringSelection(pv_value)

    def _onChoice(self, event=None, **kws):
        "choice event handler"
        if self.pv is not None:
            index = self.pv.enum_strs.index(event.GetString())
            self.pv.put(index)

    @DelayedEpicsCallback
    def _pvEvent(self, pvname=None, value=None, **kw):
        "pv event handler"
        if value is not None:
            self.SetSelection(value)

    def _SetValue(self, value):
        "set value"
        self.SetStringSelection(value)

class PVAlarm(wx.MessageDialog, PVCtrlMixin):
    """ Alarm Message for a PV: a MessageDialog will pop up when a
    PV trips some alarm level"""

    def __init__(self, parent,  pv=None,
                 font=None, fg=None, bg=None, trip_point=None, **kw):

        PVCtrlMixin.__init__(self, pv=pv, font=font, fg=None, bg=None)

    def _SetValue(self, value):
        "set value -- null op for pvAlarm"
        pass

class PVFloatCtrl(FloatCtrl, PVCtrlMixin):
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
        PVCtrlMixin.__init__(self, pv=pv, font=font, fg=None, bg=None)

    def _SetValue(self, value):
        "set widget value"
        FloatCtrl.SetValue(self, value, act=False)

    @EpicsFunction
    def SetPV(self, pv=None):
        "set pv, either an epics.PV object or a pvname"
        if isinstance(pv, epics.PV):
            self.pv = pv
        elif isinstance(pv, str):
            self.pv = epics.get_pv(pv)
        if self.pv is None:
            return
        self.pv.connection_callbacks.append(self.OnEpicsConnect)
        self.pv.get()
        self.pv.get_ctrlvars()
        # be sure to set precision before value!! or PV may be moved!!
        prec = self.pv.precision
        if prec is None:
            prec = 0
        self.SetPrecision(prec)

        self.SetValue(self.pv.char_value, act=False)

        if self.pv.type in ('string', 'char'):
            try:
                x = float(self.pv.value)
            except:
                self._warn('pvFloatCtrl needs a double or float PV')

        llim = set_float(self.pv.lower_ctrl_limit)
        hlim = set_float(self.pv.upper_ctrl_limit)
        if hlim is not None and llim is not None and hlim > llim:
            self.SetMax(hlim)
            self.SetMin(llim)
        ncback = len(self.pv.callbacks) + 1
        self.pv.add_callback(self._pvEvent, wid=self.GetId(), cb_info=ncback)
        self.SetAction(self._onEnter)

    @DelayedEpicsCallback
    def _FloatpvEvent(self, pvname=None, value=None, wid=None,
                      char_value=None, **kw):
        "PV callback / event handler for pv change"

        if pvname is None or value is None or wid is None:
            return
        if char_value is None and value is not None:
            prec = kw.get('precision', None)
            if prec not in (None, 0):
                char_value = ("%%.%if" % prec) % value
            else:
                char_value = set_float(value)
        self.SetValue(char_value, act=False)

    @EpicsFunction
    def _onEnter(self, value=None, **kw):
        "enter/return event"
        if value in (None,'') or self.pv is None:
            return
        try:
            if float(value) != self.pv.get():
                self.pv.put(float(value))
        except:
            pass

class PVBitmap(wx.StaticBitmap, PVCtrlMixin):
    """
    Static Bitmap where image is based on PV value,
    with callback for automatic updates

    """
    def __init__(self, parent,  pv=None, bitmaps=None,
                 defaultBitmap=None, **kw):
        """
        bitmaps - a dict of Value->Bitmap mappings, to automatically change
        the shown bitmap based on the PV value.

        defaultBitmap - the bitmap to show if the PV value doesn't match any
        of the values in the bitmaps dict.

        """
        wx.StaticBitmap.__init__(self, parent, wx.ID_ANY,
                                 bitmap=defaultBitmap, **kw)
        PVCtrlMixin.__init__(self, pv=pv)

        self.defaultBitmap = defaultBitmap
        if bitmaps is None:
            bitmaps = {}
        self.bitmaps = bitmaps


    def _SetValue(self, value):
        "set widget value"
        if value in self.bitmaps:
            nextBitmap = self.bitmaps[value]
        else:
            nextBitmap = self.defaultBitmap
        if nextBitmap != self.GetBitmap():
            self.SetBitmap(nextBitmap)

class PVCheckBox(wx.CheckBox, PVCtrlMixin):
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
        PVCtrlMixin.__init__(self, pv=pv, font="", fg=None, bg=None)
        wx.EVT_CHECKBOX(parent, self.GetId(), self.OnClicked)
        self.on_value = on_value
        self.off_value = off_value
        self.OnChange = None

    def _SetValue(self, value):
        "set widget value"
        if value in (self.on_value, self.off_value):
            self.Value = (value == self.on_value)
        else:
            self.Value = bool(self.pv.get())
        if callable(self.OnChange):
            self.OnChange(self)

    @EpicsFunction
    def OnClicked(self, event=None):
        "checkbox event handler"
        if self.pv is not None:
            self.pv.put(self.on_value if self.Value else self.off_value)

    def SetValue(self, new_value):
        "set widget value"
        old_value = self.Value
        wx.CheckBox.SetValue(self, new_value)
        if old_value != new_value:
            self.OnClicked(None)

    # need to redefine the value Property as the old property refs old SetValue
    Value = property(wx.CheckBox.GetValue, SetValue)

class PVFloatSpin(floatspin.FloatSpin, PVCtrlMixin):
    """
    A FloatSpin (floating-point-aware SpinCtrl) linked to a PV,
    both reads and writes the PV on changes.

    """
    def __init__(self, parent, pv=None, deadTime=2500,
                 min_val=None, max_val=None, increment=1.0, digits=-1, **kw):
        """
        Most arguments are common with FloatSpin.

        Additional Arguments:
        pv = pv to set
        deadTime = delay (ms) between user typing a value into the field,
        and it being set to the PV

        """
        floatspin.FloatSpin.__init__(self, parent, increment=increment,
                                     min_val=min_val, max_val=max_val,
                                     digits=digits, **kw)
        PVCtrlMixin.__init__(self, pv=pv, font="", fg=None, bg=None)
        floatspin.EVT_FLOATSPIN(parent, self.GetId(), self.OnSpin)

        self.deadTimer = wx.Timer(self)
        self.deadTime = deadTime
        wx.EVT_TIMER(self, self.deadTimer.GetId(), self.OnTimeout)

    @EpicsFunction
    def _SetValue(self, value):
        "set value"
        floatspin.FloatSpin.SetValue(self, float(self.pv.get()))

    @EpicsFunction
    def OnSpin(self, event=None):
        "spin event handler"
        if self.pv is not None:
            value = self.GetValue()
            if self.pv.upper_ctrl_limit != 0 or self.pv.lower_ctrl_limit != 0:
                # both zero -> not set
                if value > self.pv.upper_ctrl_limit:
                    value = self.pv.upper_ctrl_limit
                if value < self.pv.lower_ctrl_limit:
                    value = self.pv.lower_ctrl_limit
                self.SetValue(value)

    def OnTimeout(self, event):
        "timer event handler"
        # save & restore insertion point before syncing control
        savePoint = self.GetTextCtrl().InsertionPoint
        self.SyncSpinToText()
        self.GetTextCtrl().InsertionPoint = savePoint
        self.OnSpin(event)

    def OnChar(self, event):
        "floatspin char  event"
        floatspin.FloatSpin.OnChar(self, event)
        # Timer will restart if it's already running
        self.deadTimer.Start(milliseconds=self.deadTime, oneShot=True)

    def SetValue(self, value):
        floatspin.FloatSpin.SetValue(self, value)
        if hasattr(self, "pv"): # can be called before PV is assigned
            self.pv.put(value)


class PVSpinCtrl(wx.SpinCtrl, PVCtrlMixin):
    """
    A SpinCtrl  linked to a PV,
    both reads and writes the PV on changes.

    """
    def __init__(self, parent, pv=None,
                 min_val=None, max_val=None, **kws):
        """
        Most arguments are common with SpinCtrl

        Additional Arguments:
        pv = pv to set
        deadTime = delay (ms) between user typing a value into the field,
        and it being set to the PV

        """
        wx.SpinCtrl.__init__(self, parent, **kws)
        PVCtrlMixin.__init__(self, pv=pv, font="", fg=None, bg=None)
        self.Bind(wx.EVT_SPINCTRL, self.OnSpin)

    @EpicsFunction
    def _SetValue(self, value):
        "set value"
        wx.SpinCtrl.SetValue(self, self.pv.get())
        if hasattr(self, "pv"): # can be called before PV is assigned
            self.pv.put(value)

    @EpicsFunction
    def OnSpin(self, event=None):
        "spin event handler"
        self._SetValue(self.GetValue())

class PVButton(wx.Button, PVCtrlMixin):
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
        PVCtrlMixin.__init__(self, pv=pv, font="", fg=None, bg=None)
        self.pushValue = pushValue
        self.Bind(wx.EVT_BUTTON, self.OnPress)
        if isinstance(disablePV, str):
            disablePV = epics.get_pv(disablePV)
            disablePV.connect()
        self.disablePV = disablePV
        self.disableValue = disableValue
        if disablePV is not None:
            ncback = len(self.disablePV.callbacks) + 1
            self.disablePV.add_callback(self._disableEvent, wid=self.GetId(),
                                        cb_info=ncback)
        self.maskedEnabled = True

    def Enable(self, value=None):
        "enable button"
        if value is not None:
            self.maskedEnabled = value
        self._UpdateEnabled()

    @EpicsFunction
    def _UpdateEnabled(self):
        "epics function, called by event handler"
        enableValue = self.maskedEnabled
        if self.disablePV is not None and \
           (self.disablePV.get() == self.disableValue):
            enableValue = False
        if self.pv is not None and (self.pv.get() == self.pushValue):
            enableValue = False
        wx.Button.Enable(self, enableValue)

    @DelayedEpicsCallback
    def _disableEvent(self, **kw):
        "disable event handler"
        self._UpdateEnabled()

    def _SetValue(self, event):
        "set value"
        self._UpdateEnabled()

    @EpicsFunction
    def OnPress(self, event):
        "button press event handler"
        self.pv.put(self.pushValue)

class PVBitmapButton(wx.BitmapButton, PVCtrlMixin):
    """ A Button linked to a PV. When the button is pressed, a certain value
        is written to the PV (useful for momentary PVs with HIGH= set.)

    """
    def __init__(self, parent, pv=None, pushValue=1,
                 disablePV=None, disableValue=1, bitmap = None, **kw):
        """
        pv = pv to write back to
        pushValue = value to write when button is pressed
        disablePV = read this PV in order to disable the button
        disableValue = disable the button if/when the disablePV has this value
        bitmap = in image from the wx.ArtProvider library

        """
        wx.BitmapButton.__init__(self, parent, bitmap = bitmap, **kw)
        PVCtrlMixin.__init__(self, pv=pv, font="", fg=None, bg=None)
        self.pushValue = pushValue
        self.Bind(wx.EVT_BUTTON, self.OnPress)
        if isinstance(disablePV, str):
            disablePV = epics.get_pv(disablePV)
            disablePV.connect()
        self.disablePV = disablePV
        self.disableValue = disableValue
        if disablePV is not None:
            ncback = len(self.disablePV.callbacks) + 1
            self.disablePV.add_callback(self._disableEvent, wid=self.GetId(),
                                        cb_info=ncback)
        self.maskedEnabled = True

    def Enable(self, value=None):
        "enable button"
        if value is not None:
            self.maskedEnabled = value
        self._UpdateEnabled()

    @EpicsFunction
    def _UpdateEnabled(self):
        "epics function, called by event handler"
        enableValue = self.maskedEnabled
        if self.disablePV is not None and \
           (self.disablePV.get() == self.disableValue):
            enableValue = False
        from numpy import array_equal, ndarray, generic
        if isinstance(self.pushValue, (ndarray, generic)):
            if self.pv is not None and (array_equal(self.pv.get(),self.pushValue)):
                enableValue = False
        else:
            if self.pv is not None and (self.pv.get() is self.pushValue):
                enableValue = False
        wx.Button.Enable(self, enableValue)

    @DelayedEpicsCallback
    def _disableEvent(self, **kw):
        "disable event handler"
        self._UpdateEnabled()

    def _SetValue(self, event):
        "set value"
        self._UpdateEnabled()

    @EpicsFunction
    def OnPress(self, event):
        "button press event handler"
        self.pv.put(self.pushValue)

class PVRadioButton(wx.RadioButton, PVCtrlMixin):
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
        PVCtrlMixin.__init__(self, pv=pv, font="", fg=None, bg=None)
        self.pvValue = pvValue
        self.Bind(wx.EVT_RADIOBUTTON, self.OnPress)

    @EpicsFunction
    def OnPress(self, event):
        "button press event handler"
        self.pv.put(self.pvValue)

    @EpicsFunction
    def _SetValue(self, value):
        "set value"
        # uses raw PV val as is not string-converted
        if value == self.pvValue or self.pv.get() == self.pvValue:
            self.Value = True


class PVComboBox(wx.ComboBox, PVCtrlMixin):
    """ A ComboBox linked to a PV. Both reads/writes the combo value on changes

    """
    def __init__(self, parent, pv=None, **kw):
        wx.ComboBox.__init__(self, parent, **kw)
        PVCtrlMixin.__init__(self, pv=pv, font="", fg=None, bg=None)
        self.Bind(wx.EVT_TEXT, self.OnText)

    def _SetValue(self, value):
        "set value"
        if value != self.Value:
            self.Value = value

    @EpicsFunction
    def OnText(self, event):
        "text event"
        self.pv.put(self.Value)

class PVEnumComboBox(PVComboBox):
    """ A dropdown ComboBox linked to an enum PV, allows setting of enum values.
    Both reads/writes the combo value on changes
    """
    def __init__(self, parent, pv=None, **kw):
        PVComboBox.__init__(self, parent, pv, style=wx.CB_DROPDOWN|wx.CB_READONLY, **kw)

    @DelayedEpicsCallback
    def OnEpicsConnect(self, pvname=None, conn=None, pv=None):
        PVComboBox.OnEpicsConnect(self, pvname, conn, pv)
        if conn:
            self.Clear()
            for enum in self.pv.enum_strs:
                self.Append(enum)
            self.Value = self.pv.get(as_string=True)

class PVToggleButton(wx.ToggleButton, PVCtrlMixin):
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
        PVCtrlMixin.__init__(self, pv=pv)

        self.down = down
        self.up_colour = up_colour
        self.down_colour = down_colour
        self.Bind(wx.EVT_TOGGLEBUTTON, self._onButton)

    @EpicsFunction
    def _onButton(self, event=None):
        "button event handler"
        self.labels = self.pv.enum_strs
        if self.GetValue():
            self.SetLabel(self.labels[0])
            self.pv.put(self.down == 1)
            self.SetBackgroundColour(self.down_colour)
        else:
            self.SetLabel(self.labels[1])
            self.pv.put(self.down == 0)
            self.SetBackgroundColour(self.up_colour)

    @EpicsFunction
    def _SetValue(self, value):
        "set value"
        self.labels = self.pv.enum_strs
        if value == self.labels[1]:
            self.SetValue(self.down==1)
            self.SetBackgroundColour(self.down_colour if self.down==1 \
                                     else self.up_colour)
            self.SetLabel(self.labels[0])
        else:
            self.SetValue(self.down==0)
            self.SetBackgroundColour(self.down_colour if self.down==0 \
                                     else self.up_colour)
            self.SetLabel(self.labels[1])

class PVStatusBar(wx.StatusBar, PVMixin):
    """A status bar that displays a pv value

    To use in a wxFrame:
        self.SetStatusBar(pvStatusBar(prent=self, pv=PV(...), style=...)
    """

    def __init__(self, parent=None, pv=None, **kwargs):
        """
        Create a stsus bar that displays a pv value.
        """
        wx.StatusBar.__init__(self, parent, wx.ID_ANY, **kwargs)
        PVMixin.__init__(self, pv=pv)

    @EpicsFunction
    def OnPVChange(self, str_value):
        "called by PV callback"
        self.SetStatusText(str_value)


class PVCollapsiblePane(wx.CollapsiblePane, PVCtrlMixin):
    """A collapsible pane where the display on the collapsed line is set
    from a PV value
    """

    def __init__(self, parent, pv=None, minor_alarm="DARKRED", major_alarm="RED",
                 invalid_alarm="ORANGERED", **kw):
        wx.CollapsiblePane.__init__(self, parent, **kw)
        PVCtrlMixin.__init__(self, pv=pv, font=None, fg=None, bg=None)
        self._fg_colour_alarms = {
            epics.MINOR_ALARM : minor_alarm,
            epics.MAJOR_ALARM : major_alarm,
            epics.INVALID_ALARM : invalid_alarm }
        if self.pv:
            _SetValue(self.pv.value)

    def _SetValue(self, value):
        if value:
            self.SetLabel(value)
