#!/usr/bin/env python
#  M Newville <newville@cars.uchicago.edu>
#  The University of Chicago, 2010
#  Epics Open License
"""
basic device object defined
"""
from .ca import poll
from .pv  import get_pv
import time

class Device(object):
    """A simple collection of related PVs, sharing a common prefix
    string for their names, but having many 'attributes'.

    Many groups of PVs will have names made up of
         Prefix+Delimiter+Attribute
    with common Prefix and Delimiter, but a range of Attribute names.
    Many Epics Records follow this model, but a Device is only about
    PV names, and so is not exactly a mapping to an Epics Record.

    This class allows a collection of PVs to be represented simply.

      >>> dev = epics.Device('XX:m1', delim='.')
      >>> dev.put('OFF',0 )
      >>> dev.put('VAL', 0.25)
      >>> dev.get('RBV')
      >>> print dev.FOFF
      >>> print dev.get('FOFF', as_string=True)

    This will put a 0 to XX:m1.OFF, a 0.25 to XX:m1.VAL, and then
    get XX:m1.RBV and XX.m1.FOFF.

    Note access to the underlying PVs can either be with get()/put()
    methods or with attributes derived from the Attribute (Suffix) for
    that PV.  Thus
      >>> print dev.FOFF
      >>> print dev.get('FOFF')

    are equivalent, as are:
      >>> dev.VAL = 1
      >>> dev.put('VAL', 1)

    The methods do provide more options.  For example, to get the PV
    value as a string,
       Device.get(Attribute, as_string=True)
    must be used.   To put-with-wait, use
       Device.put(Attribute, value, wait=True)

    The list of attributes can be pre-loaded at initialization time.


    The attribute PVs are built as needed and held in an internal
    buffer (self._pvs).  This class is kept intentionally simple
    so that it may be subclassed.

    To pre-load attribute names on initialization, provide a
    list or tuple of attributes:

      >>> struck = epics.Device('13IDC:str:',
      ...                       attrs=('ChannelAdvance',
      ...                              'EraseStart','StopAll'))
      >>> print struck.PV('ChannelAdvance').char_value
      'External'

    The prefix is optional, and when left off, this class can
    be used as an arbitrary container of PVs, or to turn
    any subclass into an epics Device:

      >>> class MyClass(epics.Device):
      ...     def __init__(self,**kw):
      ...         epics.Device.__init__() # no Prefix!!
      ...
      >>> x = MyClass()
      >>> pv_m1 = x.PV('13IDC:m1.VAL')
      >>> x.put('13IDC:m3.VAL', 2)
      >>> print x.PV('13IDC:m3.DIR').get(as_string=True)

    Attribute aliases can also be used to be make the device
    more user-friendly:

      >>> dev = epics.Device('IOC:m1', delim='.',
      ...                    aliases={'readback': 'RBV'})
      >>> print 'rbv is', dev.RBV  # IOC:m1.RBV
      >>> print 'readback is', dev.readback  # also IOC:m1.RBV

    If you encounter issues with introspection (with IPython,
    for example), and your device has a well-defined list of
    attributes, consider clearing the `mutable` flag. Attributes
    not already in the list will then be assumed to be invalid.
    AttributeError is raised quickly without using channel access:

      >>> dev = epics.Device('IOC:m1', delim='.', mutable=False,
      ...                    aliases={'readback': 'RBV'})
      >>> print dev.foobar
      Traceback (most recent call last):
          ...
      AttributeError: Device has no attribute foobar
    """

    _prefix = None
    _delim = ''
    _pvs = {}
    _init = False
    _aliases = {}
    _mutable = True
    _nonpvs = ('_prefix', '_pvs', '_delim', '_init', '_aliases',
               '_mutable', '_nonpvs')
    def __init__(self, prefix='', attrs=None,
                 nonpvs=None, delim='', timeout=None,
                 mutable=True, aliases=None, with_poll=True):

        self._nonpvs = list(self._nonpvs)
        self._delim = delim
        self._prefix = prefix + delim
        self._pvs = {}
        self._mutable = mutable
        if aliases is None:
             aliases = {}
        self._aliases = aliases
        if nonpvs is not None:
            for npv in nonpvs:
                if npv not in self._nonpvs:
                    self._nonpvs.append(npv)

        if attrs is not None:
            for attr in attrs:
                self.PV(attr, connect=False, timeout=timeout)

        if aliases:
            for attr in aliases.values():
                if attrs is None or attr not in attrs:
                    self.PV(attr, connect=False, timeout=timeout)

        if with_poll:
            poll()
        self._init = True

    def PV(self, attr, connect=True, **kw):
        """return epics.PV for a device attribute"""
        if attr in self._aliases:
            attr = self._aliases[attr]

        if attr not in self._pvs:
            pvname = attr
            if self._prefix is not None:
                pvname = "%s%s" % (self._prefix, attr)
            self._pvs[attr] = get_pv(pvname, **kw)
        if connect and not self._pvs[attr].connected:
            self._pvs[attr].wait_for_connection()
        return self._pvs[attr]

    def add_pv(self, pvname, attr=None, **kw):
        """add a PV with an optional attribute name that may not exactly
        correspond to the mapping of Attribute -> Prefix + Delim + Attribute
        That is, with a device defined as
        >>> dev = Device('XXX', delim='.')

        getting the VAL attribute
        >>> dev.get('VAL')   # or dev.VAL

        becomes   'caget(XXX.VAL)'.  With add_pv(), one can add a
        non-conforming PV to the collection:
        >>> dev.add_pv('XXX_status.VAL', attr='status')

        and then use as
        >>> dev.get('status')  # or dev.status

        If attr is not specified, the full pvname will be used.
        """
        if attr is None:
            attr = pvname
        self._pvs[attr] = get_pv(pvname, **kw)
        return self._pvs[attr]

    def put(self, attr, value, wait=False, use_complete=False, timeout=10):
        """put an attribute value,
        optionally wait for completion or
        up to a supplied timeout value"""
        thispv = self.PV(attr)
        thispv.wait_for_connection()
        return thispv.put(value, wait=wait, use_complete=use_complete,
                          timeout=timeout)

    def get(self, attr, as_string=False, count=None, timeout=None):
        """get an attribute value,
        option as_string returns a string representation"""
        return self.PV(attr).get(as_string=as_string, count=count,
                                 timeout=timeout)

    def save_state(self):
        """return a dictionary of the values of all
        current attributes"""
        out = {}
        for key in self._pvs:
            out[key] = self._pvs[key].get()
            if  (self._pvs[key].count > 1 and
                 'char' == self._pvs[key].type):
                out[key] = self._pvs[key].get(as_string=True)
        return out

    def restore_state(self, state):
        """restore a dictionary of the values, as saved from save_state"""
        for key, val in state.items():
            if key in self._pvs and  'write' in self._pvs[key].access:
                self._pvs[key].put(val)

    def write_state(self, fname, state=None):
        """write save state  to external file.
        If state is not provided, the current state is used

        Note that this only writes data for PVs with write-access, and count=1 (except CHAR """
        if state is None:
            state = self.save_state()
        out = ["#Device Saved State for %s, prefx='%s': %s\n" % (self.__class__.__name__,
                                                                 self._prefix, time.ctime())]
        for key in sorted(state.keys()):
            if (key in self._pvs and
                'write' in self._pvs[key].access and
                (1 == self._pvs[key].count or
                 'char' == self._pvs[key].type)):
                out.append("%s  %s\n" % (key, state[key]))
        fout = open(fname, 'w')
        fout.writelines(out)
        fout.close()


    def read_state(self, fname, restore=False):
        """read state from file, optionally restore it"""
        finp = open(fname, 'r')
        textlines = finp.readlines()
        finp.close()
        state = {}
        for line in textlines:
            if line.startswith('#'):
                continue
            key, strval =  line[:-1].split(' ', 1)
            if key in self._pvs:
                dtype = self._pvs[key].type
                count = self._pvs[key].count
                val = strval
                if dtype in ('double', 'float'):
                    val = float(val)
                elif dtype in ('int', 'long', 'short', 'enum'):
                    val = int(val)
                state[key] = val
        if restore:
            self.restore_state(state)
        return state


    def get_all(self):
        """return a dictionary of the values of all
        current attributes"""
        return self.save_state()

    def add_callback(self, attr, callback, **kws):
        """add a callback function to an attribute PV,
        so that the callback function will be run when
        the attribute's value changes"""
        self.PV(attr).get()
        return self.PV(attr).add_callback(callback, **kws)

    def remove_callbacks(self, attr, index=None):
        """remove a callback function to an attribute PV"""
        self.PV(attr).remove_callback(index=index)


    def __getattr__(self, attr):
        if attr in self._aliases:
            attr = self._aliases[attr]

        if attr in self._pvs:
            return self.get(attr)
        elif attr in self.__dict__:
            return self.__dict__[attr]
        elif self._init and self._mutable and not attr.startswith('__'):
            pv = self.PV(attr, connect=True)
            if pv.connected:
                return pv.get()

        raise AttributeError('%s has no attribute %s' % (self.__class__.__name__,
                                                         attr))

    def __setattr__(self, attr, val):
        if attr in self._aliases:
            attr = self._aliases[attr]

        if attr in self._nonpvs:
            self.__dict__[attr] = val
        elif attr in self._pvs:
            self.put(attr, val)
        elif self._init and self._mutable and not attr.startswith('__'):
            try:
                self.PV(attr)
                self.put(attr, val)
            except:
                raise AttributeError('%s has no attribute %s' % (self.__class__.__name__,
                                                                 attr))
        elif attr in self.__dict__:
            self.__dict__[attr] = val
        elif self._init:
            raise AttributeError('%s has no attribute %s' % (self.__class__.__name__,
                                                             attr))

    def __dir__(self):
        # there's no cleaner method to do this until Python 3.3
        all_attrs = set(list(self._aliases.keys()) + list(self._pvs.keys()) +
                        list(self._nonpvs) +
                        list(self.__dict__.keys()) + dir(Device))
        return list(sorted(all_attrs))

    def __repr__(self):
        "string representation"
        pref = self._prefix
        if pref.endswith('.'):
            pref = pref[:-1]
        return "<Device '%s' %i attributes>" % (pref, len(self._pvs))


    def pv_property(attr, as_string=False, wait=False, timeout=10.0):
        return property(lambda self:     \
                        self.get(attr, as_string=as_string),
                        lambda self,val: \
                        self.put(attr, val, wait=wait, timeout=timeout),
                        None, None)
