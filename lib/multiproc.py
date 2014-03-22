#!/usr/bin/env python
"""
provides CAProcess, a multiprocess.Process that correctly handles Channel Access 
and CAPool, pool of CAProcesses

use CAProcess in place of multiprocess.Process if your process will be calling
Channel Access or using Epics process variables

from epics import CAProcess

"""
#
# Author:         Ken Lauer
# Created:        Feb. 27, 2014
# Modifications:  Matt Newville, changed to subclass multiprocess.Process

import multiprocessing as mp
import epics

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
    A Channel-Access aware (and safe) sublcass of multiprocess.Process 
    
    use CAProcess in place of multiprocess.Process if your Process will
    be doing CA calls!
    """
    def __init__(self, **kws):
        mp.Process.__init__(self, **kws)

    def run():
        clear_ca_cache()
        mp.Process.run()

def CAPool(processes=None, initializer=None, initargs=(), maxtasksperchild=None):
    """
    Returns a pool of CAProcess objects
    """
    from multiprocessing.pool import Pool
    Pool.Process = CAProcess
    return Pool(processes, initializer, initargs, maxtasksperchild)
