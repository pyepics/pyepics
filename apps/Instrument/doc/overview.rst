
====================================
Overview
====================================

An `Epics Instrument` is simply a grouping of low-level parameters (Process
Variables) as exposed through Epics Channel Access.  At first, this may not
seem very interesting.  However, Epics Instruments allows you to

The Epics
Instruments application allows you to group these components into a logical
group -- an Instrument.  Once an Instrument has been defined, you can then
save and restore settings for this Instrument.  Furthermore, these settings
are automatcally saved in a single, portable file for later use.


Epics Channel Access gives a simple and robust interface to its lowest
common unit -- the Process Variable or PV.  The Epics control system also
provides sophisticated ways to express and manipulate complex devices, both
physical and virtual.  Creating such devices and defining their behavior is
generally done by well-trained programmers.  The application here uses a
much simpler approach that can expose some categories of "Settings" that
may need to changed en masse, and returned to at a later time.

As defined here, An Epics Instrument is simply a named collection of Epics
Process Variables (PVs).  The PVs do not need to be physically related to
one another nor be associated with a single Epics Record or Device.
Rather, an Instrument is defined at the level of the Epics Channel Access
client, allowing a station scientist or engineer to use their own grouping
of PVs as an abstract "Instrument".  A simple example would be a pair of
motors that work together to move some device.

In addition to a name and a set of PVs, an Instrument has a set of "named
Positions".  At any point, the current values of an Instruments PVs can be
saved as its Position.  And, of course, the named Positions can then be
restored simply by selecting the Position.
