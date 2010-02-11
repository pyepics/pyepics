import time

def _fmt_time(t=None):
    if t is None: t = time.time()
    t,frac=divmod(t,1)
    return "%s.%3.3i" %(time.strftime("%Y-%h-%d %H:%M:%S"),1000.0*frac)
print _fmt_time()
