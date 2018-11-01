#!/usr/bin/env python

"""
Wrapper to the linetools XSpecGUI
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import argparse

def parser(options=None):
    parser = argparse.ArgumentParser(description='Script to coadd a set of spec1D files and 1 or more slits and 1 or more objects. Current defaults use Optimal + Fluxed extraction. [v1.1]')
    parser.add_argument("infile", type=str, help="Input file (YAML)")
    parser.add_argument("--debug", default=False, action='store_true', help="Turn debugging on")

    if options is None:
        args = parser.parse_args()
    else:
        args = parser.parse_args(options)
    return args


def main(args, unit_test=False, path=''):
    """ Runs the XSpecGui on an input file
    path : str, optional
      Mainly for running the unit test
    """

    import glob
    import yaml

    from numpy import isnan
    import pdb as debugger

    from astropy.io import fits

    from pypeit import msgs
    from pypeit.core import coadd
    from pypeit import specobjs

    # Load the input file
    with open(args.infile, 'r') as infile:
        coadd_dict = yaml.load(infile)

    # Grab object names in the spectra
    filelist = coadd_dict.pop('filenames')
    # Allow for wildcards
    files = []
    for ifl in filelist:
        if '*' in ifl:
            files += glob.glob(path+ifl)
        else:
            files += [path+ifl]
    # Load spectra
    if len(files) == 0:
        msgs.error("No files match your input list")
    else:
        msgs.info("Coadding {:d} data frames".format(len(files)))
    fdict = {}
    for ifile in files:
        # Open file
        hdulist = fits.open(ifile)
        # Grab objects
        objects = [hdu.name for hdu in hdulist][1:]
        fdict[ifile] = objects

    # Global parameters?
    if 'global' in coadd_dict.keys():
        gparam = coadd_dict.pop('global')
    else:
        gparam = {}
    if args.debug:
        gparam['debug'] = True
    sv_gparam = gparam.copy()
    # Extraction
    if 'extract' in coadd_dict.keys():
        ex_value = coadd_dict.pop('extract')
    else:
        ex_value = 'OPT'
    msgs.info("Using {:s} extraction".format(ex_value))
    # Fluxed data?
    if 'flux' in coadd_dict.keys():
        flux_value = coadd_dict.pop('flux')
    else:
        flux_value = True

    # Loop on sources
    for key in coadd_dict.keys():
        # Re-init gparam
        gparam = sv_gparam.copy()
        iobj = coadd_dict[key]['object']
        # Check iobj input
        if isinstance(iobj, list):
            if len(iobj) != len(files):
                raise IOError("Input list of object names must have same length as files")
        #
        outfile = coadd_dict[key]['outfile']

        # Generate local keywords
        try:
            local_kwargs = coadd_dict[key]['local']
        except KeyError:
            local_kwargs = {}
        else:
            for lkey in local_kwargs:
                gparam[lkey] = local_kwargs[lkey]

        if unit_test:
            return gparam, ex_value, flux_value, iobj, outfile, files, local_kwargs


        # Loop on spec1d files
        gdfiles = []
        extensions = []
        gdobj = []

        for fkey in fdict:
            # Input as str or list
            if not isinstance(iobj, list) == 1:  # Simple single object
                use_obj = iobj
            else:
                ind = files.index(fkey)
                use_obj = iobj[ind]
            # Find object indices
            mtch_obj, idx = specobjs.mtch_obj_to_objects(use_obj, fdict[fkey], **local_kwargs)
            if mtch_obj is None:
                print("No object {:s} in file {:s}".format(iobj, fkey))
            elif len(mtch_obj) == 1:
                #Check if optimal extraction is present in all  objects.
                # If not, warn the user and set ex_value to 'box'.
                hdulist = fits.open(fkey)
                try: #In case the optimal extraction array is a NaN array
                    if flux_value is True: # If we have a fluxed spectrum, look for flam
                        obj_opt = hdulist[mtch_obj[0]].data['OPT_FLAM']
                    else: # If not, look for counts
                        obj_opt = hdulist[mtch_obj[0]].data['OPT_COUNTS']
                    if any(isnan(obj_opt)):
                        msgs.warn("Object {:s} in file {:s} has a NaN array for optimal extraction. Boxcar will be used instead.".format(mtch_obj[0],fkey))
                        ex_value = 'box'
                except KeyError: #In case the array is absent altogether.
                    msgs.warn("Object {:s} in file {:s} doesn't have an optimal extraction. Boxcar will be used instead.".format(mtch_obj[0],fkey))
                    try:
                        if flux_value is True: # If we have a fluxed spectrum, look for flam
                            hdulist[mtch_obj[0]].data['BOX_FLAM']
                        else: # If not, look for counts
                            hdulist[mtch_obj[0]].data['BOX_COUNTS']
                    except KeyError:
                        #In case the boxcar extract is also absent
                        msgs.error("Object {:s} in file {:s} doesn't have a boxcar extraction either. Co-addition cannot be performed".format(mtch_obj[0],fkey))
                    ex_value = 'box'
                gdfiles.append(fkey)
                gdobj += mtch_obj
                extensions.append(idx[0]+1)
            else:
                raise ValueError("Multiple matches to object {:s} in file {:s}".format(iobj, fkey))

        # Load spectra
        if len(gdfiles) == 0:
            msgs.error("No files match your input criteria")

        spectra = coadd.load_spec(gdfiles, iextensions=extensions,
                                    extract=ex_value, flux=flux_value)
        exten = outfile.split('.')[-1]  # Allow for hdf or fits or whatever
        qafile = outfile.replace(exten, 'pdf')
        # Coadd!
        coadd.coadd_spectra(spectra, qafile=qafile, outfile=outfile, **gparam)

