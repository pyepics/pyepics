#!/usr/bin/env python
#  M Newville <newville@cars.uchicago.edu>
#  The University of Chicago, 2010
#  Epics Open License
#
# Epics Database Records (DBR) Constants and Definitions
#  most of the code here is copied from db_access.h
#
""" constants and declaration of data types for Epics database records
This is mostly copied from CA header files
"""
import ctypes
import time

HAS_NUMPY = False
try:
    import numpy
    HAS_NUMPY = True
except ImportError:
    pass

# EPICS Constants
ECA_NORMAL = 1
ECA_TIMEOUT = 80
ECA_IODONE = 339
ECA_ISATTACHED = 424

CS_CONN    = 2
OP_CONN_UP = 6
OP_CONN_DOWN = 7

CS_NEVER_SEARCH = 4
#
# Note that DBR_XXX should be replaced with dbr.XXX
# 
STRING = 0
INT    = 1
SHORT  = 1
FLOAT  = 2
ENUM   = 3
CHAR   = 4
LONG   = 5
DOUBLE = 6

TIME_STRING  = 14
TIME_INT     = 15
TIME_SHORT   = 15
TIME_FLOAT   = 16
TIME_ENUM    = 17
TIME_CHAR    = 18
TIME_LONG    = 19
TIME_DOUBLE  = 20

CTRL_STRING  = 28
CTRL_INT     = 29
CTRL_SHORT   = 29
CTRL_FLOAT   = 30
CTRL_ENUM    = 31
CTRL_CHAR    = 32
CTRL_LONG    = 33
CTRL_DOUBLE  = 34

MAX_STRING_SIZE      = 40
MAX_UNITS_SIZE       =  8
MAX_ENUM_STRING_SIZE = 26
MAX_ENUMS            = 16

EPICS2UNIX_EPOCH = 631173600.0 - time.timezone

# create_subscription mask constants
DBE_VALUE = 1
DBE_LOG = 2
DBE_ALARM = 4
DBE_PROPERTY = 8


chid_t   = ctypes.c_long

short_t  = ctypes.c_short
ushort_t = ctypes.c_ushort
int_t    = ctypes.c_int
uint_t   = ctypes.c_uint
long_t   = ctypes.c_long
ulong_t  = ctypes.c_ulong
float_t  = ctypes.c_float
double_t = ctypes.c_double
byte_t   = ctypes.c_byte
ubyte_t  = ctypes.c_ubyte
string_t = ctypes.c_char * MAX_STRING_SIZE
char_t   = ctypes.c_char
char_p   = ctypes.c_char_p
void_p   = ctypes.c_void_p
py_obj   = ctypes.py_object

value_offset = None

# extended DBR types:
class TimeStamp(ctypes.Structure):
    "emulate epics timestamp"
    _fields_ = [('secs', uint_t), ('nsec', uint_t)]
_STAT_SEV    = (('status', short_t), ('severity', short_t))
_STAT_SEV_TS = (('status', short_t), ('severity', short_t),
                ('stamp', TimeStamp))
_UNITS       = ('units', char_t * MAX_UNITS_SIZE)

class time_string(ctypes.Structure):
    "dbr time string"
    _fields_ = list(_STAT_SEV_TS) + [('value', MAX_STRING_SIZE*char_t)]

    
class time_short(ctypes.Structure):
    "dbr time short"
    _fields_ = list(_STAT_SEV_TS) + [('RISC_pad',  short_t),
                                     ('value',     short_t)]

class time_float(ctypes.Structure):
    "dbr time float"
    _fields_ = list(_STAT_SEV_TS) + [('value',  float_t)]

class time_enum(ctypes.Structure):
    "dbr time enum"
    _fields_ = list(_STAT_SEV_TS) + [('RISC_pad',  short_t),
                                     ('value',    ushort_t)]

class time_char(ctypes.Structure):
    "dbr time char"
    _fields_ = list(_STAT_SEV_TS) + [('RISC_pad0', short_t),
                                     ('RISC_pad1', byte_t),
                                     ('value',     byte_t)]

class time_long(ctypes.Structure):
    "dbr time long"
    _fields_ = list(_STAT_SEV_TS) + [('value', int_t)]
    

class time_double(ctypes.Structure):
    "dbr time double"
    _fields_ = list(_STAT_SEV_TS) + [('RISC_pad', int_t),
                                     ('value',    double_t)]    
   
    
# DBR types with full control and graphical fields
# yes, this strange order is as in db_access.h!!!
ctrl_limits = ('upper_disp_limit',   'lower_disp_limit',
               'upper_alarm_limit',  'upper_warning_limit',
               'lower_warning_limit','lower_alarm_limit',
               'upper_ctrl_limit',   'lower_ctrl_limit')

def _gen_ctrl_lims(t=short_t):
    "create types for control limits"
    return  [(s, t) for s in  ctrl_limits]

class ctrl_enum(ctypes.Structure):
    "dbr ctrl enum"
    _fields_ = list(_STAT_SEV) 
    _fields_.extend([ ('no_str', short_t),
                      ('strs', (char_t * MAX_ENUM_STRING_SIZE) * MAX_ENUMS),
                      ('value',    ushort_t)])

