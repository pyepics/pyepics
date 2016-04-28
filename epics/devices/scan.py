#!/usr/bin/env python
"""
Epics scan record
"""
from .. import Device, poll
import threading

NUM_POSITIONERS = 4
NUM_TRIGGERS    = 4
NUM_DETECTORS   = 70

class Scan(Device):
    """
    A Device representing an Epics sscan record.
    """

    attrs = ('VAL', 'SMSG', 'CMND', 'NPTS', 'EXSC', 'NAME', 'PDLY',
             'PAUS', 'CPT', 'DDLY')

    pos_attrs = ('PV', 'SP', 'EP', 'SI', 'CP', 'WD', 'PA', 'AR', 'SM')
    trig_attrs = ('PV', 'NV')

    _alias = {'device':      'P1PV',
              'start':       'P1SP',
              'end':         'P1EP',
              'step':        'P1SI',
              'table':       'P1PA',
              'absrel':      'P1AR',
              'mode':        'P1SM',
              'npts':        'NPTS',
              'execute':     'EXSC',
              'trigger':     'T1PV',
              'pause':       'PAUS',
              'current_point':  'CPT'}

    def __init__(self, name, **kwargs):
        """
        Initialize the scan.

        name: The name of the scan record.
        """
        attrs = list(self.attrs)
        for i in range(1, NUM_POSITIONERS+1):
            for a in self.pos_attrs:
                attrs.append('P%i%s' % (i, a))
        for i in range(1, NUM_TRIGGERS+1):
            for a in self.trig_attrs:
                attrs.append('T%i%s' % (i, a))
        for i in range(1, NUM_DETECTORS+1):
            attrs.append('D%2.2iPV' % i)

        self.waitSemaphore = threading.Semaphore(0)
        Device.__init__(self, name, delim='.', attrs=attrs, **kwargs)
        for attr, pv in Scan._alias.items():
            self.add_pv('%s.%s' % (name,pv), attr)

        # make sure this is really a sscan!
        rectype = self.get('RTYP')
        if rectype != 'sscan':
            raise ScanException("%s is not an Epics Scan" % name)

        self.put('SMSG', '')

    def run(self, wait=False, timeout=86400):
        """
        Execute the scan, optionally waiting for completion

        Arguments
        ---------
        wait     whether to wait for completion, True/False (default False)
        timeout  maximum time to wait in seconds, default=86400 (1 day).

        """
        self.put('EXSC', 1, wait=wait, timeout=timeout)

    def _onDone(self, **kwargs):
        if kwargs['value'] == 0:
            self.waitSemaphore.release()

    def reset(self):
        """Reset scan, clearing positioners, detectors, triggers"""
        self.put('NPTS', 0)
        for i in range(1, NUM_TRIGGERS+1):
            self.clear_trigger(i)
        for i in range(1, NUM_POSITIONERS+1):
            self.clear_positioner(i)
        for i in range(1, NUM_DETECTORS+1):
            self.clear_detector(i)
        poll(1.e-3, 1.0)

    def _print(self):
        print('PV = %s' % self.get('P1PV'))
        print('SP = %s' % self.get('P1SP'))
        print('EP = %s' % self.get('P1EP'))
        print('NPTS = %s' % self.get('NPTS'))
        print('T  = %s' % self.get('T1PV'))


    def clear_detector(self, idet=1):
        """completely clear a detector

        Arguments
        ---------
          idet    index of detector (1 through 70, default 1)
        """
        self.put("D%2.2iPV" % idet, '')
        poll(1.e-3, 1.0)

    def add_detector(self, detector):
        """add a detector to a scan definition

        Arguments
        ---------
          detector   name of detector pv

        Returns
        -------
         idet  index of detector set
        """
        idet = None
        for _idet in range(1, NUM_DETECTORS+1):
            poll(1.e-3, 1.0)
            if len(self.get('D%2.2iPV' % _idet)) < 2:
                idet = _idet
                break
        if idet is None:
            raise ScanException("%i Detectors already defined." % (NUM_DETECTORS))
        self.put("D%2.2iPV" % idet, detector, wait=True)
        return idet

    def clear_trigger(self, itrig=1):
        """completely clear a trigger

        Arguments
        ---------
          itrig    index of trigger (1 through 4, default 1)
        """
        self.put("T%iPV" % itrig, '')
        poll(1.e-3, 1.0)

    def add_trigger(self, trigger, value=1.0):
        """add a trigger to a scan definition

        Arguments
        ---------
          trigger   name of trigger pv
          value     value to send to trigger (default 1.0)

        Returns
        -------
           itrig  index of trigger set
        """
        itrig = None
        for _itrig in range(1, NUM_TRIGGERS+1):
            poll(1.e-3, 1.0)
            if len(self.get('T%iPV' % _itrig)) < 2:
                itrig = _itrig
                break
        if itrig is None:
            raise ScanException("%i Triggers already defined." % (NUM_TRIGGERS))

        self.put("T%iPV" % itrig, trigger, wait=True)
        self.put("T%iCD" % itrig, value, wait=True)
        return itrig


    def clear_positioner(self, ipos=1):
        """completely clear a positioner

        Arguments
        ---------
          ipos    index of positioner (1 through 4, default 1)
        """
        for attr in self.pos_attrs:
            nulval = 0
            if attr == 'PV': nulval = ''
            if attr == 'PA': nulval = [0]
            self.put("P%i%s" % (ipos, attr), nulval)
        self.put("R%iPV" % ipos, '')
        poll(1.e-3, 1.0)

    def add_positioner(self, drive, readback=None,
                       start=None, stop=None, step=None,
                       center=None, width=None,
                       mode='linear', absolute=True, array=None):
        """add a positioner to a scan definition

        Arguments
        ----------
         drive     name of drive pv
         readback  name of readback pv (defaults to .RBV if drive ends in .VAL)
         mode      positioner mode ('linear', 'table', fly', default 'linear')
         absolute  whether to use absolute values (True/False, default True)
         start     start value
         stop      stop value
         step      step value
         center    center value
         width     width value
         array     array of values for table or fly mode

        Returns
        -------
         ipos  index of positioner set

        """
        ipos = None
        for _ipos in range(1, NUM_POSITIONERS+1):
            poll(1.e-3, 1.0)
            if len(self.get('P%iPV' % _ipos)) < 2:
                ipos = _ipos
                break
        if ipos is None:
            raise ScanException("%i Positioners already defined." % (NUM_POSITIONERS))

        self.put('P%iPV' % ipos, drive, wait=True)
        if readback is None and drive.endswith('.VAL'):
            readback = drive[:-4] + '.RBV'
        if readback is not None:
            self.put('R%iPV' % ipos, readback)

        # set relative/absolute
        if absolute:
            self.put('P%iAR' % ipos, 0)
        else:
            self.put('P%iAR' % ipos, 1)

        # set mode
        smode = 0
        if mode.lower().startswith('table'):
            smode = 1
        elif mode.lower().startswith('fly'):
            smode = 2
        self.put('P%iSM' % ipos, smode)

        # start, stop, step, center, width
        if start is not None:
            self.put('P%iSP' % ipos, start)
        if stop is not None:
            self.put('P%iEP' % ipos, stop)
        if step is not None:
            self.put('P%iSI' % ipos, step)
        if center is not None:
            self.put('P%iCP' % ipos, center)
        if width is not None:
            self.put('P%iWD' % ipos, width)

        # table or fly mode
        if smode in (1, 2) and array is not None:
            self.put('P%iPA' % ipos, array)
        poll(1.e-3, 1.0)
        return ipos

    def set_positioner(self, ipos, drive=None, readback=None,
                       start=None, stop=None, step=None,
                       center=None, width=None,
                       mode=None, absolute=None, array=None):
        """change a positioner setting in a scan definition
        all settings are optional, and will leave other settings unchanged

        Arguments
        ----------
         drive     name of drive pv
         readback  name of readback pv
         mode      positioner mode ('linear', 'table', fly', default 'linear')
         absolute  whether to use absolute values (True/False, default True)
         start     start value
         stop      stop value
         step      step value
         center    center value
         width     width value
         array     array of values for table or fly mode

        Notes
        -----
         This allows changing a scan, for example:

             s = Scan('XXX:scan1')
             ipos1 = s.add_positioner('XXX:m1.VAL', start=-1, stop=1, step=0.1)
             ....

             s.run()

         Then changing the scan definition with

            s.set_positioner(ipos1, start=0, stop=0.2, step=0.01)
            s.run()
        """
        if ipos is None:
            raise ScanException("must give positioner index")

        if drive is not None:
            self.put('P%iPV' % ipos, drive)
        if readback is not None:
            self.put('R%iPV' % ipos, readback)
        if start is not None:
            self.put('P%iSP' % ipos, start)
        if stop is not None:
            self.put('P%iEP' % ipos, stop)
        if step is not None:
            self.put('P%iSI' % ipos, step)
        if center is not None:
            self.put('P%iCP' % ipos, center)
        if width is not None:
            self.put('P%iWD' % ipos, width)
        if array is not None:
            self.put('P%iPA' % ipos, array)

        if absolute is not None:
            if absolute:
                self.put('P%iAR' % ipos, 0)
            else:
                self.put('P%iAR' % ipos, 1)

        if mode is not None:
            smode = 0
            if mode.lower().startswith('table'):
                smode = 1
            elif mode.lower().startswith('fly'):
                smode = 2
            self.put('P%iSM' % ipos, smode)
        poll(1.e-3, 1.0)


    def after_scan(self, mode):
        """set after scan mode"""
        self.put("PASM", mode, wait=True)

    def positioner_delay(self, pdelay):
        """set positioner delay in seconds"""
        self.put("PDLY", pdelay, wait=True)

    def detector_delay(self, pdelay):
        """set detector delay in seconds"""
        self.put("DDLY", pdelay, wait=True)

class ScanException(Exception):
    """ raised to indicate a problem with a scan"""
    def __init__(self, msg, *args):
        Exception.__init__(self, *args)
        self.msg = msg
    def __str__(self):
        return str(self.msg)
