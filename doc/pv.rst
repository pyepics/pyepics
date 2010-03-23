===========================
pv module and the PV object
===========================

Overview
========

This module provides a low level wrapping of the EPICS Channel Access (CA)
library, using ctypes.  Most users of the epics module will not need to be
concerned with the details here, and only use the simple functional interface
(caget, caput), or create and use epics PV objects, or define epics devices.

The goal of ths module is to stay fairly close to the C interface to CA while
also providing a pleasant Python experience.  It is expected that anyone
looking into the details of this module is somewhat familar with Channel
Access and knows where to consult the CA reference documentation.  To that
end, this document mostly describe the differences with the C interface.

        
User-supplied Callback functions
================================

User-supplied callback functions can be provided for both put() and create_subscription()

For both cases, it is important to keep two things in mind:
   how your function will be called
   what is permissable to do inside your callback function.

