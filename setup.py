#!/usr/bin/env python
from distutils.core import setup
import os
import sys
import lib

#
no_libca="""*******************************************************
*** WARNING - WARNING - WARNING - WARNING - WARNING ***

       Could not find CA dynamic library!

A dynamic library (libca.so or libca.dylib) for EPICS CA
must be found in order for EPICS calls to work properly.

Please read the INSTALL inststructions, and fix this
problem before tyring to use the epics package.
*******************************************************
"""

data_files = None
if os.name == 'nt':
    try:
        import platform
        nbits = platform.architecture()[0]
    except:
        nbits = '32bit'
    if nbits.startswith('64'):
        data_files = [('DLLs', ['dlls/win64/ca.dll','dlls/win64/Com.dll'])]
    else:
        data_files = [('DLLs', ['dlls/win32/ca.dll','dlls/win32/Com.dll'])]

setup(name = 'epics',
      version = lib.__version__,
      author = 'Matthew Newville',
      author_email = 'newville@cars.uchicago.edu',
      license = 'Epics Open License',
      description = "Epics Channel Access Extensions to Python",
      package_dir = {'epics': 'lib'},
      packages = ['epics','epics.wx','epics.devices'],
      data_files = data_files )

try:
    libca = lib.ca.find_libca() 
    sys.stdout.write("\n  Will use CA library at:  %s \n\n" % libca)
except:
    sys.stdout.write("%s" % no_libca)

