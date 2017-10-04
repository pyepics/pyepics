
==========================================
Auto-saving: simple save/restore of PVs
==========================================

.. module:: autosave
   :synopsis: simple save/restore of PVs

The :mod:`autosave` module provides simple save/restore functionality for
PVs, with the functions :func:`save_pvs` and :func:`restore_pvs`, and an
:class:`AutoSaver` class.  These are similar to the autosave module from
synApps for IOCs in that they use a compatible *request file* which
describes the PVs to save, and a compatible *save file* which holds the
saved values. Of course, the reading and writing is done here via Channel
Access, and need not be related to an single IOC.

Use of this module requires the `pyparsing package
<http://pyparsing.wikispaces.com/>`_ to be installed.  This is a fairly
common third-party python package, included in many package managers, or
installed with tools such as *easy_install* or *pip*, or downloaded from
`PyPI <http://pypi.python.org/pypi/pyparsing>`_

Request and Save file formats are designed to be compatible with synApps
autosave.  Notably, the `file` command with macro substitutions are
supported, so that one can have a Request like::

   # My.req
   file "SimpleMotor.req", P=IOC:, Q=m1

with a  **SimpleMotor.req** file of::

   # SimpleMotor.req
   $(P)$(Q).VAL
   $(P)$(Q).DIR
   $(P)$(Q).FOFF

which can then be used for many instances of a SimpleMotor.  There is,
however, no automated mechanism for finding request files.  You will need
to include these in the working directory or specify absolute paths.

With such a file, simply using::

    import epics.autosave
    epics.autosave.save_pvs("My.req", "my_values.sav")

will save the current values for the PVs to the file **my_values.sav**.  At
a later time, these values can be restored with::

    import epics.autosave
    epics.autosave.restore_pvs("my_values.sav")

The saved file will be of nearly identical format as that of the autosave
mechanism, and the :func:`restore_pvs` function can read and restore values
using save files from autosave.  Note, however, that the purpose here is
quite different from that of the standard autosave module (which is
designed to save vales so that PVs can be **initialized** at IOC startup).
Using the functions here will really do a :func:`caput` to the saved
values.


.. function:: save_pvs(request_file, save_file)

   saves current value of PVs listed in *request_file* to the *save_file*

   :param request_file: name of Request file to read PVs to save.
   :param save_file: name of file to save values to write values to

   As discussed above, the **request_file** follows the conventions of the
   autosave module from synApps.

.. function:: restore_pvs(save_file)

   reads values from *save_file* and restores them for the corresponding PVs

   :param save_file: name of file to save values to read data from.


   Note that :func:`restore_pvs` will restore all the values it can, skipping
   over any values that it cannot restore.


:class:`AutoSaver` class
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The :class:`AutoSaver` class provides a convenient way to repeatedly save
PVs listed in a request file without having to re-connect all of the PVs.
The :class:`AutoSaver` retains the PV connections, and provides a simple
:meth:`save` method to save the current PV values to a file.  By default,
that file will be named from the request file and the current time.  This
allows you to do something like this::

    #!/usr/bin/env python
    # save PVs from a request file once per minute
    import time
    from epics.autosave import AutoSaver
    my_saver = AutoSaver("My.req")

    # save all PVs every minute for a day
    t0 = time.time()
    while True:
        if time.localtime().tm_sec < 5:
            my_saver.save()
	    time.sleep(30 - time.localtime().tm_sec)
	if time.time() - t0 > 86400.0:
	    break
        time.sleep(0.5)

This will save PVs to files with names like *My_2017Oct02_141800.sav*

.. class:: AutoSaver(request_file)

   create an Automatic Saver based on a request file.

   :param request_file: name of request file

:class:`AutoSaver` has two methods: :meth:`read_request_file` to read a
request file,  and :meth:`save` to save the results.


.. method:: read_request_file(request_file)

   read and parse request file, begin making PV connections

   :param request_file: name of request file

.. method:: save(save_file=None, verbose=False)

   read current PV values, write save file.

   :param save_file: name of save file or `None`.  If `None`, the name of
                     the request file and timestamp (to seconds) will be
                     used to build a file name.  Note that there is no
                     check for overwriting files.
   :param verbose: whether to print results to the screen [default `False`]



Supported Data Types
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

All scalar PV values can be saved and restored with the :mod:`autosave`
routines.  There is some support for waveform (array) data.  For example,
character waveforms containing for long strings can be saved and restored.
In addition, numerical arrays in waveform can be saved and restored.  For
array data, the results may not be fully compatible with the autosave
module.


Examples
==========

A simple example using the autosave module::

    import epics.autosave
    # save values
    epics.autosave.save_pvs("my_request_file.req",
                            "/tmp/my_recent_save.sav")

    # wait 30 seconds
    time.sleep(30)

    # restore those values back
    epics.autosave.restore_pvs("/tmp/my_recent_save.sav")
