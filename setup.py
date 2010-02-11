#!/usr/bin/env python
from distutils.core import setup
import os
import lib


data_files = None
if os.name == 'nt':
    print 'Windows install!'
    data_files = [('DLLs', ['win32_dlls/ca.dll','win32_dlls/Com.dll'])]

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

