import sys
from EscanWriter import EscanWriter

foldername = sys.argv[1]
w = EscanWriter(folder=foldername)
w.process()
fout = w.scanconf['filename']
# fout = 't1.out'
f = open(fout, 'w')
f.write('\n'.join(w.buff))
f.close()
