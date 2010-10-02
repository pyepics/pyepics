#
# list of local pv names to use for testing


#### 1
# this pv should be a DOUBLE.  It will NOT be set, but
# you should provide the host_name, units, and precision.  It
# is assumed to have count=1
double_pv = '13IDC:m2.VAL'
double_pv_host = 'ioc13idc.cars.aps.anl.gov:5064'
double_pv_units = 'mm'
double_pv_prec = 4

#### 2
# this pv should be an ENUM. It will NOT be set.
# provide the names of the ENUM states

#### Theae are PVs of the various native types
###  They will NOT be set.
str_pv   = '13IDC:m2.DESC'
int_pv   = '13IDC:m2.STOP'
long_pv  = '13IDC:m2.RVAL'
float_pv = '13IDC:m2.VERS'
enum_pv  = '13IDC:m2.DIR'
enum_pv_strs = ['Neg','Pos']

## Here are some waveform / array data PVs

long_arr_pv   = '13IDC:str:mca1'

# char / byte array
char_arr_pv   = '13BMD:edb:dir'

double_arr_pv = '13IDC:scan1.P1PA'

####
# provide a single motor prefix (to which '.VAL' and '.RBV' etc will be added)

motor1 = '13IDC:m2'

#### 
#  Here, provide a PV that changes at least once very 10 seconds
updating_pv1 = '13IDA:DMM1Ch3_calc.VAL'

#### 
#  Here, provide a list of PVs that  change at least once very 10 seconds
updating_pvlist = ['13BMA:DMM1Ch2_calc.VAL',
                   '13BMA:DMM1Ch3_calc.VAL',
                   '13IDA:DMM1Ch2_calc.VAL',
                   '13IDA:DMM1Ch3_calc.VAL',
                   '13IDA:DMM2Ch9_raw.VAL',
                   '13IDD:DMM3Dmm_raw.VAL']
                   

other_pvlist = [ '13IDC:scan1.P1PA',
           '13IDC:AbortScans.PROC',
           '13BMD:edb:file',
           '13BMD:edb:ExecState',
           '13IDA:m2.VAL', '13IDA:m2.DESC',
           '13IDA:m2.FOFF', '13IDA:m2.SET', '13IDA:m2.SPMG' ]

string_pvlist = ['13BMA:m1.DESC',
                 '13BMA:m2.DESC',
                 '13BMA:m3.DESC',
                 '13BMA:m4.DESC',
                 '13IDC:m1.DESC',
                 '13IDC:m2.DESC',
                 '13IDC:m3.DESC',
                 '13IDC:m4.DESC']
                 

#### alarm test

alarm_pv = '13IDC:m13.VAL'
alarm_comp='le'
alarm_trippoint = 1.60


#### motor list (for connect.py)
#  Here, provide a list of Epics Motors
motor_list= [  "13IDC:m1", "13IDC:m2", "13IDC:m3", "13IDC:m4",
               "13IDC:m5", "13IDC:m6", "13IDC:m7", "13IDC:m8",
               "13IDC:m9", "13IDC:m10", "13IDC:m11", "13IDC:m12",
               "13IDC:m13", "13IDC:m14", "13IDC:m15", "13IDC:m16",
               "13IDC:m17", "13IDC:m18", "13IDC:m19", "13IDC:m20",
               "13IDC:m21", "13IDC:m22", "13IDC:m23", "13IDC:m24",
               "13IDC:m25", "13IDC:m26", "13IDC:m27", "13IDC:m28"]

