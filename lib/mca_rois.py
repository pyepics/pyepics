import time
import sys
import epics
import ordereddict
MAX_ROIS=16

class MCA_ROIS(epics.Device):
    calib_attrs =('.CALO','.CALS','.CALQ')
    def __init__(self,prefix,mca=1,nrois=MAX_ROIS):
        self.prefix = "%smca%i" % (prefix,mca)
        self.maxrois = 16
        attrs = list(self.calib_attrs)
        for i in range(self.maxrois):
            attrs.extend(['.R%iNM' %i,'.R%iLO'%i,'.R%iHI'%i])
            
        epics.Device.__init__(self,self.prefix,attrs)
        epics.ca.poll()
       
    def getrois(self):
        rois = ordereddict.OrderedDict()        
        for i in range(self.maxrois):
            name = self.get('.R%iNM'%i)
            if name is not None and len(name.strip()) > 0:
                rois[name] = (self.get('.R%iLO'%i),self.get('.R%iHI'%i))

        self.rois = rois
        return rois

    def get_calib(self):
        return [self.get(i) for i in self.calib_attrs]

def get_MED_calib(prefix='13SDD1:',nmca=4):
    mcas = [MCA_ROIS(prefix,i+1) for i in range(nmca)]
    for m in mcas: m.get('.CALO')
    return [m.get_calib() for m in mcas]

def Write_MED_header(prefix='13SDD1:',nmca=4,filename=None):
    roidata = [MCA_ROIS(prefix,i+1).getrois() for i in range(nmca)]
    write = sys.stdout.write
    fh = None
    if filename is not None:
        fh = open(filename,'w')
        write = fh.write
    write('[rois]\n')
    write('prefix= %s\n' % prefix)
    for i, k in enumerate(roidata[0].keys()):
        s = [list(roidata[m][k]) for m in range(nmca)]
        write("ROI_%2.2i = %s || %s \n" % (i,k,repr(s)))
    write('[calib]\n')
    for i,dat in enumerate(get_MED_calib(prefix=prefix,nmca=4)):
        off,slope,quad = dat
        write("CAL_%2.2i = %.7g  %.7g %.7g \n" % (i,off,slope,quad))
    if fh is not None: fh.close()
            
def readROIFile(hfile):
    cp =  ConfigParser()
    cp.read(hfile)
    prefix = None
    rois = []
    env = []
    for a in cp.options('rois'):
        if a.lower().startswith('roi_'):
            iroi = int(a[4:])
            name,dat = cp.get('rois',a).split('||')
            rois.append((iroi,name.strip(), json.loads(dat)))
        elif a == 'prefix':
            prefix = cp.get('rois','prefix')
        
    return prefix,sorted(rois)
    

if __name__=='__main__':
    prefix= '13SDD1:'
    Write_MED_header(prefix,4,filename='X.dat')
    # x =  get_MED_calib(prefix=prefix,nmca=4)
    # print x
    #  print "ROI_%2.2i = %s || %s " % (i, ' '*(7-len(k))+k,repr(x[k]))
   
