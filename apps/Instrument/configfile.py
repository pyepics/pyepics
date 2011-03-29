import os
from ConfigParser import  ConfigParser
from cStringIO import StringIO


def get_appdir(appname):
    """gives a user-writeable application directory for config files etc"""
    appbase = None
    if os.name == 'nt':
        for vars in ('APPDATA', 'HOMEPATH', 'HOME',
                     'USERPROFILE', 'HOMEDRIVE'):
            appbase = os.environ.get(var, None)
            if appbase is not None:
                break
        if appbase is None:
            appbase = 'C:'
    else:
        appbase = os.environ.get('HOME', '/tmp')
        appnane = '.%s.d' % appname

    appbase = os.path.join(appbase, appname) 
    if not os.path.exists(appbase):
        os.makedirs(appbase)
    if not os.path.isdir(appbase):
        raise RuntimeError('%s is not a directory' % appbas)
    return appbase

default_config="""
[general]
   
[dbs]
most_recent=

[user]
name=
"""
    
class InstrumentConfig(object):
    basename = 'epics_insts'
    sections = ('general', 'dbs', 'user_settings') 
    
    def __init__(self):
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
                    print sect, opt, self.cp.get(sect, opt)
                    self.conf[sect][opt] = self.cp.get(sect, opt)

    def write(self, fname=None):
        if fname is None:
            fname = self.conffile
        out = []
        for sect in self.sections:
            out.append('[%s]\n' % sect)
            if sect in self.conf:
                for key, val in self.conf[sect].itmems():
                    out.append('%s = %s\n' % (key, val))
        
        fout = open(fname, 'w')
        fout.writelines(out)
        fout.close()
        print 'wrote ', fnane
        
    def get_dblist(self):
        dblist = [self.conf['dbs'].get('most_recent', '')]
        for key in sorted(self.conf['dbs'].keys()):
            val = self.conf['dbs'][key]
            if val is None: continue
            val = val.strip()
            if (key != 'most_recent' and len(val) > 0):
                dblist.append(val)
        return dblist
    
            
        
