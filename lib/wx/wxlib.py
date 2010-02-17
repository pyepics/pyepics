"""
wx utility functions for Epics and wxPython interaction
"""
import wx
from wx._core import PyDeadObjectError
                   
import time
import types
import fpformat
import epics
import wx.lib.buttons as buttons

def set_sizer(panel,sizer=None, style=wx.VERTICAL,fit=False):
    """ utility for setting wx Sizer  """
    if sizer is None:  sizer = wx.BoxSizer(style)
    panel.SetAutoLayout(1)
    panel.SetSizer(sizer)
    if fit: sizer.Fit(panel)

def set_float(val,default=None):
    """ utility to set a floating value, useful for converting from strings """
    if val in (None,''): return default
    try:
        return float(val)
    except:
        return default
        
class closure:
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
        if (self.func == None): return None
        self.args = args
        return apply(self.func,self.args,self.kw)


class FloatCtrl(wx.TextCtrl):
    """ Numerical Float Control::
      a wx.TextCtrl that allows only numerical input, can take a precision argument
      and optional upper / lower bounds
    """
    def __init__(self, parent, value='', min='', max='', 
                 action=None,  precision=3, action_kw={}, **kwargs):
        
        self.__digits = '0123456789.-'
        self.__prec   = precision
        if precision is None: self.__prec = 0
        self.format   = '%%.%if' % self.__prec
        
        self.__val = set_float(value)
        self.__max = set_float(max)
        self.__min = set_float(min)

        self.fgcol_valid   ="Black"
        self.bgcol_valid   ="White"
        self.fgcol_invalid ="Red"
        self.bgcol_invalid =(254,254,80)

        
        # set up action 
        self.__action = closure()  
        if callable(action):  self.__action.func = action
        if len(action_kw.keys())>0:  self.__action.kw = action_kw

        this_sty =  wx.TE_PROCESS_ENTER|wx.TE_RIGHT
        kw = kwargs
        if kw.has_key('style'): this_sty = this_sty | kw['style']
        kw['style'] = this_sty
            
        wx.TextCtrl.__init__(self, parent, wx.ID_ANY, **kw)        

        self.__CheckValid(self.__val)
        self.SetValue(self.__val)
              
        self.Bind(wx.EVT_CHAR, self.onChar)
        # self.Bind(wx.EVT_CHAR, self.CharEvent)        
        self.Bind(wx.EVT_TEXT, self.onText)

        self.Bind(wx.EVT_SET_FOCUS,  self.onSetFocus)
        self.Bind(wx.EVT_KILL_FOCUS, self.onKillFocus)
        self.Bind(wx.EVT_SIZE, self.onResize)
        self.__GetMark()

    def SetAction(self,action,action_kw={}):
        self.__action = closure()  
        if callable(action):         self.__action.func = action
        if len(action_kw.keys())>0:  self.__action.kw = action_kw
        
    def SetPrecision(self,p):
        if p is None: p = 0
        self.__prec = p
        self.format = '%%.%if' % p
        
    def __GetMark(self):
        " keep track of cursor position within text"
        try:
            self.__mark = min(wx.TextCtrl.GetSelection(self)[0],
                              len(wx.TextCtrl.GetValue(self).strip()))
        except:
            self.__mark = 0

    def __SetMark(self,m=None):
        " "
        if m==None: m = self.__mark
        self.SetSelection(m,m)

    def SetValue(self,value=None,act=True):
        " main method to set value "
        if value == None: value = wx.TextCtrl.GetValue(self).strip()
        self.__CheckValid(value)
        self.__GetMark()
        if self.__valid:
            self.__Text_SetValue(self.__val)
            self.SetForegroundColour(self.fgcol_valid)
            self.SetBackgroundColour(self.bgcol_valid)
            if  callable(self.__action) and act:  self.__action(value=self.__val)
        else:
            self.__val = self.__bound_val
            self.__Text_SetValue(self.__val)
            self.__CheckValid(self.__val)
            self.SetForegroundColour(self.fgcol_invalid)
            self.SetBackgroundColour(self.bgcol_invalid)
            wx.Bell()
        self.__SetMark()
        
    def onKillFocus(self, event):
        self.__GetMark()
        event.Skip()

    def onResize(self, event):
        event.Skip()
        
    def onSetFocus(self, event=None):
        self.__SetMark()
        if event: event.Skip()
      
    def onChar(self, event):
        """ on Character event"""
        key   = event.GetKeyCode()
        entry = wx.TextCtrl.GetValue(self).strip()
        pos   = wx.TextCtrl.GetSelection(self)
        # really, the order here is important:
        # 1. return sends to ValidateEntry
        if (key == wx.WXK_RETURN):
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
        if (chr(key) in self.__digits):
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

    def GetMin(self):  return self.__min
    def GetMax(self):  return self.__max
    def SetMin(self,min): self.__min = set_float(min)
    def SetMax(self,max): self.__max = set_float(max)
    
    def __Text_SetValue(self,value):
        wx.TextCtrl.SetValue(self, self.format % set_float(value))
        self.Refresh()
    
    def __CheckValid(self,value):
        # print ' Check valid ', value
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

