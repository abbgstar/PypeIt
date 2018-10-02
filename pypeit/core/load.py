""" Module for loading PypeIt files
"""
from __future__ import (print_function, absolute_import, division, unicode_literals)

import os

import numpy as np

from astropy import units
from astropy.time import Time
from astropy.io import fits
from astropy.table import Table

from linetools.spectra.xspectrum1d import XSpectrum1D

from pypeit import msgs
from pypeit import specobjs
from pypeit import debugger


def load_headers(datlines, spectrograph, strict=True):
    """ Load the header information for each fits file
    The cards of interest are specified in the instrument settings file
    A check of specific cards is performed if specified in settings

    Parameters
    ----------
    datlines : list
      Input (uncommented) lines specified by the user.
      datlines contains the full data path to every
      raw exposure provided by the user.

    Returns
    -------
    fitstbl : Table
      The relevant header information of all fits files
    """
    # FITS dict/table keys
    head_keys = spectrograph.header_keys()
    all_keys = []
    for key in head_keys.keys():
        all_keys += list(head_keys[key].keys())
    # Init
    fitsdict = dict({'directory': [], 'filename': [], 'utc': []})
    headdict = {}
    for k in range(spectrograph.numhead):
        headdict[k] = []
    whddict = dict({})
    for k in all_keys:
        fitsdict[k]=[]
    numfiles = len(datlines)
    # Loop on files
    for i in range(numfiles):
        # Try to open the fits file
        headarr = spectrograph.get_headarr(datlines[i], strict=strict)
        numhead = len(headarr)
        # Save the headers into its dict
        for k in range(numhead):
            headdict[k].append(headarr[k].copy())
        # Perform checks on each FITS file
        # TODO: The check_headers function currently always passes!
        # Needs to be implemented for each instrument.
        # spectrograph.check_headers() should raise an exception with an
        # appropriate message.
        try:
            spectrograph.check_headers(headarr)
        except:
            msgs.warn('File:' + msgs.newline() + datlines[i] + msgs.newline()
                      + ' does not match the expected header format of instrument:'
                      + msgs.newline() + '{0}'.format(spectrograph.spectrograph) + msgs.newline()
                      + 'The file should be removed or you should pick a different instrument.')
            numfiles -= 1
            continue
        # Now set the key values for each of the required keywords
        dspl = datlines[i].split('/')
        fitsdict['directory'].append('/'.join(dspl[:-1])+'/')
        fitsdict['filename'].append(dspl[-1])
        # Attempt to load a UTC
        utcfound = False
        for k in range(numhead):
            if 'UTC' in headarr[k].keys():
                utc = headarr[k]['UTC']
                utcfound = True
                break
            elif 'UT' in headarr[k].keys():
                utc = headarr[k]['UT']
                utcfound = True
                break
        if utcfound:
            fitsdict['utc'].append(utc)
        else:
            fitsdict['utc'].append('None') # Changed from None so it writes to disk
            msgs.warn("UTC is not listed as a header keyword in file:"+msgs.newline()+datlines[i])
        # Read binning-dependent detector properties here? (maybe read speed too)
        # Now get the rest of the keywords

        for head_idx in head_keys.keys():
            for kw, hkey in head_keys[head_idx].items():
                try:
                    value = headarr[head_idx][hkey]
                except KeyError: # Keyword not found in header
                    if kw == 'binning':
                        bin_x = None
                        bin_y = None
                        for kw_bin, hkey_bin in head_keys[head_idx].items():
                            if kw_bin == 'binning_x':
                                bin_x = headarr[head_idx][hkey_bin]
                            if kw_bin == 'binning_y':
                                bin_y = headarr[head_idx][hkey_bin]
                        if bin_x is not None and bin_y is not None:
                            value = "{},{}".format(bin_x,bin_y)
                            msgs.warn("{:s} keyword set from binning_x and binning_y.".format(hkey))
                        else:
                            value = str('None')
                            msgs.warn("{:s} keyword not in header. Setting to None".format(hkey))
                    else:
                        msgs.warn("{:s} keyword not in header. Setting to None".format(hkey))
                        value = str('None')
