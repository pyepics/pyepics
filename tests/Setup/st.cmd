errlogInit(5000)
< envPaths
dbLoadDatabase("../../dbd/CARSLinux.dbd")
CARSLinux_registerRecordDeviceDriver(pdbbase)

### Scan-support software
# crate-resident scan.  This executes 1D, 2D, 3D, and 4D scans, and caches
# 1D data, but it doesn't store anything to disk.  (You need the data catcher
# or the equivalent for that.)  This database is configured to use the
# "alldone" database (above) to figure out when motors have stopped moving
# and it's time to trigger detectors.
dbLoadRecords("Db/scan.db", "P=Py:,MAXPTS1=2000,MAXPTS2=200,MAXPTS3=20,MAXPTS4=10,MAXPTSH=10")

# Free-standing user string/number calculations (sCalcout records)
dbLoadRecords("Db/userStringCalcs10.db", "P=Py:")

# Free-standing user transforms (transform records)
dbLoadRecords("Db/userTransforms10.db", "P=Py:")

# dbLoadRecords("$(ASYN)/db/asynRecord.db", "P=13XRM:,R=asyn1,PORT=XPS1,ADDR=0,IMAX=256,OMAX=256")

# test databases
dbLoadRecords("Db/pydebug.db", "P=Py:")

iocInit

