
==========================================
Auto-saving: simple save/restore of PVs
==========================================

.. module:: autosave
   :synopsis: simple save/restore of PVs

Overview
========

The :mod:`autosave` module provides simple save/restore
functionality for PVs, similar to the autosave module in synApps
for IOCs but (obviously) via Channel Access.

Request and Save file formats are designed to be compatible with
synApps autosave.

Use of this module requires the pyparsing parser framework. 
The Debian/Ubuntu package is "python-pyparsing"
The web site is http://pyparsing.wikispaces.com/


Examples
==========


A simple example usign the autosave module::

    import epics.autosave
    # save values
    epics.autosave.save_pvs("/tmp/my_request_file.req", 
                            "/tmp/my_recent_save.sav")

    # wait 30 seconds
    time.sleep(30)

    # restore those values back
    epics.autosave.restore_pvs("/tmp/my_recent_save.sav")

