#!/usr/bin/env python
from distutils.core import setup
import os

if os.name == 'nt':
    print 'Windows install'

setup(
    name = 'epics',
    version = '3.0',
    author = 'Matthew Newville',
    author_email = 'newville@cars.uchicago.edu',
    license = 'Python',
    description = "Epics Channel Access Extensions to Python",
    package_dir = {'epics': 'lib'},
    packages = ['epics','epics.wx'],
)

