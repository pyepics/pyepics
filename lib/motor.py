#!/usr/bin/python
# This module provides support for the EPICS motor record.
# 
# Author:         Mark Rivers / Matt Newville
# Created:        Sept. 16, 2002
# Modifications:
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

import pv
import ca

import time
import exceptions

class MotorLimitException(exceptions.Exception):
    """ raised to indicate a motor limit has been reached """
    def __init__(self,msg,*args):
        self.msg = msg
    def __str__(self):
        return str(self.msg)

class MotorException(exceptions.Exception):
    """ raised to indicate a problem with a motor"""
    def __init__(self,msg,*args):
        self.msg = msg
    def __str__(self):
        return str(self.msg)

class Motor:
    """Epics Motor Class, using EpicsCA, and automatic callbacks

   This module provides a class library for the EPICS motor record.

   It uses the EpicsCA.PV class, and emulates 

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
      from EpicsCA import Motor
      m = Motor('13BMD:m38')
      m.move(10)               # Move to position 10 in user coordinates
      m.move(100, dial=True)   # Move to position 100 in dial coordinates
      m.move(1, raw=True, relative=True) # Move 1 step relative to current position

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

    __motor_params = {
        'acceleration':    ('ACCL', 'acceleration time'),
        'back_accel':      ('BACC', 'backlash acceleration time'),
        'backlash':        ('BDST', 'backlash distance'),
        'back_speed':      ('BVEL', 'backlash speed'),
        'card':            ('CARD', 'Card Number '),
        'dial_high_limit': ('DHLM', 'Dial High Limit '),
        'direction':       ('DIR',  'User Direction '),
        'dial_low_limit':  ('DLLM', 'Dial Low Limit '),
        'settle_time':     ('DLY',  'Readback settle time (s) '),
        'done_moving':     ('DMOV', 'Done moving to value'),
        'dial_readback':   ('DRBV', 'Dial Readback Value'),
        'description':     ('DESC', 'Description'),
        'dial_drive':      ('DVAL', 'Dial Desired Value'),
        'units':           ('EGU',  'Engineering Units '),
        'encoder_step':    ('ERES', 'Encoder Step Size '),
        'freeze_offset':   ('FOFF', 'Offset-Freeze Switch '),
        'move_fraction':   ('FRAC', 'Move Fraction'),
        'hi_severity':     ('HHSV', 'Hihi Severity '),
        'hi_alarm':        ('HIGH', 'High Alarm Limit '),
        'hihi_alarm':      ('HIHI', 'Hihi Alarm Limit '),
        'high_limit':      ('HLM',  'User High Limit  '),
        'high_limit_set':  ('HLS',  'High Limit Switch  '),
        'hw_limit':        ('HLSV', 'HW Lim. Violation Svr '),
        'home_forward':    ('HOMF', 'Home Forward  '),
        'home_reverse':    ('HOMR', 'Home Reverse  '),
        'high_op_range':   ('HOPR', 'High Operating Range'),
        'high_severity':   ('HSV',  'High Severity '),
        'integral_gain':   ('ICOF', 'Integral Gain '),
        'jog_accel':       ('JAR',  'Jog Acceleration (EGU/s^2) '),
        'jog_forward':     ('JOGF', 'Jog motor Forward '),
        'jog_reverse':     ('JOGR', 'Jog motor Reverse'),
        'jog_speed':       ('JVEL', 'Jog Velocity '),
        'last_dial_val':   ('LDVL', 'Last Dial Des Val '),
        'low_limit':       ('LLM',  'User Low Limit  '),
        'low_limit_set':   ('LLS',  'At Low Limit Switch'),
        'lo_severity':     ('LLSV', 'Lolo Severity  '),
        'lolo_alarm':      ('LOLO', 'Lolo Alarm Limit  '),
        'low_op_range':    ('LOPR', 'Low Operating Range '),
        'low_alarm':       ('LOW', ' Low Alarm Limit '),
        'last_rel_val':    ('LRLV', 'Last Rel Value  '),
        'last_dial_drive': ('LRVL', 'Last Raw Des Val  '),
        'last_SPMG':       ('LSPG', 'Last SPMG  '),
        'low_severity':    ('LSV',  'Low Severity  '),
        'last_drive':      ('LVAL', 'Last User Des Val'),
        'soft_limit':      ('LVIO', 'Limit violation  '),
        'in_progress':     ('MIP',  'Motion In Progress '),
        'missed':          ('MISS', 'Ran out of retries '),
        'moving':          ('MOVN', 'Motor is moving  '),
        'resolution':      ('MRES', 'Motor Step Size (EGU)'),
        'motor_status':    ('MSTA', 'Motor Status  '),
        'offset':          ('OFF',  'User Offset (EGU) '),
        'output_mode':     ('OMSL', 'Output Mode Select  '),
        'output':          ('OUT',  'Output Specification '),
        'prop_gain':       ('PCOF', 'Proportional Gain '),
        'precision':       ('PREC', 'Display Precision '),
        'readback':        ('RBV',  'User Readback Value '),
        'retry_max':       ('RTRY', 'Max retry count    '),
        'retry_count':     ('RCNT', 'Retry count  '),
        'retry_deadband':  ('RDBD', 'Retry Deadband (EGU)'),
        'dial_difference': ('RDIF', 'Difference rval-rrbv '),
        'raw_encoder_pos': ('REP',  'Raw Encoder Position '),
        'raw_high_limit':  ('RHLS', 'Raw High Limit Switch'),
        'raw_low_limit':   ('RLLS', 'Raw Low Limit Switch'),
        'relative_value':  ('RLV',  'Relative Value    '),
        'raw_motor_pos':   ('RMP',  'Raw Motor Position '),
        'raw_readback':    ('RRBV', 'Raw Readback Value '),
        'readback_res':    ('RRES', 'Readback Step Size (EGU)'),
        'raw_drive':       ('RVAL', 'Raw Desired Value  '),
        'dial_speed':      ('RVEL', 'Raw Velocity '),
        's_speed':         ('S',    'Speed (RPS)  '),
        's_back_speed':    ('SBAK', 'Backlash Speed (RPS)  '),
        's_base_speed':    ('SBAS', 'Base Speed (RPS)'),
        's_max_speed':     ('SMAX', 'Max Velocity (RPS)'),
        'set':             ('SET',  'Set/Use Switch '),
        'stop_go':         ('SPMG', 'Stop/Pause/Move/Go '),
        's_revolutions':   ('SREV', 'Steps per Revolution '),
        'stop':            ('STOP', 'Stop  '),
        't_direction':     ('TDIR', 'Direction of Travel '),
        'tweak_forward':   ('TWF',  'Tweak motor Forward '),
        'tweak_reverse':   ('TWR',  'Tweak motor Reverse '),
        'tweak_val':       ('TWV',  'Tweak Step Size (EGU) '),
        'use_encoder':     ('UEIP', 'Use Encoder If Present'),
        'u_revolutions':   ('UREV', 'EGU per Revolution  '),
        'use_rdbl':        ('URIP', 'Use RDBL Link If Present'),
        'drive':           ('VAL',  'User Desired Value'),
        'base_speed':      ('VBAS', 'Base Velocity (EGU/s)'),
        'slew_speed':      ('VELO', 'Velocity (EGU/s) '),
        'version':         ('VERS', 'Code Version '),
        'max_speed':       ('VMAX', 'Max Velocity (EGU/s)'),
        'use_home':        ('ATHM', 'uses the Home switch'),
        'deriv_gain':      ('DCOF', 'Derivative Gain '),
        'use_torque':      ('CNEN', 'Enable torque control '),
        'device_type':     ('DTYP', 'Device Type'),
        'record_type':     ('RTYP', 'Record Type'),
        'status':          ('STAT', 'Status')}
        
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
                   'high_limit_set', 'low_limit_set', 'soft_limit','status')

    
    _user_params = ('drive','readback','user')
    _dial_params = ('dial_drive','dial_readback','dial')
    _raw_params  = ('raw_drive','raw_readback','raw')

    def __init__(self, name=None,timeout=1.):
        self._dat = {}
        if (not name):  raise MotorException, "must supply motor name"             

        if name.endswith('.VAL'): name = name[:-4]
        self.pvname = name
        # make sure motor is enabled:
        try:
            p = pv.PV("%s.RTYP" % name)
            rectype = p.get()
            if rectype is None:  rectype = p.get() # try again for unconnected PVs
        except:
            rectype = None
            
        if rectype != 'motor':
            raise MotorException, "%s is not an Epics Motor" % name

        self._dat['enable'] = pv.PV("%s_able.VAL" % name)
        isEnabled = (0 == self._dat['enable'].get() )
        if not isEnabled: self._dat['enable'].put(0)        
        

        for attr in self.__init_list:   self.store_attr(attr)
        self.connect_all()
        
        self._dat['drive'].get()

    def connect_all(self):
        for p in self._dat.values():  p.get()

    def __repr__(self):
        return "<EpicsCA.Motor:  %s '%s'>" % (self.pvname, self.get_field('description'))

    def __str__(self):
        return self.__repr__()

    
    def __getattr__(self,attr):
        " internal method "
        if self.__motor_params.has_key(attr):
            return self.get_field(attr)
        elif self.__dict__.has_key(attr):
            return self.__dict__[attr]
        else:
            raise MotorException, "EpicsMotor has no attribute %s" % attr
     
    def __setattr__(self,attr,val):
        if self.__motor_params.has_key(attr):
            # print ' Epics Motor SetAttr: ', attr, val
            return self.put_field(attr,val)
        else:
            self.__dict__[attr] = val

    def has_attr(self,attr):  return self._dat.has_key(attr)
    
    def store_attr(self,attr):
        if not self._dat.has_key(attr) and self.__motor_params.has_key(attr):
            pvname = "%s.%s" % (self.pvname,self.__motor_params[attr][0])
            self._dat[attr] = pv.PV(pvname)
            self._dat[attr].connect()
        return self._dat.has_key(attr)
    

    def check_limits(self):
        """ check motor limits:
        returns None if no limits are violated
        raises expection if a limit is violated"""
        for field,msg in (('soft_limit',     'Soft limit violation'),
                          ('high_limit_set', 'High hard limit violation'),
                          ('low_limit_set',  'Low  hard limit violation')):
            if self.get_field(field)!= 0:
                raise MotorLimitException, msg
        return
    
    def within_limits(self,val,lims):
        """ returns whether a value for a motor is within drive limits,"""

        if lims == 'user':
            hlim = self.get_field('high_limit')
            llim = self.get_field('low_limit')
        elif lims == 'dial':
            hlim = self.get_field('dial_high_limit')
            llim = self.get_field('dial_low_limit')
        elif lims == 'raw':
            hlim = self.get_field('raw_high_limit')
            llim = self.get_field('raw_low_limit')

        return (val <= hlim and val >= llim)

    def move(self,val=None,relative=None,wait=False, timeout=3600.0,
             dial=False,step=False,raw=False, ignore_limits=False):

        """ moves motor drive to position

        arguments:
         value          value to move to (float) [Must be provided]
         relative       move relative to current position    (T/F) [F]
         wait           whether to wait for move to complete (T/F) [F]
         dial           use dial coordinates                 (T/F) [F]
         raw            use raw coordinates                  (T/F) [F]
         step           use raw coordinates (backward compat)(T/F) [F]
         ignore_limits  try move without regard to limits    (T/F) [F]
         timeout        max time for move to complete (in seconds) [3600]
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
        if dial:         drv,rbv,lims = self._dial_params
        if step or raw:  drv,rbv,lims = self._raw_params

        if (relative):  val = val + self.get_field(rbv)

        # Check for limit violations
        if not ignore_limits:
            limits_ok = self.within_limits(val,lims)
            if not limits_ok: return -1
            
        stat = self.put_field(drv,val,wait=wait,timeout=timeout)
        ret = stat
        if stat == 1:  ret = 0
        if stat == -2: ret = -1
        try:
            self.check_limits()
        except:
            ret = -1
        return ret

    def wait_for_put(self,field,timeout=3600.):
        """ wait for put on a field to complete:
  
           returns True  if put completed before timeout
           returns False if put timed out
           """
        t0  = time.time()
        pvn = self._dat[field]
        while not pvn.put_complete:
            ca.poll()
            time.sleep(0.001)
            if time.time()-t0 > timeout:  return False

        return True
    
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
        
    def tweak(self,dir='forward',wait=False,timeout=3600.0):
        """ move the motor by the tweak_val
       
        takes optional args:
         dir            direction of motion (forward/reverse)  [forward]
                           must start with 'rev' or 'back' for a reverse tweak.
         wait           wait for move to complete before returning (T/F) [F]
         timeout        max time for move to complete (in seconds) [3600]           
        """
        
        ifield = 'tweak_forward'
        if dir.startswith('rev') or dir.startswith('back'):
            ifield = 'tweak_reverse'
            
        stat = self.put_field(drv,val,wait=wait,timeout=timeout)
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
      
    def wait(self, **kw):
        "deprecated:  use move(val, wait=True)"
        raise MotorException, 'wait() deprecated: use move(val, wait=True)'

    def stop(self):
        "stop motor right now"
        self.put_field('stop',1)
        ca.poll()
        

    def get_pv(self,attr):
        "return full PV for a field"
        if (not self._dat.has_key('drive')): return None
        if not self.__motor_params.has_key(attr):
            return None
        else:
            return "%s.%s" % (self.pvname,self.__motor_params[attr][0])

    def put_field(self,attr,val,wait=False,timeout=300):
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
        if not self.store_attr(attr): return None
        return self._dat[attr].put(val,wait=wait,timeout=timeout)
    
    def get_field(self,attr,as_string=False):
        if not self.store_attr(attr): return None
        return self._dat[attr].get(as_string=as_string)

    def clear_field_callback(self,attr):
        try:
            self._dat[attr].remove_callback(index=attr)
        except:
            self._dat[attr].clear_callbacks()

    def set_field_callback(self,attr,callback,kw={}):
        if not self.store_attr(attr): return None
        kw_args = {}
        kw_args['field'] = attr
        kw_args['motor'] = self
        kw_args.update(kw)
        self._dat[attr].set_callback(callback=callback,index=attr,**kw_args)

    def refresh(self):
        """ refresh all motor parameters currently in use:
        make sure all used attributes are up-to-date."""
        for i in self._dat.keys():
            if self.__motor_params.has_key(i):
                self.get_field(i)

    def lookup_attribute(self,suffix):
        """
        Reverse look-up of an attribute name given the PV suffix
        """
        suf = suffix.lower()
        if ((suf.find('.') == 0) or (suf.find('_') == 0)): suf =  suf[1:]
        for (name,ext) in  self.__motor_params.items():
            if (suf == ext[0].lower()): return name
        return None


    def show_info(self):
        " show basic motor settings "
        self.refresh()
        print self
        print "--------------------------------------"
        for i in ('description', 'drive','readback', 'slew_speed',
                  'precision','tweak_val','low_limit', 'high_limit',
                  'stop_go', 'set', 'status'):
            j = i
            if (len(j) < 16): j = "%s%s" % (j,' '*(16-len(j)))
            print "%s = %s" % (j, self.get_field(i,as_string=1))
        print "--------------------------------------"

    def show_all(self):
        """ show all motor attributes"""
        print " Motor %s [%s]\n" % (self.pvname,self.get_field('description'))
        print "   field      PV Suffix     value            description"
        print " ------------------------------------------------------------"
        self.refresh()
        list = self.__motor_params.keys()
        list.sort()
        for attr in list:
            l = attr 
            if (len(attr)<15): l  = l + ' '*(15-len(l))
            suf = self.__motor_params[attr][0]
            pvn  = "%s.%s" % (self.pvname, suf)
            if (len(suf)<5): suf = suf  +' '*(5-len(suf))            
            val = self.get_field(attr,as_string=1)
            if (val):
                if (len(val)<12): val  = val + ' '*(12-len(val))
            print " %s  %s  %s  %s" % (l,suf,val,
                                       self.__motor_params[attr][1])


if (__name__ == '__main__'):
    import sys
    for i in sys.argv[1:]:
        x = EpicsMotor(i)
        x.show_info()
