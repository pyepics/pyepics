"""
This module provides simple save/restore functionality for PVs, similar to
the autosave module in synApps for IOCs but (obviously) via Channel Access.

Request & Save file formats are designed to be compatible with synApps autosave.

Use of this module requires the pyparsing parser framework. 
The Debian/Ubuntu package is "python-pyparsing"
The web site is http://pyparsing.wikispaces.com/

"""
from . import save_restore

AutoSaver = save_restore.AutoSaver
restore_pvs = save_restore.restore_pvs
save_pvs = save_restore.save_pvs
