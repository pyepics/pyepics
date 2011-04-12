from escan_data import escan_data


def escan2xafs(fname, channel='Fe Ka'):
    edat = escan_data(fname)
    print '  channel=%s, file=%s' % (channel, fname)
    i0 = edat.get_data('i0', correct=False)
    energy  = edat.x
    fl_raw  = edat.get_data(channel, norm=None, correct=False)
    fl_corr = edat.get_data(channel, norm=None, correct=True)

    mu_corr = fl_corr /i0

    index = edat.sums_names.index(channel)
    slist = edat.sums_list[index]
    npts = len(energy)
    cname = channel.replace(' ', '_')
    out = []
    print ' Writing %i pts for channel=%s, file=%s' % (npts, cname, fname)
    out.append('# XAFS Data Saved from escan data file %s\n' % fname)
    out.append('# Channel = %s\n' % channel)
    out.append('# DeadTime Correction = True\n')
    out.append('# Summed Channels %s (counting from 0) from escan datafile\n' % slist)
    out.append('#--------------------------------------------------------\n')
    out.append('# energy    mu_corr    i0    %s_corr  %s_raw\n' % (cname, cname))

    for ipt in range(npts):
        out.append(' %.3f  %9g %i  %.4f   %i\n' % (energy[ipt], mu_corr[ipt], i0[ipt],
                                                     fl_corr[ipt], fl_raw[ipt]))
                                                     
        
    
    f = open("%s.xmu" % fname, 'w')
    f.writelines(out)
    f.close()


escan2xafs('test.001', 'Fe Ka')
    
