#!/usr/bin/env python
"""
Provides CAProcess, a multiprocessing.Process that correctly handles Channel Access
and CAPool, pool of CAProcesses

Use CAProcess in place of multiprocessing.Process if your process will be calling
Channel Access or using Epics process variables

   from epics import (CAProcess, CAPool)

"""
#
# Author:         Ken Lauer
# Created:        Feb. 27, 2014
# Modifications:  Matt Newville, changed to subclass multiprocessing.Process
#                 3/28/2014  KL, added CAPool

import multiprocessing as mp
from multiprocessing.pool import Pool
from . import ca
from .ca import clear_cache


__all__ = ['CAProcess', 'CAPool', 'clear_ca_cache']

class CAProcess(mp.Process):
    """
    A Channel-Access aware (and safe) subclass of multiprocessing.Process

    Use CAProcess in place of multiprocessing.Process if your Process will
    be doing CA calls!
    """
    def __init__(self, **kws):
        mp.Process.__init__(self, **kws)

    def run(self):
        ca.initial_context = None
        clear_cache()
        mp.Process.run(self)


class CAPool(Pool):
    """
    An EPICS-aware multiprocessing.Pool of CAProcesses.
    """
    def __init__(self, *args, **kwargs):
        self.Process = CAProcess

        Pool.__init__(self, *args, **kwargs)
