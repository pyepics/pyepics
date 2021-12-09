#
# list of local pv names to use for testing


#### 1
# this pv should be a DOUBLE.  It will NOT be set, but
# you should provide the host_name, units, and precision.  It
# is assumed to have count=1
double_pv = 'PyTest:ao1'
double_pv_units = 'microns'
double_pv_prec = 4

double_pv2 = 'PyTest:ao2'

pause_pv  = 'PyTest:pause'
#### 2
# this pv should be an ENUM. It will NOT be set.
# provide the names of the ENUM states

#### Theae are PVs of the various native types
###  They will NOT be set.
str_pv   = 'PyTest:ao1.DESC'
int_pv   = 'PyTest:long2'
long_pv  = 'PyTest:long2'
float_pv = 'PyTest:ao3'
enum_pv  = 'PyTest:mbbo1'
enum_pv_strs = ['Stop', 'Start', 'Pause', 'Resume']

proc_pv = 'PyTest:ao1.PROC'

## Here are some waveform / array data PVs
long_arr_pv   = 'PyTest:long2k'
double_arr_pv = 'PyTest:double2k'
string_arr_pv = 'PyTest:string128'
# char / byte array
char_arr_pv   = 'PyTest:char128'
char_arrays   = ['PyTest:char128', 'PyTest:char2k', 'PyTest:char64k']
long_arrays   = ['PyTest:long128', 'PyTest:long2k', 'PyTest:long64k']
double_arrays   = ['PyTest:double128', 'PyTest:double2k', 'PyTest:double64k']


####
# provide a single motor prefix (to which '.VAL' and '.RBV' etc will be added)

motor_list = ['sim:mtr%d' % i for i in range(1, 7)]
motor1 = motor_list[0]
motor2 = motor_list[1]

####
#  Here, provide a PV that changes at least once very 10 seconds
updating_pv1  = 'PyTest:ao1'
updating_str1 = 'PyTest:char256'

####
#  Here, provide a list of PVs that  change at least once very 10 seconds
updating_pvlist = ['PyTest:ao1', 'PyTest:ai1', 'PyTest:long1', 'PyTest:ao2']
#### alarm test

non_updating_pv = 'PyTest:ao4'

alarm_pv = 'PyTest:long1'
alarm_comp='ge'
alarm_trippoint = 7


#### subarray test
subarr_driver = 'PyTest:wave_test'
subarr1       = 'PyTest:subArr1'
subarr2       = 'PyTest:subArr2'
subarr3       = 'PyTest:subArr3'
subarr4       = 'PyTest:subArr4'
zero_len_subarr1 = 'PyTest:ZeroLenSubArr1'


#### clear cache tests
clear_cache_enabled = 'PyTestClearCache:enabled'
clear_cache_beacons = ['PyTestClearCache:{}'.format(i) for i in range(1, 10)]
