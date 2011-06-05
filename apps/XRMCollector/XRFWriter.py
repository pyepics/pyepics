import sys
import os
import time
import glob

from ConfigParser import  ConfigParser
from EscanWriter import readEnvironFile, readScanConfig
from read_xmap_netcdf import read_xmap_netcdf

def readROIFile(hfile):
    cp =  ConfigParser()
    cp.read(hfile)
    roiout = []
    try:
        rois = cp.options('rois')
    except:
        print 'rois not found'
        return []

    for a in cp.options('rois'):
        if a.lower().startswith('roi'):
            iroi = int(a[3:])
            name, dat = cp.get('rois',a).split('|')
            xdat = [int(i) for i in dat.split()]
            dat = [(xdat[0], xdat[1]), (xdat[2], xdat[3]),
                   (xdat[4], xdat[5]), (xdat[6], xdat[7])]
            roiout.append((iroi, name.strip(), dat))
    roiout = sorted(roiout)
    calib = {}
    calib['CAL_OFFSET'] = cp.get('calibration', 'OFFSET')
    calib['CAL_SLOPE']  = cp.get('calibration', 'SLOPE')
    calib['CAL_QUAD']   = cp.get('calibration', 'QUAD')
    calib['CAL_TWOTHETA']   = ' 0 0 0 0'
    return roiout, calib


ROI4_TMPL ="""ROI_%i_LEFT:   %s %s %s %s
ROI_%i_RIGHT:  %s %s %s %s
ROI_%i_LABEL:  %s & %s & %s & %s &
"""
def WriteFullXRF(folder):
    conf = readScanConfig(folder)
    xrffile = "%s.xrf" % conf[0]['filename']
    rois, calib = readROIFile(os.path.join(folder, 'ROI.dat'))
    env = readEnvironFile(os.path.join(folder, 'Environ.dat'))

    roilines = []
    for roidat in rois:
        i, name, bds = roidat
        roilines.append(ROI4_TMPL %(i,bds[0][0], bds[1][0], bds[2][0], bds[3][0],
                                    i, bds[0][1], bds[1][1], bds[2][1], bds[3][1],
                                    i, name, name, name, name))

    ltime, rtime, spectra = None, None, None

    filelist = glob.glob(os.path.join(folder, 'xmap.*'))
    for xmapfile in filelist:
        xmapdat = read_xmap_netcdf(xmapfile, verbose=False)
        if spectra is None:
            spectra = xmapdat.data[:]
        else:
            spectra = spectra + xmapdat.data[:]
        if ltime is None:
            ltime = xmapdat.liveTime[:]
        else:
            ltime = ltime + xmapdat.liveTime[:]
        if rtime is None:
            rtime = xmapdat.realTime[:]
        else:
            rtime = rtime + xmapdat.realTime[:]

    spectra = spectra.sum(axis=0)
    rtime = rtime.sum(axis=0)
    ltime = ltime.sum(axis=0)

    nchan, nelem = spectra.shape
    nrois = len(rois)
    fp = open(xrffile, 'w')

    fp.write('VERSION:    3.1\n')
    fp.write('ELEMENTS:   %i\n' % nelem)
    fp.write('DATE:       %s\n' % time.ctime())
    fp.write('CHANNELS:   %i\n' % nchan)
    fp.write('ROIS:       %i %i %i %i\n' % (nrois, nrois, nrois, nrois))
    fp.write('REAL_TIME:  %f %f %f %f\n' % (rtime[0], rtime[1], rtime[2], rtime[3]))
    fp.write('LIVE_TIME:  %f %f %f %f\n' % (ltime[0], ltime[1], ltime[2], ltime[3]))
    for key in ('CAL_OFFSET', 'CAL_SLOPE', 'CAL_QUAD', 'CAL_TWOTHETA'):
        fp.write('%s: %s\n' % (key, calib[key]))
    fp.writelines(roilines)
    for eline in env:
        eline = eline.strip()[1:]
        fp.write("ENVIRONMENT: %s\n" % eline)
    fp.write("DATA:\n")
    spectra = spectra.transpose()
    for px in spectra:
        fp.write(" %i %i %i %i\n" % (px[0], px[1], px[2], px[3]))

spectra = WriteFullXRF('Map')
# write_medfile(full_spectra)
