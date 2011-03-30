#!/usr/bin/env python
"""
SQLAlchemy wrapping of Instrument database

Main Class for full Database:  InstrumentDB

classes for Tables:
  Instrument
  Position


"""

import os
import sys
import json

import numpy
from datetime import datetime

from creator import make_newdb, backup_versions


from sqlalchemy import MetaData, create_engine, and_
from sqlalchemy.orm import sessionmaker,  mapper, relationship, backref
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import  NoResultFound

def isInstrumentDB(dbname):
    """test if a file is a valid Instrument Library file:
       must be a sqlite db file, with tables named
          'info', 'instrument', 'position', 'pv', 
       'info' table must have an entries named 'version' and 'create_date'
    """

    try:
        engine  = create_engine('sqlite:///%s' % dbname)
        metadata =  MetaData(engine)
        metadata.reflect()
    except:
        return False

    if ('info' in metadata.tables and
        'instrument' in metadata.tables and
        'position' in metadata.tables and
        'pv' in metadata.tables):
        info = metadata.tables['info'].select().execute().fetchall()
        keys = [row.key for row in info]
        return ('version' in keys and 'create_date' in keys)
    return False

def json_encode(val):
    "simple wrapper around json.dumps"
    if val is None or isinstance(val, (str, unicode)):
        return val
    return  json.dumps(val)

def valid_score(score, smin=0, smax=5):
    """ensure that the input score is an integr
    in the range [smin, smax]  (inclusive)"""
    return max(smin, min(smax, int(score)))
    

def isotime2datetime(isotime):
    sdate, stime = isotime.replace('T', ' ').split(' ')
    syear, smon, sday = [int(x) for x in sdate.split('-')]
    sfrac = '0'
    if '.' in stime:
        stime, sfrac = stime.split('.')
    shour, smin, ssec  = [int(x) for x in stime.split(':')]
    susec = int(1e6*float('.%s' % sfrac))

    return datetime(syear, smon, sday, shour, smin, ssec, susec)

def None_or_one(val, msg='Expected 1 or None result'):
    """expect result (as from query.all() to return
    either None or exactly one result
    """
    if len(val) == 1:
        return val[0]
    elif len(val) == 0:
        return None
    else:
        raise InstrumentDBException(msg)            


class InstrumentDBException(Exception):
    """DB Access Exception: General Errors"""
    def __init__(self, msg):
        Exception.__init__(self)
        self.msg = msg
    def __str__(self):
        return self.msg


class _BaseTable(object):
    "generic class to encapsulate SQLAlchemy table"
    def __repr__(self):
        name = self.__class__.__name__
        fields = ['%s' % getattr(self, 'name', 'UNNAMED')]
        return "<%s(%s)>" % (name, ', '.join(fields))


class Info(_BaseTable):
    "general information table (versions, etc)"
    def __repr__(self):
        name = self.__class__.__name__
        fields = ['%s=%s' % (getattr(self, 'key', '?'),
                             getattr(self, 'value', '?'))]
        return "<%s(%s)>" % (name, ', '.join(fields))

class Instrument(_BaseTable):
    "instrument table"
    pass 

class Position(_BaseTable):
    "position table"
    pass

class Position_PV(_BaseTable):
    "position-pv join table"    
    def __repr__(self):
        name = self.__class__.__name__
        fields = ['%s=%s' % (getattr(self, 'pv', '?'),
                             getattr(self, 'value', '?'))]
        return "<%s(%s)>" % (name, ', '.join(fields))

class Command(_BaseTable):
    "command table"    
    pass

class PVType(_BaseTable):
    "pvtype table"
    pass

class PV(_BaseTable):
    "pv table"


class Instrument_Precommand(_BaseTable):
    "instrument precommand table"
    pass

class Instrument_Postcommand(_BaseTable):
    "instrument postcommand table"
    pass

