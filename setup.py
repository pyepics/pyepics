#!/usr/bin/env python
from distutils.core import setup
import os
import lib

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
        
setup(
    name = 'epics',
    version = lib.__version__,
    author = 'Matthew Newville',
    author_email = 'newville@cars.uchicago.edu',
    license = 'Python',
    description = "Epics Channel Access Extensions to Python",
    package_dir = {'epics': 'lib'},
    packages = ['epics','epics.wx'],
    data_files = data_files,
)

