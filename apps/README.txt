This directory contains Applications using PyEpics.   The intention is
to include programs that are either general-purpose or can be looked
at as example channel access applications.  These applications may
not be well-documented and may require additional third-party
libraries to work.

A list of the current apps:

    Instruments: Epics Instruments is a GUI app that allows an end-
user to group Epics PVs into a named "Instrument".  Many Instruments
can be defined, with each Instrument having its own Tab in a Notebook
-style window.  Most PVs will be displayed as simple name/value pairs,
but the PV type will be used to determine if the input text box allows
numeric-only, general strings.  For enum PVs, a drop-down list of state
names will be shown.  For PVs for a motor record, a full Motor panel
will be shown.  For all cases, editing in the text boxes is easy, and
many entry errors (eg, letters for a float value) are avoided.

Each Instrument has a set of named positions that save the values for
all PVs in that instrument when the position is named.  Any of the
named positions can be "restored", that is, all the PVs moved to the
values when the position was named at any time.

The set of defined instruments shown in the application, and all the
named positions are stored in a single file -- an sqlite3 database
file.  Multiple instances of the program can be running on the same
subnet and even computer without stepping on one another, though
the application works hard to prevent a second instance from using
an open-and-working definition file.


    Dependencies:  wxPython, sqlalchemy.