class catimer:
    """ Epics Event Timer:
    combines a wxTimer and ca.poll to manage Epics Events in a wx Application.
    """
    def __init__(self,parent, time=25, **kw):
        self.parent = parent
        self.callbacks = {} 
        self.needs_callback = []
        self.time = time
        self._timer = wx.Timer(self.parent)
        self.StartTimer()
        
    def StopTimer(self):
        self._timer.Stop()
        
    def StartTimer(self):
        self.parent.Bind(wx.EVT_TIMER, self.pend)
        self._timer.Start(self.time)

    def _proxy_callback(self,pvname=None,wid=-1,**kw):
        if pvname not in self.needs_callback:
            self.needs_callback.append((pvname,wid,kw))

    def __default_callback(self,pvname=None,char_value=None,**kw):
        try:
            print "  %s= %s  at %s " % (pvname, char_value, time.ctime())
        except:
            print " _def callback execption??" , pvname, char_value

    def add_callback(self,pv,callback,wid,**kw):
        if pv is None: return
        index = pv.add_callback(self._proxy_callback,**kw)
        if callback is None:
            callback = self.__default_callback

        if pv.pvname not in self.callbacks:
            self.callbacks[pv.pvname] = {}
        self.callbacks[pv.pvname][wid] = (callback,kw,pv,index)

    def remove_callback(self,pvname,wid=-1, **kw):
        try:
            cb,kw,pv,index = self.callbacks[pvname].pop(wid)
            pv.remove_callback(index=index)
        except:
            print 'Timer Failed to remove callback' , pvname,wid

    def remove_all_callback(self):
        try:
            self.needs_callback = []
            for pvname,d in self.callbacks.items():
                for wid in d:
                    cb,kw,pv,index = d[wid]
                    print 'timer remove callback: ', pvname, pv, index, cb
                    pv.remove_callback(index=index)

        except:
            print 'remove all callbacks failed'

          
    def __del__(self):
        try:
            self.remove_all_callbacks()
        except:
            pass
        
    def pend(self,foo=None,**more):
        epics.poll()
        if len(self.needs_callback) == 0 : return
        print 'tick ', len(self.needs_callback), len(self.callbacks)

        for pvname,xxid,kw in self.needs_callback:
            for wid,dat in self.callbacks[pvname].items():
                cb, kw_custom,pv,index = dat
                kw.update(kw_custom)
                if 'wid' not in kw: kw['wid']=xxid
                if 'pvname' not in kw: kw['pvname']=pvname
                try:
                    cb(**kw)
                except PyDeadObjectError:                    
                    print ' no callback for dead PV object?? ', pvname

        self.needs_callback = []


class pvTimerMixin(object):
    def onClose(self, evt, **kw):
        print 'pvTimerMixin. onclose ',id(self.timer), evt, kw, len(self.callbacks)
        epics.ca.poll()
        self.remove_callbacks()
        evt.Skip()
        print 'pvCtrlMixin Done.'
        
    def add_callback(self,pv,cb,wid,**kw):
        self.timer.add_callback(pv, cb, wid, **kw)
        self.callbacks.append((pv.pvname, wid))
        print 'pvTimerMixin: Add Callback ', id(self.timer), pv.pvname, wid, len(self.callbacks), len(self.timer.callbacks)
                       
    def remove_callbacks(self):
        print 'pvTimerMixin remove callbacks ', id(self.timer), len(self.callbacks)
        for pvname,wid in self.callbacks:
            print '   remove callback ', id(self.timer), pvname, wid
            self.timer.remove_callback(pvname,wid)
        print '----'
        epics.ca.poll()
        print '-->> -'
        
    def __init__(self,timer=None):
        self.timer = timer 
        if self.timer is None:
            print 'Create New Timer'
            self.timer = catimer(self)
        self.callbacks = []

        wx.EVT_CLOSE(self, self.onClose)        
    
