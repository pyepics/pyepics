#!/usr/bin/python
# This module provides support for the EPICS motor record.
#
# TODO: convert to using device.py
# 
# Author:         Mark Rivers / Matt Newville
# Created:        Sept. 16, 2002
# Modifications:
#   Jun 14, 2010  MN
#       migrated more fully to pyepics3, using epics.Device
# 
#   Jan 16, 2008  MN
#       use new EpicsCA.PV put-with-user-wait
#       wait() method no longer needed
#       added MotorException and MotorLimitException
#       many fixes to use newer python constructs
# 
#   Aug 19, 2004  MN
#                 1. improved setting / checking of monitors on motor attributes
#                 2. add 'RTYP' and 'DTYP' to motor parameters.
#                 3. make sure the motor is a motor object, else raise a MotorException.
#   May 11, 2003  MN
#                 1. added get_pv(attribute) to return PV for attribute
#                 2. added __check_attr_stored(attr) method to
#                    consolidate checking if a PV is currently stored.
#   Feb 27, 2003  M Newville altered EpicsMotor:
#                 1. uses the EpicsCA.PV class, which automatically
#                    uses monitors to efficiently determine when to
#                    get PV values from the IOC
#                 2. increase the number of Motor attributes.
#                 3. increase the number of 'virtual attributes'.
#                    For example,
#                      >>>m = EpicsMotor('13BMD:m38')
#                      >>>m.drive = 20.
#                    causes the motor to move to 20 (user units).
#

import sys
import time

from . import pv
from . import ca
from . import device

class MotorLimitException(Exception):
    """ raised to indicate a motor limit has been reached """
    def __init__(self,msg,*args):
        self.msg = msg
    def __str__(self):
        return str(self.msg)

class MotorException(Exception):
    """ raised to indicate a problem with a motor"""
    def __init__(self,msg,*args):
        self.msg = msg
    def __str__(self):
        return str(self.msg)

