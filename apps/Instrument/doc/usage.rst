====================================
Using Epics Instruments
====================================

Getting Started
=================


To run Epics Instruments, click on the icon.  You will see a small window
to select an Epics Instrument File.  If this is your first time using the
application, choose a name, and hit return to start a new Instrument File.
The next time you run Epics Instruments, it should remember which files
you've recently used, and present you with a drop-down list of Instrument
Files.


Defining an Instrument
==========================



The Instrument File
==========================

All the information for definitions of your Instruments and their Positions
are saved in a single file -- the Instruments file, with a default
extension of '.ein' (Epics INstruments).   You can use many different
Instrument Files for different domains of use. 

The Instrument File is an SQLite database file, and can be browsed and
manipulated with external tools.  Of course, this can be a very efficient
way of corrupting the data, so do this with caution.  A further note of
caution is to avoid having a single Instrument file open by multiple
applications -- this can also cause corruption.  The Instrument files can
be moved around and copied without problems.


 