class pvCtrlMixin(pvTimerMixin):
    """ mixin for wx Controls with epics PVs:  connects to PV,
    sets a catimer, which manages callback events for the PV

    An overriding class must provide a method called _SetValue, which
    will set the contents of the corresponding widget.
    
    """

    def __init__(self,pvname=None, timer=None,
                 font=None, fg=None, bg=None):
        if font is None:  font = wx.Font(12,wx.SWISS,wx.NORMAL,wx.BOLD,False)
        
        pvTimerMixin.__init__(self,timer)

        self.pv = None
        try:
            if font is not None:  self.SetFont(font)
            if fg   is not None:  self.SetForegroundColour(fg)
            if bg   is not None:  self.SetBackgroundColour(fg)
        except:
            pass
        if pvname is not None: self.set_pv(pvname)

        wx.EVT_CLOSE(self, self.onClose)
        
#     def __del__(self):
#         try:
#             self.timer.remove_callback(self.pvname, wid=self.wid)
#         except:
#             pass
        
    def _SetValue(self,value):
        print 'pvCtrlMixin._SetValue must be overwritten for ', self.pv.pvname
        
    def update(self,value=None):
        if value is None: value = self.pv.get(as_string=True)
        self._SetValue(value)

    def getValue(self,as_string=True):
        return self.pv.get(as_string=as_string)
        
    def _pvEvent(self,pvname=None,value=None,wid=None,char_value=None,**kw):
        # if pvname is None or id == 0: return
        print 'Mixin _pvEvent' , pvname, wid, value, char_value
        pvname is None or value is None or wid is None:
            print 'Null Event'
            return
        if char_value is not None:
            self._SetValue(char_value)
        elif value is not None:
            self._SetValue(set_float(value))
            
    def set_pv(self,pvname=None):
        self.pv = epics.PV(pvname)
        if self.pv is None: return
        self.pv.connect()
        if not self.pv.connected: return
        self._SetValue(self.pv.char_value)
        self.add_callback(self.pv, self._pvEvent, self.GetId() )



class pvTextCtrl(wx.TextCtrl,pvCtrlMixin):
    """ text control for PV display (as normal string), with callback for automatic updates"""
    def __init__(self, parent,  pvname=None, timer=None,
                 font=None, fg=None, bg=None, **kw):

        wx.TextCtrl.__init__(self,parent, wx.ID_ANY, value='', **kw)
        pvCtrlMixin.__init__(self,pvname=pvname,timer=timer,
                             font=font,fg=None,bg=None)
    def _SetValue(self,value):
        self.SetValue(value)

class pvText(wx.StaticText,pvCtrlMixin):
    """ static text for PV display, with callback for automatic updates"""
    def __init__(self, parent, pvname=None, timer=None,
                 as_string=True,
                 font=None, fg=None, bg=None, **kw):
        
        self.as_string = as_string
        self.pvname =pvname

        userstyle = kw.get('style',None)
        kw['style'] = wx.ALIGN_RIGHT | wx.ST_NO_AUTORESIZE
        # if userstyle:         kw['style'] = kw['style'] | userstyle

        # print 'pvText ', kw['style'], wx.ALIGN_RIGHT, userstyle
        
        wx.StaticText.__init__(self,parent,wx.ID_ANY,label='',**kw)
        pvCtrlMixin.__init__(self,pvname=pvname,timer=timer,
                             font=font,fg=None,bg=None)
    def _SetValue(self,value):
        self.SetLabel(self.getValue(as_string=self.as_string)+ ' ')
        