class Motor(device.Device):
    """Epics Motor Class for pyepics3
    
   This module provides a class library for the EPICS motor record.

   It uses the epics PV class

   Virtual attributes:
      These attributes do not appear in the dictionary for this class, but
      are implemented with the __getattr__ and __setattr__ methods.  They
      simply get or putthe appropriate motor record fields.  All attributes
      can be both read and written unless otherwise noted. 

      Attribute        Description                  Field
      ---------        -----------------------      -----
      drive            Motor Drive Value            .VAL
      readback         Motor Readback Value         .RBV    (read-only) 
      slew_speed       Slew speed or velocity       .VELO
      base_speed       Base or starting speed       .VBAS
      acceleration     Acceleration time (sec)      .ACCL
      description      Description of motor         .DESC
      resolution       Resolution (units/step)      .MRES
      high_limit       High soft limit (user)       .HLM
      low_limit        Low soft limit (user)        .LLM
      dial_high_limit  High soft limit (dial)       .DHLM
      dial_low_limit   Low soft limit (dial)        .DLLM
      backlash         Backlash distance            .BDST
      offset           Offset from dial to user     .OFF
      done_moving      1=Done, 0=Moving, read-only  .DMOV
 
   Exceptions:
      The check_limits() method raises an 'MotorLimitException' if a soft limit
      or hard limit is detected.  The move() method calls
      check_limits() unless they are called with the 
      ignore_limits=True keyword set.

   Example use:
      from epics import Motor
      m = Motor('13BMD:m38')
      m.move(10)               # Move to position 10 in user coordinates
      m.move(100, dial=True)   # Move to position 100 in dial coordinates
      m.move(1, step=True, relative=True) # Move 1 step relative to current position

      m.stop()                 # Stop moving immediately
      high = m.high_limit      # Get the high soft limit in user coordinates
      m.dial_high_limit = 100  # Set the high limit to 100 in dial coodinates
      speed = m.slew_speed     # Get the slew speed
      m.acceleration = 0.1     # Set the acceleration to 0.1 seconds
      p=m.get_position()       # Get the desired motor position in user coordinates
      p=m.get_position(dial=1) # Get the desired motor position in dial coordinates
      p=m.get_position(readback=1) # Get the actual position in user coordinates
      p=m.get_position(readback=1, step=1) Get the actual motor position in steps
      p=m.set_position(100)   # Set the current position to 100 in user coordinates
         # Puts motor in Set mode, writes value, puts back in Use mode.
      p=m.set_position(10000, step=1) # Set the current position to 10000 steps

    """
    # parameter name (short), PV suffix,  longer description

    __motor_attrs = {
        'enabled': '_able.VAL', 
        'acceleration':    '.ACCL',
        'back_accel':      '.BACC',
        'backlash':        '.BDST',
        'back_speed':      '.BVEL',
        'card':            '.CARD',
        'dial_high_limit': '.DHLM',
        'direction':       '.DIR',
        'dial_low_limit':  '.DLLM',
        'settle_time':     '.DLY',
        'done_moving':     '.DMOV',
        'dial_readback':   '.DRBV',
        'description':     '.DESC',
        'dial_drive':      '.DVAL',
        'units':           '.EGU',
        'encoder_step':    '.ERES',
        'freeze_offset':   '.FOFF',
        'move_fraction':   '.FRAC',
        'hi_severity':     '.HHSV',
        'hi_alarm':        '.HIGH',
        'hihi_alarm':      '.HIHI',
        'high_limit':      '.HLM',
        'high_limit_set':  '.HLS',
        'hw_limit':        '.HLSV',
        'home_forward':    '.HOMF',
        'home_reverse':    '.HOMR',
        'high_op_range':   '.HOPR',
        'high_severity':   '.HSV',
        'integral_gain':   '.ICOF',
        'jog_accel':       '.JAR',
        'jog_forward':     '.JOGF',
        'jog_reverse':     '.JOGR',
        'jog_speed':       '.JVEL',
        'last_dial_val':   '.LDVL',
        'low_limit':       '.LLM',
        'low_limit_set':   '.LLS',
        'lo_severity':     '.LLSV',
        'lolo_alarm':      '.LOLO',
        'low_op_range':    '.LOPR',
        'low_alarm':       '.LOW',
        'last_rel_val':    '.LRLV',
        'last_dial_drive': '.LRVL',
        'last_SPMG':       '.LSPG',
        'low_severity':    '.LSV',
        'last_drive':      '.LVAL',
        'soft_limit':      '.LVIO',
        'in_progress':     '.MIP',
        'missed':          '.MISS',
        'moving':          '.MOVN',
        'resolution':      '.MRES',
        'motor_status':    '.MSTA',
        'offset':          '.OFF',
        'output_mode':     '.OMSL',
        'output':          '.OUT',
        'prop_gain':       '.PCOF',
        'precision':       '.PREC',
        'readback':        '.RBV',
        'retry_max':       '.RTRY',
        'retry_count':     '.RCNT',
        'retry_deadband':  '.RDBD',
        'dial_difference': '.RDIF',
        'raw_encoder_pos': '.REP',
        'raw_high_limit':  '.RHLS',
        'raw_low_limit':   '.RLLS',
        'relative_value':  '.RLV',
        'raw_motor_pos':   '.RMP',
        'raw_readback':    '.RRBV',
        'readback_res':    '.RRES',
        'raw_drive':       '.RVAL',
        'dial_speed':      '.RVEL',
        's_speed':         '.S',
        's_back_speed':    '.SBAK',
        's_base_speed':    '.SBAS',
        's_max_speed':     '.SMAX',
        'set':             '.SET',
        'stop_go':         '.SPMG',
        's_revolutions':   '.SREV',
        'stop':            '.STOP',
        't_direction':     '.TDIR',
        'tweak_forward':   '.TWF',
        'tweak_reverse':   '.TWR',
        'tweak_val':       '.TWV',
        'use_encoder':     '.UEIP',
        'u_revolutions':   '.UREV',
        'use_rdbl':        '.URIP',
        'drive':           '.VAL',
        'base_speed':      '.VBAS',
        'slew_speed':      '.VELO',
        'version':         '.VERS',
        'max_speed':       '.VMAX',
        'use_home':        '.ATHM',
        'deriv_gain':      '.DCOF',
        'use_torque':      '.CNEN',
        'device_type':     '.DTYP',
        'record_type':     '.RTYP',
        'status':          '.STAT'}
        
