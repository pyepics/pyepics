============================================
:mod:`epics.wx`   wxPython Widgets for epics
============================================

Overview
========

.. module:: wx
   :synopsis: wxPython objects for epics

This module provides a set of wxPython classes for epics PVs.

        
..  _wx-functions-label:

Sub-classed wx Widgets for Epics
=================================

pvCltrMixin
~~~~~~~~~~~~

.. class:: pvText(parent, pvname=None, font=None, fg=None, bg=None, **kw)

   This is a mixin class for wx Controls with epics PVs:  This connects to
   PV, and manages callback events for the PV.   A class that inherits from
   this class **must** provide a method called `_SetValue`, which will set
   the contents of the corresponding widget.

pvText       
~~~~~~~~

.. class:: pvText(parent, pvname=None, font=None, fg=None, bg=None, **kw)



pvTextCtrl   
~~~~~~~~~~~

pvAlarm   
~~~~~~~~~~

pvFloatCtrl  
~~~~~~~~~~~


pvEnumButton
~~~~~~~~~~~~~~~~~~

pvEnumChoice 
~~~~~~~~~~~~~~~~~~



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

