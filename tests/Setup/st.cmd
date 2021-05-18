errlogInit(5000)
epicsEnvSet("IOC","iocPyEpicsTest")
dbLoadDatabase("softIoc.dbd")
dbLoadRecords("pydebug.db", "P=PyTest:")

iocInit
