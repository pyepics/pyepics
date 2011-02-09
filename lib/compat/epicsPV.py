"""
Port of Mark Rivers epicsPV class to use epics.PV

Matt Newville  7-April-2010

Original comments:

This module defines the epicsPV class, which adds additional features to
Geoff Savage's CaChannel class.

Author:         Mark Rivers
Created:        Sept. 16, 2002.
Modifications:
"""
import epics

class epicsPV(epics.PV):
    """
    This class subclasses PV to provide a compatible API to Mark Rivers
    epicsPV class
    
    - setMonitor() sets a generic callback routine for value change events.
    Subsequent getw(), getValue() or array_get() calls will return the
    value from the most recent callback, and hence do not result in any
    network activity or latency.  This can greatly improve performance.
        
    - checkMonitor() returns a flag to indicate if a callback has occured
    since the last call to checkMonitor(), getw(), getValue() or
    array_get().  It can be used to increase efficiency in polling
    applications.
        
    - getControl() reads the "control" and other information from an
    EPICS PV without having to use callbacks.
    In addition to the PV value, this will return the graphic, control and
    alarm limits, etc.

    - putWait() calls array_put_callback() and waits for the callback to
    occur before it returns.  This allows programs to use array_put_callback()
    synchronously and without user-written callbacks.
    
    Created:  Mark Rivers, Sept. 16, 2002.
    Modifications:
    """

    def __init__(self, pvname=None, wait=True):
        """
        Keywords:
        pvname:
        An optional name of an EPICS Process Variable.
        
        wait: If wait==True and pvname != None then this constructor will do
        a wait for connection for the PV.  If wait==0 and pvname != None
        then the PV will eventually connect...
        
        """
        # Invoke the base class initialization
        PV.__init__(self, pvname)
        self.monitorState = False
        if pvname is not None and wait:
            self.connect()

    def _getCallback(self, pvname=None, value=None, **kw):
        self.monitorState = True

    def setMonitor(self):
        """
        Sets a simple callback routine for value change events
        to note when a change occurs.
        """
        self.monitorState = False
        self.add_callback(callback=self._getCallback)

    def clearMonitor(self):
        """
        Cancels the effect of a previous call to setMonitor().
        """
        self.monitorState = False

    def checkMonitor(self):
        """
        Returns True to indicate if a value callback has occured,
        indicating a new value is available since the last check.
        Returns False if no such callback has occurred.
        """
        epics.poll()
        out =  self.monitorState
        self.monitorState = False
        return out

    def getControl(self):
        """
        returns a dictionary of control information for a PV
        Example::
        
        >>> pv = epicsPV('13IDC:m1')
        >>> for field, value in pv.getControl().items():
        >>>    print field, ':', value
        status  :  0
        severity  :  0
        precision  :  5
        units  :  mm
        lower_alarm_limit  :  0.0
        upper_alarm_limit  :  0.0
        lower_warning_limit  :  0.0
        upper_warning_limit  :  0.0
        lower_disp_limit  :  -2.4
        upper_disp_limit  :  2.4
        upper_ctrl_limit  :  2.4
        lower_ctrl_limit  :  -2.4
        """
        epics.poll()
        return self.get_ctrlvars()
      
    def array_get(self, count=None):
        """ returns PV value    """
        return self.getw(count=count)

    def getw(self, count=None):
        """ returns PV value"""
        return self.get(count=count)

    def getValue(self):
        """  get most recent value for PV   """
        return self.get()
    
    def putw(self, value, wait=False):
        """ set PV value"""
        self.put(value, wait=wait)
        
    def putWait(self, value):
        """ put PV value, waits for the callback to
        occur before it returns.  """
        self.put(value, wait=True)
      
