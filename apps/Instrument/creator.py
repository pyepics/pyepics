#!/usr/bin/env python
"""
 provides make_newdb() function to create an empty Epics Instrument Library

"""
import sys
import os

from datetime import datetime

from sqlalchemy.orm import sessionmaker, create_session
from sqlalchemy import MetaData, create_engine, \
     Table, Column, Integer, Float, String, Text, DateTime, ForeignKey

from utils import dumpsql, backup_versions

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
    info    = [["version", "1.1"],
               ["verify_erase", "1"],
               ["verify_move",   "1"],
               ["create_date", '<now>'],
               ["modify_date", '<now>']]

    pvtype = [['generic',   'Generic PV'],
              ['numeric',   'Numeric Value'],
              ['enum',      'Enumeration Value'],
              ['string',    'String Value'],
              ['motor',     'Motor Value']]

def  make_newdb(dbname, server= 'sqlite'):
    engine  = create_engine('%s:///%s' % (server, dbname))
    metadata =  MetaData(engine)
    
    instrument = NamedTable('instrument', metadata,
                            cols=[Column('show', Integer, default=1),
                                  Column('order', Integer)])

    command    = NamedTable('command', metadata,
                            cols=[StrCol('command'),
                                  StrCol('arguments'),
                                  StrCol('output_value'),
                                  StrCol('output_name')])

    position  = NamedTable('position', metadata,
                           cols=[Column('date', DateTime),
                                 PointerCol('instrument')])
    
    instrument_precommand = NamedTable('instrument_precommand', metadata,
                                       cols=[Column('iorder', Integer),
                                             PointerCol('command'),
                                             PointerCol('instrument')])
                                     
    instrument_postcommand = NamedTable('instrument_postcommand', metadata,
                                        cols=[Column('iorder', Integer), 
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
                        StrCol('notes'),                        
                        PointerCol('position'),
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

    
if __name__ == '__main__':
    dbname = 'Test.ein'
    backup_versions(dbname)
    make_newdb(dbname)
    print '''%s  created and initialized.''' % dbname
    dumpsql(dbname)
