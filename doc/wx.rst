============================================
:mod:`epics.wx`   wxPython Widgets for epics
============================================

Overview
========

.. module:: wx
   :synopsis: wxPython objects for epics

This module provides a set of wxPython classes for epics PVs. Most of these are
derived from wxPython widgets, with special support added for epics PVs,
especially regarding when to automatically update the widget based on a
changing value for a PV.

        
..  _wx-functions-label:

Sub-classed wx Widgets for Epics
=================================

pvCtrlMixin
~~~~~~~~~~~~

.. class:: pvCtrlMixin(parent, pvname=None, font=None, fg=None, bg=None, **kw)

   This is a mixin class for wx Controls with epics PVs:  This connects to
   PV, and manages callback events for the PV.   A class that inherits from
   this class **must** provide a method called `_SetValue`, which will set
   the contents of the corresponding widget.

   In general, the widgets will automatically update when the PV
   changes. Where appropriate, setting the value with the widget will set
   the PV value.

pvText       
~~~~~~~~

.. class:: pvText(parent, pvname=None, font=None, fg=None, bg=None, **kw)

    derived from wx.StaticText  and pvCtrlMixin, this is a StaticText
    widget whose value is set to the string representation of the value for
    the corresponding PV.


pvTextCtrl   
~~~~~~~~~~~

.. class:: pvTextCtrl(parent, pvname=None, font=None, fg=None, bg=None, **kw)

    derived from wx.TextCtrl and pvCtrlMixin, this is a TextCtrl widget
    whose value is set to the string representation of the value for the
    corresponding PV.  Setting the value of the widget will set the PV
    value. 


pvFloatCtrl  
~~~~~~~~~~~

.. class:: pvFloatCtrl(parent, pvname=None, font=None, fg=None, bg=None, **kw)

    A special variation of a wx.TextCtrl that allows only floating point
    numbers, as associated with a double, float, or integer PV.  Trying to
    type in a non-numerical value will be ignored.  Furthermore, if a PV's
    limits can be determined, they will be used to limit the allowed range
    of input values.  For a value that is within limits, the value will be
    `put` to the PV on return.  Out-of-limit values will be highlighted in
    a different color.


pvEnumButtons
~~~~~~~~~~~~~~~~~~

.. class:: pvEnumButtons(parent, pvname=None, font=None, fg=None, bg=None, **kw)

   This will create a wx.Panel of buttons (a button bar), 1 for each
   enumeration state of an enum PV.  The set of buttons will correspond to
   the current state of the PV


pvEnumChoice 
~~~~~~~~~~~~~~~~~~

.. class:: pvEnumChoice(parent, pvname=None, font=None, fg=None, bg=None, **kw)

   This will create a dropdown list (a wx.Choice) with a list of enumeration
   states for an enum PV.  


pvAlarm   
~~~~~~~~~~

.. class:: pvAlarm(parent, pvname=None, font=None, fg=None, bg=None, trip_point=None, **kw)

    This will create a pop-up message (wx.MessageDialog) that is shown when
    the corresponding PV trips the alarm level.

Decorators
==========

.. function:: DelayedEpicsCallback

decorator to wrap an Epics callback in a wx.CallAfter,
so that the wx and epics ca threads do not clash
This also checks for dead wxPython objects (say, from a
closed window), and remove callbacks to them.

..  function::  EpicsFunction

decorator to wrap function in a wx.CallAfter() so that
Epics calls can be made in a separate thread, and asynchronously.

This decorator should be used for all code that mix calls to wx and epics    

