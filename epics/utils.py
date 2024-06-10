"""
String and data utils
"""
import sys
import os

IOENCODING =  os.environ.get('PYEPICS_ENCODING',
              os.environ.get('PYTHONIOENCODING',
                             'utf-8'))

def str2bytes(st1):
    'string to byte conversion'
    if isinstance(st1, bytes):
        return st1
    return bytes(st1, IOENCODING)

def bytes2str(st1):
    'byte to string conversion'
    if isinstance(st1, str):
        return st1
    elif isinstance(st1, bytes):
        return str(st1, IOENCODING)
    else:
        return str(st1)

def strjoin(sep, seq):
    "join string sequence with a separator"
    if isinstance(sep, bytes):
        sep = bytes2str(sep)
    if len(seq) == 0:
        seq = ''
    elif isinstance(seq[0], bytes):
        tmp =[]
        for i in seq:
            if i == b'\x00':
                break
            tmp.append(bytes2str(i))
        seq = tmp
    return sep.join(seq)


def clib_search_path(lib):
    '''Assemble path to c library.

    Parameters
    ----------
    lib : str
        Either 'ca' or 'Com'.

    Returns
    --------
    str : string

    Examples
    --------
    >>> clib_search_path('ca')
    'linux64/libca.so'

    '''

    # determine which libca / libCom dll is appropriate
    try:
        import platform
        nbits = platform.architecture()[0]
        mach = platform.machine()
    except:
        nbits = '32bit'
        mach = 'x86_64'

    nbits = nbits.replace('bit', '')
    if mach.startswith('arm'):
        nbits = 'arm'

    libfmt = 'lib%s.so'
    if os.name == 'nt':
        libsrc = 'win'
        libfmt = '%s.dll'
    elif sys.platform == 'darwin':
        libsrc = 'darwin'
        if platform.machine() == 'arm64':
            libsrc, nbits = 'darwinarm', '64'
        libfmt = 'lib%s.dylib'
    elif sys.platform.startswith('linux'):
        libsrc = 'linux'

    else:
        return None

    return os.path.join("%s%s" % (libsrc, nbits), libfmt % lib)
