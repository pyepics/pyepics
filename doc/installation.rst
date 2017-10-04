
====================================
Downloading and Installation
====================================

Prerequisites
~~~~~~~~~~~~~~~

PyEpics works with Python version 2.7, 3.5, or 3.6.  It is supported and
regularly used and tested on 64-bit Linux, 64-bit Mac OSX, 64-bit Windows,
and 32-bit Windows. It should still work on 32-bit Linux, and may work with
older versions of Python, but these are rarely tested. For Windows, use of
pyepics with IronPython (Python written with .NET) has been recently
reported, but is not routinely tested.

Version 3.14 or higher of the EPICS Channel Access library is required for
pyepics to actually communicate with Epics variables.  Specifically, the
shared libraries libca and libCom (*libca.so* and *libCom.so* on Linux,
*libca.dylib* and *libCom.dylib* on Mac OSX, or *ca.dll* and *Com.dll* on
Windows) from *Epics Base* are required to use this module. Some features,
including 'subarray records' will only work with version 3.14.12 and
higher, and version 3.15 or higher is recommended.

For all supported operating systems, pre-built and recent versions of libca
and libCom are provided, and will be installed within the python packages
directory and used by default.  Though they will be found by default by
pyepics, these libraries will be hard for other applications to find, and
so should not cause conflicts with other CA client programs.  We regularly
test with these libraries and recommend using them.  If you want to not use
them or even install them, instructions for how to do this are given below.

The Python `numpy module <http://numpy.scipy.org/>`_ is highly
recommended, though it is not required. If available, it will be used
to automatically convert between EPICS waveforms and numpy arrays.

The `autosave` module requires the `pyparsing` package, which is widely
available and often installed by default with many Python distributions.
The `wx` module requires the `wxPython` package, and the `qt` module
requires `PyQt` or `PySide`.


Downloads and Installation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. _pyepics github repository:    http://github.com/pyepics/pyepics
.. _Python Setup Tools:           http://pypi.python.org/pypi/setuptools
.. _pyepics PyPi:                 https://pypi.python.org/pypi/pyepics/
.. _pyepics CARS downloads:       http://cars9.uchicago.edu/software/python/pyepics3/src/


The latest stable version of the pyepics package is 3.3.0.  Source code
kits and Windows installers can be found at `pyepics PyPI`_.  With `Python
Setup Tools`_ now standard for Python 2.7 and above, the simplest way to
install the pyepics is with::

     pip install pyepics

If you're using Anaconda, there are a few conda channels for pyepics,
including::

     conda install -c GSECARS pyepics

You can also download the source package, unpack it, and install with::

     python setup.py install

If you know that you will not want to use the default version of *libca*,
you can suppress the installation of the default versions by setting the
environmental variable `NOLIBCA` at install time, as with::

    NOLIBCA=1 python setup.py install

or::

    NOLIBCA=1 pip install pyepics

Note that this should be considered an expert-level option.


Getting Started, Setting up the Epics Environment
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

As mentioned above, pyepics must be able to find and load the Channel
Access dynamic library (*libca.so*, *libca.dylib*, or *ca.dll* depending on
the system) at runtime in order to actually work.  By default, the provided
versions of these libraries will be installed and used.

If you wish to use a different version of *libca*, there are a few ways to
specify how that will be found. First, you can set the environmental
variable ``PYEPICS_LIBCA`` to the full path of the dynamic library, for
example::

   > export PYEPICS_LIBCA=/usr/local/epics/base-3.15.5/lib/linux-x86_64/libca.so

For experts who want to never use the default version, installation of
*libca* (and *libCom*) can be turned off by setting the environmental
variable `NOLIBCA` at install time, as shown above.  If you do this, you
will want to make sure that *libca.so* can be found in your `PATH`
environmental variable, or in `LD_LIBRARY_PATH` or `DYLD_LIBRARY_PATH` on
Mac OSX.

To find out which CA library will be used by pyepics, use:
    >>> import epics
    >>> epics.ca.find_libca()

which will print out the full path of the CA dynamic library that will be used.

With the Epics library loaded, you will need to be able to connect to Epics
Process Variables. Generally, these variables are provided by Epics I/O
controllers (IOCs) that are processes running on some device on the
network.  If you are connecting to PVs provided by IOCs on your local
subnet, you should have no trouble.  If trying to reach further network,
you may need to set the environmental variable ``EPICS_CA_ADDR_LIST`` to
specify which networks to search for PVs.


Testing
~~~~~~~~~~~~~

Automated and continuous unit-testing is done with the TravisCI
(https://travis-ci.org/pyepics/pyepics) for Python 2.7, 3.5, and 3.6 using
an Epics IOC running in a Docker image.  Many tests located in the `tests`
folder can also be run using the script ``tests/simulator.py`` as long as
the Epics database in ``tests/pydebug.db`` is loaded in a local IOC.  In
addition, tests are regularly run on Mac OSX, and 32-bit and 64-bit
Windows.


Development Version
~~~~~~~~~~~~~~~~~~~~~~~~

Development of pyepics is done through the `pyepics github
repository`_.  To get a read-only copy of the latest version, use one
of::

   git clone http://github.com/pyepics/pyepics.git
   git clone git@github.com/pyepics/pyepics.git



Getting Help
~~~~~~~~~~~~~~~~~~~~~~~~~

For questions, bug reports, feature request, please consider using the
following methods:

 1.  Send email to the Epics Tech Talk mailing list.  You can send mail
     directly to Matt Newville <newville@cars.uchicago.ed>, but the mailing
     list has many Epics experts reading it, so someone else interested or
     knowledgeable about the topic might provide an answer. Since the
     mailing list is archived and the main mailing list for Epics work, a
     question to the mailing list has a better chance of helping someone
     else.

 2.  Create an Issue on http://github.com/pyepics/pyepics.  Though the
     github Issues seem to be intended for bug tracking, they are a fine
     way to catalog various kinds of questions and feature requests.

 3.  If you are sure you have found a bug in existing code, or have
     some code you think would be useful to add to pyepics, consider
     making a Pull Request on http://github.com/pyepics/pyepics.


License
~~~~~~~~~~~~~~~~~~~

The pyepics source code, this documentation, and all material
associated with it are distributed under the Epics Open License:

.. include:: ../LICENSE

In plain English, this says that there is no warranty or guarantee that the
code will actually work, but you can do anything you like with this code
except a) claim that you wrote it or b) claim that the people who did write
it endorse your use of the code. Unless you're the US government, in which
case you can probably do whatever you want.

Acknowledgments
~~~~~~~~~~~~~~~~~~~~~~

pyepics was originally written and is maintained by Matt Newville
<newville@cars.uchicago.ed>.  Many important contributions to the library
have come from Angus Gratton while at the Australian National University,
and from Daron Chabot and Ken Lauer.  Several other people have provided
valuable additions, suggestions, or bug reports, which has greatly improved
the quality of the library:  Robbie Clarken, Daniel Allen, Michael Abbott,
Thomas Caswell, Alain Peteut, Steven Hartmann, Rokvintar, Georg Brandl,
Niklas Claesson, Jon Brinkmann, Marco Cammarata, Craig Haskins, David Vine,
Pete Jemian, Andrew Johnson, Janko Kolar, Irina Kosheleva, Tim Mooney, Eric
Norum, Mark Rivers, Friedrich Schotte, Mark Vigder, Steve Wasserman, and
Glen Wright.