class InstrumentDB(object):
    "interface to Instrument Database"
    def __init__(self, dbname=None):
        self.engine = None
        self.session = None
        self.metadata = None
        self.update_mod_time = None

        if dbname is not None:
            self.connect(dbname)
            
    def create_newdb(self, dbname, connect=False):
        "create a new, empty database"
        if os.path.exists(dbname):
            backup_versions(dbname)
        make_newdb(dbname)
        if connect:
            self.connect(dbname)

    def connect(self, dbname):
        "connect to an existing database"
        if not os.path.exists(dbname):
            raise IOError("Database '%s' not found!" % dbname)

        if not isInstrumentDB(dbname):
            raise ValueError("'%s' is not an Instrument file!" % dbname)

        self.dbname = dbname
        self.engine = create_engine('sqlite:///%s' % self.dbname)
        self.metadata =  MetaData(self.engine)
        
        self.metadata.reflect()
        tables = self.tables = self.metadata.tables
        self.session = sessionmaker(bind=self.engine)()

        mapper(Info,     tables['info'])
        mapper(Command,  tables['command'])
        mapper(PV,       tables['pv'])
               
        mapper(Instrument, tables['instrument'],
               properties={'pvs': relationship(PV,
                                               backref='instrument',
                                    secondary=tables['instrument_pv'])})
               
        mapper(PVType,   tables['pvtype'],
               properties={'pv':
                           relationship(PV, backref='pvtype')})
               
        mapper(Position, tables['position'], 
               properties={'instrument': relationship(Instrument,
                                                      backref='positions'),
                           'pvs': relationship(Position_PV) })

        mapper(Position_PV, tables['position_pv'], 
               properties={'pv':relationship(PV)})
        
        mapper(Instrument_Precommand,  tables['instrument_precommand'], 
               properties={'instrument': relationship(Instrument,
                                                      backref='precommands'),
                           'command':   relationship(Command,
                                                     backref='inst_precoms')})
        mapper(Instrument_Postcommand,   tables['instrument_postcommand'], 
               properties={'instrument': relationship(Instrument,
                                                      backref='postcommands'),
                           'command':   relationship(Command,
                                                     backref='inst_postcoms')})
    def commit(self):
        "commit session state"
        self.set_mod_time()        
        return self.session.commit()
        
    def close(self):
        "close session"
        self.session.commit()
        self.session.flush()
        self.session.close()

    def query(self, *args, **kws):
        "generic query"
        return self.session.query(*args, **kws)

    def set_info(self, key, value):
        """set key / value in the info table"""
        table = self.tables['info']
        vals  = self.query(table).filter(Info.key==key).all()
        if len(vals) < 1:
            # none found -- insert
            table.insert().execute(key=key, value=value)
        else:
            table.update(whereclause="key='%s'" % key).execute(value=value)
            
    def set_mod_time(self):
        """set modify_date in info table"""
        if self.update_mod_time is None:
            self.update_mod_time = self.tables['info'].update(
                whereclause="key='modify_date'")
        self.update_mod_time.execute(value=datetime.isoformat(datetime.now()))

    def __addRow(self, table, argnames, argvals, **kws):
        """add generic row"""
        me = table() #
        arg0 = argnames[0]
        val0 = argvals[0]
        for name, val in zip(argnames, argvals):
            setattr(me, name, val)
        for key, val in kws.items():
            if key == 'attributes':
                val = json_encode(val)
            setattr(me, key, val)
        try:
            self.session.add(me)
            # self.session.commit()
        except IntegrityError, msg:
            self.session.rollback()
            raise Warning('Could not add data to table %s\n%s' % (table, msg))

        return me
    # return self.query(table).filter(getattr(table, arg0)==val0).one()
        

    def _get_foreign_keyid(self, table, value, name='name',
                           keyid='id', default=None):
        """generalized lookup for foreign key
arguments
    table: a valid table class, as mapped by mapper.
    value: can be one of the following
         table instance:  keyid is returned
         string:          'name' attribute (or set which attribute with 'name' arg)
            a valid id
            """
        if isinstance(value, table):
            return getattr(table, keyid)
        else:
            if isinstance(value, (str, unicode)):
                xfilter = getattr(table, name)
            elif isinstance(value, int):
                xfilter = getattr(table, keyid)
            else:
                return default
            try:
                query = self.query(table).filter(
                    xfilter==value)
                return getattr(query.one(), keyid)
            except (IntegrityError, NoResultFound):
                return default

        return default

    def get_instrument(self, name):
        """return instrument by name
        """
        if isinstance(name, Instrument):
            return name
        out = self.query(Instrument).filter(Instrument.name==name).all()
        return None_or_one(out, 'get_instrument expected 1 or None Instrument')

    def get_pv(self, name):
        """return pv by name
        """
        if isinstance(name, PV):
            return name
        out = self.query(PV).filter(PV.name==name).all()
        return None_or_one(out, 'get_pv expected 1 or None PV')

    def get_position(self, name, instrument=None):
        """return position from namea and instrument
        """
        inst = None
        if instrument is not None:
            inst = self.get_instrument(instrument)

        filter = Position.name==name
        if inst is not None:
            filter = and_(filter, Position.instrument_id==inst.id)

        out =  self.query(Position).filter(filter).all()
        return None_or_one(out, 'get_position expected 1 or None Position')

    def get_position_pv(self, name, instrument=None):
        """return position from namea and instrument
        """
        inst = None
        if instrument is not None:
            inst = self.get_instrument(instrument)

        filter = Position.name==name
        if inst is not None:
            filter = and_(filter, Position.instrument_id==inst.id)

        out =  self.query(Position).filter(filter).all()
        return None_or_one(out, 'get_position expected 1 or None Position')

    def add_instrument(self, name, pvs=None, notes=None,
                       attributes=None, **kws):
        """add instrument
        notes and attributes optional
        returns Instruments instance"""
        kws['notes'] = notes
        kws['attributes'] = attributes

        inst = self.__addRow(Instrument, ('name',), (name,), **kws)
        if pvs is not None:
            pvlist = []
            for pvname in pvs:
                thispv = self.get_pv(pvname)
                if thispv is None:
                    thispv = self.add_pv(pvname)
                pvlist.append(thispv)
            inst.pvs = pvlist
        self.session.add(inst)
        self.commit()
        return inst
        
    def add_pv(self, name, notes=None, attributes=None, **kws):
        """add pv
        notes and attributes optional
        returns PV instance"""
        kws['notes'] = notes
        kws['attributes'] = attributes

        row = self.__addRow(PV, ('name',), (name,), **kws)
        self.commit()
        return row
        
    def add_info(self, key, value):
        """add Info key value pair -- returns Info instance"""
        row = self.__addRow(Info, ('key', 'value'), (key, value))
        self.commit()        
        return row
    
    def save_position(self, posname, inst, values, **kw):
        """save position for instrument
        """
        inst = self.get_instrument(inst)
        if inst is None:
            raise InstrumentDBException('Save Postion needs valid instrument')
            
        posname = posname.strip()
        pos  = self.get_position(posname, inst)
        if pos is None:
            pos = Position()
            pos.name = posname
            pos.instrument = inst
            pos.date = datetime.now()
            
        pvnames = [pv.name for pv in inst.pvs]

        # check for missing pvs in values
        missing_pvs = []
        for pv in pvnames:
            if pv not in values:
                missing_pvs.append(pv)
                
        if len(missing_pvs) > 0:
            raise InstrumentDBException('Save Postion: missing pvs:\n %s' %
                                        missing_pvs)
        
        pos_pvs = []
        for name in pvnames:
            ppv = Position_PV()
            ppv.pv = self.get_pv(name)
            ppv.date = datetime.now()
            ppv.notes = "'%s' / '%s'" % (inst.name, posname)
            ppv.value = values[name]
            pos_pvs.append(ppv)
        pos.pvs = pos_pvs
        
        self.session.add(pos)
        self.commit()
        
    def restore_position(self, posname, inst, exclude_pvs=None):
        """restore named position for instrument
        """
        inst = self.get_instrument(inst)
        if inst is None:
            raise InstrumentDBException('restore_postion needs valid instrument')
            
        posname = posname.strip()
        pos  = self.get_position(posname, inst)
        if inst is None:
            raise InstrumentDBException("restore_postion  position '%s' not found" % posname)
        
        if exclude_pvs is None:
            exclude_pvs = []

        settings = self.get_position(posname, inst)
        print 'Pre_Commands: ', inst.precommands
        
        for pvpos in settings.pvs:
            pvname = pvpos.pv.name
            if pvname not in exclude_pvs:
                print 'caput(%s, %s)' % (pvname, pvpos.value)

        print 'Post_Commands: ',  inst.postcommands
