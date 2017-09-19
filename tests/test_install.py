import pytest
import os
import sys 
import re

import epics


# These tests should only be run by Travis CI
pytestmark = pytest.mark.skipif(os.getenv('TRAVIS') is None,
                                reason='TRAVIS is not defined')

def test_libca_init():
    assert epics.ca.initialize_libca()
    
# Skip if Travis defines NOLIBCA
@pytest.mark.skipif(os.getenv('NOLIBCA') is not None,
                    reason='NOLIBCA is defined')
def test_install_encapsulation():
    libca = epics.ca.find_libca()
    system = sys.platform
    
    if 'linux' in system:
        assert re.search('.*/epics/clibs/.*/libca\.so$', libca)
    elif 'darwin' in system:
        assert re.search('.*/epics/clibs/.*/libca\.dylib$', libca)
    elif 'win' in system:
        assert re.search('.*\epics\clibs\.*/ca\\.dll$', libca)
    else:
        raise 'Are you using BSD? You are hardcore...'

# Skip if NOLIBCA is not defined
@pytest.mark.skipif(os.getenv('NOLIBCA') is None,
                    reason='NOLIBCA is not defined')
def test_install_no_libs():
    libca = epics.ca.find_libca()
    system = sys.platform

    if 'linux' in system:
        assert re.search('.*/epics/clibs/.*/libca\.so$', libca) is None
    elif 'darwin' in system:
        assert re.search('.*/epics/clibs/.*/libca\.dylib$', libca) is None
    elif 'win' in system:
        assert re.search('.*\epics\clibs\.*/ca\\.dll$', libca) is None
    else:
        raise 'Are you using BSD? You are hardcore...'
