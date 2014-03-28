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
import epics


__all__ = ['CAProcess', 'CAPool', 'clear_ca_cache']


def clear_ca_cache():
    """
    Clears global pyepics state and fixes the CA context
    such that forked subprocesses created with multiprocessing
    can safely use pyepics.
    """

    # Clear global pyepics state variables
    epics._CACHE_.clear()
    epics._MONITORS_.clear()
    epics.ca._cache.clear()
    epics.ca._put_done.clear()

    # The old context is copied directly from the old process
    # in systems with proper fork() implementations
    epics.ca.detach_context()
    epics.ca.create_context()


class CAProcess(mp.Process):
    """
    A Channel-Access aware (and safe) subclass of multiprocessing.Process

    Use CAProcess in place of multiprocessing.Process if your Process will
    be doing CA calls!
    """
    def __init__(self, **kws):
        mp.Process.__init__(self, **kws)

    def run(self):
        clear_ca_cache()
        mp.Process.run(self)


class CAPool(Pool):
    """
    An EPICS-aware multiprocessing.Pool of CAProcesses.
    """
    def __init__(self, *args, **kwargs):
        self.Process = CAProcess

        Pool.__init__(self, *args, **kwargs)
