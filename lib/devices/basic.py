#!/usr/bin/python 
import epics

"""This is a quick attempt to create generic devices for many
of the more common epics records.  These may be incomplete
and/or under-powered.
"""
class fields:
    common  = ('VAL','EGU','HOPR','LOPR','PREC','NAME','DESC','DTYP')
    alarm   = ('HIHI','LOLO','HIGH','LOW','HHSV','LLSV','HSV','LSV','HYST')
    monitor = ('ADEL','MDEL')
    output  = ('OMSL','DOL','OIF','DRVH','DRVL','OROC','OVAL')

class basicDevice(epics.Device):
    def __init__(self,prefix,attrs):
        if prefix.endswith('.'): prefix = prefix[:-1]
        epics.Device.__init__(self,prefix,sep='.',attrs=attrs)
    
class ai(basicDevice):
    """ 
    Simple analog input device
    """
    _fields = ('INP', 'LINR','RVAL','ROFF','EGUF','EGUL',
              'AOFF','ASLO', 'ESLO','EOFF','SMOO')
    def __init__(self,prefix):
        attrs  = (self._fields + fields.common +
                  fields.alarm + fields.monitor)
        basicDevice.__init__(self,prefix,attrs)

class ao(basicDevice):
    """ 
    Simple analog output device
    """
    _fields = ('OUT', 'LINR','RVAL','ROFF','EGUF','EGUL',
               'AOFF','ASLO', 'ESLO','EOFF')
    def __init__(self,prefix):
        attrs  = (self._fields + fields.common +
                  fields.alarm + fields.monitor + fields.output)        
        basicDevice.__init__(self,prefix,attrs)

class bi(basicDevice):
    """ 
    Simple binary input device
    """
    _fields = ('INP', 'ZNAM','ONAM','RVAL')

    def __init__(self,prefix):
        attrs  = (self._fields + fields.common )

        basicDevice.__init__(self,prefix,attrs)        

class bo(basicDevice):
    """ 
    Simple binary output device
    """
    _fields = ('DOL', 'OMSL','RVAL','HIGH','ZNAM','ONAM')
    def __init__(self,prefix):
        attrs  = (self._fields + fields.common )
        basicDevice.__init__(self,prefix,attrs)
