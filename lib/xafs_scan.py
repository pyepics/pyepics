
def xafs_scan(e0, regions):
    eout = []
    for start, stop, step, tx in regions:
        for ipt in range(int( (stop-start)/step + 0.1)):
            eout.append(e0 + start + step*ipt)
    return eout

xout = xafs_scan(5989, [(-35, -5, 2, 1), (-5, 25, 0.1, 1), (25, 255, 2, 1)])
print len(xout)

