from EscanWriter import EscanWriter
from mapper import mapper
import os


m = mapper('13XRM:map:')

basedir = m.basedir
scandir = m.workdir
fname   = m.filename

outfile = os.path.join(basedir, scandir, fname)
print outfile

saver   = EscanWriter(folder="%s/%s" %(basedir, scandir))

nlines = saver.process()

f = open(outfile, 'w')
f.write("%s\n" % '\n'.join(saver.buff))
f.close()


