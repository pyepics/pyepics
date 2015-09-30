.. _arrays-label:

============================================
Working with waveform / array data
============================================

Though most EPICS Process Variables hold single values, PVs can hold array
data from EPICS waveform records.  These are always data of a homogenous
data type, and have a fixed maximum element count (defined when the
waveform is created from the host EPICS process).  Epics waveforms are
most naturally mapped to Arrays from the `numpy module
<http://numpy.scipy.org/>`_, and this is strongly encouraged.

Arrays without Numpy
~~~~~~~~~~~~~~~~~~~~~~~~

If you have numpy installed, and use the default *as_numpy=True* in
:meth:`ca.get`, :meth:`pv.get` or :meth:`epics.caget`, you will get a
numpy array for the value of a waveform PV.  If you do *not* have numpy
installed, or explicitly use *as_numpy=False* in a get request, you will
get the raw C-like array reference from the Python
`ctypes module <http://docs.python.org/library/ctypes.html#arrays>`_.
These objects are not normally meant for casual use, but are not too
difficult to work with either.  They can be easily converted to a simple
Python list with something like::

    >>> import epics
    >>> epics.ca.HAS_NUMPY = False # turn numpy off for session
    >>> p = epics.PV('XX:scan1.P1PA')
    >>> p.get()
    <epics.dbr.c_double_Array_500 object at 0x853980c>
    >>> ldat = list(p.get())

Note that this conversion to a list can be very slow for large arrays.


Variable Length Arrays:  NORD  and NELM
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

While the maximum length of an array is fixed, the length of data you get
back from a monitor, :meth:`ca.get`, :meth:`pv.get`, or :meth:`epics.caget`
may be shorter than the maximumn length, reflecting the most recent data
put to that PV.  That is, if some process puts a smaller array to a PV than
its maximum length, monitors on that PV may receive only the changed data.
For example::

    >>> import epics
    >>> p = epics.PV('Py:double2k')
    >>> print p
    <PV 'Py:double2k', count=2048/2048, type=double, access=read/write>
    >>> import numpy
    >>> p.put(numpy.arange(10)/5.0)
    >>> print p.get()
    array([ 0. ,  0.2,  0.4,  0.6,  0.8,  1. ,  1.2,  1.4,  1.6,  1.8])

To be clear, the :meth:`pv.put` above could be done in a separate process
-- the :meth:`pv.get` is not using a value cached from the :meth:`pv.put`.

This feature seems to depend on the record definition, and requires version
3.14.12.1 of Epics base or higher, and can be checked by comparing
:meth:`ca.version` with the string '4.13'.

Character Arrays
~~~~~~~~~~~~~~~~~~~~~~~~

As noted in other sections, character waveforms can be used to hold strings
longer than 40 characters, which is otherwise a fundamental limit for
native Epics strings.  Character waveforms shorter than
:data:`ca.AUTOMONITOR_MAXLENGTH` can be turned into strings with an
optional *as_string=True* to :meth:`ca.get`, :meth:`pv.get` , or
:meth:`epics.caget`.  If you've defined a Epics waveform record as::


    record(waveform,"$(P):filename")  {
              field(DTYP,"Soft Channel")
              field(DESC,"file name")
              field(NELM,"128")
              field(FTVL,"CHAR")
     }

Then you can use this record with:

    >>> import epics
    >>> pvname = 'PREFIX:filename.VAL'
    >>> pv  = epics.PV(pvname)
    >>> print pv.info
    ....
    >>> plain_val = pv.get()
    >>> print plain_val
    array([ 84,  58,  92, 120,  97, 115,  95, 117, 115, 101, 114,  92,  77,
         97, 114,  99, 104,  50,  48,  49,  48,  92,  70,  97, 115, 116,
         77,  97, 112])
    >>> char_val = pv.get(as_string=True)
    >>> print char_val
    'T:\\xas_user\\March2010\\FastMap'

