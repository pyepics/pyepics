====================================
Downloading and Installation
====================================

Prerequisites
~~~~~~~~~~~~~~~

PyEpics works with Python version 3.8 and higher.  At this writing,
automated testing is done with versions 3.8 through 3.12,
PyEpics may still work with Python 3.7 or even 3.6, but no testing or support
is available for these.

Pyepics is supported and regularly used on 64-bit Linux, 64-bit Windows, 64-bit
Mac OSX with both Intel and Arm processors.  PyEpics should also work on Linux
with ARM processors including raspberry Pi and may still work on 32-bit Windows
and Linux, though these systems are not tested regularly. As of this writing,
automated testing is done only for Linux64.

The EPICS Channel Access library Version 3.14.12 or higher is required for
pyepics, and versions 7.0.4 or higher are strongly recommended.  More
specifically, pyepics requires the shared libraries *libca* and *libCom*
(*libca.so* and *libCom.so* on Linux, *libca.dylib* and *libCom.dylib* on
Mac OSX, or *ca.dll* and *Com.dll* on Windows) from *Epics Base*.

For Linux64, Linux32, LinuxArm, Windows64, Windows32, Darwin64 (MacOS) on
x86-64, and Darwin64 (MacOS) on arm64, pre-built versions of *libca* (and
*libCom*) are provided and will be installed into the python packages directory
and used by default. This means that you do not need to install Epics base
libraries or any other packages to use pyepics.  These libraries have been
built with 3.16.2 or 7.0.7 - further details are given in the `clibs` folder of
the source kit.  For Epics experts who may want to use their own versions the
*libca* from Epics base, instructions for how to do this are given below.

The Python `numpy <https://numpy.org/>`_ module is highly recommended. and will
be used to automatically convert between EPICS waveforms and numpy arrays if
available.

The `autosave` module requires the `pyparsing` package, which is widely
available and often installed by default with many Python distributions.
The `wx` module requires the `wxPython` package, and the `qt` module
requires `PyQt` or `PySide`.


Downloads and Installation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. _pyepics github repository:    https://github.com/pyepics/pyepics
.. _pyepics PyPi:                 https://pypi.python.org/pypi/pyepics/

The latest stable version of the pyepics package is |release| which can be
installed with::

     pip install pyepics

If you're using Anaconda Python, there are a few conda channels that
provide the latest versions, but the version on `PyPI` should be considered
the reference version.  You can also download the source package, unpack
it, and install with::

     pip install .


Getting Started, Setting up the Epics Environment
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Pyepics will find and load the Channel Access dynamic library (*libca.so*,
*libca.dylib*, or *ca.dll* depending on the system) at runtime in order to
actually work.  For the most commonly used operating systems and
architectures, modern version of these libraries are provided, and will be
installed and used with pyepics.  We strongly recommend using these.

If these provided versions of *libca* do not work for you, please let us know.
If you need to or wish to use a different version of *libca*, you can set the
environmental variable ``PYEPICS_LIBCA`` to the full path of the dynamic
library to use as *libca*, for example::

   > export PYEPICS_LIBCA=/usr/local/epics/base-7.0.4/lib/linux-x86_64/libca.so

Note that *libca* will need to find another Epics CA library *libCom*.  This
is almost always in the same folder as *libca*, but you may need to make sure
that the *libca* you are pointing to can find the required *libCom*. To
find out which CA library will be used by pyepics, use:

    >>> import epics
    >>> epics.ca.find_libca()

which will print out the full path of the CA dynamic library that will be used.

With the Epics CA library loaded, you will need to be able to connect to Epics
Process Variables. Generally, these variables are provided by Epics I/O
controllers (IOCs) that are processes running on some device on the network.
If you are connecting to PVs provided by IOCs on your local subnet, you should
have no trouble.  If trying to reach IOCs outside of your immediate subnet, you
may need to set the environmental variable ``EPICS_CA_ADDR_LIST`` to specify
which networks to search for PVs.


Testing
~~~~~~~~~~~~~

Automated testing of PyEpics is done with the Github actions, for Python 3.8,
3.9, 3.10, 3.11, and 3.12.  This uses an ubuntu-linux environment.

To run these tests yourself, you will need the `pytest` python module. You
will also need to run an Epics softIOC as a separate process, and a
simulator that updates PV values as a separate process.  These can all run
on the same machine or different machines on your network as long as all
processes can see all the PVs (all using a prefix of `PyTest:`).  The
softIoc cannot be run in a separate terminal process or using the
`procServ` program.  To setup the testing environment, first start the
testing softIoc in one shell, with::

     ~> cd tests/Setup
     ~> softIoc ./st.cmd

If you have `procServ` installed, you can do::

     ~> cd tests/Setup
     ~> bash ./start_ioc.sh

which will put the IOC properly as a background process. Second, run the
simulator (also in `tests/Setup`) so that Epics channels are changing::

     ~> python simulator.py

Again, these do not have to be run on the same machine as your tests, but
the PVs here will need to be discoverable by all the processes involved.

Now, you are ready to run the tests in the `tests` folder.  In many
scenarios for Python libraries, one would be able to run all the tests, and
measure the testing coverage with a single command.  Because the pyepics
test will change underlying threading contexts, a simple ::

     ~> cd ..
     ~> pytest test_*.py

will show many failures.  Instead you should run each test as a separate
run of `pytest`::

     ~> for testfile in test_*.py; do  pytest $testfile ; done


The automated testing process also uses the `coverage` tool to help
identify which parts of the code is actually run by the tests.
Unfortunately, the code for using GUI are not easily tested by the
automated procedures.  In addition, a softIoc would need to support all of
the subclasses of Device, which cannot be gauranteed.

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

 2.  Create an Issue on https://github.com/pyepics/pyepics.  Though the
     github Issues seem to be intended for bug tracking, they are a fine
     way to catalog various kinds of questions and feature requests.

 3.  If you are sure you have found a bug in existing code, or have
     some code you think would be useful to add to pyepics, consider
     making a Pull Request on https://github.com/pyepics/pyepics.


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
