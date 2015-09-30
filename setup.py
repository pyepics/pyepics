#!/usr/bin/env python
# from distutils.core import setup
from setuptools import setup

import os
import sys
import epics
import shutil

import versioneer
versioneer.VCS = 'git'
versioneer.versionfile_source = 'epics/_version.py'
versioneer.versionfile_build = 'epics/_version.py'
versioneer.tag_prefix = ''
versioneer.parentdir_prefix = 'pyepics-'


long_desc = '''Python Interface to the Epics Channel Access protocol
of the Epics control system.   PyEpics provides 3 layers of access to
Channel Access (CA):
  1. a light wrapping of the CA C library calls, using ctypes. This
     provides a procedural CA library in which the user is expected
     to manage Channel IDs. It is mostly provided as a foundation
     upon which higher-level access is built.
  2. PV() (Process Variable) objects, which represent the basic object
     in CA, allowing one to keep a persistent connection to a remote
     Process Variable.
  3. A simple set of functions caget(), caput() and so on to mimic
     the CA command-line tools and give the simplest access to CA.

In addition, the library includes convenience classes to define
Devices -- collections of PVs that might represent an Epics Record
or physical device (say, a camera, amplifier, or power supply), and
to help write GUIs for CA.
'''

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

# for Windows, we provide dlls
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
    shutil.copy(os.path.join('epics', 'utils3.py'),
                os.path.join('epics', 'utils3_save_py.txt'))
    shutil.copy(os.path.join('epics', 'utils2.py'),
                os.path.join('epics', 'utils3.py'))

setup(name = 'pyepics',
      version = versioneer.get_version(),
      cmdclass = versioneer.get_cmdclass(),
      author       = 'Matthew Newville',
      author_email = 'newville@cars.uchicago.edu',
      url          = 'http://pyepics.github.io/pyepics/',
      download_url = 'http://pyepics.github.io/pyepics/',      
      license      = 'Epics Open License',
      description  = "Epics Channel Access for Python",
      long_description = long_desc,
      platforms    = ['Windows', 'Linux', 'Mac OS X'],
      classifiers  = ['Intended Audience :: Science/Research',
                      'Operating System :: OS Independent',
                      'Programming Language :: Python',
                      'Topic :: Scientific/Engineering'],      
      packages = ['epics','epics.wx','epics.devices',
                  'epics.compat', 'epics.autosave'],
      data_files = data_files )

try:
    libca = epics.ca.find_libca() 
    sys.stdout.write("\n  Will use CA library at:  %s \n\n" % libca)
except:
    sys.stdout.write("%s" % no_libca)