This example uses :meth:`pv.get` but :meth:`ca.get` is essentially
equivalent, as its *as_string* parameter works exactly the same way.

Note that Epics character waveforms as defined as above are really arrays
of bytes.  The converion to a string assumes the ASCII character set.
Unicode is not directly supported.  If you are storing non-ASCII data, you
would have to convert the raw array data yourself, perhaps like this (for
Python3)::

    >>> arr_data = pv.get()
    >>> arr_bytes = bytes(list(array_data))
    >>> arr_string = str(arr_bytes, 'LATIN-1')


.. _arrays-large-label:

Strategies for working with large arrays
============================================

EPICS Channels / Process Variables usually have values that can be stored
with a small number of bytes.  This means that their storage and transfer
speeds over real networks is not a significant concern.  However, some
Process Variables can store much larger amounts of data (say, several
megabytes) which means that some of the assumptions about dealing with
Channels / PVs may need reconsideration.

When using PVs with large array sizes (here, I'll assert that *large* means
more than a few thousand elements), it is necessary to make sure that the
environmental variable ``EPICS_CA_MAX_ARRAY_BYTES`` is suitably set.
Unfortunately, this represents a pretty crude approach to memory management
within Epics for handling array data as it is used not only sets how large
an array the client can accept, but how much memory will be allocated on
the server.  In addition, this value must be set prior to using the CA
library -- it cannot be altered during the running of a CA program.

Normally, the default value for ``EPICS_CA_MAX_ARRAY_BYTES`` is 16384 (16k,
and it turns out that you cannot set it smaller than this value!).  As
Python is used for clients, generally running on workstations or servers
with sufficient memory, this default value is changed to 2**24, or 16Mb)
when :mod:`epics.ca` is initialized.  If the environmental variable
``EPICS_CA_MAX_ARRAY_BYTES`` has not already been set.

The other main issue for PVs holding large arrays is whether they should be
automatically monitored.  For PVs holding scalar data or small arrays, any
penalty for automatically monitoring these variables (that is, causing
network traffic every time a PV changes) is a small price to pay for being
assured that the latest value is always available.  As arrays get larger
(as for data streams from Area Detectors), it is less obvious that
automatic monitoring is desirable.

The Python :mod:`epics.ca` module defines a variable
:data:`ca.AUTOMONITOR_MAXLENGTH` which controls whether array PVs are
automatically monitored.  The default value for this variable is 65536, but
can be changed at runtime.  Arrays with fewer elements than
:data:`ca.AUTOMONITOR_MAXLENGTH` will be automatically monitored, unless
explicitly set, and arrays larger than :data:`AUTOMONITOR_MAXLENGTH` will
not be automatically monitored unless explicitly set. Auto-monitoring of
PVs can be be explicitly set with

   >>> pv2 = epics.PV('ScalerPV', auto_monitor=True)
   >>> pv1 = epics.PV('LargeArrayPV', auto_monitor=False)


Example handling Large Arrays
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Here is an example reading data from an `EPICS areaDetector
<http://cars9.uchicago.edu/software/epics/areaDetector.html>`_, as if it
were an image from a digital camera.  This uses the `Python Imaging Library
<http://www.pythonware.com/products/pil/>`_ for much of the image
processing:


    >>> import epics
    >>> import Image
    >>> pvname = '13IDCPS1:image1:ArrayData'
    >>> img_pv  = epics.PV(pvname)
    >>>
    >>> raw_image = img_pv.get()
    >>> im_mode = 'RGB'
    >>> im_size = (1360, 1024)
    >>> img = Image.frombuffer(im_mode, im_size, raw_image,
                                'raw', im_mode, 0, 1)
    >>> img.show()

The result looks like this (taken with a Prosilica GigE camera):

.. image:: AreaDetector1.png


A more complete application for reading and displaying image from Epics
Area Detectors is included  at `http://github.com/pyepics/epicsapps/
<http://github.com/pyepics/epicsapps/>`_.