class ctrl_short(ctypes.Structure):
    "dbr ctrl short"
    _fields_ = list(_STAT_SEV) + [_UNITS] +  _gen_ctrl_lims(t=short_t)
    _fields_.extend([('value', short_t )])
    
class ctrl_char(ctypes.Structure):
    "dbr ctrl long"
    _fields_ = list(_STAT_SEV) +[_UNITS] +  _gen_ctrl_lims(t=byte_t)    
    _fields_.extend([('RISC_pad', byte_t), ('value', ubyte_t)])
    
class ctrl_long(ctypes.Structure):
    "dbr ctrl long"
    _fields_ = list(_STAT_SEV) +[_UNITS] +  _gen_ctrl_lims(t=int_t)
    _fields_.extend([('value', int_t)])
    
class ctrl_float(ctypes.Structure):
    "dbr ctrl float"    
    _fields_ = list(_STAT_SEV)
    _fields_.extend([('precision',   short_t),
                     ('RISC_pad',    short_t)] + [_UNITS])
    _fields_.extend( _gen_ctrl_lims(t=float_t) )
    _fields_.extend([('value', float_t)])


class ctrl_double(ctypes.Structure):
    "dbr ctrl double"
    _fields_ = list(_STAT_SEV)
    _fields_.extend([('precision',   short_t),
                     ('RISC_pad',    short_t)] + [_UNITS])
    _fields_.extend( _gen_ctrl_lims(t=double_t) )
    _fields_.extend([('value',       double_t)])
    
    
NP_Map = {}
if HAS_NUMPY:
    NP_Map = {INT:    numpy.int16,
              FLOAT:  numpy.float32,
              ENUM:   numpy.uint16,
              CHAR:   numpy.uint8,
              LONG:   numpy.int32,
              DOUBLE: numpy.float64}
    

# map of Epics DBR types to ctypes types
Map = {STRING: string_t,
       INT:    short_t,
       FLOAT:  float_t,
       ENUM:   ushort_t,
       CHAR:   ubyte_t,
       LONG:   int_t,
       DOUBLE: double_t,

       TIME_STRING: time_string,
       TIME_INT: time_short, 
       TIME_SHORT:  time_short,
       TIME_FLOAT: time_float,
       TIME_ENUM:  time_enum,
       TIME_CHAR:  time_char,
       TIME_LONG:  time_long,
       TIME_DOUBLE: time_double,
       # Note: there is no ctrl string in the C definition
       CTRL_STRING:   time_string,
       CTRL_SHORT: ctrl_short,
       CTRL_INT:   ctrl_short,
       CTRL_FLOAT: ctrl_float,
       CTRL_ENUM:  ctrl_enum, 
       CTRL_CHAR:  ctrl_char,
       CTRL_LONG:  ctrl_long,
       CTRL_DOUBLE: ctrl_double
       }

def Name(ftype, reverse=False):
    """ convert integer data type to dbr Name, or optionally reverse that
    look up (that is, name to integer)"""
    m = {STRING: 'STRING',
         INT: 'INT',
         FLOAT: 'FLOAT',
         ENUM: 'ENUM',
         CHAR: 'CHAR',
         LONG: 'LONG',
         DOUBLE: 'DOUBLE',
         
         TIME_STRING: 'TIME_STRING',
         TIME_SHORT: 'TIME_SHORT',
         TIME_FLOAT: 'TIME_FLOAT',
         TIME_ENUM: 'TIME_ENUM',
         TIME_CHAR: 'TIME_CHAR',
         TIME_LONG: 'TIME_LONG',
         TIME_DOUBLE: 'TIME_DOUBLE',
         
         CTRL_STRING: 'CTRL_STRING',
         CTRL_SHORT: 'CTRL_SHORT',
         CTRL_FLOAT: 'CTRL_FLOAT',
         CTRL_ENUM: 'CTRL_ENUM',
         CTRL_CHAR: 'CTRL_CHAR',
         CTRL_LONG: 'CTRL_LONG',
         CTRL_DOUBLE: 'CTRL_DOUBLE',
         }
    if reverse:
        name = ftype.upper()
        if name in list(m.values()):
            for key, val in m.items():
                if name == val: return key
                
    return m.get(ftype,'unknown')

def cast_args(args):
    """returns pointer to arg type for casting """
    count, ftype = args.count, args.type
    #if ftype == STRING:
    #    print 'THIS IS CAST ARG for STRING '
    #    count = MAX_STRING_SIZE
    if ftype not in Map:
        ftype = double_t
    return ctypes.cast(args.raw_dbr, ctypes.POINTER(count*Map[ftype]))

class event_handler_args(ctypes.Structure):
    "event handler arguments"
    _fields_ = [('usr',     py_obj),
                ('chid',    chid_t),   
                ('type',    long_t),   
                ('count',   long_t),      
                ('raw_dbr', void_p),    
                ('status',  int_t)]

class connection_args(ctypes.Structure):
    "connection arguments"
    _fields_ = [('chid', chid_t), ('op', long_t)]

class exception_handler_args(ctypes.Structure):
    "exception arguments"
    _fields_ = [('usr',   void_p),
                ('chid',  chid_t),
                ('type',  int_t),
                ('count', int_t), 
                ('addr',  void_p),
                ('stat',  int_t),
                ('op',    int_t),
                ('ctx',   char_p), 
                ('pFile', char_p), 
                ('lineNo', int_t)] 

