from EscanWriter import EscanWriter

import sys
foldername = sys.argv[1]

w = EscanWriter(folder = foldername)
w.process()
f = open('testEscan.dat','w')
f.write('\n'.join(w.buff))
f.close()