#                except IndexError:
#                    debugger.set_trace()
                # Convert the input time into hours -- Should we really do this here??
                if kw == 'time':
                    if spectrograph.timeunit == 's'  : value = float(value)/3600.0    # Convert seconds to hours
                    elif spectrograph.timeunit == 'm'  : value = float(value)/60.0      # Convert minutes to hours
                    elif spectrograph.timeunit in Time.FORMATS.keys() : # Astropy time format
                        if spectrograph.timeunit in ['mjd']:
                            ival = float(value)
                        else:
                            ival = value
                        tval = Time(ival, scale='tt', format=spectrograph.timeunit)
                        # dspT = value.split('T')
                        # dy,dm,dd = np.array(dspT[0].split('-')).astype(np.int)
                        # th,tm,ts = np.array(dspT[1].split(':')).astype(np.float64)
                        # r=(14-dm)/12
                        # s,t=dy+4800-r,dm+12*r-3
                        # jdn = dd + (153*t+2)/5 + 365*s + s/4 - 32083
                        # value = jdn + (12.-th)/24 + tm/1440 + ts/86400 - 2400000.5  # THIS IS THE MJD
                        value = tval.mjd * 24.0 # Put MJD in hours
                    else:
                        msgs.error('Bad time unit')
                # Put the value in the keyword
                typv = type(value)
                if typv is int or typv is np.int_:
                    fitsdict[kw].append(value)
                elif typv is float or typv is np.float_:
                    fitsdict[kw].append(value)
                elif isinstance(value, str) or typv is np.string_:
                    fitsdict[kw].append(value.strip())
                elif typv is bool or typv is np.bool_:
                    fitsdict[kw].append(value)
                else:
                    msgs.bug("I didn't expect a useful header ({0:s}) to contain type {1:s}".format(kw, typv).replace('<type ','').replace('>',''))
        msgs.info("Successfully loaded headers for file:" + msgs.newline() + datlines[i])

    # Check if any other settings require header values to be loaded
    msgs.info("Checking spectrograph settings for required header information")
    '''  # I HOPE THIS IS NO LONGER NEEDED
    # Just use the header info from the last file
    keylst = []
    generate_updates(settings_spect.copy(), keylst, [], whddict, headarr)
    '''

    # Convert the fitsdict arrays into numpy arrays
    for k in fitsdict.keys():
        fitsdict[k] = np.array(fitsdict[k])
    #
    msgs.info("Headers loaded for {0:d} files successfully".format(numfiles))
    if numfiles != len(datlines):
        msgs.warn("Headers were not loaded for {0:d} files".format(len(datlines) - numfiles))
    if numfiles == 0:
        msgs.error("The headers could not be read from the input data files." + msgs.newline() +
                   "Please check that the settings file matches the data.")
    #  Might have to carry the headers around separately
    #    as packing them into a table could be problematic..
    #for key in headdict.keys():
    #    fitsdict['head{:d}'.format(key)] = headdict[key]
    # Return after creating a Table
    fitstbl = Table(fitsdict)
    fitstbl.sort('time')

    # Add instrument (PYPIT name; mainly for saving late in the game)
    fitstbl['instrume'] = spectrograph.spectrograph

    # Instrument specific
    spectrograph.add_to_fitstbl(fitstbl)

    # Return
    return fitstbl


def load_extraction(name, frametype='<None>', wave=True):
    msgs.info("Loading a pre-existing {0:s} extraction frame:".format(frametype)+msgs.newline()+name)
    props_savas = dict({"ORDWN":"ordwnum"})
    props = dict({})
    props_allow = props_savas.keys()
    infile = fits.open(name)
    sciext = np.array(infile[0].data, dtype=np.float)
    sciwav = -999999.9*np.ones((sciext.shape[0],sciext.shape[1]))
    hdr = infile[0].header
    norders = hdr["NUMORDS"]
    pxsz    = hdr["PIXSIZE"]
    props = dict({})
    for o in range(norders):
        hdrname = "CDELT{0:03d}".format(o+1)
        cdelt = hdr[hdrname]
        hdrname = "CRVAL{0:03d}".format(o+1)
        crval = hdr[hdrname]
        hdrname = "CLINV{0:03d}".format(o+1)
        clinv = hdr[hdrname]
        hdrname = "CRPIX{0:03d}".format(o+1)
        crpix = hdr[hdrname]
        hdrname = "CNPIX{0:03d}".format(o+1)
        cnpix = hdr[hdrname]
        sciwav[:cnpix,o] = 10.0**(crval + cdelt*(np.arange(cnpix)-crpix))
        #sciwav[:cnpix,o] = clinv * 10.0**(cdelt*(np.arange(cnpix)-crpix))
        #sciwav[:cnpix,o] = clinv * (1.0 + pxsz/299792.458)**np.arange(cnpix)
    for k in props_allow:
        prsav = np.zeros(norders)
        try:
            for o in range(norders):
                hdrname = "{0:s}{1:03d}".format(k,o+1)
                prsav[o] = hdr[hdrname]
            props[props_savas[k]] = prsav.copy()
        except:
            pass
    del infile, hdr, prsav
    if wave is True:
        return sciext, sciwav, props
    else:
        return sciext, props


def load_ordloc(fname):
    # Load the files
    mstrace_bname, mstrace_bext = os.path.splitext(fname)
    lname = mstrace_bname+"_ltrace"+mstrace_bext
    rname = mstrace_bname+"_rtrace"+mstrace_bext
    # Load the order locations
    ltrace = np.array(fits.getdata(lname, 0),dtype=np.float)
    msgs.info("Loaded left order locations for frame:"+msgs.newline()+fname)
    rtrace = np.array(fits.getdata(rname, 0),dtype=np.float)
    msgs.info("Loaded right order locations for frame:"+msgs.newline()+fname)
    return ltrace, rtrace


