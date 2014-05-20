
==========================================
Auto-saving: simple save/restore of PVs
==========================================

.. module:: autosave
   :synopsis: simple save/restore of PVs

The :mod:`autosave` module provides simple save/restore functionality for
PVs, with the functions :func:`save_pvs` and :func:`restore_pvs`.  These
are similar to the autosave module from synApps for IOCs in that they use a
compatible *request file* which describes the PVs to save, and a compatible
*save file* which holds the saved values. Of course, the reading and
writing is done here via Channel Access, and need not be related to any
particular running IOC.

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
however, no mechanism for automatically finding request files.

With such a file, simply using::

    import epics.autosave
    epics.autosave.save_pvs("My.req", "my_values.sav")

will save the current values for the PVs to the file **my_values.sav**.  At
a later time, these values can be restored with

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

A simple example usign the autosave module::

    import epics.autosave
    # save values
    epics.autosave.save_pvs("my_request_file.req", 
                            "/tmp/my_recent_save.sav")

    # wait 30 seconds
    time.sleep(30)

    # restore those values back
    epics.autosave.restore_pvs("/tmp/my_recent_save.sav")

