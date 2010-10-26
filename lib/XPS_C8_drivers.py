# XPS Python class
#
#  for XPS-C8 Firmware V2.5.x
#
#  See Programmer's manual for more information on XPS function calls
#
# Modified by Matt Newville: 01-Apr-2010
#    -  replaced tabs with 4 spaces
#    -  replaced very frequent occurences of
#          if (XPS.__usedSockets[socketId] == 0):   return
#       with "withValidSocket" decorator, whch raises an exception
#       if there is not a valid socket.
# ade many return values "consistent".

import socket

        
class XPSException(Exception):
    """XPS Controller Exception"""
    def __init__(self, msg,*args):
        self.msg = msg
    def __str__(self):
        return str(self.msg)

        

class XPS:
    # Defines
    MAX_NB_SOCKETS = 100

    # Global variables
    __sockets = {}
    __usedSockets = {}
    __nbSockets = 0

    # Initialization Function
    def __init__ (self):
        XPS.__nbSockets = 0
        for socketId in range(self.MAX_NB_SOCKETS):
            XPS.__usedSockets[socketId] = 0
            
    def withValidSocket(fcn):
        """ decorator to ensure that a valid socket is passed as the first argument
        before   calling decorated function"""
        def wrapper(*args,**kw):
            try:
                sid = args[1]
                if XPS.__usedSockets[sid] == 0:
                    raise XPSException('invalid socket at function %s' % fcn.__name__)
            except IndexError:
                raise XPSException('no socket specified for fucntion %s' % fcn.__name__)
            return fcn(*args,**kw)
        return wrapper

    # Send command and get return
    @withValidSocket
    def __sendAndReceive (self, socketId, command):
        try:
            XPS.__sockets[socketId].send(command)
            ret = XPS.__sockets[socketId].recv(1024)
            while (ret.find(',EndOfAPI') == -1):
                ret += XPS.__sockets[socketId].recv(1024)
        except socket.timeout:
            return [-2, '']
        except socket.error (errNb, errString):
            print 'Socket error : ' + errString
            return [-2, '']

        for i in range(len(ret)):
            if (ret[i] == ','):
                return [int(ret[0:i]), ret[i+1:-9]]

    def Send(self, socketId=None, cmd=None,check=False):
        # if socket left off, use the last one used / connected
        if socketId is None: socketId = self.socketId
        self.socketId = socketId        
        err,msg = self.__sendAndReceive(socketId, cmd)
        if err != 0 and check:
            raise XPSException(msg)
        return err,msg

    # TCP_ConnectToServer
    def TCP_ConnectToServer (self, IP, port, timeOut):
        socketId = 0
        if (XPS.__nbSockets < self.MAX_NB_SOCKETS):
            while (XPS.__usedSockets[socketId] == 1 and socketId < self.MAX_NB_SOCKETS):
                socketId += 1
                self.socketId = socketId
            if (socketId == self.MAX_NB_SOCKETS):
                return -1
        else:
            return -1

        XPS.__usedSockets[socketId] = 1
        XPS.__nbSockets += 1
        try:
            XPS.__sockets[socketId] = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            XPS.__sockets[socketId].connect((IP, port))
            XPS.__sockets[socketId].settimeout(timeOut)
            XPS.__sockets[socketId].setblocking(1)
        except socket.error:
            return -1
        return socketId

    # TCP_SetTimeout
    def TCP_SetTimeout (self, socketId, timeOut):
        if (XPS.__usedSockets[socketId] == 1):
            XPS.__sockets[socketId].settimeout(timeOut)

    # TCP_CloseSocket
    def TCP_CloseSocket (self, socketId):
        if (socketId >= 0 and socketId < self.MAX_NB_SOCKETS):
            try:
                XPS.__sockets[socketId].close()
                XPS.__usedSockets[socketId] = 0
                XPS.__nbSockets -= 1
            except socket.error:
                pass

    # GetLibraryVersion
    def GetLibraryVersion (self):
        return ['XPS-C8 Firmware V2.5.x']

    # ControllerStatusGet :  Read controller current status
    def ControllerStatusGet (self, socketId=None):
        error, returnedString = self.Send(socketId=socketId, cmd='ControllerStatusGet(int *)')
        if error != 0:
            raise XPSException(returnedString)

        i, j, retList = 0, 0, [error]
        while ((i+j) < len(returnedString) and returnedString[i+j] != ','):
            j += 1
        retList.append(eval(returnedString[i:i+j]))

        return retList

    # ControllerStatusStringGet :  Return the controller status string corresponding to the controller status code
    def ControllerStatusStringGet (self, socketId, ControllerStatusCode):
        command = 'ControllerStatusStringGet(' + str(ControllerStatusCode) + ',char *)'
        return self.Send(socketId, command)

    # ElapsedTimeGet :  Return elapsed time from controller power on
    def ElapsedTimeGet (self, socketId):
        command = 'ElapsedTimeGet(double *)'
        [error, returnedString] = self.Send(socketId, command)
        if (error != 0):
            return [error, returnedString]

        i, j, retList = 0, 0, [error]
        while ((i+j) < len(returnedString) and returnedString[i+j] != ','):
            j += 1
        retList.append(eval(returnedString[i:i+j]))

        return retList


    # ErrorStringGet :  Return the error string corresponding to the error code
    def ErrorStringGet (self, socketId, ErrorCode):
        return  self.Send(socketId,'ErrorStringGet(' + str(ErrorCode) + ',char *)')


    # FirmwareVersionGet :  Return firmware version
    def FirmwareVersionGet (self, socketId):
        return self.__sendAndReceive(socketId, 'FirmwareVersionGet(char *)')

    # TCLScriptExecute :  Execute a TCL script from a TCL file
    def TCLScriptExecute (self, socketId, TCLFileName, TaskName, ParametersList):
        cmd = 'TCLScriptExecute(' + TCLFileName + ',' + TaskName + ',' + ParametersList + ')'
        return self.__sendAndReceive(socketId, cmd)

    # TCLScriptExecuteAndWait :  Execute a TCL script from a TCL file and wait the end of execution to return
    @withValidSocket
    def TCLScriptExecuteAndWait (self, socketId, TCLFileName, TaskName, InputParametersList):
        command = 'TCLScriptExecuteAndWait(' + TCLFileName + ',' + TaskName + ',' + InputParametersList + ',char *)'
        [error, returnedString] = self.__sendAndReceive(socketId, command)
        return [error, returnedString]


    # TCLScriptExecuteWithPriority :  Execute a TCL script with defined priority
    @withValidSocket
    def TCLScriptExecuteWithPriority (self, socketId, TCLFileName, TaskName, TaskPriorityLevel, ParametersList):
        command = 'TCLScriptExecuteWithPriority(' + TCLFileName + ',' + TaskName + ',' + TaskPriorityLevel + ',' + ParametersList + ')'
        [error, returnedString] = self.__sendAndReceive(socketId, command)
        return [error, returnedString]


    # TCLScriptKill :  Kill TCL Task
    @withValidSocket
    def TCLScriptKill (self, socketId, TaskName):
        command = 'TCLScriptKill(' + TaskName + ')'
        [error, returnedString] = self.__sendAndReceive(socketId, command)
        return [error, returnedString]


    # TimerGet :  Get a timer
    @withValidSocket
    def TimerGet (self, socketId, TimerName):
        command = 'TimerGet(' + TimerName + ',int *)'
        [error, returnedString] = self.__sendAndReceive(socketId, command)
        if (error != 0):
            return [error, returnedString]

        i, j, retList = 0, 0, [error]
        while ((i+j) < len(returnedString) and returnedString[i+j] != ','):
            j += 1
        retList.append(eval(returnedString[i:i+j]))

        return retList

    # TimerSet :  Set a timer
    def TimerSet (self, socketId, TimerName, FrequencyTicks):
        return  self.Send(socketId, 'TimerSet(%s, %i)' % (TimerName, FrequencyTicks))

    # Reboot :  Reboot the controller
    def Reboot (self, socketId):
        return self.Send(socketId, 'Reboot()')

    # Login :  Log in
    def Login (self, socketId, Name, Password):
        return self.Send(socketId, 'Login(%s, %s)' %(Name,Password))

    def CloseAllOtherSockets (self, socketId):
        return  self.Send(socketId, 'CloseAllOtherSockets()')

    # HardwareDateAndTimeGet :  Return hardware date and time
    def HardwareDateAndTimeGet (self, socketId):
        return self.Send(socketId, 'HardwareDateAndTimeGet(char *)')

    # HardwareDateAndTimeSet :  Set hardware date and time
    def HardwareDateAndTimeSet (self, socketId, DateAndTime):
        return self.Send(socketId, 'HardwareDateAndTimeSet(%s)' % DateAndTime )

    # EventExtendedConfigurationTriggerSet :  Configure one or several events
    def EventExtendedConfigurationTriggerSet (self, socketId, ExtendedEventName, EventParameter1, EventParameter2, EventParameter3, EventParameter4):

        command = 'EventExtendedConfigurationTriggerSet('
        for i in range(len(ExtendedEventName)):
            if (i > 0):
                command += ','
            command += ExtendedEventName[i] + ',' + EventParameter1[i] + ',' + EventParameter2[i] + ',' + EventParameter3[i] + ',' + EventParameter4[i]
        command += ')'
        [error, returnedString] = self.__sendAndReceive(socketId, command)
        return [error, returnedString]

    # EventExtendedConfigurationTriggerGet :  Read the event configuration
    def EventExtendedConfigurationTriggerGet (self, socketId):
        return self.Send(socketId, 'EventExtendedConfigurationTriggerGet(char *)')

    # EventExtendedConfigurationActionSet :  Configure one or several actions
    def EventExtendedConfigurationActionSet (self, socketId, ExtendedActionName, ActionParameter1, ActionParameter2, ActionParameter3, ActionParameter4):
        command = 'EventExtendedConfigurationActionSet('
        for i in range(len(ExtendedActionName)):
            if (i > 0):
                command += ','
            command += ExtendedActionName[i] + ',' + ActionParameter1[i] + ',' + ActionParameter2[i] + ',' + ActionParameter3[i] + ',' + ActionParameter4[i]
        command += ')'

        [error, returnedString] = self.__sendAndReceive(socketId, command)
        return [error, returnedString]


    # EventExtendedConfigurationActionGet :  Read the action configuration
    def EventExtendedConfigurationActionGet (self, socketId):
        return self.Send(socketId,  'EventExtendedConfigurationActionGet(char *)')

    # EventExtendedStart :  Launch the last event and action configuration and return an ID
    def EventExtendedStart (self, socketId):

        command = 'EventExtendedStart(int *)'
        [error, returnedString] = self.__sendAndReceive(socketId, command)
        if (error != 0):
            return [error, returnedString]
        i, j, retList = 0, 0, [error]
        while ((i+j) < len(returnedString) and returnedString[i+j] != ','):
            j += 1
        retList.append(eval(returnedString[i:i+j]))

        return retList

    # EventExtendedAllGet :  Read all event and action configurations
    def EventExtendedAllGet (self, socketId):
        return self.Send(socketId, 'EventExtendedAllGet(char *)')

    # EventExtendedGet :  Read the event and action configuration defined by ID
    def EventExtendedGet (self, socketId, ID):
        return self.Send(socketId, 'EventExtendedGet(%i, char *,char *)' % ID)

    # EventExtendedRemove :  Remove the event and action configuration defined by ID
    def EventExtendedRemove (self, socketId, ID):
        return self.Send(socketId, 'EventExtendedRemove(%i)' % ID)

    # EventExtendedWait :  Wait events from the last event configuration
    def EventExtendedWait (self, socketId):
        return self.Send(socketId,  'EventExtendedWait()')

    # GatheringConfigurationGet : Read different mnemonique type
    def GatheringConfigurationGet (self, socketId):
        return self.Send(socketId,  'GatheringConfigurationGet(char *)')

    # GatheringConfigurationSet :  Configuration acquisition
    def GatheringConfigurationSet (self, socketId, outputs):
        command = 'GatheringConfigurationSet(%s)' % ','.join(outputs)
        return  self.__sendAndReceive(socketId, command)


    # GatheringCurrentNumberGet :  Maximum number of samples and current number during acquisition
    def GatheringCurrentNumberGet (self, socketId):

        command = 'GatheringCurrentNumberGet(int *,int *)'
        [error, returnedString] = self.__sendAndReceive(socketId, command)
        if (error != 0):
            return [error, returnedString]

        i, j, retList = 0, 0, [error]
        for paramNb in range(2):
            while ((i+j) < len(returnedString) and returnedString[i+j] != ','):
                j += 1
            retList.append(eval(returnedString[i:i+j]))
            i, j = i+j+1, 0

        return retList


    # GatheringStopAndSave :  Stop acquisition and save data
    def GatheringStopAndSave (self, socketId):
        return self.Send(socketId, 'GatheringStopAndSave()')

    # GatheringDataAcquire :  Acquire a configured data
    def GatheringDataAcquire (self, socketId):
        return self.Send(socketId,  'GatheringDataAcquire()')

    # GatheringDataGet :  Get a data line from gathering buffer
    def GatheringDataGet (self, socketId, IndexPoint):
        return self.Send(socketId,  'GatheringDataGet(%i,char *)' % IndexPoint)

    # GatheringDataMultipleLinesGet :  Get multiple data lines from gathering buffer
    def GatheringDataMultipleLinesGet (self, socketId, IndexPoint, NumberOfLines):
        return self.Send(socketId, 'GatheringDataMultipleLinesGet(%i, %i,char *)' % (IndexPoint, NumberOfLines))

    # GatheringReset :  Empty the gathered data in memory to start new gathering from scratch
    def GatheringReset (self, socketId):
        return self.Send(socketId,  'GatheringReset()')

    # GatheringRun :  Start a new gathering
    def GatheringRun (self, socketId, DataNumber, Divisor):

        command = 'GatheringRun(' + str(DataNumber) + ',' + str(Divisor) + ')'
        [error, returnedString] = self.__sendAndReceive(socketId, command)
        return [error, returnedString]


    # GatheringRunAppend :  Re-start the stopped gathering to add new data
    def GatheringRunAppend (self, socketId):
        return self.Send(socketId,  'GatheringRunAppend()')

    # GatheringStop :  Stop the data gathering (without saving to file)
    def GatheringStop (self, socketId):
        return self.Send(socketId,  'GatheringStop()')

    # GatheringExternalConfigurationSet :  Configuration acquisition
    def GatheringExternalConfigurationSet (self, socketId, Type):
        command = 'GatheringExternalConfigurationSet('
        for i in range(len(Type)):
            if (i > 0):
                command += ','
            command += Type[i]
        command += ')'

        [error, returnedString] = self.__sendAndReceive(socketId, command)
        return [error, returnedString]


    # GatheringExternalConfigurationGet :  Read different mnemonique type
    def GatheringExternalConfigurationGet (self, socketId):
        return self.Send(socketId,  'GatheringExternalConfigurationGet(char *)')

    # GatheringExternalCurrentNumberGet :  Maximum number of samples and current number during acquisition
    def GatheringExternalCurrentNumberGet (self, socketId):
        command = 'GatheringExternalCurrentNumberGet(int *,int *)'
        [error, returnedString] = self.__sendAndReceive(socketId, command)
        if (error != 0):
            return [error, returnedString]

        i, j, retList = 0, 0, [error]
        for paramNb in range(2):
            while ((i+j) < len(returnedString) and returnedString[i+j] != ','):
                j += 1
            retList.append(eval(returnedString[i:i+j]))
            i, j = i+j+1, 0

        return retList


    # GatheringExternalDataGet :  Get a data line from external gathering buffer
    def GatheringExternalDataGet (self, socketId, IndexPoint):

        command = 'GatheringExternalDataGet(' + str(IndexPoint) + ',char *)'
        [error, returnedString] = self.__sendAndReceive(socketId, command)
        return [error, returnedString]


    # GatheringExternalStopAndSave :  Stop acquisition and save data
    def GatheringExternalStopAndSave (self, socketId):
        return self.Send(socketId,  'GatheringExternalStopAndSave()')

    # GlobalArrayGet :  Get global array value
    def GlobalArrayGet (self, socketId, Number):
        return self.Send(socketId,  'GlobalArrayGet(%i,char *)' % Number)

    # GlobalArraySet :  Set global array value
    def GlobalArraySet (self, socketId, Number, ValueString):
        if (XPS.__usedSockets[socketId] == 0):
            return

        command = 'GlobalArraySet(' + str(Number) + ',' + ValueString + ')'
        [error, returnedString] = self.__sendAndReceive(socketId, command)
        return [error, returnedString]


    # DoubleGlobalArrayGet :  Get double global array value
    def DoubleGlobalArrayGet (self, socketId, Number):
        if (XPS.__usedSockets[socketId] == 0):
            return

        command = 'DoubleGlobalArrayGet(' + str(Number) + ',double *)'
        [error, returnedString] = self.__sendAndReceive(socketId, command)
        if (error != 0):
            return [error, returnedString]

        i, j, retList = 0, 0, [error]
        while ((i+j) < len(returnedString) and returnedString[i+j] != ','):
            j += 1
        retList.append(eval(returnedString[i:i+j]))

        return retList


    # DoubleGlobalArraySet :  Set double global array value
    def DoubleGlobalArraySet (self, socketId, Number, DoubleValue):
        if (XPS.__usedSockets[socketId] == 0):
            return

        command = 'DoubleGlobalArraySet(' + str(Number) + ',' + str(DoubleValue) + ')'
        [error, returnedString] = self.__sendAndReceive(socketId, command)
        return [error, returnedString]


    # GPIOAnalogGet :  Read analog input or analog output for one or few input
    def GPIOAnalogGet (self, socketId, GPIOName):
        if (XPS.__usedSockets[socketId] == 0):
            return

        command = 'GPIOAnalogGet('
        for i in range(len(GPIOName)):
            if (i > 0):
                command += ','
            command += GPIOName[i] + ',' + 'double *'
        command += ')'

        [error, returnedString] = self.__sendAndReceive(socketId, command)
        if (error != 0):
            return [error, returnedString]

        i, j, retList = 0, 0, [error]
        for paramNb in range(len(GPIOName)):
            while ((i+j) < len(returnedString) and returnedString[i+j] != ','):
                j += 1
            retList.append(eval(returnedString[i:i+j]))
            i, j = i+j+1, 0

        return retList


    # GPIOAnalogSet :  Set analog output for one or few output
    def GPIOAnalogSet (self, socketId, GPIOName, AnalogOutputValue):
        if (XPS.__usedSockets[socketId] == 0):
            return

        command = 'GPIOAnalogSet('
        for i in range(len(GPIOName)):
            if (i > 0):
                command += ','
            command += GPIOName[i] + ',' + str(AnalogOutputValue[i])
        command += ')'

        [error, returnedString] = self.__sendAndReceive(socketId, command)
        return [error, returnedString]


    # GPIOAnalogGainGet :  Read analog input gain (1, 2, 4 or 8) for one or few input
    def GPIOAnalogGainGet (self, socketId, GPIOName):
        if (XPS.__usedSockets[socketId] == 0):
            return

        command = 'GPIOAnalogGainGet('
        for i in range(len(GPIOName)):
            if (i > 0):
                command += ','
            command += GPIOName[i] + ',' + 'int *'
        command += ')'

        [error, returnedString] = self.__sendAndReceive(socketId, command)
        if (error != 0):
            return [error, returnedString]

        i, j, retList = 0, 0, [error]
        for paramNb in range(len(GPIOName)):
            while ((i+j) < len(returnedString) and returnedString[i+j] != ','):
                j += 1
            retList.append(eval(returnedString[i:i+j]))
            i, j = i+j+1, 0

        return retList


    # GPIOAnalogGainSet :  Set analog input gain (1, 2, 4 or 8) for one or few input
    def GPIOAnalogGainSet (self, socketId, GPIOName, AnalogInputGainValue):
        if (XPS.__usedSockets[socketId] == 0):
            return

        command = 'GPIOAnalogGainSet('
        for i in range(len(GPIOName)):
            if (i > 0):
                command += ','
            command += GPIOName[i] + ',' + str(AnalogInputGainValue[i])
        command += ')'

        [error, returnedString] = self.__sendAndReceive(socketId, command)
        return [error, returnedString]


    # GPIODigitalGet :  Read digital output or digital input 
    def GPIODigitalGet (self, socketId, GPIOName):
        if (XPS.__usedSockets[socketId] == 0):
            return

        command = 'GPIODigitalGet(' + GPIOName + ',unsigned short *)'
        [error, returnedString] = self.__sendAndReceive(socketId, command)
        if (error != 0):
            return [error, returnedString]

        i, j, retList = 0, 0, [error]
        while ((i+j) < len(returnedString) and returnedString[i+j] != ','):
            j += 1
        retList.append(eval(returnedString[i:i+j]))

        return retList


    # GPIODigitalSet :  Set Digital Output for one or few output TTL
    def GPIODigitalSet (self, socketId, GPIOName, Mask, DigitalOutputValue):
        if (XPS.__usedSockets[socketId] == 0):
            return

        command = 'GPIODigitalSet(' + GPIOName + ',' + str(Mask) + ',' + str(DigitalOutputValue) + ')'
        [error, returnedString] = self.__sendAndReceive(socketId, command)
        return [error, returnedString]


    # GroupAccelerationSetpointGet :  Return setpoint accelerations
    def GroupAccelerationSetpointGet (self, socketId, GroupName, nbElement):
        if (XPS.__usedSockets[socketId] == 0):
            return

        command = 'GroupAccelerationSetpointGet(' + GroupName + ','
        for i in range(nbElement):
            if (i > 0):
                command += ','
            command += 'double *'
        command += ')'

        [error, returnedString] = self.__sendAndReceive(socketId, command)
        if (error != 0):
            return [error, returnedString]

        i, j, retList = 0, 0, [error]
        for paramNb in range(nbElement):
            while ((i+j) < len(returnedString) and returnedString[i+j] != ','):
                j += 1
            retList.append(eval(returnedString[i:i+j]))
            i, j = i+j+1, 0

        return retList


    # GroupAnalogTrackingModeEnable :  Enable Analog Tracking mode on selected group
    def GroupAnalogTrackingModeEnable (self, socketId, GroupName, Type):
        if (XPS.__usedSockets[socketId] == 0):
            return

        command = 'GroupAnalogTrackingModeEnable(' + GroupName + ',' + Type + ')'
        [error, returnedString] = self.__sendAndReceive(socketId, command)
        return [error, returnedString]


    # GroupAnalogTrackingModeDisable :  Disable Analog Tracking mode on selected group
    def GroupAnalogTrackingModeDisable (self, socketId, GroupName):
        if (XPS.__usedSockets[socketId] == 0):
            return

        command = 'GroupAnalogTrackingModeDisable(' + GroupName + ')'
        [error, returnedString] = self.__sendAndReceive(socketId, command)
        return [error, returnedString]


    # GroupCorrectorOutputGet :  Return corrector outputs
    def GroupCorrectorOutputGet (self, socketId, GroupName, nbElement):
        if (XPS.__usedSockets[socketId] == 0):
            return

        command = 'GroupCorrectorOutputGet(' + GroupName + ','
        for i in range(nbElement):
            if (i > 0):
                command += ','
            command += 'double *'
        command += ')'

        [error, returnedString] = self.__sendAndReceive(socketId, command)
        if (error != 0):
            return [error, returnedString]

        i, j, retList = 0, 0, [error]
        for paramNb in range(nbElement):
            while ((i+j) < len(returnedString) and returnedString[i+j] != ','):
                j += 1
            retList.append(eval(returnedString[i:i+j]))
            i, j = i+j+1, 0

        return retList


    # GroupCurrentFollowingErrorGet :  Return current following errors
    def GroupCurrentFollowingErrorGet (self, socketId, GroupName, nbElement):
        if (XPS.__usedSockets[socketId] == 0):
            return

        command = 'GroupCurrentFollowingErrorGet(' + GroupName + ','
        for i in range(nbElement):
            if (i > 0):
                command += ','
            command += 'double *'
        command += ')'

        [error, returnedString] = self.__sendAndReceive(socketId, command)
        if (error != 0):
            return [error, returnedString]

        i, j, retList = 0, 0, [error]
        for paramNb in range(nbElement):
            while ((i+j) < len(returnedString) and returnedString[i+j] != ','):
                j += 1
            retList.append(eval(returnedString[i:i+j]))
            i, j = i+j+1, 0

        return retList


    # GroupHomeSearch :  Start home search sequence
    def GroupHomeSearch (self, socketId, GroupName):
        if (XPS.__usedSockets[socketId] == 0):
            return

        command = 'GroupHomeSearch(' + GroupName + ')'
        [error, returnedString] = self.__sendAndReceive(socketId, command)
        return [error, returnedString]


    # GroupHomeSearchAndRelativeMove :  Start home search sequence and execute a displacement
    def GroupHomeSearchAndRelativeMove (self, socketId, GroupName, TargetDisplacement):
        if (XPS.__usedSockets[socketId] == 0):
            return

        command = 'GroupHomeSearchAndRelativeMove(' + GroupName + ','
        for i in range(len(TargetDisplacement)):
            if (i > 0):
                command += ','
            command += str(TargetDisplacement[i])
        command += ')'

        [error, returnedString] = self.__sendAndReceive(socketId, command)
        return [error, returnedString]


   # GroupInitialize :  Start the initialization
    def GroupInitialize (self, socketId, GroupName):
        if (XPS.__usedSockets[socketId] == 0):
            return

        command = 'GroupInitialize(' + GroupName + ')'
        [error, returnedString] = self.__sendAndReceive(socketId, command)
        return [error, returnedString]


    # GroupInitializeWithEncoderCalibration :  Start the initialization with encoder calibration
    def GroupInitializeWithEncoderCalibration (self, socketId, GroupName):
        if (XPS.__usedSockets[socketId] == 0):
            return

        command = 'GroupInitializeWithEncoderCalibration(' + GroupName + ')'
        [error, returnedString] = self.__sendAndReceive(socketId, command)
        return [error, returnedString]


    # GroupJogParametersSet :  Modify Jog parameters on selected group and activate the continuous move
    def GroupJogParametersSet (self, socketId, GroupName, Velocity, Acceleration):
        if (XPS.__usedSockets[socketId] == 0):
            return

        command = 'GroupJogParametersSet(' + GroupName + ','
        for i in range(len(Velocity)):
            if (i > 0):
                command += ','
            command += str(Velocity[i]) + ',' + str(Acceleration[i])
        command += ')'

        [error, returnedString] = self.__sendAndReceive(socketId, command)
        return [error, returnedString]


    # GroupJogParametersGet :  Get Jog parameters on selected group
    def GroupJogParametersGet (self, socketId, GroupName, nbElement):
        if (XPS.__usedSockets[socketId] == 0):
            return

        command = 'GroupJogParametersGet(' + GroupName + ','
        for i in range(nbElement):
            if (i > 0):
                command += ','
            command += 'double *' + ',' + 'double *'
        command += ')'

        [error, returnedString] = self.__sendAndReceive(socketId, command)
        if (error != 0):
            return [error, returnedString]

        i, j, retList = 0, 0, [error]
        for paramNb in range(nbElement*2):
            while ((i+j) < len(returnedString) and returnedString[i+j] != ','):
                j += 1
            retList.append(eval(returnedString[i:i+j]))
            i, j = i+j+1, 0

        return retList


    # GroupJogCurrentGet :  Get Jog current on selected group
    def GroupJogCurrentGet (self, socketId, GroupName, nbElement):
        if (XPS.__usedSockets[socketId] == 0):
            return

        command = 'GroupJogCurrentGet(' + GroupName + ','
        for i in range(nbElement):
            if (i > 0):
                command += ','
            command += 'double *' + ',' + 'double *'
        command += ')'

        [error, returnedString] = self.__sendAndReceive(socketId, command)
        if (error != 0):
            return [error, returnedString]

        i, j, retList = 0, 0, [error]
        for paramNb in range(nbElement*2):
            while ((i+j) < len(returnedString) and returnedString[i+j] != ','):
                j += 1
            retList.append(eval(returnedString[i:i+j]))
            i, j = i+j+1, 0

        return retList


    # GroupJogModeEnable :  Enable Jog mode on selected group
    def GroupJogModeEnable (self, socketId, GroupName):
        if (XPS.__usedSockets[socketId] == 0):
            return

        command = 'GroupJogModeEnable(' + GroupName + ')'
        [error, returnedString] = self.__sendAndReceive(socketId, command)
        return [error, returnedString]


    # GroupJogModeDisable :  Disable Jog mode on selected group
    def GroupJogModeDisable (self, socketId, GroupName):
        if (XPS.__usedSockets[socketId] == 0):
            return

        command = 'GroupJogModeDisable(' + GroupName + ')'
        [error, returnedString] = self.__sendAndReceive(socketId, command)
        return [error, returnedString]


    # GroupKill :  Kill the group
    def GroupKill (self, socketId, GroupName):
        if (XPS.__usedSockets[socketId] == 0):
            return

        command = 'GroupKill(' + GroupName + ')'
        [error, returnedString] = self.__sendAndReceive(socketId, command)
        return [error, returnedString]


    # GroupMoveAbort :  Abort a move
    def GroupMoveAbort (self, socketId, GroupName):
        if (XPS.__usedSockets[socketId] == 0):
            return

        command = 'GroupMoveAbort(' + GroupName + ')'
        [error, returnedString] = self.__sendAndReceive(socketId, command)
        return [error, returnedString]


    # GroupMoveAbsolute :  Do an absolute move
    def GroupMoveAbsolute (self, socketId, GroupName, TargetPosition):
        if (XPS.__usedSockets[socketId] == 0):
            return

        command = 'GroupMoveAbsolute(' + GroupName + ','
        for i in range(len(TargetPosition)):
            if (i > 0):
                command += ','
            command += str(TargetPosition[i])
        command += ')'

        [error, returnedString] = self.__sendAndReceive(socketId, command)
        return [error, returnedString]


    # GroupMoveRelative :  Do a relative move
    def GroupMoveRelative (self, socketId, GroupName, TargetDisplacement):
        if (XPS.__usedSockets[socketId] == 0):
            return

        command = 'GroupMoveRelative(' + GroupName + ','
        for i in range(len(TargetDisplacement)):
            if (i > 0):
                command += ','
            command += str(TargetDisplacement[i])
        command += ')'

        [error, returnedString] = self.__sendAndReceive(socketId, command)
        return [error, returnedString]


    # GroupMotionDisable :  Set Motion disable on selected group
    def GroupMotionDisable (self, socketId, GroupName):
        if (XPS.__usedSockets[socketId] == 0):
            return

        command = 'GroupMotionDisable(' + GroupName + ')'
        [error, returnedString] = self.__sendAndReceive(socketId, command)
        return [error, returnedString]


    # GroupMotionEnable :  Set Motion enable on selected group
    def GroupMotionEnable (self, socketId, GroupName):
        if (XPS.__usedSockets[socketId] == 0):
            return

        command = 'GroupMotionEnable(' + GroupName + ')'
        [error, returnedString] = self.__sendAndReceive(socketId, command)
        return [error, returnedString]


    # GroupPositionCorrectedProfilerGet :  Return corrected profiler positions
    def GroupPositionCorrectedProfilerGet (self, socketId, GroupName, PositionX, PositionY):
        if (XPS.__usedSockets[socketId] == 0):
            return

        command = 'GroupPositionCorrectedProfilerGet(' + GroupName + ',' + str(PositionX) + ',' + str(PositionY) + ',double *,double *)'
        [error, returnedString] = self.__sendAndReceive(socketId, command)
        if (error != 0):
            return [error, returnedString]

        i, j, retList = 0, 0, [error]
        for paramNb in range(2):
            while ((i+j) < len(returnedString) and returnedString[i+j] != ','):
                j += 1
            retList.append(eval(returnedString[i:i+j]))
            i, j = i+j+1, 0

        return retList


    # GroupPositionCurrentGet :  Return current positions
    def GroupPositionCurrentGet (self, socketId, GroupName, nbElement):
        if (XPS.__usedSockets[socketId] == 0):
            return

        command = 'GroupPositionCurrentGet(' + GroupName + ','
        for i in range(nbElement):
            if (i > 0):
                command += ','
            command += 'double *'
        command += ')'

        [error, returnedString] = self.__sendAndReceive(socketId, command)
        if (error != 0):
            return [error, returnedString]

        i, j, retList = 0, 0, [error]
        for paramNb in range(nbElement):
            while ((i+j) < len(returnedString) and returnedString[i+j] != ','):
                j += 1
            retList.append(eval(returnedString[i:i+j]))
            i, j = i+j+1, 0

        return retList


    # GroupPositionPCORawEncoderGet :  Return PCO raw encoder positions
    def GroupPositionPCORawEncoderGet (self, socketId, GroupName, PositionX, PositionY):
        if (XPS.__usedSockets[socketId] == 0):
            return

        command = 'GroupPositionPCORawEncoderGet(' + GroupName + ',' + str(PositionX) + ',' + str(PositionY) + ',double *,double *)'
        [error, returnedString] = self.__sendAndReceive(socketId, command)
        if (error != 0):
            return [error, returnedString]

        i, j, retList = 0, 0, [error]
        for paramNb in range(2):
            while ((i+j) < len(returnedString) and returnedString[i+j] != ','):
                j += 1
            retList.append(eval(returnedString[i:i+j]))
            i, j = i+j+1, 0

        return retList


    # GroupPositionSetpointGet :  Return setpoint positions
    def GroupPositionSetpointGet (self, socketId, GroupName, nbElement):
        if (XPS.__usedSockets[socketId] == 0):
            return

        command = 'GroupPositionSetpointGet(' + GroupName + ','
        for i in range(nbElement):
            if (i > 0):
                command += ','
            command += 'double *'
        command += ')'

        [error, returnedString] = self.__sendAndReceive(socketId, command)
        if (error != 0):
            return [error, returnedString]

        i, j, retList = 0, 0, [error]
        for paramNb in range(nbElement):
            while ((i+j) < len(returnedString) and returnedString[i+j] != ','):
                j += 1
            retList.append(eval(returnedString[i:i+j]))
            i, j = i+j+1, 0

        return retList


    # GroupPositionTargetGet :  Return target positions
    def GroupPositionTargetGet (self, socketId, GroupName, nbElement):
        if (XPS.__usedSockets[socketId] == 0):
            return

        command = 'GroupPositionTargetGet(' + GroupName + ','
        for i in range(nbElement):
            if (i > 0):
                command += ','
            command += 'double *'
        command += ')'

        [error, returnedString] = self.__sendAndReceive(socketId, command)
        if (error != 0):
            return [error, returnedString]

        i, j, retList = 0, 0, [error]
        for paramNb in range(nbElement):
            while ((i+j) < len(returnedString) and returnedString[i+j] != ','):
                j += 1
            retList.append(eval(returnedString[i:i+j]))
            i, j = i+j+1, 0

        return retList


    # GroupReferencingActionExecute :  Execute an action in referencing mode
    def GroupReferencingActionExecute (self, socketId, PositionerName, ReferencingAction, ReferencingSensor, ReferencingParameter):
        if (XPS.__usedSockets[socketId] == 0):
            return

        command = 'GroupReferencingActionExecute(' + PositionerName + ',' + ReferencingAction + ',' + ReferencingSensor + ',' + str(ReferencingParameter) + ')'
        [error, returnedString] = self.__sendAndReceive(socketId, command)
        return [error, returnedString]


    # GroupReferencingStart :  Enter referencing mode
    def GroupReferencingStart (self, socketId, GroupName):
        if (XPS.__usedSockets[socketId] == 0):
            return

        command = 'GroupReferencingStart(' + GroupName + ')'
        [error, returnedString] = self.__sendAndReceive(socketId, command)
        return [error, returnedString]


    # GroupReferencingStop :  Exit referencing mode
    def GroupReferencingStop (self, socketId, GroupName):
        if (XPS.__usedSockets[socketId] == 0):
            return

        command = 'GroupReferencingStop(' + GroupName + ')'
        [error, returnedString] = self.__sendAndReceive(socketId, command)
        return [error, returnedString]


    # GroupStatusGet :  Return group status
    def GroupStatusGet (self, socketId, GroupName):
        if (XPS.__usedSockets[socketId] == 0):
            return

        command = 'GroupStatusGet(' + GroupName + ',int *)'
        [error, returnedString] = self.__sendAndReceive(socketId, command)
        if (error != 0):
            return [error, returnedString]

        i, j, retList = 0, 0, [error]
        while ((i+j) < len(returnedString) and returnedString[i+j] != ','):
            j += 1
        retList.append(eval(returnedString[i:i+j]))

        return retList


    # GroupStatusStringGet :  Return the group status string corresponding to the group status code
    def GroupStatusStringGet (self, socketId, GroupStatusCode):
        if (XPS.__usedSockets[socketId] == 0):
            return

        command = 'GroupStatusStringGet(' + str(GroupStatusCode) + ',char *)'
        [error, returnedString] = self.__sendAndReceive(socketId, command)
        return [error, returnedString]


    # GroupVelocityCurrentGet :  Return current velocities
    def GroupVelocityCurrentGet (self, socketId, GroupName, nbElement):
        if (XPS.__usedSockets[socketId] == 0):
            return

        command = 'GroupVelocityCurrentGet(' + GroupName + ','
        for i in range(nbElement):
            if (i > 0):
                command += ','
            command += 'double *'
        command += ')'

        [error, returnedString] = self.__sendAndReceive(socketId, command)
        if (error != 0):
            return [error, returnedString]

        i, j, retList = 0, 0, [error]
        for paramNb in range(nbElement):
            while ((i+j) < len(returnedString) and returnedString[i+j] != ','):
                j += 1
            retList.append(eval(returnedString[i:i+j]))
            i, j = i+j+1, 0

        return retList


    # KillAll :  Put all groups in 'Not initialized' state
    def KillAll (self, socketId):
        if (XPS.__usedSockets[socketId] == 0):
            return

        command = 'KillAll()'
        [error, returnedString] = self.__sendAndReceive(socketId, command)
        return [error, returnedString]


    # PositionerAnalogTrackingPositionParametersGet :  Read dynamic parameters for one axe of a group for a future analog tracking position
    def PositionerAnalogTrackingPositionParametersGet (self, socketId, PositionerName):
        if (XPS.__usedSockets[socketId] == 0):
            return

        command = 'PositionerAnalogTrackingPositionParametersGet(' + PositionerName + ',char *,double *,double *,double *,double *)'
        [error, returnedString] = self.__sendAndReceive(socketId, command)
        if (error != 0):
            return [error, returnedString]

        i, j, retList = 0, 0, [error]
        for paramNb in range(4):
            while ((i+j) < len(returnedString) and returnedString[i+j] != ','):
                j += 1
            retList.append(eval(returnedString[i:i+j]))
            i, j = i+j+1, 0

        return retList


    # PositionerAnalogTrackingPositionParametersSet :  Update dynamic parameters for one axe of a group for a future analog tracking position
    def PositionerAnalogTrackingPositionParametersSet (self, socketId, PositionerName, GPIOName, Offset, Scale, Velocity, Acceleration):
        if (XPS.__usedSockets[socketId] == 0):
            return

        command = 'PositionerAnalogTrackingPositionParametersSet(' + PositionerName + ',' + GPIOName + ',' + str(Offset) + ',' + str(Scale) + ',' + str(Velocity) + ',' + str(Acceleration) + ')'
        [error, returnedString] = self.__sendAndReceive(socketId, command)
        return [error, returnedString]


    # PositionerAnalogTrackingVelocityParametersGet :  Read dynamic parameters for one axe of a group for a future analog tracking velocity
    def PositionerAnalogTrackingVelocityParametersGet (self, socketId, PositionerName):
        if (XPS.__usedSockets[socketId] == 0):
            return

        command = 'PositionerAnalogTrackingVelocityParametersGet(' + PositionerName + ',char *,double *,double *,double *,int *,double *,double *)'
        [error, returnedString] = self.__sendAndReceive(socketId, command)
        if (error != 0):
            return [error, returnedString]

        i, j, retList = 0, 0, [error]
        for paramNb in range(6):
            while ((i+j) < len(returnedString) and returnedString[i+j] != ','):
                j += 1
            retList.append(eval(returnedString[i:i+j]))
            i, j = i+j+1, 0

        return retList


    # PositionerAnalogTrackingVelocityParametersSet :  Update dynamic parameters for one axe of a group for a future analog tracking velocity
    def PositionerAnalogTrackingVelocityParametersSet (self, socketId, PositionerName, GPIOName, Offset, Scale, DeadBandThreshold, Order, Velocity, Acceleration):
        if (XPS.__usedSockets[socketId] == 0):
            return

        command = 'PositionerAnalogTrackingVelocityParametersSet(' + PositionerName + ',' + GPIOName + ',' + str(Offset) + ',' + str(Scale) + ',' + str(DeadBandThreshold) + ',' + str(Order) + ',' + str(Velocity) + ',' + str(Acceleration) + ')'
        [error, returnedString] = self.__sendAndReceive(socketId, command)
        return [error, returnedString]


    # PositionerBacklashGet :  Read backlash value and status
    def PositionerBacklashGet (self, socketId, PositionerName):
        if (XPS.__usedSockets[socketId] == 0):
            return

        command = 'PositionerBacklashGet(' + PositionerName + ',double *,char *)'
        [error, returnedString] = self.__sendAndReceive(socketId, command)
        if (error != 0):
            return [error, returnedString]

        i, j, retList = 0, 0, [error]
        for paramNb in range(2):
            while ((i+j) < len(returnedString) and returnedString[i+j] != ','):
                j += 1
            retList.append(eval(returnedString[i:i+j]))
            i, j = i+j+1, 0

        return retList


    # PositionerBacklashSet :  Set backlash value
    def PositionerBacklashSet (self, socketId, PositionerName, BacklashValue):
        if (XPS.__usedSockets[socketId] == 0):
            return

        command = 'PositionerBacklashSet(' + PositionerName + ',' + str(BacklashValue) + ')'
        [error, returnedString] = self.__sendAndReceive(socketId, command)
        return [error, returnedString]


    # PositionerBacklashEnable :  Enable the backlash
    def PositionerBacklashEnable (self, socketId, PositionerName):
        if (XPS.__usedSockets[socketId] == 0):
            return

        command = 'PositionerBacklashEnable(' + PositionerName + ')'
        [error, returnedString] = self.__sendAndReceive(socketId, command)
        return [error, returnedString]


    # PositionerBacklashDisable :  Disable the backlash
    def PositionerBacklashDisable (self, socketId, PositionerName):
        if (XPS.__usedSockets[socketId] == 0):
            return

        command = 'PositionerBacklashDisable(' + PositionerName + ')'
        [error, returnedString] = self.__sendAndReceive(socketId, command)
        return [error, returnedString]


    # PositionerCorrectorNotchFiltersSet :  Update filters parameters 
    def PositionerCorrectorNotchFiltersSet (self, socketId, PositionerName, NotchFrequency1, NotchBandwith1, NotchGain1, NotchFrequency2, NotchBandwith2, NotchGain2):
        if (XPS.__usedSockets[socketId] == 0):
            return

        command = 'PositionerCorrectorNotchFiltersSet(' + PositionerName + ',' + str(NotchFrequency1) + ',' + str(NotchBandwith1) + ',' + str(NotchGain1) + ',' + str(NotchFrequency2) + ',' + str(NotchBandwith2) + ',' + str(NotchGain2) + ')'
        [error, returnedString] = self.__sendAndReceive(socketId, command)
        return [error, returnedString]


    # PositionerCorrectorNotchFiltersGet :  Read filters parameters 
    def PositionerCorrectorNotchFiltersGet (self, socketId, PositionerName):
        if (XPS.__usedSockets[socketId] == 0):
            return

        command = 'PositionerCorrectorNotchFiltersGet(' + PositionerName + ',double *,double *,double *,double *,double *,double *)'
        [error, returnedString] = self.__sendAndReceive(socketId, command)
        if (error != 0):
            return [error, returnedString]

        i, j, retList = 0, 0, [error]
        for paramNb in range(6):
            while ((i+j) < len(returnedString) and returnedString[i+j] != ','):
                j += 1
            retList.append(eval(returnedString[i:i+j]))
            i, j = i+j+1, 0

        return retList


    # PositionerCorrectorPIDFFAccelerationSet :  Update corrector parameters
    def PositionerCorrectorPIDFFAccelerationSet (self, socketId, PositionerName, ClosedLoopStatus, KP, KI, KD, KS, IntegrationTime, DerivativeFilterCutOffFrequency, GKP, GKI, GKD, KForm, FeedForwardGainAcceleration):
        if (XPS.__usedSockets[socketId] == 0):
            return

        command = 'PositionerCorrectorPIDFFAccelerationSet(' + PositionerName + ',' + str(ClosedLoopStatus) + ',' + str(KP) + ',' + str(KI) + ',' + str(KD) + ',' + str(KS) + ',' + str(IntegrationTime) + ',' + str(DerivativeFilterCutOffFrequency) + ',' + str(GKP) + ',' + str(GKI) + ',' + str(GKD) + ',' + str(KForm) + ',' + str(FeedForwardGainAcceleration) + ')'
        [error, returnedString] = self.__sendAndReceive(socketId, command)
        return [error, returnedString]


    # PositionerCorrectorPIDFFAccelerationGet :  Read corrector parameters
    def PositionerCorrectorPIDFFAccelerationGet (self, socketId, PositionerName):
        if (XPS.__usedSockets[socketId] == 0):
            return

        command = 'PositionerCorrectorPIDFFAccelerationGet(' + PositionerName + ',bool *,double *,double *,double *,double *,double *,double *,double *,double *,double *,double *,double *)'
        [error, returnedString] = self.__sendAndReceive(socketId, command)
        if (error != 0):
            return [error, returnedString]

        i, j, retList = 0, 0, [error]
        for paramNb in range(12):
            while ((i+j) < len(returnedString) and returnedString[i+j] != ','):
                j += 1
            retList.append(eval(returnedString[i:i+j]))
            i, j = i+j+1, 0

        return retList


    # PositionerCorrectorPIDFFVelocitySet :  Update corrector parameters
    def PositionerCorrectorPIDFFVelocitySet (self, socketId, PositionerName, ClosedLoopStatus, KP, KI, KD, KS, IntegrationTime, DerivativeFilterCutOffFrequency, GKP, GKI, GKD, KForm, FeedForwardGainVelocity):
        if (XPS.__usedSockets[socketId] == 0):
            return

        command = 'PositionerCorrectorPIDFFVelocitySet(' + PositionerName + ',' + str(ClosedLoopStatus) + ',' + str(KP) + ',' + str(KI) + ',' + str(KD) + ',' + str(KS) + ',' + str(IntegrationTime) + ',' + str(DerivativeFilterCutOffFrequency) + ',' + str(GKP) + ',' + str(GKI) + ',' + str(GKD) + ',' + str(KForm) + ',' + str(FeedForwardGainVelocity) + ')'
        [error, returnedString] = self.__sendAndReceive(socketId, command)
        return [error, returnedString]


    # PositionerCorrectorPIDFFVelocityGet :  Read corrector parameters
    def PositionerCorrectorPIDFFVelocityGet (self, socketId, PositionerName):
        if (XPS.__usedSockets[socketId] == 0):
            return

        command = 'PositionerCorrectorPIDFFVelocityGet(' + PositionerName + ',bool *,double *,double *,double *,double *,double *,double *,double *,double *,double *,double *,double *)'
        [error, returnedString] = self.__sendAndReceive(socketId, command)
        if (error != 0):
            return [error, returnedString]

        i, j, retList = 0, 0, [error]
        for paramNb in range(12):
            while ((i+j) < len(returnedString) and returnedString[i+j] != ','):
                j += 1
            retList.append(eval(returnedString[i:i+j]))
            i, j = i+j+1, 0

        return retList


    # PositionerCorrectorPIDDualFFVoltageSet :  Update corrector parameters
    def PositionerCorrectorPIDDualFFVoltageSet (self, socketId, PositionerName, ClosedLoopStatus, KP, KI, KD, KS, IntegrationTime, DerivativeFilterCutOffFrequency, GKP, GKI, GKD, KForm, FeedForwardGainVelocity, FeedForwardGainAcceleration, Friction):
        if (XPS.__usedSockets[socketId] == 0):
            return

        command = 'PositionerCorrectorPIDDualFFVoltageSet(' + PositionerName + ',' + str(ClosedLoopStatus) + ',' + str(KP) + ',' + str(KI) + ',' + str(KD) + ',' + str(KS) + ',' + str(IntegrationTime) + ',' + str(DerivativeFilterCutOffFrequency) + ',' + str(GKP) + ',' + str(GKI) + ',' + str(GKD) + ',' + str(KForm) + ',' + str(FeedForwardGainVelocity) + ',' + str(FeedForwardGainAcceleration) + ',' + str(Friction) + ')'
        [error, returnedString] = self.__sendAndReceive(socketId, command)
        return [error, returnedString]


    # PositionerCorrectorPIDDualFFVoltageGet :  Read corrector parameters
    def PositionerCorrectorPIDDualFFVoltageGet (self, socketId, PositionerName):
        if (XPS.__usedSockets[socketId] == 0):
            return

        command = 'PositionerCorrectorPIDDualFFVoltageGet(' + PositionerName + ',bool *,double *,double *,double *,double *,double *,double *,double *,double *,double *,double *,double *,double *,double *)'
        [error, returnedString] = self.__sendAndReceive(socketId, command)
        if (error != 0):
            return [error, returnedString]

        i, j, retList = 0, 0, [error]
        for paramNb in range(14):
            while ((i+j) < len(returnedString) and returnedString[i+j] != ','):
                j += 1
            retList.append(eval(returnedString[i:i+j]))
            i, j = i+j+1, 0

        return retList


    # PositionerCorrectorPIPositionSet :  Update corrector parameters
    def PositionerCorrectorPIPositionSet (self, socketId, PositionerName, ClosedLoopStatus, KP, KI, IntegrationTime):
        if (XPS.__usedSockets[socketId] == 0):
            return

        command = 'PositionerCorrectorPIPositionSet(' + PositionerName + ',' + str(ClosedLoopStatus) + ',' + str(KP) + ',' + str(KI) + ',' + str(IntegrationTime) + ')'
        [error, returnedString] = self.__sendAndReceive(socketId, command)
        return [error, returnedString]


    # PositionerCorrectorPIPositionGet :  Read corrector parameters
    def PositionerCorrectorPIPositionGet (self, socketId, PositionerName):
        if (XPS.__usedSockets[socketId] == 0):
            return

        command = 'PositionerCorrectorPIPositionGet(' + PositionerName + ',bool *,double *,double *,double *)'
        [error, returnedString] = self.__sendAndReceive(socketId, command)
        if (error != 0):
            return [error, returnedString]

        i, j, retList = 0, 0, [error]
        for paramNb in range(4):
            while ((i+j) < len(returnedString) and returnedString[i+j] != ','):
                j += 1
            retList.append(eval(returnedString[i:i+j]))
            i, j = i+j+1, 0

        return retList


    # PositionerCorrectorTypeGet :  Read corrector type
    def PositionerCorrectorTypeGet (self, socketId, PositionerName):
        if (XPS.__usedSockets[socketId] == 0):
            return

        command = 'PositionerCorrectorTypeGet(' + PositionerName + ',char *)'
        [error, returnedString] = self.__sendAndReceive(socketId, command)
        return [error, returnedString]


    # PositionerCurrentVelocityAccelerationFiltersSet :  Set current velocity and acceleration cut off frequencies
    def PositionerCurrentVelocityAccelerationFiltersSet (self, socketId, PositionerName, CurrentVelocityCutOffFrequency, CurrentAccelerationCutOffFrequency):
        if (XPS.__usedSockets[socketId] == 0):
            return

        command = 'PositionerCurrentVelocityAccelerationFiltersSet(' + PositionerName + ',' + str(CurrentVelocityCutOffFrequency) + ',' + str(CurrentAccelerationCutOffFrequency) + ')'
        [error, returnedString] = self.__sendAndReceive(socketId, command)
        return [error, returnedString]


    # PositionerCurrentVelocityAccelerationFiltersGet :  Get current velocity and acceleration cut off frequencies
    def PositionerCurrentVelocityAccelerationFiltersGet (self, socketId, PositionerName):
        if (XPS.__usedSockets[socketId] == 0):
            return

        command = 'PositionerCurrentVelocityAccelerationFiltersGet(' + PositionerName + ',double *,double *)'
        [error, returnedString] = self.__sendAndReceive(socketId, command)
        if (error != 0):
            return [error, returnedString]

        i, j, retList = 0, 0, [error]
        for paramNb in range(2):
            while ((i+j) < len(returnedString) and returnedString[i+j] != ','):
                j += 1
            retList.append(eval(returnedString[i:i+j]))
            i, j = i+j+1, 0

        return retList


    # PositionerDriverStatusGet :  Read positioner driver status
    def PositionerDriverStatusGet (self, socketId, PositionerName):
        if (XPS.__usedSockets[socketId] == 0):
            return

        command = 'PositionerDriverStatusGet(' + PositionerName + ',int *)'
        [error, returnedString] = self.__sendAndReceive(socketId, command)
        if (error != 0):
            return [error, returnedString]

        i, j, retList = 0, 0, [error]
        while ((i+j) < len(returnedString) and returnedString[i+j] != ','):
            j += 1
        retList.append(eval(returnedString[i:i+j]))

        return retList


    # PositionerDriverStatusStringGet :  Return the positioner driver status string corresponding to the positioner error code
    def PositionerDriverStatusStringGet (self, socketId, PositionerDriverStatus):
        if (XPS.__usedSockets[socketId] == 0):
            return

        command = 'PositionerDriverStatusStringGet(' + str(PositionerDriverStatus) + ',char *)'
        [error, returnedString] = self.__sendAndReceive(socketId, command)
        return [error, returnedString]


    # PositionerEncoderAmplitudeValuesGet :  Read analog interpolated encoder amplitude values
    def PositionerEncoderAmplitudeValuesGet (self, socketId, PositionerName):
        if (XPS.__usedSockets[socketId] == 0):
            return

        command = 'PositionerEncoderAmplitudeValuesGet(' + PositionerName + ',double *,double *,double *,double *)'
        [error, returnedString] = self.__sendAndReceive(socketId, command)
        if (error != 0):
            return [error, returnedString]

        i, j, retList = 0, 0, [error]
        for paramNb in range(4):
            while ((i+j) < len(returnedString) and returnedString[i+j] != ','):
                j += 1
            retList.append(eval(returnedString[i:i+j]))
            i, j = i+j+1, 0

        return retList


    # PositionerEncoderCalibrationParametersGet :  Read analog interpolated encoder calibration parameters
    def PositionerEncoderCalibrationParametersGet (self, socketId, PositionerName):
        if (XPS.__usedSockets[socketId] == 0):
            return

        command = 'PositionerEncoderCalibrationParametersGet(' + PositionerName + ',double *,double *,double *,double *)'
        [error, returnedString] = self.__sendAndReceive(socketId, command)
        if (error != 0):
            return [error, returnedString]

        i, j, retList = 0, 0, [error]
        for paramNb in range(4):
            while ((i+j) < len(returnedString) and returnedString[i+j] != ','):
                j += 1
            retList.append(eval(returnedString[i:i+j]))
            i, j = i+j+1, 0

        return retList


    # PositionerErrorGet :  Read and clear positioner error code
    def PositionerErrorGet (self, socketId, PositionerName):
        if (XPS.__usedSockets[socketId] == 0):
            return

        command = 'PositionerErrorGet(' + PositionerName + ',int *)'
        [error, returnedString] = self.__sendAndReceive(socketId, command)
        if (error != 0):
            return [error, returnedString]

        i, j, retList = 0, 0, [error]
        while ((i+j) < len(returnedString) and returnedString[i+j] != ','):
            j += 1
        retList.append(eval(returnedString[i:i+j]))

        return retList


    # PositionerErrorRead :  Read only positioner error code without clear it
    def PositionerErrorRead (self, socketId, PositionerName):
        if (XPS.__usedSockets[socketId] == 0):
            return

        command = 'PositionerErrorRead(' + PositionerName + ',int *)'
        [error, returnedString] = self.__sendAndReceive(socketId, command)
        if (error != 0):
            return [error, returnedString]

        i, j, retList = 0, 0, [error]
        while ((i+j) < len(returnedString) and returnedString[i+j] != ','):
            j += 1
        retList.append(eval(returnedString[i:i+j]))

        return retList


    # PositionerErrorStringGet :  Return the positioner status string corresponding to the positioner error code
    def PositionerErrorStringGet (self, socketId, PositionerErrorCode):
        if (XPS.__usedSockets[socketId] == 0):
            return

        command = 'PositionerErrorStringGet(' + str(PositionerErrorCode) + ',char *)'
        [error, returnedString] = self.__sendAndReceive(socketId, command)
        return [error, returnedString]


    # PositionerExcitationSignalGet :  Read disturbing signal parameters
    def PositionerExcitationSignalGet (self, socketId, PositionerName):
        if (XPS.__usedSockets[socketId] == 0):
            return

        command = 'PositionerExcitationSignalGet(' + PositionerName + ',int *,double *,double *,double *)'
        [error, returnedString] = self.__sendAndReceive(socketId, command)
        if (error != 0):
            return [error, returnedString]

        i, j, retList = 0, 0, [error]
        for paramNb in range(4):
            while ((i+j) < len(returnedString) and returnedString[i+j] != ','):
                j += 1
            retList.append(eval(returnedString[i:i+j]))
            i, j = i+j+1, 0

        return retList


    # PositionerExcitationSignalSet :  Update disturbing signal parameters
    def PositionerExcitationSignalSet (self, socketId, PositionerName, Mode, Frequency, Amplitude, Time):
        if (XPS.__usedSockets[socketId] == 0):
            return

        command = 'PositionerExcitationSignalSet(' + PositionerName + ',' + str(Mode) + ',' + str(Frequency) + ',' + str(Amplitude) + ',' + str(Time) + ')'
        [error, returnedString] = self.__sendAndReceive(socketId, command)
        return [error, returnedString]


    # PositionerHardwareStatusGet :  Read positioner hardware status
    def PositionerHardwareStatusGet (self, socketId, PositionerName):
        if (XPS.__usedSockets[socketId] == 0):
            return

        command = 'PositionerHardwareStatusGet(' + PositionerName + ',int *)'
        [error, returnedString] = self.__sendAndReceive(socketId, command)
        if (error != 0):
            return [error, returnedString]

        i, j, retList = 0, 0, [error]
        while ((i+j) < len(returnedString) and returnedString[i+j] != ','):
            j += 1
        retList.append(eval(returnedString[i:i+j]))

        return retList


    # PositionerHardwareStatusStringGet :  Return the positioner hardware status string corresponding to the positioner error code
    def PositionerHardwareStatusStringGet (self, socketId, PositionerHardwareStatus):
        if (XPS.__usedSockets[socketId] == 0):
            return

        command = 'PositionerHardwareStatusStringGet(' + str(PositionerHardwareStatus) + ',char *)'
        [error, returnedString] = self.__sendAndReceive(socketId, command)
        return [error, returnedString]


    # PositionerHardInterpolatorFactorGet :  Get hard interpolator parameters
    def PositionerHardInterpolatorFactorGet (self, socketId, PositionerName):
        if (XPS.__usedSockets[socketId] == 0):
            return

        command = 'PositionerHardInterpolatorFactorGet(' + PositionerName + ',int *)'
        [error, returnedString] = self.__sendAndReceive(socketId, command)
        if (error != 0):
            return [error, returnedString]

        i, j, retList = 0, 0, [error]
        while ((i+j) < len(returnedString) and returnedString[i+j] != ','):
            j += 1
        retList.append(eval(returnedString[i:i+j]))

        return retList


    # PositionerHardInterpolatorFactorSet :  Set hard interpolator parameters
    def PositionerHardInterpolatorFactorSet (self, socketId, PositionerName, InterpolationFactor):
        if (XPS.__usedSockets[socketId] == 0):
            return

        command = 'PositionerHardInterpolatorFactorSet(' + PositionerName + ',' + str(InterpolationFactor) + ')'
        [error, returnedString] = self.__sendAndReceive(socketId, command)
        return [error, returnedString]


    # PositionerMaximumVelocityAndAccelerationGet :  Return maximum velocity and acceleration of the positioner
    def PositionerMaximumVelocityAndAccelerationGet (self, socketId, PositionerName):
        if (XPS.__usedSockets[socketId] == 0):
            return

        command = 'PositionerMaximumVelocityAndAccelerationGet(' + PositionerName + ',double *,double *)'
        [error, returnedString] = self.__sendAndReceive(socketId, command)
        if (error != 0):
            return [error, returnedString]

        i, j, retList = 0, 0, [error]
        for paramNb in range(2):
            while ((i+j) < len(returnedString) and returnedString[i+j] != ','):
                j += 1
            retList.append(eval(returnedString[i:i+j]))
            i, j = i+j+1, 0

        return retList


    # PositionerMotionDoneGet :  Read motion done parameters
    def PositionerMotionDoneGet (self, socketId, PositionerName):
        if (XPS.__usedSockets[socketId] == 0):
            return

        command = 'PositionerMotionDoneGet(' + PositionerName + ',double *,double *,double *,double *,double *)'
        [error, returnedString] = self.__sendAndReceive(socketId, command)
        if (error != 0):
            return [error, returnedString]

        i, j, retList = 0, 0, [error]
        for paramNb in range(5):
            while ((i+j) < len(returnedString) and returnedString[i+j] != ','):
                j += 1
            retList.append(eval(returnedString[i:i+j]))
            i, j = i+j+1, 0

        return retList


    # PositionerMotionDoneSet :  Update motion done parameters
    def PositionerMotionDoneSet (self, socketId, PositionerName, PositionWindow, VelocityWindow, CheckingTime, MeanPeriod, TimeOut):
        if (XPS.__usedSockets[socketId] == 0):
            return

        command = 'PositionerMotionDoneSet(' + PositionerName + ',' + str(PositionWindow) + ',' + str(VelocityWindow) + ',' + str(CheckingTime) + ',' + str(MeanPeriod) + ',' + str(TimeOut) + ')'
        [error, returnedString] = self.__sendAndReceive(socketId, command)
        return [error, returnedString]


    # PositionerPositionCompareAquadBAlwaysEnable :  Enable AquadB signal in always mode
    def PositionerPositionCompareAquadBAlwaysEnable (self, socketId, PositionerName):
        if (XPS.__usedSockets[socketId] == 0):
            return

        command = 'PositionerPositionCompareAquadBAlwaysEnable(' + PositionerName + ')'
        [error, returnedString] = self.__sendAndReceive(socketId, command)
        return [error, returnedString]


    # PositionerPositionCompareAquadBWindowedGet :  Read position compare AquadB windowed parameters
    def PositionerPositionCompareAquadBWindowedGet (self, socketId, PositionerName):
        if (XPS.__usedSockets[socketId] == 0):
            return

        command = 'PositionerPositionCompareAquadBWindowedGet(' + PositionerName + ',double *,double *,bool *)'
        [error, returnedString] = self.__sendAndReceive(socketId, command)
        if (error != 0):
            return [error, returnedString]

        i, j, retList = 0, 0, [error]
        for paramNb in range(3):
            while ((i+j) < len(returnedString) and returnedString[i+j] != ','):
                j += 1
            retList.append(eval(returnedString[i:i+j]))
            i, j = i+j+1, 0

        return retList


    # PositionerPositionCompareAquadBWindowedSet :  Set position compare AquadB windowed parameters
    def PositionerPositionCompareAquadBWindowedSet (self, socketId, PositionerName, MinimumPosition, MaximumPosition):
        if (XPS.__usedSockets[socketId] == 0):
            return

        command = 'PositionerPositionCompareAquadBWindowedSet(' + PositionerName + ',' + str(MinimumPosition) + ',' + str(MaximumPosition) + ')'
        [error, returnedString] = self.__sendAndReceive(socketId, command)
        return [error, returnedString]


    # PositionerPositionCompareGet :  Read position compare parameters
    def PositionerPositionCompareGet (self, socketId, PositionerName):
        if (XPS.__usedSockets[socketId] == 0):
            return

        command = 'PositionerPositionCompareGet(' + PositionerName + ',double *,double *,double *,bool *)'
        [error, returnedString] = self.__sendAndReceive(socketId, command)
        if (error != 0):
            return [error, returnedString]

        i, j, retList = 0, 0, [error]
        for paramNb in range(4):
            while ((i+j) < len(returnedString) and returnedString[i+j] != ','):
                j += 1
            retList.append(eval(returnedString[i:i+j]))
            i, j = i+j+1, 0

        return retList


    # PositionerPositionCompareSet :  Set position compare parameters
    def PositionerPositionCompareSet (self, socketId, PositionerName, MinimumPosition, MaximumPosition, PositionStep):
        if (XPS.__usedSockets[socketId] == 0):
            return

        command = 'PositionerPositionCompareSet(' + PositionerName + ',' + str(MinimumPosition) + ',' + str(MaximumPosition) + ',' + str(PositionStep) + ')'
        [error, returnedString] = self.__sendAndReceive(socketId, command)
        return [error, returnedString]


    # PositionerPositionCompareEnable :  Enable position compare
    def PositionerPositionCompareEnable (self, socketId, PositionerName):
        if (XPS.__usedSockets[socketId] == 0):
            return

        command = 'PositionerPositionCompareEnable(' + PositionerName + ')'
        [error, returnedString] = self.__sendAndReceive(socketId, command)
        return [error, returnedString]


    # PositionerPositionCompareDisable :  Disable position compare
    def PositionerPositionCompareDisable (self, socketId, PositionerName):
        if (XPS.__usedSockets[socketId] == 0):
            return

        command = 'PositionerPositionCompareDisable(' + PositionerName + ')'
        [error, returnedString] = self.__sendAndReceive(socketId, command)
        return [error, returnedString]


    # PositionerPositionComparePulseParametersGet :  Get position compare PCO pulse parameters
    def PositionerPositionComparePulseParametersGet (self, socketId, PositionerName):
        if (XPS.__usedSockets[socketId] == 0):
            return

        command = 'PositionerPositionComparePulseParametersGet(' + PositionerName + ',double *,double *)'
        [error, returnedString] = self.__sendAndReceive(socketId, command)
        if (error != 0):
            return [error, returnedString]

        i, j, retList = 0, 0, [error]
        for paramNb in range(2):
            while ((i+j) < len(returnedString) and returnedString[i+j] != ','):
                j += 1
            retList.append(eval(returnedString[i:i+j]))
            i, j = i+j+1, 0

        return retList


    # PositionerPositionComparePulseParametersSet :  Set position compare PCO pulse parameters
    def PositionerPositionComparePulseParametersSet (self, socketId, PositionerName, PCOPulseWidth, EncoderSettlingTime):
        if (XPS.__usedSockets[socketId] == 0):
            return

        command = 'PositionerPositionComparePulseParametersSet(' + PositionerName + ',' + str(PCOPulseWidth) + ',' + str(EncoderSettlingTime) + ')'
        [error, returnedString] = self.__sendAndReceive(socketId, command)
        return [error, returnedString]


    # PositionerRawEncoderPositionGet :  Get the raw encoder position
    def PositionerRawEncoderPositionGet (self, socketId, PositionerName, UserEncoderPosition):
        if (XPS.__usedSockets[socketId] == 0):
            return

        command = 'PositionerRawEncoderPositionGet(' + PositionerName + ',' + str(UserEncoderPosition) + ',double *)'
        [error, returnedString] = self.__sendAndReceive(socketId, command)
        if (error != 0):
            return [error, returnedString]

        i, j, retList = 0, 0, [error]
        while ((i+j) < len(returnedString) and returnedString[i+j] != ','):
            j += 1
        retList.append(eval(returnedString[i:i+j]))

        return retList


    # PositionersEncoderIndexDifferenceGet :  Return the difference between index of primary axis and secondary axis (only after homesearch)
    def PositionersEncoderIndexDifferenceGet (self, socketId, PositionerName):
        if (XPS.__usedSockets[socketId] == 0):
            return

        command = 'PositionersEncoderIndexDifferenceGet(' + PositionerName + ',double *)'
        [error, returnedString] = self.__sendAndReceive(socketId, command)
        if (error != 0):
            return [error, returnedString]

        i, j, retList = 0, 0, [error]
        while ((i+j) < len(returnedString) and returnedString[i+j] != ','):
            j += 1
        retList.append(eval(returnedString[i:i+j]))

        return retList


    # PositionerSGammaExactVelocityAjustedDisplacementGet :  Return adjusted displacement to get exact velocity
    def PositionerSGammaExactVelocityAjustedDisplacementGet (self, socketId, PositionerName, DesiredDisplacement):
        if (XPS.__usedSockets[socketId] == 0):
            return

        command = 'PositionerSGammaExactVelocityAjustedDisplacementGet(' + PositionerName + ',' + str(DesiredDisplacement) + ',double *)'
        [error, returnedString] = self.__sendAndReceive(socketId, command)
        if (error != 0):
            return [error, returnedString]

        i, j, retList = 0, 0, [error]
        while ((i+j) < len(returnedString) and returnedString[i+j] != ','):
            j += 1
        retList.append(eval(returnedString[i:i+j]))

        return retList


    # PositionerSGammaParametersGet :  Read dynamic parameters for one axe of a group for a future displacement 
    def PositionerSGammaParametersGet (self, socketId, PositionerName):
        if (XPS.__usedSockets[socketId] == 0):
            return

        command = 'PositionerSGammaParametersGet(' + PositionerName + ',double *,double *,double *,double *)'
        [error, returnedString] = self.__sendAndReceive(socketId, command)
        if (error != 0):
            return [error, returnedString]

        i, j, retList = 0, 0, [error]
        for paramNb in range(4):
            while ((i+j) < len(returnedString) and returnedString[i+j] != ','):
                j += 1
            retList.append(eval(returnedString[i:i+j]))
            i, j = i+j+1, 0

        return retList


    # PositionerSGammaParametersSet :  Update dynamic parameters for one axe of a group for a future displacement
    def PositionerSGammaParametersSet (self, socketId, PositionerName, Velocity, Acceleration, MinimumTjerkTime, MaximumTjerkTime):
        if (XPS.__usedSockets[socketId] == 0):
            return

        command = 'PositionerSGammaParametersSet(' + PositionerName + ',' + str(Velocity) + ',' + str(Acceleration) + ',' + str(MinimumTjerkTime) + ',' + str(MaximumTjerkTime) + ')'
        [error, returnedString] = self.__sendAndReceive(socketId, command)
        return [error, returnedString]


    # PositionerSGammaPreviousMotionTimesGet :  Read SettingTime and SettlingTime
    def PositionerSGammaPreviousMotionTimesGet (self, socketId, PositionerName):
        if (XPS.__usedSockets[socketId] == 0):
            return

        command = 'PositionerSGammaPreviousMotionTimesGet(' + PositionerName + ',double *,double *)'
        [error, returnedString] = self.__sendAndReceive(socketId, command)
        if (error != 0):
            return [error, returnedString]

        i, j, retList = 0, 0, [error]
        for paramNb in range(2):
            while ((i+j) < len(returnedString) and returnedString[i+j] != ','):
                j += 1
            retList.append(eval(returnedString[i:i+j]))
            i, j = i+j+1, 0

        return retList


    # PositionerStageParameterGet :  Return the stage parameter
    def PositionerStageParameterGet (self, socketId, PositionerName, ParameterName):
        if (XPS.__usedSockets[socketId] == 0):
            return

        command = 'PositionerStageParameterGet(' + PositionerName + ',' + ParameterName + ',char *)'
        [error, returnedString] = self.__sendAndReceive(socketId, command)
        return [error, returnedString]


    # PositionerStageParameterSet :  Save the stage parameter
    def PositionerStageParameterSet (self, socketId, PositionerName, ParameterName, ParameterValue):
        if (XPS.__usedSockets[socketId] == 0):
            return

        command = 'PositionerStageParameterSet(' + PositionerName + ',' + ParameterName + ',' + ParameterValue + ')'
        [error, returnedString] = self.__sendAndReceive(socketId, command)
        return [error, returnedString]


    # PositionerTimeFlasherGet :  Read time flasher parameters
    def PositionerTimeFlasherGet (self, socketId, PositionerName):
        if (XPS.__usedSockets[socketId] == 0):
            return

        command = 'PositionerTimeFlasherGet(' + PositionerName + ',double *,double *,double *,bool *)'
        [error, returnedString] = self.__sendAndReceive(socketId, command)
        if (error != 0):
            return [error, returnedString]

        i, j, retList = 0, 0, [error]
        for paramNb in range(4):
            while ((i+j) < len(returnedString) and returnedString[i+j] != ','):
                j += 1
            retList.append(eval(returnedString[i:i+j]))
            i, j = i+j+1, 0

        return retList


    # PositionerTimeFlasherSet :  Set time flasher parameters
    def PositionerTimeFlasherSet (self, socketId, PositionerName, MinimumPosition, MaximumPosition, TimeInterval):
        if (XPS.__usedSockets[socketId] == 0):
            return

        command = 'PositionerTimeFlasherSet(' + PositionerName + ',' + str(MinimumPosition) + ',' + str(MaximumPosition) + ',' + str(TimeInterval) + ')'
        [error, returnedString] = self.__sendAndReceive(socketId, command)
        return [error, returnedString]


    # PositionerTimeFlasherEnable :  Enable time flasher
    def PositionerTimeFlasherEnable (self, socketId, PositionerName):
        if (XPS.__usedSockets[socketId] == 0):
            return

        command = 'PositionerTimeFlasherEnable(' + PositionerName + ')'
        [error, returnedString] = self.__sendAndReceive(socketId, command)
        return [error, returnedString]


    # PositionerTimeFlasherDisable :  Disable time flasher
    def PositionerTimeFlasherDisable (self, socketId, PositionerName):
        if (XPS.__usedSockets[socketId] == 0):
            return

        command = 'PositionerTimeFlasherDisable(' + PositionerName + ')'
        [error, returnedString] = self.__sendAndReceive(socketId, command)
        return [error, returnedString]


    # PositionerUserTravelLimitsGet :  Read UserMinimumTarget and UserMaximumTarget
    def PositionerUserTravelLimitsGet (self, socketId, PositionerName):
        if (XPS.__usedSockets[socketId] == 0):
            return

        command = 'PositionerUserTravelLimitsGet(' + PositionerName + ',double *,double *)'
        [error, returnedString] = self.__sendAndReceive(socketId, command)
        if (error != 0):
            return [error, returnedString]

        i, j, retList = 0, 0, [error]
        for paramNb in range(2):
            while ((i+j) < len(returnedString) and returnedString[i+j] != ','):
                j += 1
            retList.append(eval(returnedString[i:i+j]))
            i, j = i+j+1, 0

        return retList


    # PositionerUserTravelLimitsSet :  Update UserMinimumTarget and UserMaximumTarget
    def PositionerUserTravelLimitsSet (self, socketId, PositionerName, UserMinimumTarget, UserMaximumTarget):
        if (XPS.__usedSockets[socketId] == 0):
            return

        command = 'PositionerUserTravelLimitsSet(' + PositionerName + ',' + str(UserMinimumTarget) + ',' + str(UserMaximumTarget) + ')'
        [error, returnedString] = self.__sendAndReceive(socketId, command)
        return [error, returnedString]


    # PositionerCorrectorAutoTuning :  Astrom&Hagglund based auto-tuning
    def PositionerCorrectorAutoTuning (self, socketId, PositionerName, TuningMode):
        if (XPS.__usedSockets[socketId] == 0):
            return

        command = 'PositionerCorrectorAutoTuning(' + PositionerName + ',' + str(TuningMode) + ',double *,double *,double *)'
        [error, returnedString] = self.__sendAndReceive(socketId, command)
        if (error != 0):
            return [error, returnedString]

        i, j, retList = 0, 0, [error]
        for paramNb in range(3):
            while ((i+j) < len(returnedString) and returnedString[i+j] != ','):
                j += 1
            retList.append(eval(returnedString[i:i+j]))
            i, j = i+j+1, 0

        return retList


    # PositionerAccelerationAutoScaling :  Astrom&Hagglund based auto-scaling
    def PositionerAccelerationAutoScaling (self, socketId, PositionerName):
        if (XPS.__usedSockets[socketId] == 0):
            return

        command = 'PositionerAccelerationAutoScaling(' + PositionerName + ',double *)'
        [error, returnedString] = self.__sendAndReceive(socketId, command)
        if (error != 0):
            return [error, returnedString]

        i, j, retList = 0, 0, [error]
        while ((i+j) < len(returnedString) and returnedString[i+j] != ','):
            j += 1
        retList.append(eval(returnedString[i:i+j]))

        return retList


    # MultipleAxesPVTVerification :  Multiple axes PVT trajectory verification
    def MultipleAxesPVTVerification (self, socketId, GroupName, TrajectoryFileName):
        if (XPS.__usedSockets[socketId] == 0):
            return

        command = 'MultipleAxesPVTVerification(' + GroupName + ',' + TrajectoryFileName + ')'
        [error, returnedString] = self.__sendAndReceive(socketId, command)
        return [error, returnedString]


    # MultipleAxesPVTVerificationResultGet :  Multiple axes PVT trajectory verification result get
    def MultipleAxesPVTVerificationResultGet (self, socketId, PositionerName):
        if (XPS.__usedSockets[socketId] == 0):
            return

        command = 'MultipleAxesPVTVerificationResultGet(' + PositionerName + ',char *,double *,double *,double *,double *)'
        [error, returnedString] = self.__sendAndReceive(socketId, command)
        if (error != 0):
            return [error, returnedString]

        i, j, retList = 0, 0, [error]
        for paramNb in range(4):
            while ((i+j) < len(returnedString) and returnedString[i+j] != ','):
                j += 1
            retList.append(eval(returnedString[i:i+j]))
            i, j = i+j+1, 0

        return retList


    # MultipleAxesPVTExecution :  Multiple axes PVT trajectory execution
    def MultipleAxesPVTExecution (self, socketId, GroupName, TrajectoryFileName, ExecutionNumber):
        if (XPS.__usedSockets[socketId] == 0):
            return

        command = 'MultipleAxesPVTExecution(' + GroupName + ',' + TrajectoryFileName + ',' + str(ExecutionNumber) + ')'
        [error, returnedString] = self.__sendAndReceive(socketId, command)
        return [error, returnedString]


    # MultipleAxesPVTParametersGet :  Multiple axes PVT trajectory get parameters
    def MultipleAxesPVTParametersGet (self, socketId, GroupName):
        if (XPS.__usedSockets[socketId] == 0):
            return

        command = 'MultipleAxesPVTParametersGet(' + GroupName + ',char *,int *)'
        [error, returnedString] = self.__sendAndReceive(socketId, command)
        if (error != 0):
            return [error, returnedString]

        i, j, retList = 0, 0, [error]
        while ((i+j) < len(returnedString) and returnedString[i+j] != ','):
            j += 1
        retList.append(eval(returnedString[i:i+j]))

        return retList


    # MultipleAxesPVTPulseOutputSet :  Configure pulse output on trajectory
    def MultipleAxesPVTPulseOutputSet (self, socketId, GroupName, StartElement, EndElement, TimeInterval):
        if (XPS.__usedSockets[socketId] == 0):
            return

        command = 'MultipleAxesPVTPulseOutputSet(' + GroupName + ',' + str(StartElement) + ',' + str(EndElement) + ',' + str(TimeInterval) + ')'
        [error, returnedString] = self.__sendAndReceive(socketId, command)
        return [error, returnedString]


    # MultipleAxesPVTPulseOutputGet :  Get pulse output on trajectory configuration
    def MultipleAxesPVTPulseOutputGet (self, socketId, GroupName):
        if (XPS.__usedSockets[socketId] == 0):
            return

        command = 'MultipleAxesPVTPulseOutputGet(' + GroupName + ',int *,int *,double *)'
        [error, returnedString] = self.__sendAndReceive(socketId, command)
        if (error != 0):
            return [error, returnedString]

        i, j, retList = 0, 0, [error]
        for paramNb in range(3):
            while ((i+j) < len(returnedString) and returnedString[i+j] != ','):
                j += 1
            retList.append(eval(returnedString[i:i+j]))
            i, j = i+j+1, 0

        return retList


    # SingleAxisSlaveModeEnable :  Enable the slave mode
    def SingleAxisSlaveModeEnable (self, socketId, GroupName):
        if (XPS.__usedSockets[socketId] == 0):
            return

        command = 'SingleAxisSlaveModeEnable(' + GroupName + ')'
        [error, returnedString] = self.__sendAndReceive(socketId, command)
        return [error, returnedString]


    # SingleAxisSlaveModeDisable :  Disable the slave mode
    def SingleAxisSlaveModeDisable (self, socketId, GroupName):
        if (XPS.__usedSockets[socketId] == 0):
            return

        command = 'SingleAxisSlaveModeDisable(' + GroupName + ')'
        [error, returnedString] = self.__sendAndReceive(socketId, command)
        return [error, returnedString]


    # SingleAxisSlaveParametersSet :  Set slave parameters
    def SingleAxisSlaveParametersSet (self, socketId, GroupName, PositionerName, Ratio):
        if (XPS.__usedSockets[socketId] == 0):
            return

        command = 'SingleAxisSlaveParametersSet(' + GroupName + ',' + PositionerName + ',' + str(Ratio) + ')'
        [error, returnedString] = self.__sendAndReceive(socketId, command)
        return [error, returnedString]


    # SingleAxisSlaveParametersGet :  Get slave parameters
    def SingleAxisSlaveParametersGet (self, socketId, GroupName):
        if (XPS.__usedSockets[socketId] == 0):
            return

        command = 'SingleAxisSlaveParametersGet(' + GroupName + ',char *,double *)'
        [error, returnedString] = self.__sendAndReceive(socketId, command)
        if (error != 0):
            return [error, returnedString]

        i, j, retList = 0, 0, [error]
        while ((i+j) < len(returnedString) and returnedString[i+j] != ','):
            j += 1
        retList.append(eval(returnedString[i:i+j]))

        return retList


    # SpindleSlaveModeEnable :  Enable the slave mode
    def SpindleSlaveModeEnable (self, socketId, GroupName):
        if (XPS.__usedSockets[socketId] == 0):
            return

        command = 'SpindleSlaveModeEnable(' + GroupName + ')'
        [error, returnedString] = self.__sendAndReceive(socketId, command)
        return [error, returnedString]


    # SpindleSlaveModeDisable :  Disable the slave mode
    def SpindleSlaveModeDisable (self, socketId, GroupName):
        if (XPS.__usedSockets[socketId] == 0):
            return

        command = 'SpindleSlaveModeDisable(' + GroupName + ')'
        [error, returnedString] = self.__sendAndReceive(socketId, command)
        return [error, returnedString]


    # SpindleSlaveParametersSet :  Set slave parameters
    def SpindleSlaveParametersSet (self, socketId, GroupName, PositionerName, Ratio):
        if (XPS.__usedSockets[socketId] == 0):
            return

        command = 'SpindleSlaveParametersSet(' + GroupName + ',' + PositionerName + ',' + str(Ratio) + ')'
        [error, returnedString] = self.__sendAndReceive(socketId, command)
        return [error, returnedString]


    # SpindleSlaveParametersGet :  Get slave parameters
    def SpindleSlaveParametersGet (self, socketId, GroupName):
        if (XPS.__usedSockets[socketId] == 0):
            return

        command = 'SpindleSlaveParametersGet(' + GroupName + ',char *,double *)'
        [error, returnedString] = self.__sendAndReceive(socketId, command)
        if (error != 0):
            return [error, returnedString]

        i, j, retList = 0, 0, [error]
        while ((i+j) < len(returnedString) and returnedString[i+j] != ','):
            j += 1
        retList.append(eval(returnedString[i:i+j]))

        return retList


    # GroupSpinParametersSet :  Modify Spin parameters on selected group and activate the continuous move
    def GroupSpinParametersSet (self, socketId, GroupName, Velocity, Acceleration):
        if (XPS.__usedSockets[socketId] == 0):
            return

        command = 'GroupSpinParametersSet(' + GroupName + ',' + str(Velocity) + ',' + str(Acceleration) + ')'
        [error, returnedString] = self.__sendAndReceive(socketId, command)
        return [error, returnedString]


    # GroupSpinParametersGet :  Get Spin parameters on selected group
    def GroupSpinParametersGet (self, socketId, GroupName):
        if (XPS.__usedSockets[socketId] == 0):
            return

        command = 'GroupSpinParametersGet(' + GroupName + ',double *,double *)'
        [error, returnedString] = self.__sendAndReceive(socketId, command)
        if (error != 0):
            return [error, returnedString]

        i, j, retList = 0, 0, [error]
        for paramNb in range(2):
            while ((i+j) < len(returnedString) and returnedString[i+j] != ','):
                j += 1
            retList.append(eval(returnedString[i:i+j]))
            i, j = i+j+1, 0

        return retList


    # GroupSpinCurrentGet :  Get Spin current on selected group
    def GroupSpinCurrentGet (self, socketId, GroupName):
        if (XPS.__usedSockets[socketId] == 0):
            return

        command = 'GroupSpinCurrentGet(' + GroupName + ',double *,double *)'
        [error, returnedString] = self.__sendAndReceive(socketId, command)
        if (error != 0):
            return [error, returnedString]

        i, j, retList = 0, 0, [error]
        for paramNb in range(2):
            while ((i+j) < len(returnedString) and returnedString[i+j] != ','):
                j += 1
            retList.append(eval(returnedString[i:i+j]))
            i, j = i+j+1, 0

        return retList


    # GroupSpinModeStop :  Stop Spin mode on selected group with specified acceleration
    def GroupSpinModeStop (self, socketId, GroupName, Acceleration):
        if (XPS.__usedSockets[socketId] == 0):
            return

        command = 'GroupSpinModeStop(' + GroupName + ',' + str(Acceleration) + ')'
        [error, returnedString] = self.__sendAndReceive(socketId, command)
        return [error, returnedString]


    # XYLineArcVerification :  XY trajectory verification
    def XYLineArcVerification (self, socketId, GroupName, TrajectoryFileName):
        if (XPS.__usedSockets[socketId] == 0):
            return

        command = 'XYLineArcVerification(' + GroupName + ',' + TrajectoryFileName + ')'
        [error, returnedString] = self.__sendAndReceive(socketId, command)
        return [error, returnedString]


    # XYLineArcVerificationResultGet :  XY trajectory verification result get
    def XYLineArcVerificationResultGet (self, socketId, PositionerName):
        if (XPS.__usedSockets[socketId] == 0):
            return

        command = 'XYLineArcVerificationResultGet(' + PositionerName + ',char *,double *,double *,double *,double *)'
        [error, returnedString] = self.__sendAndReceive(socketId, command)

        if (error != 0):
            return [error, returnedString]

        i, j, retList = 0, 0, [error]
        for paramNb in range(4):
            while ((i+j) < len(returnedString) and returnedString[i+j] != ','):
                j += 1
            retList.append((returnedString[i:i+j]))
            i, j = i+j+1, 0

        return retList


    # XYLineArcExecution :  XY trajectory execution
    def XYLineArcExecution (self, socketId, GroupName, TrajectoryFileName, Velocity, Acceleration, ExecutionNumber):
        if (XPS.__usedSockets[socketId] == 0):
            return

        command = 'XYLineArcExecution(' + GroupName + ',' + TrajectoryFileName + ',' + str(Velocity) + ',' + str(Acceleration) + ',' + str(ExecutionNumber) + ')'
        [error, returnedString] = self.__sendAndReceive(socketId, command)
        return [error, returnedString]


    # XYLineArcParametersGet :  XY trajectory get parameters
    def XYLineArcParametersGet (self, socketId, GroupName):
        if (XPS.__usedSockets[socketId] == 0):
            return

        command = 'XYLineArcParametersGet(' + GroupName + ',char *,double *,double *,int *)'
        [error, returnedString] = self.__sendAndReceive(socketId, command)
        if (error != 0):
            return [error, returnedString]

        i, j, retList = 0, 0, [error]
        for paramNb in range(3):
            while ((i+j) < len(returnedString) and returnedString[i+j] != ','):
                j += 1
            retList.append(eval(returnedString[i:i+j]))
            i, j = i+j+1, 0

        return retList


    # XYLineArcPulseOutputSet :  Configure pulse output on trajectory
    def XYLineArcPulseOutputSet (self, socketId, GroupName, StartLength, EndLength, PathLengthInterval):
        if (XPS.__usedSockets[socketId] == 0):
            return

        command = 'XYLineArcPulseOutputSet(' + GroupName + ',' + str(StartLength) + ',' + str(EndLength) + ',' + str(PathLengthInterval) + ')'
        [error, returnedString] = self.__sendAndReceive(socketId, command)
        return [error, returnedString]


    # XYLineArcPulseOutputGet :  Get pulse output on trajectory configuration
    def XYLineArcPulseOutputGet (self, socketId, GroupName):
        if (XPS.__usedSockets[socketId] == 0):
            return

        command = 'XYLineArcPulseOutputGet(' + GroupName + ',double *,double *,double *)'
        [error, returnedString] = self.__sendAndReceive(socketId, command)
        if (error != 0):
            return [error, returnedString]

        i, j, retList = 0, 0, [error]
        for paramNb in range(3):
            while ((i+j) < len(returnedString) and returnedString[i+j] != ','):
                j += 1
            retList.append(eval(returnedString[i:i+j]))
            i, j = i+j+1, 0

        return retList


    # XYZGroupPositionCorrectedProfilerGet :  Return corrected profiler positions
    def XYZGroupPositionCorrectedProfilerGet (self, socketId, GroupName, PositionX, PositionY, PositionZ):
        if (XPS.__usedSockets[socketId] == 0):
            return

        command = 'XYZGroupPositionCorrectedProfilerGet(' + GroupName + ',' + str(PositionX) + ',' + str(PositionY) + ',' + str(PositionZ) + ',double *,double *,double *)'
        [error, returnedString] = self.__sendAndReceive(socketId, command)
        if (error != 0):
            return [error, returnedString]

        i, j, retList = 0, 0, [error]
        for paramNb in range(3):
            while ((i+j) < len(returnedString) and returnedString[i+j] != ','):
                j += 1
            retList.append(eval(returnedString[i:i+j]))
            i, j = i+j+1, 0

        return retList


    # XYZSplineVerification :  XYZ trajectory verifivation
    def XYZSplineVerification (self, socketId, GroupName, TrajectoryFileName):
        if (XPS.__usedSockets[socketId] == 0):
            return

        command = 'XYZSplineVerification(' + GroupName + ',' + TrajectoryFileName + ')'
        [error, returnedString] = self.__sendAndReceive(socketId, command)
        return [error, returnedString]


    # XYZSplineVerificationResultGet :  XYZ trajectory verification result get
    def XYZSplineVerificationResultGet (self, socketId, PositionerName):
        if (XPS.__usedSockets[socketId] == 0):
            return

        command = 'XYZSplineVerificationResultGet(' + PositionerName + ',char *,double *,double *,double *,double *)'
        [error, returnedString] = self.__sendAndReceive(socketId, command)
        if (error != 0):
            return [error, returnedString]

        i, j, retList = 0, 0, [error]
        for paramNb in range(4):
            while ((i+j) < len(returnedString) and returnedString[i+j] != ','):
                j += 1
            retList.append(eval(returnedString[i:i+j]))
            i, j = i+j+1, 0

        return retList


    # XYZSplineExecution :  XYZ trajectory execution
    def XYZSplineExecution (self, socketId, GroupName, TrajectoryFileName, Velocity, Acceleration):
        if (XPS.__usedSockets[socketId] == 0):
            return

        command = 'XYZSplineExecution(' + GroupName + ',' + TrajectoryFileName + ',' + str(Velocity) + ',' + str(Acceleration) + ')'
        [error, returnedString] = self.__sendAndReceive(socketId, command)
        return [error, returnedString]


    # XYZSplineParametersGet :  XYZ trajectory get parameters
    def XYZSplineParametersGet (self, socketId, GroupName):
        if (XPS.__usedSockets[socketId] == 0):
            return

        command = 'XYZSplineParametersGet(' + GroupName + ',char *,double *,double *,int *)'
        [error, returnedString] = self.__sendAndReceive(socketId, command)
        if (error != 0):
            return [error, returnedString]

        i, j, retList = 0, 0, [error]
        for paramNb in range(3):
            while ((i+j) < len(returnedString) and returnedString[i+j] != ','):
                j += 1
            retList.append(eval(returnedString[i:i+j]))
            i, j = i+j+1, 0

        return retList


    # OptionalModuleExecute :  Execute an optional module
    def OptionalModuleExecute (self, socketId, ModuleFileName, TaskName):
        if (XPS.__usedSockets[socketId] == 0):
            return

        command = 'OptionalModuleExecute(' + ModuleFileName + ',' + TaskName + ')'
        [error, returnedString] = self.__sendAndReceive(socketId, command)
        return [error, returnedString]


    # OptionalModuleKill :  Kill an optional module
    def OptionalModuleKill (self, socketId, TaskName):
        if (XPS.__usedSockets[socketId] == 0):
            return

        command = 'OptionalModuleKill(' + TaskName + ')'
        [error, returnedString] = self.__sendAndReceive(socketId, command)
        return [error, returnedString]


    # EEPROMCIESet :  Set CIE EEPROM reference string
    def EEPROMCIESet (self, socketId, CardNumber, ReferenceString):
        if (XPS.__usedSockets[socketId] == 0):
            return

        command = 'EEPROMCIESet(' + str(CardNumber) + ',' + ReferenceString + ')'
        [error, returnedString] = self.__sendAndReceive(socketId, command)
        return [error, returnedString]


    # EEPROMDACOffsetCIESet :  Set CIE DAC offsets
    def EEPROMDACOffsetCIESet (self, socketId, PlugNumber, DAC1Offset, DAC2Offset):
        if (XPS.__usedSockets[socketId] == 0):
            return

        command = 'EEPROMDACOffsetCIESet(' + str(PlugNumber) + ',' + str(DAC1Offset) + ',' + str(DAC2Offset) + ')'
        [error, returnedString] = self.__sendAndReceive(socketId, command)
        return [error, returnedString]


    # EEPROMDriverSet :  Set Driver EEPROM reference string
    def EEPROMDriverSet (self, socketId, PlugNumber, ReferenceString):
        return self.__sendAndReceive(socketId,
                                     'EEPROMDriverSet(%i,%s)' % (PlugNumber, ReferenceString))

    # EEPROMINTSet :  Set INT EEPROM reference string
    def EEPROMINTSet (self, socketId, CardNumber, ReferenceString):
        return self.Send(socketId,
                                     'EEPROMINTSet(%i, %s)' % (CardNumber, ReferenceString))

    # CPUCoreAndBoardSupplyVoltagesGet :  Get power informations
    def CPUCoreAndBoardSupplyVoltagesGet (self, socketId):
        cmd = 'CPUCoreAndBoardSupplyVoltagesGet(%s)' % ','.join(['double *']*8)
        self.Send(socketId,cmd,check=True)
        i, j, retList = 0, 0, [error]
        for paramNb in range(8):
            while ((i+j) < len(returnedString) and returnedString[i+j] != ','):
                j += 1
            retList.append(eval(returnedString[i:i+j]))
            i, j = i+j+1, 0

        return retList


    # CPUTemperatureAndFanSpeedGet :  Get CPU temperature and fan speed
    def CPUTemperatureAndFanSpeedGet (self, socketId=None):
        err,msg=self.Send(socketId,
                          'CPUTemperatureAndFanSpeedGet(double *,double *)', check=True)
        i, j, retList = 0, 0, [err]
        for paramNb in range(2):
            while ((i+j) < len(msg) and msg[i+j] != ','):
                j += 1
            retList.append(float(msg[i:i+j]))
            i, j = i+j+1, 0

        return retList

    # ActionListGet :  Action list
    def ActionListGet (self, socketId):
        return  self.Send(socketId, 'ActionListGet(char *)')

    # ActionExtendedListGet :  Action extended list
    def ActionExtendedListGet (self, socketId):
        return self.Send(socketId, 'ActionExtendedListGet(char *)')

    # APIExtendedListGet :  API method list
    def APIExtendedListGet (self, socketId):
        return self.Send(socketId, 'APIExtendedListGet(char *)')

    # APIListGet :  API method list without extended API
    def APIListGet (self, socketId):
        return self.Send(socketId, 'APIListGet(char *)')

    # ControllerStatusListGet :  Controller status list
    def ControllerStatusListGet (self, socketId):
        return self.Send(socketId, 'ControllerStatusListGet(char *)')

    # ErrorListGet :  Error list
    def ErrorListGet (self, socketId):
        return self.Send(socketId, 'ErrorListGet(char *)')

    # EventListGet :  General event list
    def EventListGet (self, socketId):
        return  self.Send(socketId, 'EventListGet(char *)')

    # GatheringListGet :  Gathering type list
    def GatheringListGet (self, socketId):
        return  self.Send(socketId, 'GatheringListGet(char *)')

    # GatheringExtendedListGet :  Gathering type extended list
    def GatheringExtendedListGet (self, socketId):
        return self.Send(socketId, 'GatheringExtendedListGet(char *)')

    # GatheringExternalListGet :  External Gathering type list
    def GatheringExternalListGet (self, socketId):
        return self.Send(socketId, 'GatheringExternalListGet(char *)')

    # GroupStatusListGet :  Group status list
    def GroupStatusListGet (self, socketId):
        return  self.Send(socketId, 'GroupStatusListGet(char *)')

    # HardwareInternalListGet :  Internal hardware list
    def HardwareInternalListGet (self, socketId):
        return self.Send(socketId, 'HardwareInternalListGet(char *)')

    # HardwareDriverAndStageGet :  Smart hardware
    def HardwareDriverAndStageGet (self, socketId=None, PlugNumber=1):
        return  self.Send(socketId, 'HardwareDriverAndStageGet(%i, char *,char *)' % PlugNumber)

    # ObjectsListGet :  Group name and positioner name
    def ObjectsListGet (self, socketId=None):
        return  self.Send(socketId, 'ObjectsListGet(char *)')

    # PositionerErrorListGet :  Positioner error list
    def PositionerErrorListGet (self, socketId=None):
        return  self.Send(socketId, 'PositionerErrorListGet(char *)')

    # PositionerHardwareStatusListGet :  Positioner hardware status list
    def PositionerHardwareStatusListGet (self, socketId=None):
        return self.Send(socketId, 'PositionerHardwareStatusListGet(char *)')

    # PositionerDriverStatusListGet :  Positioner driver status list
    def PositionerDriverStatusListGet (self, socketId=None):
        return self.Send(socketId, 'PositionerDriverStatusListGet(char *)')

    # ReferencingActionListGet :  Get referencing action list
    def ReferencingActionListGet (self, socketId=None):
        return  self.Send(socketId, 'ReferencingActionListGet(char *)')

    # ReferencingSensorListGet :  Get referencing sensor list
    def ReferencingSensorListGet (self, socketId=None):
        return self.Send(socketId, 'ReferencingSensorListGet(char *)')

    # GatheringUserDatasGet :  Return UserDatas values
    def GatheringUserDatasGet (self, socketId):
        cmd = 'GatheringUserDatasGet(%s)' % ','.join(['double *']*8)
        err,msg=self.Send(socketId, cmd, check=True)

        i, j, retList = 0, 0, [err]
        for paramNb in range(8):
            while ((i+j) < len(msg) and msg[i+j] != ','):
                j += 1
            retList.append(float(msg[i:i+j]))
            i, j = i+j+1, 0
        return retList

    # SocketsStatusGet :  Get sockets current status
    def SocketsStatusGet (self, socketId=None):
        return self.Send(socketId, 'SocketsStatusGet(char *)')

    # TestTCP :  Test TCP/IP transfert
    def TestTCP (self, socketId=None, InputString=''):
        return self.Send(socketId, 'TestTCP(%s,char *)' % InputString)
