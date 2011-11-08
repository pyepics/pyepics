====================================
Applications built with PyEpics
====================================

Several applications built on top of PyEpics are available at
`http://github.com/pyepics/epicsapps/
<http://github.com/pyepics/epicsapps/>`_.  These are meant to be both
useful applications on their own, and examples for showing how one can
build complex applications with PyEpics.  The list of applications will be
expanding.  Many of these rely on wxPython and possibly other 3rd party
modules.


Strip Chart
~~~~~~~~~~~~~~

A simple "live plot" of a set of PVs, similar to the common Epics
StripTool.

Epics Instruments
~~~~~~~~~~~~~~~~~~~~

This application helps you organize PVs, by grouping them into instruments.
Each instrument is a loose collection of PVs, but can have a set of named
positions that you can tell it.  That is, you can save the current set of
PV values by giving it a simple name.  After that, you can recall the saved
values of each instrument, putting all or some of the PVs back to the saved
values.   The Epics Instrument application organizes instruments with
tabbed windows, so that you can have a compact view of many instruments,
saving and restoring positions as you wish.



Sample Stage
~~~~~~~~~~~~~~

A GSECARS-specific GUI for moving a set of motors for a sample stage,
grabbing microscope images from a webcam, and saving named positions.


Ion Chamber
~~~~~~~~~~~~~~

This non-GUI application is synchrotron-beamline specific.  It reads
several settings for the photo-current of an ion chamber and calculates
absorbed and transmitted flux in photons/sec, and writes these back to PVs
(an associated .db file and medm .adl file are provided).  The script runs
in a loop, updating the flux values continuously.


