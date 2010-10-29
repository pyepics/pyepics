#!/usr/bin/python
import time
import os
from string import printable
from random import seed, randrange

WIN_BASE = 'T:\\'
UNIX_BASE = '/cars5/Data/'

def unixpath(d):
    if d.startswith(WIN_BASE):
        d = d.replace(WIN_BASE, UNIX_BASE)

    d = d.replace('\\','/')
    if not d.endswith('/'): d = '%s/' % d        
    return d

def winpath(d):
    if d.startswith('//'): d = d[1:]
    if d.startswith(UNIX_BASE):
        d = d.replace(UNIX_BASE, WIN_BASE)
    d = d.replace('/','\\')
    if not d.endswith('\\'): d = '%s\\' % d            
    return d

def nativepath(d):
    if os.name == 'nt':
        return winpath(d)
    return unixpath(d)

class debugtime(object):
    """ simple class to use for testing of timing:
    create with:
    >>> d = debugtime()

    then use
    >>> d.add('msg11')

    to record times at code points.  Print out results with
    >>> d.show()
    which prints messages, total exec time, and time since
    previous message.
    """
    def __init__(self):
        self.clear()

    def clear(self):
        self.times = []

    def add(self,msg=''):
        # print msg
        self.times.append((msg,time.time()))

    def show(self):
        m0,t0 = self.times[0]
        tlast= t0
        print "# %s  %s " % (m0,time.ctime(t0))
        print "#----------------"
        print "#       Message                       Total     Delta"
        for m,t in self.times[1:]:
            tt = t-t0
            dt = t-tlast
            if len(m)<32:
                m = m + ' '*(32-len(m))
            print "  %32s    %.3f    %.3f" % (m,tt, dt)
            tlast = t
    
def random_string(n):
    """  random_string(n)
    generates a random string of length n, that will match this pattern:
       [a-z][a-z0-9](n-1)
    """
    seed(time.time())
    s = [printable[randrange(0,36)] for i in range(n-1)]
    s.insert(0, printable[randrange(10,36)])
    return ''.join(s)

def pathOf(dir,base,ext):
    p = os.path
    return p.normpath(p.normcase(p.join(dir,"%s.%s" % (base,ext))))

def increment_filename(inpfile,ndigits=3):
    """
    increment a data filename, returning a new (non-existing) filename
 
       first see if a number is before '.'.  if so, increment it.
       second look for number in the prefix. if so, increment it.
       lastly, insert a '_001' before the '.', preserving suffix.

    the numerical part of the file name will contain at least three digits.

    >>> increment_filename('a.002')
    'a.003'
    >>> increment_filename('a.999')
    'a.1000'
    >>> increment_filename('b_017.xrf')
    'b_018.xrf'
    >>> increment_filename('x_10300243.dat')
    'x_10300244.dat'
    
    >>> increment_filename('x.dat')
    'x_001.dat'

    >>> increment_filename('C:/program files/oo/data/x.002')
    'C:/program files/ifeffit/data/x.003'

    >>> increment_filename('a_001.dat')
    'a_002.dat'
    >>> increment_filename('a_6.dat')
    'a_007.dat'
    
    >>> increment_filename('a_001.002')
    'a_001.003'

    >>> increment_filename("path/a.003")
    'path/a.004'
"""

    (dir,  file) = os.path.split(inpfile)
    (base, ext)  = os.path.splitext(file)
    ext   = ext[1:]
    if ndigits < 3: ndigits=3
    form  = "%%.%ii" % ndigits
    def _incr(base,ext):
        try: # first, try incrementing the file extension
            ext = form % (int(ext)+1)
        except ValueError:
            try: #  try incrementing the part of the base after the last '_'
                bparts = base.split('_')
                bparts[-1] = form % (int(bparts[-1])+1)
                base = '_'.join(bparts)
            except:  # last, add a '_001' appendix
                base = "%s_001" % base
        return (base,ext)

    # increment once
    base,ext = _incr(base,ext)
    fout     = pathOf(dir,base,ext)

    # then gaurantee that file does not exist,
    # continuing to increment if necessary
    while(os.path.exists(fout)):
        base,ext = _incr(base,ext)
        fout     = pathOf(dir,base,ext)
    return fout

def new_filename(fname=None,ndigits=3):
    """ generate a new file name, either based on
    filename or generating a random one
    
    >>> new_filename(fname='x.001')   
    'x.002'
    # if 'x.001' exists
    """
    if fname is None:
        ext = ("%%.%ii" % ndigits) % 1
        fname = "%s.%s" % (random_string(6), ext)
        
    if os.path.exists(fname):  
        fname = increment_filename(fname,ndigits=ndigits)

    return fname

if (__name__ == '__main__'):
    test = ( ('a.002', 'a.003'),
             ('a.999', 'a.1000'),
             ('b_017.xrf',  'b_018.xrf'),
             ('x_10300243.dat', 'x_10300244.dat'),
             ('x.dat' , 'x_001.dat'),
             ('C:/program files/data/x.002',
              'C:/program files/data/x.003'),
             ('a_001.dat', 'a_002.dat'),
             ('a_6.dat', 'a_007.dat'),
             ('a_001.002', 'a_001.003'),
             ('path/a.003',  'path/a.004'))
    npass = nfail = 0
    for inp,out in test:
        tval = increment_filename(inp)
        if tval != out:
            print "Error converting " , inp
            print "Got '%s'  expected '%s'" % (tval, out)
            nfail = nfail + 1
        else:
            npass = npass + 1
    print 'Passed %i of %i tests' % (npass, npass+nfail)
