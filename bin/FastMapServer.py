#!/usr/bin/python2.6
import sys
sys.path.insert(0,'lib')

from collector import TrajectoryScan
t = TrajectoryScan(configfile='default.scn')
t.mainloop()
