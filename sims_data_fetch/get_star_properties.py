import os
import numpy as np

from lsst.utils import getPackageDir
from lsst.sims.catUtils.baseCatalogModels import StarObj
from lsst.sims.utils import ObservationMetaData
from lsst.sims.utils import equatorialFromGalactic

def get_kurucz_phys(sed_name_in):
    """
    Read in the name of a kurucz SED file.  Return it's
    T_eff, metallicity, log(surface gravity)
    """
    sed_name = sed_name_in.replace('.gz','')
    if sed_name[1] == 'p':
        metallicity_sgn = 1.0
    elif sed_name[1] == 'm':
        metallicity_sgn = -1.0
    else:
        raise RuntimeError('Cannot parse metallicity sign of %s' % sed_name)

    new_name = sed_name.replace('.','_').split('_')

    metallicity = 0.1*metallicity_sgn*float(new_name[0][2:])

    teff = float(new_name[-1])

    logg = 0.1*np.float(new_name[3][1:])

    return teff, metallicity, logg


def get_wd_phys(sed_name):
    """
    Read in the name of a white dwarf SED,
    return its T_eff, metallicity (which we don't actually have),
    and log(surface gravity)
    """
    new_name = sed_name.replace('.','_').split('_')
    if new_name[1]!='He':
        logg = 0.1*float(new_name[2])
        teff = float(new_name[4])
    else:
        logg = 0.1*float(new_name[3])
        teff = float(new_name[5])


    return teff, -999.0, logg


def get_mlt_phys(sed_name):
    """
    Read in the name of an M/L/T dwarf SED and return
    its T_eff, metallicity, and log(surface gravity)
    """

    new_name = sed_name.replace('+','-').replace('a','-').split('-')

    logg_sgn_dex = len(new_name[0])

    if sed_name[logg_sgn_dex] == '-':
        logg_sgn = 1.0
    elif sed_name[logg_sgn_dex] == '+':
        logg_sgn = -1.0
    else:
        raise RuntimeError('Cannot get logg_sgn for %s' % sed_name)

    metallicity_sgn_dex = len(new_name[0]) + len(new_name[1]) + 1

    if sed_name[metallicity_sgn_dex] == '-':
        metallicity_sgn = -1.0
    elif sed_name[metallicity_sgn_dex] == '+':
        metallicity_sgn = 1.0
    else:
        raise RuntimeError('Cannot get metallicity_sgn for %s' % sed_name)

    teff = 100.0*float(new_name[0][3:])
    metallicity = metallicity_sgn*float(new_name[2])
    logg = logg_sgn*float(new_name[1])

    return teff, metallicity, logg


def get_physical_characteristics(sed_name):
    """
    Read in the name of an SED file.
    Return (in this order) Teff, metallicity (FeH), log(g)
    """
    sed_name = sed_name.strip()

    if not hasattr(get_physical_characteristics, 'teff_dict'):
        get_physical_characteristics.teff_dict = {}
        get_physical_characteristics.logg_dict = {}
        get_physical_characteristics.metal_dict = {}

    if sed_name in get_physical_characteristics.teff_dict:
        return (get_physical_characteristics.teff_dict[sed_name],
                get_physical_characteristics.metal_dict[sed_name],
                get_physical_characteristics.logg_dict[sed_name])

    if sed_name.startswith('bergeron'):
        sub_dir = 'wDs'
    elif sed_name.startswith('lte'):
        sub_dir = 'mlt'
    elif sed_name[0] == 'k':
        sub_dir = 'kurucz'
    else:
        raise RuntimeError("Do not understand name %s" % sed_name)



    if 'kurucz' in sub_dir:
        tt,mm,gg =  get_kurucz_phys(sed_name)
    elif sub_dir == 'wDs':
        tt,mm,gg = get_wd_phys(sed_name)
    elif sub_dir == 'mlt':
        tt,mm,gg = get_mlt_phys(sed_name)
    else:
        raise RuntimeError('Do not know how to get '
                           'physical characteristics for '
                           'sub_dir %s' % sub_dir)

    get_physical_characteristics.teff_dict[sed_name] = tt
    get_physical_characteristics.metal_dict[sed_name] = mm
    get_physical_characteristics.logg_dict[sed_name] = gg

    return tt, mm, gg


if __name__ == "__main__":

    # find the RA, Dec of the north Galactic pole
    ra, dec = equatorialFromGalactic(0.0, 90.0)

    # define a field of view that is a circle of radius 1 degree
    # around that point
    obs = ObservationMetaData(pointingRA=ra, pointingDec=dec,
                              boundType='circle',
                              boundLength=1.0)

    # connect to our database of simulated stars
    # (if you want to do this from off campus, talk to me;
    # there are more authentication steps you need to go through)
    star_db = StarObj(database='LSSTCATSIM',
                      host='fatboy.phys.washington.edu',
                      port=1433, driver='mssql+pymssql')

    # define the columns you want to get from the database
    # (note: the query automatically adds the 'simobjid'
    # column to the front; that is just an integer
    # uniquely identifying each star)
    column_names = ['ra', 'decl', 'sedFilename', 'rmag']

    results = star_db.query_columns(colnames=column_names,
                                    obs_metadata=obs)

    # results is now an iterator over chunks of stars
    # to get numpy arrays of teff, metallicity, logg, and rmag
    # use
    teff = []
    metallicity = []
    logg = []
    rmag = []
    for chunk in results:
        for line in chunk:
            phys_params = get_physical_characteristics(line['sedFilename'])
            teff.append(phys_params[0])
            metallicity.append(phys_params[1])
            logg.append(phys_params[2])
            rmag.append(line['rmag'])

    teff = np.array(teff)
    metallicity = np.array(metallicity)
    logg = np.array(logg)
    rmag = np.array(rmag)
