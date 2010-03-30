#
# list of local pv names to use for testing


#### 1
# this pv should be a DOUBLE.  It will NOT be set, but
# you should provide the host_name, units, and precision.  It
# is assumed to have count=1
double_pv = '13IDA:m1.VAL'
double_pv_host = 'ioc13ida.cars.aps.anl.gov:5064'
double_pv_units = 'mm'
double_pv_prec = 3

#### 2
# this pv should be an ENUM. It will NOT be set.
# provide the names of the ENUM states
enum_pv = '13IDA:m1.DIR'
enum_pv_strs = ['Neg','Pos']

#### 3
# this pv should be a STRING. It will NOT be set.
# provide its value
str_pv = '13IDA:m1.DESC'
str_pv_val = 'Hor. slit pos.'


#### 4
#  Here, provide a PV that changes at least once very 10 seconds
updating_pv1 = '13IDA:DMM1Ch3_calc.VAL'

#### 5
#  Here, provide a list of PVs that  change at least once very 10 seconds
updating_pvlist = ['13BMA:DMM1Ch2_calc.VAL',
                   '13BMA:DMM1Ch3_calc.VAL',
                   '13IDA:DMM1Ch2_calc.VAL',
                   '13IDA:DMM1Ch3_calc.VAL',
                   '13IDA:DMM2Ch9_raw.VAL',
                   '13IDD:DMM3Dmm_raw.VAL']
                   

other_pvlist = [ '13IDC:scan1.P1PA',
           '13IDC:AbortScans.PROC',
           '13XRM:edb:file',
           '13XRM:edb:ExecState',
           '13IDA:m2.VAL', '13IDA:m2.DESC',
           '13IDA:m2.FOFF', '13IDA:m2.SET', '13IDA:m2.SPMG' ]