class pvEnumButtons(wx.Panel,pvCtrlMixin):
    """ a panel of buttons for Epics ENUM controls """
    def __init__(self, parent, pvname=None, timer=None,
                 orientation=wx.HORIZONTAL,  **kw):

        wx.Panel.__init__(self, parent, wx.ID_ANY, **kw)
        pvCtrlMixin.__init__(self,pvname=pvname,timer=timer)
        
        if self.pv.type != 'enum':
            print 'need an enumeration type for pvEnumButtons! '
            return
        self.pv.get(as_string=True)
        
        sizer = wx.BoxSizer(orientation)
        self.buttons = []
        for i,label in enumerate(self.pv.enum_strs):
            b = buttons.GenToggleButton(self, -1, label)
            self.buttons.append(b)
            b.Bind(wx.EVT_BUTTON, closure(self._onButton, index=i) )
            sizer.Add(b, flag = wx.ALL)
            b.SetToggle(0)

        self.buttons[self.pv.value].SetToggle(1)
                   
        self.SetAutoLayout(True)
        self.SetSizer(sizer)
        sizer.Fit(self)
        
    def _onButton(self,event=None,index=None, **kw):
        if self.pv is None: return
        if index is not None:
            self.pv.put(index)

    def _pvEvent(self,pvname=None,value=None,wid=None,**kw):
        if pvname is None or value is None: return
        for i,btn in enumerate(self.buttons):
            btn.up =  (i != value)
            btn.Refresh()

    def _SetValue(self,value): pass

class pvEnumChoice(wx.Choice,pvCtrlMixin):
    """ a dropdown choice for Epics ENUM controls """
    
    def __init__(self, parent, pvname=None, timer=None,   **kw):
        wx.Choice.__init__(self, parent, wx.ID_ANY, **kw)
        pvCtrlMixin.__init__(self,pvname=pvname,timer=timer)

        if self.pv.type != 'enum':
            print 'need an enumeration type for pvEnumBuattons! '
            return

        self.Clear()
        self.pv.get(as_string=True)
        
        self.AppendItems(self.pv.enum_strs)
        self.SetSelection(self.pv.value)
        self.Bind(wx.EVT_CHOICE, self.onChoice)

    def onChoice(self,event=None, **kw):
        if self.pv is None: return
        index = self.pv.enum_strs.index(event.GetString())
        self.pv.put(index)

    def _pvEvent(self,pvname=None,value=None,wid=None,**kw):
        if pvname is None or value is None: return
        self.SetSelection(value)

    def _SetValue(self,value):
        self.SetStringSelection(value)


class pvAlarm(wx.MessageDialog,pvCtrlMixin):
    """ Alarm Message for a PV: a MessageDialog will pop up when a
    PV trips some alarm level"""
   
    def __init__(self, parent,  pvname=None, timer=None,
                 font=None, fg=None, bg=None, trip_point=None, **kw):

        pvCtrlMixin.__init__(self,pvname=pvname,timer=timer,
                             font=font,fg=None,bg=None)
       
    def _SetValue(self,value): pass
    
        
class pvFloatCtrl(FloatCtrl,pvCtrlMixin):
    """ float control for PV display of numerical data,
    with callback for automatic updates, and
    automatic determination of string/float controls """
    def __init__(self, parent, pvname=None, timer=None,
                 font=None, fg=None, bg=None, precision=None,**kw):

        self.pv = None
        FloatCtrl.__init__(self, parent, value=0,
                           precision=precision,action= self._onEnter)
        pvCtrlMixin.__init__(self,pvname=pvname,timer=timer,
                             font=font,fg=None,bg=None)

    def _SetValue(self,value):
        self.SetValue(value)
    
    def set_pv(self,pvname=None):
        self.pv = epics.PV(pvname)
        if self.pv is None: return
        
        self.pv.get()
        self.pv.get_ctrlvars()
        # be sure to set precision before value!! or PV may be moved!!
        prec = self.pv.precision
        if prec is None: prec = 0
        self.SetPrecision(prec)

        self.SetValue( self.pv.char_value)
        
       
        if self.pv.type in ('string','char'):
            print 'Float Control for string / character data??  '

        self.SetMin(self.pv.lower_ctrl_limit)
        self.SetMax(self.pv.upper_ctrl_limit)

        self.add_callback(self.pv, self._pvEvent, self.GetId())

    def _onEnter(self,value=None,**kw):
        if value in (None,'') or self.pv is None: return 
        try:
            if float(value) != self.pv.get():
                self.pv.put(float(value))
        except:
            pass