def load_specobj(fname):
    """ Load a spec1d file into a list of SpecObjExp objects
    Parameters
    ----------
    fname : str

    Returns
    -------
    specObjs : list of SpecObjExp
    head0
    """
    speckeys = ['WAVE', 'SKY', 'MASK', 'FLAM', 'FLAM_IVAR', 'FLAM_SIG', 'COUNTS_IVAR', 'COUNTS']
    #
    specObjs = []
    hdulist = fits.open(fname)
    head0 = hdulist[0].header
    for hdu in hdulist:
        if hdu.name == 'PRIMARY':
            continue
        # Parse name
        idx = hdu.name
        objp = idx.split('-')
        if objp[-2][0:3] == 'DET':
            det = int(objp[-2][3:])
        else:
            det = int(objp[-2][1:])
        # Load data
        spec = Table(hdu.data)
        shape = (len(spec), 1024)  # 2nd number is dummy
        # Init
        #specobj = specobjs.SpecObj(shape, 'dum_config', int(objp[-1][1:]),
        #                           int(objp[-2][1:]), [float(objp[1][1:])/10000.]*2, 0.5,
        #                           float(objp[0][1:])/1000., 'unknown')
        # New and wrong
        try:
            specobj = specobjs.SpecObj(shape, None, None, idx = idx)
        except:
            debugger.set_trace()
            msgs.error("BUG ME")
        # TODO -- Figure out if this is a default
        # Add trace
        try:
            specobj.trace = spec['TRACE']
        except:
            # KLUDGE!
            specobj.trace = np.arange(len(spec['BOX_WAVE']))
        # Add spectrum
        if 'BOX_COUNTS' in spec.keys():
            for skey in speckeys:
                try:
                    specobj.boxcar[skey] = spec['BOX_{:s}'.format(skey)].data
                except KeyError:
                    pass
            # Add units on wave
            specobj.boxcar['WAVE'] = specobj.boxcar['WAVE'] * units.AA

        if 'OPT_COUNTS' in spec.keys():
            for skey in speckeys:
                try:
                    specobj.optimal[skey] = spec['OPT_{:s}'.format(skey)].data
                except KeyError:
                    pass
            # Add units on wave
            specobj.optimal['WAVE'] = specobj.optimal['WAVE'] * units.AA
        # Append
        specObjs.append(specobj)
    # Return
    return specObjs, head0


def load_tilts(fname):
    # Load the files
    msarc_bname, msarc_bext = os.path.splitext(fname)
    tname = msarc_bname+"_tilts"+msarc_bext
    sname = msarc_bname+"_satmask"+msarc_bext
    # Load the order locations
    tilts = np.array(fits.getdata(tname, 0),dtype=np.float)
    msgs.info("Loaded order tilts for frame:"+msgs.newline()+fname)
    satmask = np.array(fits.getdata(sname, 0),dtype=np.float)
    msgs.info("Loaded saturation mask for frame:"+msgs.newline()+fname)
    return tilts, satmask


def load_1dspec(fname, exten=None, extract='OPT', objname=None, flux=False):
    """
    Parameters
    ----------
    fname : str
      Name of the file
    exten : int, optional
      Extension of the spectrum
      If not given, all spectra in the file are loaded
    extract : str, optional
      Extraction type ('opt', 'box')
    objname : str, optional
      Identify extension based on input object name
    flux : bool, optional
      Return fluxed spectra?

    Returns
    -------
    spec : XSpectrum1D

    """
    # Keywords for Table
    rsp_kwargs = {}
    rsp_kwargs['wave_tag'] = '{:s}_WAVE'.format(extract)
    if flux:
        rsp_kwargs['flux_tag'] = '{:s}_FLAM'.format(extract)
        rsp_kwargs['sig_tag'] = '{:s}_FLAM_SIG'.format(extract)
    else:
        rsp_kwargs['flux_tag'] = '{:s}_COUNTS'.format(extract)
        rsp_kwargs['sig_tag'] = '{:s}_COUNTS_SIG'.format(extract)

    # Identify extension from objname?
    if objname is not None:
        hdulist = fits.open(fname)
        hdu_names = [hdu.name for hdu in hdulist]
        exten = hdu_names.index(objname)
        if exten < 0:
            msgs.error("Bad input object name: {:s}".format(objname))

    # Load
    spec = XSpectrum1D.from_file(fname, exten=exten, **rsp_kwargs)
    # Return
    return spec

def waveids(fname):
    infile = fits.open(fname)
    pixels=[]
    msgs.info("Loading fitted arc lines")
    try:
        o = 1
        while True:
            pixels.append(infile[o].data.astype(np.float))
            o+=1
    except:
        pass
    return pixels
