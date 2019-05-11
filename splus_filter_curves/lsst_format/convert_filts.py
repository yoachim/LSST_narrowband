import numpy as np
import glob


# Let's make a set of filter throughput curves that can drop right into syseng_throughputs

if __name__ == "__main__":

    filenames = glob.glob('../*.dat')
    names = ['wave', 'through']
    types = [float, float]
    for fname in filenames:
        data = np.loadtxt(fname, dtype=list(zip(names, types)))
        # convert to nm
        data['wave'] = data['wave']/10.

        out_name = fname.split('.')[-2][1:] + '_band_Response.dat'
        np.savetxt(out_name, data)

