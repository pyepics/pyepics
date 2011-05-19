#!/usr/bin/python
"""
 This module provides support for the EPICS motor record.
"""
# 
# Author:         Mark Rivers / Matt Newville
# Created:        Sept. 16, 2002
# Modifications:
#   Oct 15, 2010  MN
#       API Change, fuller inttegration with epics.Device,
#       much simpler interface
#              m = Motor('XXX:m1')
#              print m.get_field('drive')  # mapped to .VAL
#       becomes
#              m = Motor('XXX:m1')
#              print m.VAL
#              print m.drive     # now an alias to 'VAL'
#
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
#                 1. improved setting/checking of monitors on motor attributes
#                 2. add 'RTYP' and 'DTYP' to motor parameters.
#                 3. make sure the motor is a motor object, else
#                              raise a MotorException.
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

from . import ca
from . import device

class MotorLimitException(Exception):
    """ raised to indicate a motor limit has been reached """
    def __init__(self, msg, *args):
        Exception.__init__(self, *args)
        self.msg = msg
    def __str__(self):
        return str(self.msg)

class MotorException(Exception):
    """ raised to indicate a problem with a motor"""
    def __init__(self, msg, *args):
        Exception.__init__(self, *args)
        self.msg = msg
    def __str__(self):
        return str(self.msg)

