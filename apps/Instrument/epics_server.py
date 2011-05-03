#!/usr/bin/python
import time
import epics
import epics.devices
from instrument import isInstrumentDB, InstrumentDB

class EpicsInstrumentServer(epics.Device):
    """
    Epics Device that attaches to an Instrument Database, as defined
    by instrument.db

    """
    _nonpvs = ('_prefix', '_pvs', '_delim', '_request',
               '_moving', '_instname', '_inst')

    attrs = ('TSTAMP', 'UNIXTS', 'ExecCommand', 'Move',
             'InstName', 'PosName', 'InstOK', 'PosOK',
             'CommandName', 'aCommandOK',
             'CommandArg1', 'CommandArg2', 'Message')

    def __init__(self, prefix, db=None):
        if not prefix.endswith(':'):
            prefix = "%s:" % prefix

        epics.Device.__init__(self, prefix, delim='',
                              attrs=self.attrs)

        self._moving = False
        self._request = {}
        self._inst = None
        self.add_callback('InstName', self.OnInstName)
        self.add_callback('PosName', self.OnPosName)
        self.add_callback('Move', self.OnMove)

    def MoveDone(self):
        self.put('Message', 'Move complete')
        self.put('Move', 0)
        self._moving = False

    def OnMove(self, pvname=None, value=None, **kw):
        self._request['Move'] = value==1

    def OnPosName(self, pvname=None, value=None, **kw):
        self._request['Pos'] = value

    def OnInstName(self, pvname=None, value=None, **kw):
        self._request['Inst'] = value

    def SetTimeStamp(self):
        "set timestamp"
        self.put('TSTAMP', time.strftime("%Y-%b-%d %H:%M:%S"))

    def SetInfo(self, message=''):
        self.put('Info', str(message))

    def Start(self, message='Starting'):
        "set timestamp"
        self.put('Info', str(message))
        self.put('Move', 0)
        time.sleep(0.1)
        self.OnInstName(value=self.get('InstName'))
        self.OnPosName(value=self.get('PosName'))

    def Shutdown(self):
        "set timestamp"
        self.put('Info', 'offline')
        self.put('Message', '')
        self.put('InstOK', 0)
        self.put('PosOK', 0)
        self.put('Move', 0)
