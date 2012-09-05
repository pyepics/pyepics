#!/usr/bin/env python
# from distutils.core import setup
from setuptools import setup

import os
import sys
import lib
import shutil

long_desc = '''Python Interface to the Epics Channel Access protocol
of the Epics control system. '''

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
        data_files = [('DLLs', ['dlls/win64/ca.dll','dlls/win64/Com.dll']),
                      ('', ['dlls/win64/carepeater.exe'])]        
    else:
        data_files = [('DLLs', ['dlls/win32/ca.dll','dlls/win32/Com.dll']),
                      ('', ['dlls/win32/carepeater.exe'])]

PY_MAJOR, PY_MINOR = sys.version_info[:2]
if PY_MAJOR == 2 and PY_MINOR < 6:
    shutil.copy(os.path.join('lib', 'utils3.py'),
                os.path.join('lib', 'utils3_save_py.txt'))
    shutil.copy(os.path.join('lib', 'utils2.py'),
                os.path.join('lib', 'utils3.py'))

setup(name = 'pyepics',
      version      = lib.__version__,
      author       = 'Matthew Newville',
      author_email = 'newville@cars.uchicago.edu',
      url          = 'http://pyepics.github.com/pyepics/',
      download_url = 'http://pyepics.github.com/pyepics/',      
      license      = 'Epics Open License',
      description  = "Epics Channel Access for Python",
      long_description = long_desc,
      platforms    = ('Windows', 'Linux', 'Mac OS X'),
      classifiers  = ['Intended Audience :: Science/Research',
                      'Operating System :: OS Independent',
                      'Programming Language :: Python',
                      'Topic :: Scientific/Engineering'],      
      package_dir = {'epics': 'lib'},
      packages = ['epics','epics.wx','epics.devices',
                  'epics.compat', 'epics.autosave'],
      data_files = data_files )

try:
    libca = lib.ca.find_libca() 
    sys.stdout.write("\n  Will use CA library at:  %s \n\n" % libca)
except:
    sys.stdout.write("%s" % no_libca)

