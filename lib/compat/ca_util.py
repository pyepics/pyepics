#!/usr/bin/env python

"""ca_util.py is a wrapper around pyepics that allows the caller to write,
e.g.,
    caget("xxx:m1")
instead of having to write
    m1 = CaChannel()
    m1.searchw("xxx:m1")
    m1.getw()
Also, ca_util defends against null PV names and some effects of short-term
CA disconnections, and it can verify that caput*() operations succeeded.

This is a port of Tim Mooney's wrapper around CaChannel to pyepics.
"""

# Port of Tim Mooney's wrapper around CaChannel to pyepics
# Tim Mooney 12/05/2008

code = '''
version = "3.0"

import epics
import time
import sys

# DBR types
# ca.DBR_STRING = 0
# ca.DBR_SHORT = 1 
# ca.DBR_INT = 1 
# ca.DBR_FLOAT = 2
# ca.DBR_ENUM = 3
# ca.DBR_CHAR = 4
# ca.DBR_LONG = 5
# ca.DBR_DOUBLE = 6

#######################################################################
# Human readable exception description
#	try:
#		x = x + 1
#	except:
#		print formatExceptionInfo()
import sys
import traceback
def formatExceptionInfo(maxTBlevel=5):
	cla, exc, trbk = sys.exc_info()
	excName = cla.__name__
	try:
		excArgs = exc.__dict__["args"]
	except KeyError:
		excArgs = "<no args>"
	excTb = traceback.format_tb(trbk, maxTBlevel)
	return (excName, excArgs, excTb)

#######################################################################
# channel-access connection states
ca_states = {}
# ...from cadef.h:
ca_states[ca.cs_never_conn] = "never connected"
ca_states[ca.cs_prev_conn] = "previously connected"
ca_states[ca.cs_conn] = "connected"
ca_states[ca.cs_closed] = "closed"
# ...from CaChannel.py (only with the patch from 04/29/04):
try:
	ca_states[ca.cs_never_search] = "never searched"
except AttributeError:
	file = getCaChannelFileName()
	using_old_CaChannel = 1
	print "ca_util: You're using an old version of CaChannel (%s)." % getCaChannelFileName()
	pass
	


#######################################################################
# default settings for ca_util
defaultTimeout = None		# 'None' means use CaChannel's timeout
defaultRetries = 3
readCheckTolerance = None	# 'None" means don't check

def set_ca_util_defaults(timeout=None, retries=None, read_check_tolerance=None):
	"""
	usage: old = set_ca_util_defaults(timeout=None, retries=None,
	             read_check_tolerance=None)
	alternate: set_ca_util_defaults(defaultsList), where defaultsList is like
	the list returned by get_ca_util_defaults()
	Setting an argument to the string "NONE" disables it.
	Returns the list of previous default values:
	    [defaultTimeout, defaultRetries, readCheckTolerance]
	"""
	global defaultTimeout, defaultRetries, readCheckTolerance
	old = [defaultTimeout, defaultRetries, readCheckTolerance]
	if type(timeout) == type([]):
		argList = timeout
		timeout = argList[0]
		retries = argList[1]
		read_check_tolerance = argList[2]
	if (timeout!=None) : defaultTimeout = timeout
	if (retries!=None) : defaultRetries = retries
	if (read_check_tolerance!=None) : readCheckTolerance = read_check_tolerance
	return old

def get_ca_util_defaults():
	"""
	usage: myList = get_ca_util_defaults()
	myList is set to [defaultTimeout, defaultRetries, readCheckTolerance]
	"""
	global defaultTimeout, defaultRetries, readCheckTolerance
	return [defaultTimeout, defaultRetries, readCheckTolerance]

def set_ca_util_default_timeout(timeout=None):
	"""
	usage: old = set_ca_util_default_timeout(timeout=None)
	If timeout == "NONE", then ca_util doesn't specify any timeout in
	calls to underlying software.
	Returns previous default timeout.
	"""
	global defaultTimeout
	old = defaultTimeout
	defaultTimeout = timeout
	return old

def get_ca_util_default_timeout():
	global defaultTimeout
	return defaultTimeout

def set_ca_util_default_retries(retries=None):
	"""
	usage: old = set_ca_util_default_retries(retries=None)
	If retries == "NONE", then ca_util doesn't do any retries.
	Returns previous default retries.
	"""
	global defaultRetries
	old = defaultRetries
	defaultRetries = retries
	return old

def get_ca_util_default_retries():
	global defaultRetries
	return defaultRetries

def set_ca_util_default_read_check_tolerance(read_check_tolerance=None):
	"""
	usage: old = set_ca_util_default_read_check_tolerance(read_check_tolerance=None)
	If read_check_tolerance == "NONE", then ca_util doesn't compare the value
	it reads to the value it wrote.
	Returns previous default tolerance.
	"""
	global readCheckTolerance
	old = readCheckTolerance
	readCheckTolerance = read_check_tolerance
	return old

def get_ca_util_default_read_check_tolerance():
	global readCheckTolerance
	return readCheckTolerance


#######################################################################
# The dictionary, cadict, will be used to associate PV names with the
# machinery required to talk to EPICS PV's.  If no entry is found (the
# name hasn't been used yet in a ca call), then we create a new instance
# of CaChannel, connect it to the PV, and put it in the dictionary.  We also
# include a flag some of the ca_util routines can use to check if a callback
# has occurred for this PV.

class cadictEntry:
	def __init__(self, channel):
		self.channel = channel
		self.callbackReceived = 0	# reserved for use by caputw()
		self.field_type = channel.field_type()
		self.element_count = channel.element_count()
		#self.host_name = channel.host_name()

cadict = {}

#######################################################################
ca_utilExceptionStrings = ["No name was provided.", "Readback disagrees with put value.",
                           "PV is not connected."]
EXCEPTION_NULL_NAME          = 0
EXCEPTION_READBACK_DISAGREES = 1
EXCEPTION_NOT_CONNECTED      = 2

class ca_utilException(Exception):
	def __init__(self, *args):
		Exception.__init__(self, *args)
		self.errorNumber = args[0]

	def __int__(self):
		return int(self.errorNumber)

	def __str__(self):
		return ca_utilExceptionStrings[self.errorNumber]


#######################################################################
def convertToType(type, value):
	if type == ca.DBR_STRING:
		return str(value)
	elif type == ca.DBR_SHORT or type == ca.DBR_INT or type == ca.DBR_LONG:
		try:
			n = int(value)
		except:
			n = 0
		return n
	elif type == ca.DBR_FLOAT or type == ca.DBR_DOUBLE:
		try:
			n = float(value)
		except:
			n = 0.0
		return n
	elif type == ca.DBR_ENUM:
		return value
	elif type == ca.DBR_CHAR:
		return value
	else:
		return value

#######################################################################
def checkName(name, timeout=None, retries=None):
	"""
	usage: checkName("xxx:m1.VAL", timeout=None, retries=None)
	Intended for internal use by ca_util functions.
	"""

	global cadict, defaultTimeout, defaultRetries
	if not name:
		raise ca_utilException, EXCEPTION_NULL_NAME
		return

	if ((timeout == None) and (defaultTimeout != None)): timeout = defaultTimeout
	if (timeout == "NONE"): timeout = None

	if ((retries == None) and (defaultRetries != None)): retries = defaultRetries
	if ((retries == None) or (retries == "NONE")): retries = 0

	tries = 0
	while (not cadict.has_key(name)) and (tries <= retries):
		# Make a new entry in the PV-name dictionary
		try:
			channel = CaChannel.CaChannel()
			if (timeout != None): channel.setTimeout(timeout)
			channel.searchw(name)
			cadict[name] = cadictEntry(channel)
		except CaChannel.CaChannelException, status:
			del channel
			tries += 1

	if (not cadict.has_key(name)):
		print "ca_util.checkName: Can't connect to '%s'" % name
		raise CaChannel.CaChannelException, status

#######################################################################
def castate(name=None, timeout=None, retries=None):
	"""usage: val = castate("xxx:m1.VAL", timeout=None, retries=None)
	   Try to read a PV, to find out whether it's really connected, and
	   whether caller is permitted to read and write it, without allowing
	   any exceptions to be thrown at the caller.
	"""

	global cadict, defaultTimeout, defaultRetries

	if not name: return "Null name has no state"

	# The only reliable way to check the *current* state of a PV is to attempt to use it.
	try:
		val = caget(name, timeout=timeout, retries=retries)
	except CaChannel.CaChannelException, status:
		pass

	try:
		checkName(name, timeout=timeout)
	except CaChannel.CaChannelException, status:
		return "not connected"
	except:
		return "error"

	try:
		state = cadict[name].channel.state()
	except CaChannel.CaChannelException, status:
		return "not connected"
	except:
		return "error"
	else:
		try:
			read_access = cadict[name].channel.read_access()
			write_access = cadict[name].channel.write_access()
			if ca_states.has_key(state):
				s = ca_states[state]
			else:
				s = "unknown state"
			if not read_access: s += ", noread"
			if not write_access: s += ", nowrite"
			return s
		except:
			return "error"

#######################################################################
def caget(name, timeout=None, retries=None, req_type=None, req_count=None):
	"""usage: val = caget("xxx:m1.VAL", timeout=None, retries=None,
	                req_type=None, req_count=None)"""

	global cadict, defaultTimeout, defaultRetries

	if not name:
		print "caget: no PV name supplied"
		raise ca_utilException, EXCEPTION_NULL_NAME
		return 0
	if ((timeout==None) and (defaultTimeout != None)): timeout = defaultTimeout
	if (timeout == "NONE"): timeout = None
	if ((retries==None) and (defaultRetries != None)): retries = defaultRetries
	if ((retries == None) or (retries == "NONE")): retries = 0
	retries = max(retries,0)
	retry = retries + 1
	success = 0

	# CaChannel sometimes chokes when it tries to process a channel that has been disconnected.
	# The simplest fix is to clear the channel and reconnect to the PV, which we can do cleanly
	# by deleting our dict entry for the channel, and calling checkName() to make a new entry.

	while ((not success) and (retry > 0)):
		checked = 0
		while ((not checked) and (retry > 0)):
			retry -= 1
			try:
				checkName(name, timeout=timeout)
			except CaChannel.CaChannelException, status:
				if retry <= 0:
					raise CaChannel.CaChannelException, status
					return 0
			else:
				checked = 1

		entry = cadict[name]
		if (timeout != None): entry.channel.setTimeout(timeout)
		if req_type == None:
			req_type=entry.field_type
		# kludge for broken DBR_CHAR
		if req_type == ca.DBR_CHAR:
			req_type = ca.DBR_INT
		if req_count == None:
			req_count = entry.element_count
		req_count = max(0, min(req_count, entry.element_count))
		try:
			if (using_old_CaChannel):
				val = entry.channel.getw(req_type=req_type)
			else:
				val = entry.channel.getw(req_type=req_type, count=req_count)
		except CaChannel.CaChannelException, status:
			#print "getw threw an exception (%s)" % status
			if ((int(status) == ca.ECA_BADTYPE) or (int(status) == ca.ECA_DISCONN)):
				# Delete dictionary entry.  This clears the CA connection.
				print "caget: Repairing CA connection to ", name
				del cadict[name]
				retry += 1
			if retry <= 0:
				raise CaChannel.CaChannelException, status
				return 0
		else:
			success = 1
	return val

def isNumber(s):
	try:
		n = int(s)
	except:
		return False
	return True

#######################################################################
def same(value, readback, native_readback, field_type, read_check_tolerance):
	"""For internal use by ca_util"""
	#print "ca_util.same(): field_type=%s" % field_type
	#print "ca_util.same(): value='%s'; readback='%s', native_readback='%s'" % (str(value), str(readback), str(native_readback))
	#print "ca_util.same(): type(value)=%s; type(readback)=%s, type(native_readback)=%s" % (type(value),
	#	type(readback), type(native_readback))

	if field_type in [ca.DBR_FLOAT, ca.DBR_DOUBLE]:
		return (abs(float(readback)-float(value)) < read_check_tolerance)
	elif field_type in [ca.DBR_INT, ca.DBR_SHORT, ca.DBR_LONG]:
		return (abs(int(readback)-int(value)) == 0)
	elif field_type == ca.DBR_ENUM:
		if str(value) == str(readback):
			return True
		if str(value) == str(native_readback):
			return True
		return False
	else:
		return (str(value) == str(readback))

#######################################################################
def caput(name, value, timeout=None, req_type=None, retries=None, read_check_tolerance=None):
	"""
	usage: caput("xxx:m1.VAL", new_value, timeout=None, req_type=None,
	       retries=None, read_check_tolerance=None)
	Put a value, and optionally check that the value arrived safely.
	If read_check_tolerance == None (or is not supplied) then the default
	read-check tolerance is used.  If read_check_tolerance == "NONE", then no
	read check is done.
	If read_check_tolerance != "NONE", then floating point numbers must be
	closer than the tolerance, and other types must agree exactly.
	Note that defaults for timeout, retries, and read_check_tolerance can be
	set for all ca_util functions, using the command set_ca_util_defaults().
	"""

	_caput("caput", name, value, 0, timeout, req_type, retries, read_check_tolerance)


#######################################################################
def __ca_util_waitCB(epics_args, user_args):
	"""Function for internal use by caputw()."""
	#print "__ca_util_waitCB: %s done\n" % user_args[0]
	cadict[user_args[0]].callbackReceived = 1

#######################################################################
def caputw(name, value, wait_timeout=None, timeout=None, req_type=None, retries=None,
 read_check_tolerance=None):
	"""
	usage: caputw("xxx:m1.VAL", new_value, wait_timeout=None, timeout=None,
	       req_type=None, retries=None, read_check_tolerance=None)
	Put a value, optionally check that the value arrived safely, and wait (no
	longer than wait_timeout) for processing to complete. If
	read_check_tolerance == None (or is not supplied) then the default
	read-check tolerance is used.  If read_check_tolerance == "NONE", then no
	read check is done. If read_check_tolerance != "NONE", then floating point
	numbers must be closer than the tolerance, and other types must agree
	exactly. Note that defaults for timeout, retries, and read_check_tolerance
	can be set for all ca_util functions, using the command
	set_ca_util_defaults().
	"""

	_caput("caputw", name, value, wait_timeout, timeout, req_type, retries, read_check_tolerance)


#######################################################################
def _caput(function, name, value, wait_timeout=None, timeout=None, req_type=None, retries=None, read_check_tolerance=None):

	global cadict, defaultTimeout, defaultRetries, readCheckTolerance

	#print function
	if not name:
		print "%s: no PV name supplied" % function
		raise ca_utilException, EXCEPTION_NULL_NAME
		return
	if ((timeout == None) and (defaultTimeout != None)): timeout = defaultTimeout
	if ((retries == None) and (defaultRetries != None)): retries = defaultRetries
	if ((retries == None) or (retries == "NONE")): retries = 0
	if ((read_check_tolerance == None) and (readCheckTolerance != None)):
		read_check_tolerance = readCheckTolerance

	retries = max(retries,0)
	retry = retries + 1
	success = 0

	checkName(name, timeout=timeout, retries=retries)

	while ((not success) and (retry > 0)):

		retry -= 1
		entry = cadict[name]

		state = castate(name, timeout)
		#print "%s: state='%s'" % (function, state)
		if (state != 'connected'):
			print "%s: Repairing CA connection to '%s'" % (function, name)
			del cadict[name]
			retry += 1
		else:
			if req_type == None:
				req_type=entry.field_type
			if ((timeout != None) and (timeout != "NONE")): entry.channel.setTimeout(timeout)
			entry.callbackReceived = 0 # in case we're doing caputw()
			#value = convertToType(value, req_type)
			try:
				if function == "caput":
					entry.channel.putw(value, req_type=req_type)
				else: #caputw
					retval = entry.channel.array_put_callback(value,req_type,entry.element_count,__ca_util_waitCB,name)
			except CaChannel.CaChannelException, status:
				print "put() threw an exception (%s)" % status
				if ((int(status) == ca.ECA_BADTYPE) or (int(status) == ca.ECA_DISCONN)):
					# Delete dictionary entry.  This clears the CA connection.
					print "%s: Repairing CA connection to '%s'" % (function, name)
					del cadict[name]
					retry += 1
				if retry <= 0:
					raise CaChannel.CaChannelException, status
					entry.callbackReceived = 1
					return
			else:
				if ((read_check_tolerance == None) or (read_check_tolerance == "NONE")):
					success = True
				else:
					if timeout:
						ca.pend_io(timeout)
					else:
						ca.pend_io(1.0)
					readback_success = False
					count = 0
					while ((not readback_success) and (count < retries+1)):
						try:
							readback = caget(name, req_type=req_type)
							native_readback = caget(name)
							readback_success = True
							if same(value, readback, native_readback, entry.field_type, read_check_tolerance):
								success = True
								#print "%s: Success\n" % (function)
							else:
								print "%s: readback '%s' disagrees with the value '%s' we wrote." % (function, readback, value)
								raise ca_utilException, EXCEPTION_READBACK_DISAGREES
								entry.callbackReceived = 1
						except CaChannel.CaChannelException, status:
							print "%s: exception during readback." % (function)
							count += 1

	if success and (function == "caputw"):
		start_time = time.time()
		timed_out = 0
		while (not entry.callbackReceived) and (not timed_out):
			#print "waiting for ", name
			time.sleep(0.1)
			#ca.pend_io(0.1)
			ca.poll()
			if (not wait_timeout):
				timed_out = 0
			else:
				timed_out = ((time.time()-start_time) > wait_timeout)

		if not entry.callbackReceived:
			print "Execution not completed by wait_timeout (%d seconds)" % wait_timeout

#######################################################################
def camonitor(name, function, user_args=None, timeout=None, retries=None):
	"""
	usage: camonitor("xxx:m1.VAL", python_function, user_args, timeout=None,
	       retries=None)
	Don't forget to call ca.pend_event(<pend_time_in_seconds>) periodically.
	"""

	global defaultTimeout, defaultRetries

	if not name:
		print "camonitor: no PV name supplied"
		raise ca_utilException, EXCEPTION_NULL_NAME
		return
	if not function:
		print "camonitor: no callback function supplied"
		raise ca_utilException, EXCEPTION_NULL_NAME
		return
	if not user_args: user_args = name
	if ((timeout==None) and (defaultTimeout != None)): timeout = defaultTimeout
	if ((retries==None) and (defaultRetries != None)): retries = defaultRetries
	if ((retries == None) or (retries == "NONE")): retries = 0

	retries = max(retries,0)
	retry = retries + 1
	success = 0

	while ((not success) and (retry > 0)):
		checked = 0
		while ((not checked) and (retry > 0)):
			retry -= 1
			try:
				checkName(name, timeout=timeout)
			except CaChannel.CaChannelException, status:
				if retry <= 0:
					raise CaChannel.CaChannelException, status
					return
			else:
				checked = 1

		entry = cadict[name]
		if ((timeout != None) and (timeout != "NONE")): entry.channel.setTimeout(timeout)
		try:
			entry.channel.add_masked_array_event(entry.field_type,entry.element_count,ca.DBE_VALUE, function, user_args)
		except CaChannel.CaChannelException, status:
			#print "add_masked_array_event threw an exception (%s)" % status
			if ((int(status) == ca.ECA_BADTYPE) or (int(status) == ca.ECA_DISCONN)):
				# Delete dictionary entry.  This clears the CA connection.
				print "camonitor: Repairing CA connection to ", name
				del cadict[name]
				retry += 1
			if retry <= 0:
				raise CaChannel.CaChannelException, status
				return 0
		else:
			success = 1

#######################################################################
def caunmonitor(name, timeout=None):
	"""usage: caunmonitor("xxx:m1.VAL", timeout=None)"""

	global defaultTimeout

	if not name:
		print "caunmonitor: no PV name supplied"
		raise ca_utilException, EXCEPTION_NULL_NAME
		return
	if ((timeout==None) and (defaultTimeout != None)): timeout = defaultTimeout

	if not cadict.has_key(name):
		print "ca_util has no connection to '%s'" % name
		raise ca_utilException, NOCONNECTION
		return

	channel = cadict[name].channel
	if ((timeout != None) and (timeout != "NONE")): channel.setTimeout(timeout)
	try:
		channel.clear_event()
	except CaChannel.CaChannelException, status:
		print "caunmonitor: CaChannel exception, status=%d (%s)" % (status, ca.message(status))
		return

#######################################################################
def test_monitor_function(epics_args, user_args):
	"""Example callback routine for use with camonitor()."""
	print 'test_monitor_function:'
	print "...epics_args: ", repr(epics_args)
	print "...user_args: ", repr(user_args)





#-------------------------------------------------------------------------------------------
# miscellaneous functions that might be useful, but haven't been integrated into the package

#######################################################################
def endianUs():
	"""
	usage: endianUs()
	Returns one of "Little Endian", "Big Endian", "Unknown Endian".
	"""

	from struct import pack
	if pack('<h', 1) == pack('=h',1):
		return "Little Endian"
	elif pack('>h', 1) == pack('=h',1):
		return "Big Endian"
	else:
		return "Unknown Endian"

#######################################################################
def printExceptionInfo(maxTBlevel=15):
	"""Intended for internal use by ca_util functions."""

	import sys, traceback
	cla, exc, trbk = sys.exc_info()
	excName = cla.__name__
	try:
		excArgs = exc.__dict__["args"]
	except KeyError:
		excArgs = "<no args>"
	excTb = traceback.format_tb(trbk, maxTBlevel)
	print "Unanticipated exception: %s %s\n" % (excName, excArgs)
	if (len(excTb) > 0):
		print "Traceback:"
		for trace in excTb:
			print trace,
	return
'''
