
====================================
Downloading and Installation
====================================

Prerequisites
~~~~~~~~~~~~~~~

PyEpics works with Python version 2.7, 3.5, 3.6, and 3.7.  It is supported
and regularly used and tested on 64-bit Linux, 64-bit Mac OSX, and 64-bit
Windows.  It is known to work on Linux with ARM processors including
raspberry Pi, though this is not part of the automated testing set.
Pyepics may still work on 32-bit Windows and Linux, but these systems are
not tested regularly. It may also work with older versions of Python (such
as 3.4), but these are no longer tested or supported. For Windows, pyepics
has been reported to work with IronPython (that is, Python written in the
.NET framework), but this is not routinely tested.

The EPICS Channel Access library Version 3.14.12 or higher is required for
pyepics and 3.15 or higher are strongly recommended.  More specifically,
pyepics requires e shared libraries libca and libCom (*libca.so* and
*libCom.so* on Linux, *libca.dylib* and *libCom.dylib* on Mac OSX, or
*ca.dll* and *Com.dll* on Windows) from *Epics Base*.

For all supported operating systems and some less-well-tested systems (all
of linux-64, linux-32,linux-arm, windows-64, windows-32, and darwin-64),
pre-built versions of *libca* (and *libCom*) built with 3.16.2 are
provided, and will be installed within the python packages directory and
used by default.  This means that you do not need to install Epics base
libraries or any other packages to use pyepics.  For Epics experts who may
want to use their own versions the *libca* from Epics base, instructions
for how to do this are given below.

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


The latest stable version of the pyepics package is |release|.  Source code
kits and Windows installers can be found at `pyepics PyPI`_, and can be
installed with::

     pip install pyepics

If you're using Anaconda Python, there are a few conda channels for pyepics,
including::

     conda install -c GSECARS pyepics

You can also download the source package, unpack it, and install with::

     python setup.py install


Getting Started, Setting up the Epics Environment
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

As mentioned above, pyepics must be able to find and load the Channel
Access dynamic library (*libca.so*, *libca.dylib*, or *ca.dll* depending on
the system) at runtime in order to actually work.  For the most commonly
used operating systems and architectures, modern version of these libraries
are provided, and will be installed and used with pyepics.  We strongly
recommend using these.

If these provided versions of *libca* do not work for you, please let us know.
If you need to or wish to use a different version of *libca*, you can set the
environmental variable ``PYEPICS_LIBCA`` to the full path of the dynamic
library to use as *libca*, for example::

   > export PYEPICS_LIBCA=/usr/local/epics/base-3.15.5/lib/linux-x86_64/libca.so

Note that *libca* will need to find another Epics CA library *libCom*.  This
is almost always in the same folder as *libca*, but you may need to make sure
that the *libca* you are pointing to can find the required *libCom*.  The
methods for telling shared libraries (or executable files) how to find other
shared libraries varies with system, but you may need to set other
environmental variables such as ``LD_LIBRARY_PATH`` or ``DYLIB_LIBRARY_PATH``
or use `ldconfig`.  If you're having trouble with any of these things,
ask your local Epics gurus or contact the authors.

To find out which CA library will be used by pyepics, use:
    >>> import epics
    >>> epics.ca.find_libca()

which will print out the full path of the CA dynamic library that will be used.

With the Epics library loaded, you will need to be able to connect to Epics
Process Variables. Generally, these variables are provided by Epics I/O
controllers (IOCs) that are processes running on some device on the
network.  If you are connecting to PVs provided by IOCs on your local
subnet, you should have no trouble.  If trying to reach IOCs outside of
your immediate subnet, you may need to set the environmental variable
``EPICS_CA_ADDR_LIST`` to specify which networks to search for PVs.


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
repository`_.  To get a copy of the latest version do::

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
valuable additions, suggestions, pull requests or bug reports, which has
greatly improved the quality of the library: Robbie Clarken, Daniel Allen,
Michael Abbott, Thomas Caswell, Alain Peteut, Steven Hartmann, Rokvintar,
Georg Brandl, Niklas Claesson, Jon Brinkmann, Marco Cammarata, Craig
Haskins, David Vine, Pete Jemian, Andrew Johnson, Janko Kolar, Irina
Kosheleva, Tim Mooney, Eric Norum, Mark Rivers, Friedrich Schotte, Mark
Vigder, Steve Wasserman, and Glen Wright.
