#!/usr/bin/env python
"""

 provides make_newdb() function to create an empty Epics Instrument Library

"""
import sys
import os

import shutil
from datetime import datetime

from sqlalchemy.orm import sessionmaker, create_session
from sqlalchemy import MetaData, create_engine, \
     Table, Column, Integer, Float, String, Text, DateTime, ForeignKey

def PointerCol(name, other=None, keyid='id', **kws):
    if other is None:
        other = name
    return Column("%s_%s" % (name, keyid), None,
                  ForeignKey('%s.%s' % (other, keyid), **kws))
    
def StrCol(name, size=None, **kws):
    if size is None:
        return Column(name, Text, **kws)
    else:
        return Column(name, String(size), **kws)

def NamedTable(tablename, metadata, keyid='id', nameid='name',
               name=True, notes=True, attributes=True, cols=None):
    args  = [Column(keyid, Integer, primary_key=True)]
    if name:
        args.append(StrCol(nameid, nullable=False, unique=True))
    if notes:
        args.append(StrCol('notes'))
    if attributes:
        args.append(StrCol('attributes'))
    if cols is not None:
        args.extend(cols)
    return Table(tablename, metadata, *args)

class InitialData:
    info    = [["version", "1.0.0"],
               ["create_date", '<now>'], 
               ["modify_date", '<now>']]

    pvtype = [['generic','Generic PV'], ['motor','Motor Value']]

def  make_newdb(dbname, server= 'sqlite'):
    engine  = create_engine('%s:///%s' % (server, dbname))
    metadata =  MetaData(engine)
    
    instrument = NamedTable('instrument', metadata)
    command    = NamedTable('command', metadata,
                            nameid='command',
                            cols=[StrCol('arguments')])
                                      
    position  = NamedTable('position', metadata,
                           cols=[Column('submission_date', DateTime),
                                 PointerCol('instrument')])

    instrument_precommand = NamedTable('instrument_precommand', metadata,
                                       cols=[Column('index', Integer), #  order of commands
                                             PointerCol('command'),
                                             PointerCol('instrument')])
                                     
    instrument_postcommand = NamedTable('instrument_postcommand', metadata,
                                        cols=[Column('index', Integer), #  order of commands                                       
                                              PointerCol('command'),
                                              PointerCol('instrument')])

    pvtype  = NamedTable('pvtype', metadata)
    pv      = NamedTable('pv', metadata, cols=[PointerCol('pvtype')])
    
    instrument_pv = Table('instrument_pv', metadata,
                          Column('id', Integer, primary_key=True), 
                          PointerCol('instrument') ,
                          PointerCol('pv'))

    position_pv = Table('position_pv', metadata,
                        Column('id', Integer, primary_key=True),
                        PointerCol('position') ,
                        PointerCol('pv'),
                        StrCol('value'))                        
                        
                        
    info       = Table('info', metadata,
                       Column('key', Text, primary_key=True, unique=True), 
                       StrCol('value'))

    metadata.create_all()
    session = sessionmaker(bind=engine)()

    for name, notes in InitialData.pvtype:
        pvtype.insert().execute(name=name, notes=notes)

    now = datetime.isoformat(datetime.now())

    for key, value in InitialData.info:
        if value == '<now>':
            value = now
        info.insert().execute(key=key, value=value)

    session.commit()    


def dumpsql(dbname, fname='MyInstrument_init.sql'):
    """ dump SQL statements for an sqlite db"""
    os.system('echo .dump | sqlite3 %s > %s' % (dbname, fname))
    
def backup_versions(fname, max=10):
    """keep backups of a file -- up to 'max', in order"""
    if os.path.exists(fname):
        for i in range(max-1, 0, -1):
            fb0 = "%s.%i" % (fname, i)
            fb1 = "%s.%i" % (fname, i+1)
            if os.path.exists(fb0):
                print ' %s -> %s ' % (fb0, fb1)
                shutil.move(fb0, fb1)
        print ' %s -> %s.1 ' % (fname, fname)                
        shutil.move(fname, "%s.1" % fname)        

    
if __name__ == '__main__':
    dbname = 'MyInstrument.einst'
    if os.path.exists(dbname):
        backup_versions(dbname)
        
    make_newdb(dbname)
    print '''%s  created and initialized.''' % dbname
    dumpsql(dbname)