## fields not implemented:
##    
    # VOF   Variable Offset
    # SSET  Set SET Mode 
    # STOO  STOP OutLink 
    # SUSE  Set USE Mode  
    # RLNK  Readback OutLink  
    # RINP  RMP Input Link 
    # CDIR  Command direction
    # DIFF  Difference dval-drbv
    # DOL   Desired Output Location
    # FOF   Freeze Offset  
    # MMAP  Monitor Mask  
    # NMAP  Monitor Mask  
    # POST  Post-move commands
    # PP    Post process command
    # PREM  Pre-move commands 
    # PERL  Periodic Limits
    # RDBL  Readback Location
    # INIT  Startup commands 
    
    __init_list = ('drive','description', 'readback','precision',
                   'tweak_val','tweak_forward','tweak_reverse',
                   'done_moving','set','stop', 'low_limit','high_limit',
                   'high_limit_set', 'low_limit_set', 'soft_limit','status',
                   'device_type',  'record_type', 'enabled')
    
    _user_params = ('drive','readback','user')
    _dial_params = ('dial_drive','dial_readback','dial')
    _raw_params  = ('raw_drive','raw_readback','raw')

    def __init__(self, name=None, timeout=3.0):
        if name is None:
            raise MotorException("must supply motor name")
        
        if name.endswith('.VAL'):   name = name[:-4]
        if name.endswith('.'):         name = name[:-1]
            
        device.Device.__init__(self, name, [self.__motor_attrs[i] for i in self.__init_list])
        
        self.pvname = name
        # make sure motor is enabled:
        t0 = time.time()
        connected = False
        while not connected:
            connected = self.PV('.RTYP').connected
            time.sleep(0.001)
            if (time.time()-t0 > timeout):
                raise MotorException("Cannot connect to %s" % name)                
            rectype = self.PV('.RTYP').get()

        rectype = self.PV('.RTYP').get()            
        if rectype != 'motor':
            raise MotorException("%s is not an Epics Motor" % name)

        self._callbacks = {}

    def __repr__(self):
        return "<epics.Motor: %s: '%s'>" % (self.pvname, self.get_field('description'))

    def __str__(self):
        return self.__repr__()

    def __getattr__(self,attr):
        " internal method "
        if attr in self.__motor_attrs:
            return self.get_field(attr)
        elif attr in self.__dict__:
            return self.__dict__[attr]
        else:
            raise MotorException("EpicsMotor has no attribute %s" % attr)

    def __setattr__(self,attr,val):
        if attr in self.__motor_attrs:
            return self.put_field(attr,val)
        else:
            self.__dict__[attr] = val

    def put_field(self, attr, val, wait=False, timeout=30):
        """set a Motor attribute (field) to a value
        example:
          >>> motor = Motor('XX:m1')
          >>> motor.put_field('slew_speed', 2)

        which would be equivalent to
          >>> motor.slew_speed = 2

        setting the optional 'wait' keyword to True will
        cause this routine to wait to return until the
        put is complete.  This is most useful when setting
        the field may take time to complete, as when moving
        the motor position.  That is,
          >>> motor.put_field('drive', 2, wait=True)

        will wait until the motor has moved to drive position 2.
        """
        x = self.get_field(attr)
        
        suffix =self.__motor_attrs[attr]
        return self.PV(suffix).put(val, wait=wait, timeout=timeout)
    
    def get_field(self, attr, as_string=False):
        "get a motor attribute by name"
        if attr not in self.__motor_attrs:
            raise MotorException("EpicsMotor has no attribute %s" % attr)
        
        suffix =self.__motor_attrs[attr]
        return self.PV(suffix).get(as_string=as_string)

    def check_limits(self):
        """ check motor limits:
        returns None if no limits are violated
        raises expection if a limit is violated"""
        for field,msg in (('soft_limit',     'Soft limit violation'),
                          ('high_limit_set', 'High hard limit violation'),
                          ('low_limit_set',  'Low  hard limit violation')):
            if self.get_field(field)!= 0:
                raise MotorLimitException(msg)
        return
    
    def within_limits(self, val, limits='user'):
        """ returns whether a value for a motor is within drive limits,"""
        
        if limits == 'user':
            hlim = self.get_field('high_limit')
            llim = self.get_field('low_limit')
        elif limits == 'dial':
            hlim = self.get_field('dial_high_limit')
            llim = self.get_field('dial_low_limit')
        elif limits in ('step', 'raw'):
            hlim = self.get_field('raw_high_limit')
            llim = self.get_field('raw_low_limit')
        return (val <= hlim and val >= llim)

    def move(self, val=None, relative=None, wait=False, timeout=300.0,
             dial=False, step=False, raw=False, ignore_limits=False):

        """ moves motor drive to position

        arguments:
         val            value to move to (float) [Must be provided]
         relative       move relative to current position    (T/F) [F]
         wait           whether to wait for move to complete (T/F) [F]
         dial           use dial coordinates                 (T/F) [F]
         raw            use raw coordinates                  (T/F) [F]
         step           use raw coordinates (backward compat)(T/F) [F]
         ignore_limits  try move without regard to limits    (T/F) [F]
         timeout        max time for move to complete (in seconds) [300]
        returns:
          None : unable to move, invalid value given
          -1   : target value outside limits -- no move attempted
          -2   : with wait=True, wait time exceeded timeout
          0    : move executed successfully

          will raise an exception if a motor limit is met.
          
        """
        try:
            val = float(val)
        except TypeError:
            return None

        drv,rbv,lims = self._user_params
        if dial:
            drv, rbv, lims = self._dial_params
        if step or raw:
            drv, rbv, lims = self._raw_params
            ignore_limits = True
            
        if (relative):
            val = val + self.get_field(rbv)

        # Check for limit violations
        if not ignore_limits:
            limits_ok = self.within_limits(val,lims)
            if not limits_ok:
                return -1
            
        stat = self.put_field(drv,val,wait=wait,timeout=timeout)
        ret = stat
        if stat == 1:
            ret = 0
        if stat == -2:
            ret = -1
        try:
            self.check_limits()
        except:
            ret = -1
        return ret

    def get_position(self, dial=False, readback=False, step=False, raw=False):
        """
        Returns the target or readback motor position in user, dial or step
        coordinates.
      
      Keywords:
         readback:
            Set readback=True to return the readback position in the
            desired coordinate system.  The default is to return the
            drive position of the motor.
            
         dial:
            Set dial=True to return the position in dial coordinates.
            The default is user coordinates.
            
         raw (or step):
            Set raw=True to return the raw position in steps.
            The default is user coordinates.

         Notes:
            The "raw" or "step" and "dial" keywords are mutually exclusive.
            The "readback" keyword can be used in user, dial or step 
            coordinates.
            
      Examples:
        m=epicsMotor('13BMD:m38')
        m.move(10)                   # Move to position 10 in user coordinates
        p=m.get_position(dial=True)  # Read the target position in dial coordinates
        p=m.get_position(readback=True, step=True) # Read the actual position in steps
        """
        # xx
        (drv,rbv) = ('drive','readback')
        if dial:        (drv,rbv) = ('dial_drive','dial_readback')
        if step or raw: (drv,rbv) = ('raw_drive','raw_readback')        
            
        if readback:
            return self.get_field(rbv)
        else:
            return self.get_field(drv)
        
    def tweak(self, dir='forward', wait=False, timeout=300.0):
        """ move the motor by the tweak_val
       
        takes optional args:
         dir            direction of motion (forward/reverse)  [forward]
                           must start with 'rev' or 'back' for a reverse tweak.
         wait           wait for move to complete before returning (T/F) [F]
         timeout        max time for move to complete (in seconds) [300]           
        """
        
        ifield = 'tweak_forward'
        if dir.startswith('rev') or dir.startswith('back'):
            ifield = 'tweak_reverse'
            
        stat = self.put_field(ifield, 1, wait=wait, timeout=timeout)
        ret = stat
        if stat == 1:  ret = 0
        if stat == -2: ret = -1
        try:
            self.check_limits()
        except:
            ret = -1
        return ret

        
    def set_position(self, position, dial=False, step=False, raw=False):
        """
      Sets the motor position in user, dial or step coordinates.
      
      Inputs:
         position:
            The new motor position
            
      Keywords:
         dial:
            Set dial=True to set the position in dial coordinates.
            The default is user coordinates.
            
         raw:
            Set raw=True to set the position in raw steps.
            The default is user coordinates.
            
      Notes:
         The 'raw' and 'dial' keywords are mutually exclusive.
         
      Examples:
         m=epicsMotor('13BMD:m38')
         m.set_position(10, dial=True)   # Set the motor position to 10 in 
                                      # dial coordinates
         m.set_position(1000, raw=True) # Set the motor position to 1000 steps
         """

        # Put the motor in "SET" mode
        self.put_field('set',1)

      
        # determine which drive value to use
        drv = 'drive'
        if dial: drv = 'dial_drive'
        if step or raw: drv = 'raw_drive'

        self.put_field(drv,position)
        
        # Put the motor back in "Use" mode
        self.put_field('set',0)
      
    def get_pv(self,attr):
        "return  PV for a field"
        return self.PV(self.__motor_attrs[attr] )

    def clear_callback(self, attr='drive'):
        try:
            index = self._callbacks.get(attr,None)
            if index is not None:
                self.get_pv(attr).remove_callback(index=index)
        except:
            self.get_pv(attr).clear_callbacks()

    def set_callback(self, attr='drive', callback=None, kw=None):
        self.get_field(attr)

        kw_args = {}
        kw_args['motor_field'] = attr
        if kw is not None:
            kw_args.update(kw)
        # print 'Hello ', attr, self.get_pv(attr), kw_args
        index = self.get_pv(attr).add_callback(callback=callback,**kw_args)
        self._callbacks[attr] = index

    def refresh(self):
        """ refresh all motor parameters currently in use:
        make sure all used attributes are up-to-date."""
        ca.poll()


    def show_info(self):
        " show basic motor settings "
        self.refresh()
        o = []
        o.append(repr(self))
        o.append( "--------------------------------------")
        for i in ('description', 'drive','readback', 'slew_speed',
                  'precision','tweak_val','low_limit', 'high_limit',
                  'stop_go', 'set', 'status'):
            j = i
            if (len(j) < 16): j = "%s%s" % (j,' '*(16-len(j)))
            o.append("%s = %s" % (j, self.get_field(i,as_string=True)))
        o.append("--------------------------------------")
        sys.stdout.write("%s\n" % "\n".join(o))

    def show_all(self):
        """ show all motor attributes"""
        o = []
        add = o.append
        add("#Motor %s" % (self.pvname))
        add("#  field               value                 PV name")
        add("#------------------------------------------------------------")
        self.refresh()
        klist =list( self.__motor_attrs.keys())
        klist.sort()

        for attr in klist:
            label = attr  + ' '*(18-min(18,len(attr)))

            value = self.get_field(attr, as_string=True)
            pvname  = self.get_pv(attr).pvname

            if value is None: value = 'Not Connected??'
            value = value + ' '*(18-min(18,len(value)))
                                 
            add(" %s  %s  %s" % (label, value, pvname))
            
        sys.stdout.write("%s\n" % "\n".join(o))

        
if (__name__ == '__main__'):
    import sys
    for i in sys.argv[1:]:
        m = Motor(i)
        m.show_info()
