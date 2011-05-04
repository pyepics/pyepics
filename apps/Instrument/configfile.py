import os
from ConfigParser import  ConfigParser
from cStringIO import StringIO

def get_appdir(appname):
    """gives a user-writeable application directory for config files etc"""
    appbase = None
    if os.name == 'nt':
        for var in ('APPDATA', 'HOMEPATH', 'HOME',
                     'USERPROFILE', 'HOMEDRIVE'):
            appbase = os.environ.get(var, None)
            if appbase is not None:
                break
        if appbase is None:
            appbase = 'C:'
    else:
        appbase = os.environ.get('HOME', '/tmp')
        appname = '.%s' % appname
    appbase = os.path.join(appbase, appname)
    if not os.path.exists(appbase):
        os.makedirs(appbase)
    if not os.path.isdir(appbase):
        raise RuntimeError('%s is not a directory' % appbas)
    return appbase

default_config="""
[dbs]
most_recent=MyInstruments.ein
"""
    
class InstrumentConfig(object):
    basename = 'epics_insts'
    sections = ('dbs',)
    
    def __init__(self, name=None):
        self.conffile = name
        if name is None:
            self.conffile = os.path.join(get_appdir(self.basename),
                                         'config.ini')
        self.conf = {}
        self.cp =  ConfigParser()
        self.read()
        
    def read(self):
        for s in self.sections:
            self.conf[s] = {}
        if not os.path.exists(self.conffile):
            self.cp.readfp(StringIO(default_config))
        self.cp.read(self.conffile)

        for sect in self.sections:
            if self.cp.has_section(sect):
                for opt in self.cp.options(sect):
                    if opt is None:
                        continue
                    self.conf[sect][opt] = self.cp.get(sect, opt)

    def write(self, fname=None):
        if fname is None:
            fname = self.conffile
        out = []
        for sect in self.sections:
            out.append('[%s]\n' % sect)
            if sect == 'dbs':
                maxcount = 10
            if sect in self.conf:
                count = 0
                for key in sorted(self.conf[sect]):
                    val = self.conf[sect][key]
                    if count < maxcount:
                        out.append('%s = %s\n' % (key, val))
                        count += 1
                        
        fout = open(fname, 'w')
        fout.writelines(out)
        fout.close()
        
    def get_dblist(self):
        dblist = [self.conf['dbs'].get('most_recent', '')]
        for key in sorted(self.conf['dbs'].keys()):
            val = self.conf['dbs'][key]
            if val is None: continue
            val = val.strip()
            if (key != 'most_recent' and len(val) > 0):
                dblist.append(val)
        return dblist

    def set_current_db(self, dbname):
        dblist = self.get_dblist()
        idx = 1
        newlist = [dbname]
        for name in dblist:
            if len(name.strip()) > 0 and name not in newlist:
                key = 'v%2.2i' % idx
                self.conf['dbs'][key] = name
                idx += 1
                
        self.conf['dbs']['most_recent'] = dbname
