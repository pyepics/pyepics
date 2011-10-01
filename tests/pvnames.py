#
# list of local pv names to use for testing


#### 1
# this pv should be a DOUBLE.  It will NOT be set, but
# you should provide the host_name, units, and precision.  It
# is assumed to have count=1
double_pv = 'Py:ao1'
double_pv_units = 'microns'
double_pv_prec = 4

double_pv2 = 'Py:ao2'

pause_pv  = 'Py:pause'
#### 2
# this pv should be an ENUM. It will NOT be set.
# provide the names of the ENUM states

#### Theae are PVs of the various native types
###  They will NOT be set.
str_pv   = 'Py:ao1.DESC'
int_pv   = 'Py:long2'
long_pv  = 'Py:long2'
float_pv = 'Py:ao3'
enum_pv  = 'Py:mbbo1'
enum_pv_strs = ['Stop', 'Start', 'Pause', 'Resume']

## Here are some waveform / array data PVs
long_arr_pv   = 'Py:long2k'
double_arr_pv = 'Py:double2k'
string_arr_pv = 'Py:string128'
# char / byte array
char_arr_pv   = 'Py:char128'
char_arrays   = ['Py:char128', 'Py:char2k', 'Py:char64k']
long_arrays   = ['Py:long128', 'Py:long2k', 'Py:long64k']
double_arrays   = ['Py:double128', 'Py:double2k', 'Py:double64k']


####
# provide a single motor prefix (to which '.VAL' and '.RBV' etc will be added)

motor1 = '13XRM:m1'
motor2 = '13XRM:m3'
motor_list = ['13XRM:m1', '13XRM:m2', '13XRM:m3', '13XRM:m4']
####
#  Here, provide a PV that changes at least once very 10 seconds
updating_pv1  = 'Py:ao1'
updating_str1 = 'Py:char256'

####
#  Here, provide a list of PVs that  change at least once very 10 seconds
updating_pvlist = ['Py:ao1', 'Py:ai1', 'Py:long1', 'Py:ao2']
#### alarm test

non_updating_pv = 'Py:ao4'

alarm_pv = 'Py:long1'
alarm_comp='ge'
alarm_trippoint = 7


#### subarray test
subarr_driver = 'Py:wave_test'
subarr1       = 'Py:subArr1'
subarr2       = 'Py:subArr2'
subarr3       = 'Py:subArr3'
subarr4       = 'Py:subArr4'
