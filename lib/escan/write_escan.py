import sys
from EscanWriter import EscanWriter

foldername = sys.argv[1]
w = EscanWriter(folder=foldername)
w.process()
fout = w.scanconf['filename']
# fout = 't1.out'
print 'writing %s' % fout
f = open(fout, 'w')
f.write('\n'.join(w.buff))
f.write('\n')
f.close()