class Motor(device.Device):
    """Epics Motor Class for pyepics3
    
   This module provides a class library for the EPICS motor record.

   It uses the epics.Device and epics.PV classese

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

    #
    _extras =  {
        'disabled':   '_able.VAL', }
    
    _alias = {
        'acceleration':    'ACCL',
        'back_accel':      'BACC',
        'backlash':        'BDST',
        'back_speed':      'BVEL',
        'card':            'CARD',
        'dial_high_limit': 'DHLM',
        'direction':       'DIR',
        'dial_low_limit':  'DLLM',
        'settle_time':     'DLY',
        'done_moving':     'DMOV',
        'dial_readback':   'DRBV',
        'description':     'DESC',
        'dial_drive':      'DVAL',
        'units':           'EGU',
        'encoder_step':    'ERES',
        'freeze_offset':   'FOFF',
        'move_fraction':   'FRAC',
        'hi_severity':     'HHSV',
        'hi_alarm':        'HIGH',
        'hihi_alarm':      'HIHI',
        'high_limit':      'HLM',
        'high_limit_set':  'HLS',
        'hw_limit':        'HLSV',
        'home_forward':    'HOMF',
        'home_reverse':    'HOMR',
        'high_op_range':   'HOPR',
        'high_severity':   'HSV',
        'integral_gain':   'ICOF',
        'jog_accel':       'JAR',
        'jog_forward':     'JOGF',
        'jog_reverse':     'JOGR',
        'jog_speed':       'JVEL',
        'last_dial_val':   'LDVL',
        'low_limit':       'LLM',
        'low_limit_set':   'LLS',
        'lo_severity':     'LLSV',
        'lolo_alarm':      'LOLO',
        'low_op_range':    'LOPR',
        'low_alarm':       'LOW',
        'last_rel_val':    'LRLV',
        'last_dial_drive': 'LRVL',
        'last_SPMG':       'LSPG',
        'low_severity':    'LSV',
        'last_drive':      'LVAL',
        'soft_limit':      'LVIO',
        'in_progress':     'MIP',
        'missed':          'MISS',
        'moving':          'MOVN',
        'resolution':      'MRES',
        'motor_status':    'MSTA',
        'offset':          'OFF',
        'output_mode':     'OMSL',
        'output':          'OUT',
        'prop_gain':       'PCOF',
        'precision':       'PREC',
        'readback':        'RBV',
        'retry_max':       'RTRY',
        'retry_count':     'RCNT',
        'retry_deadband':  'RDBD',
        'dial_difference': 'RDIF',
        'raw_encoder_pos': 'REP',
        'raw_high_limit':  'RHLS',
        'raw_low_limit':   'RLLS',
        'relative_value':  'RLV',
        'raw_motor_pos':   'RMP',
        'raw_readback':    'RRBV',
        'readback_res':    'RRES',
        'raw_drive':       'RVAL',
        'dial_speed':      'RVEL',
        's_speed':         'S',
        's_back_speed':    'SBAK',
        's_base_speed':    'SBAS',
        's_max_speed':     'SMAX',
        'set':             'SET',
        'stop_go':         'SPMG',
        's_revolutions':   'SREV',
        'stop':            'STOP',
        't_direction':     'TDIR',
        'tweak_forward':   'TWF',
        'tweak_reverse':   'TWR',
        'tweak_val':       'TWV',
        'use_encoder':     'UEIP',
        'u_revolutions':   'UREV',
        'use_rdbl':        'URIP',
        'drive':           'VAL',
        'base_speed':      'VBAS',
        'slew_speed':      'VELO',
        'version':         'VERS',
        'max_speed':       'VMAX',
        'use_home':        'ATHM',
        'deriv_gain':      'DCOF',
        'use_torque':      'CNEN',
        'device_type':     'DTYP',
        'record_type':     'RTYP',
        'status':          'STAT'}
        
    _init_list   = ('VAL', 'DESC', 'RTYP', 'RBV', 'PREC', 'TWV', 'FOFF')
    _nonpvs = ('_prefix', '_pvs', '_delim', '_init', '_init_list',
               '_alias', '_extras')
        
    def __init__(self, name=None, timeout=3.0):
        if name is None:
            raise MotorException("must supply motor name")

        if name.endswith('.VAL'):
            name = name[:-4]
        if name.endswith('.'):
            name = name[:-1]

        self._prefix = name
        device.Device.__init__(self, name, delim='.', 
                               attrs=self._init_list,
                               timeout=timeout)

         # make sure this is really a motor!
        rectype = self.get('RTYP')
        if rectype != 'motor':
            raise MotorException("%s is not an Epics Motor" % name)

        for key, val in self._extras.items():
            pvname = "%s%s" % (name, val)
            self.add_pv(pvname, attr=key)

        # self.put('disabled', 0)
        self._callbacks = {}

    def __repr__(self):
        return "<epics.Motor: %s: '%s'>" % (self._prefix,  self.DESC)

    def __str__(self):
        return self.__repr__()

    def __getattr__(self, attr):
        " internal method "
        if attr in self._alias:
            attr = self._alias[attr]
        if attr in self._pvs:
            return self.get(attr)
        if not attr.startswith('__'):
            try:
                self.PV(attr)
                return self.get(attr)
            except:
                raise MotorException("EpicsMotor has no attribute %s" % attr)
        else:
            return self._pvs[attr]
                
    def __setattr__(self, attr, val):
        # print 'SET ATTR ', attr, val
        if attr in ('name', '_prefix', '_pvs', '_delim', '_init',
                    '_alias', '_nonpvs', '_extra', '_callbacks'):
            self.__dict__[attr] = val
            return 
        if attr in self._alias:
            attr = self._alias[attr]
        if attr in self._pvs:
            return self.put(attr, val)
        elif attr in self.__dict__: 
            self.__dict__[attr] = val           
        elif self._init:
            try:
                self.PV(attr)
                return self.put(attr, val)
            except:
                raise MotorException("EpicsMotor has no attribute %s" % attr)

    def check_limits(self):
        """ check motor limits:
        returns None if no limits are violated
        raises expection if a limit is violated"""
        for field, msg in (('LVIO', 'Soft limit violation'),
                           ('HLS',  'High hard limit violation'),
                           ('LLS',  'Low  hard limit violation')):
            if self.get(field) != 0:
                raise MotorLimitException(msg)
        return
    
    def within_limits(self, val, dial=False):
        """ returns whether a value for a motor is within drive limits
        with dial=True   dial limits are used (default is user limits)"""
        ll_name, hl_name = 'LLM', 'HLM'
        if dial:
            ll_name, hl_name = 'DLLM', 'DHLM'
        return (val <= self.get(hl_name) and val >= self.get(ll_name))

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

        drv, rbv, lims = ('VAL', 'RBV', 'user')
        if dial:
            drv, rbv, lims = ('DVAL', 'DRBV', 'dial')
        if step or raw:
            drv, rbv, lims = ('RVAL', 'RRBV', None)

        if relative:
            val += self.get(rbv)

        # Check for limit violations
        if lims is not None and not ignore_limits:
            limits_ok = self.within_limits(val, lims)
            if not limits_ok:
                return -1
        stat = self.put(drv, val, wait=wait, timeout=timeout)
        ret = stat
        if stat == 1:
            ret = 0
        if stat == -2:
            ret = -1
        try:
            self.check_limits()
        except MotorLimitException:
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
        pos, rbv = ('VAL','RBV')
        if dial:
            pos, rbv = ('DVAL', 'DRBV')
        elif step or raw:
            pos, rbv = ('RVAL', 'RRBV')
        if readback:
            pos = rbv
        return self.get(pos)
        
    def tweak(self, direction='foreward', wait=False, timeout=300.0):
        """ move the motor by the tweak_val
       
        takes optional args:
         direction    direction of motion (forward/reverse)  [forward]
                         must start with 'rev' or 'back' for a reverse tweak.
         wait         wait for move to complete before returning (T/F) [F]
         timeout      max time for move to complete (in seconds) [300]
        """
        
        ifield = 'TWF'
        if direction.startswith('rev') or direction.startswith('back'):
            ifield = 'TWR'
            
        stat = self.put(ifield, 1, wait=wait, timeout=timeout)
        ret = stat
        if stat == 1:
            ret = 0
        if stat == -2:
            ret = -1
        try:
            self.check_limits()
        except MotorLimitException:
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
        self.put('SET', 1)

        # determine which drive value to use
        drv = 'VAL'
        if dial:
            drv = 'DVAL'
        elif step or raw:
            drv = 'RVAL'

        self.put(drv, position)
        
        # Put the motor back in "Use" mode
        self.put('SET', 0)
      
    def get_pv(self, attr):
        "return  PV for a field"
        return self.PV(attr)

    def clear_callback(self, attr='drive'):
        "clears callback for attribute"
        try:
            index = self._callbacks.get(attr, None)
            if index is not None:
                self.PV(attr).remove_callback(index=index)
        except:
            self.PV(attr).clear_callbacks()

    def set_callback(self, attr='VAL', callback=None, kws=None):
        "define a callback for an attribute"
        self.get(attr)
        kw_args = {}
        kw_args['motor_field'] = attr
        if kws is not None:
            kw_args.update(kws)

        index = self.PV(attr).add_callback(callback=callback, **kw_args)
        self._callbacks[attr] = index

    def refresh(self):
        """ refresh all motor parameters currently in use:
        make sure all used attributes are up-to-date."""
        ca.poll()

    def StopNow(self):
        "stop motor as soon as possible"
        save_val = self.get('SPMG')
        self.put('SPMG', 0)
        time.sleep(0.10)
        self.put('SPMG', save_val)
        
            
    def make_step_list(self, minstep=0.0, maxstep=None, decades=10):
        """ create a reasonable list of motor steps, as for a dropdown menu
        The list is based on motor range Mand precision"""

        if maxstep is None:
            maxstep = 0.6 * abs(self.HLM - self.LLM)
        steplist = []
        for i in range(decades):
            for step in [j* 10**(i - self.PREC) for j in (1, 2, 5)]:
                if (step <= maxstep and step > 0.98*minstep):
                    steplist.append(step)
        return steplist
        
    def get_info(self):
        "return information, current field values"
        out = {}
        for attr in ('DESC', 'VAL', 'RBV', 'PREC', 'VELO', 'STAT', 
                     'SET', 'TWV','LLM', 'HLM', 'SPMG'):
            out[attr] = self.get(attr, as_string=True)
        return out
    
    def show_info(self):
        " show basic motor settings "
        ca.poll()
        out = []
        out.append(repr(self))
        out.append( "--------------------------------------")
        for nam, val in self.get_info().items():
            if len(nam) < 16:
                nam = "%s%s" % (nam, ' '*(16-len(nam)))
            out.append("%s = %s" % (nam, val))
        out.append("--------------------------------------")
        ca.write("\n".join(out))

    def show_all(self):
        """ show all motor attributes"""
        out = []
        add = out.append
        add("# Motor %s" % (self._prefix))
        add("#  field               value                 PV name")
        add("#------------------------------------------------------------")
        ca.poll()
        klist = list( self._alias.keys())
        klist.sort()
        for attr in klist:
            suff = self._alias[attr]
            # pvn = self._alias[attr]
            label = attr  + ' '*(18-min(18, len(attr)))
            value = self.get(suff, as_string=True)
            pvname  = self.PV(suff).pvname
            if value is None:
                value = 'Not Connected??'
            value = value + ' '*(18-min(18, len(value)))
            # print " %s  %s  %s" % (label, value, pvname)
            add(" %s  %s  %s" % (label, value, pvname))
            
        ca.write("\n".join(out))

if (__name__ == '__main__'):
    for arg in sys.argv[1:]:
        m = Motor(arg)
        m.show_info()
