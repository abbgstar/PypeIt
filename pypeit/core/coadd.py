""" Class for coaddition
"""
from __future__ import absolute_import, division, print_function

import numpy as np
from numpy.ma.core import MaskedArray
import scipy.stats
from  scipy.signal import medfilt

from matplotlib import pyplot as plt
from matplotlib import gridspec
from matplotlib.backends.backend_pdf import PdfPages

import astropy.stats
from astropy import units

from linetools.spectra.xspectrum1d import XSpectrum1D
from linetools.spectra.utils import collate

from pypeit import msgs
from pypeit.core import load
from pypeit import utils
from pypeit import debugger

# TODO
    # Shift spectra
    # Scale by poly
    # Better rejection
    # Grow mask in final_rej?


def new_wave_grid(waves, wave_method='iref', iref=0, A_pix=None, v_pix=None, **kwargs):
    """ Create a new wavelength grid for the
    spectra to be rebinned and coadded on

    Parameters
    ----------
    waves : masked ndarray
        Set of N original wavelength arrays
        Nspec, Npix
    wave_method : str, optional
        Desired method for creating new wavelength grid.
        'iref' -- Use the first wavelength array (default)
        'velocity' -- Constant velocity
        'pixel' -- Constant pixel grid
        'concatenate' -- Meld the input wavelength arrays
    iref : int, optional
      Reference spectrum
    A_pix : float
      Pixel size in same units as input wavelength array (e.g. Angstroms)
    v_pix : float
      Pixel size in km/s for velocity method
      If not input, the median km/s per pixel is calculated and used

    Returns
    -------
    wave_grid : ndarray
        New wavelength grid, not masked
    """
    # Eventually add/change this to also take in slf, which has
    # slf._argflag['reduce']['pixelsize'] = 2.5?? This won't work
    # if running coadding outside of PYPIT, which we'd like as an
    # option!
    if not isinstance(waves, MaskedArray):
        waves = np.ma.array(waves)

    if wave_method == 'velocity':  # Constant km/s
        # Find the median velocity of a pixel in the input
        # wavelength grid

        spl = 299792.458
        if v_pix is None:
            dv = spl * np.abs(waves - np.roll(waves,1)) / waves   # km/s
            v_pix = np.median(dv)

        # Generate wavelenth array
        wave_grid_min = np.min(waves)
        wave_grid_max = np.max(waves)
        x = np.log10(v_pix/spl + 1)
        npix = int(np.log10(wave_grid_max/wave_grid_min) / x) + 1
        wave_grid = wave_grid_min * 10**(x*np.arange(npix))

        #while max(wave_grid) <= wave_grid_max:
        #    # How do we determine a reasonable constant velocity? (the 100. here is arbitrary)
        #    step = wave_grid[count] * (100. / 299792.458)
        #    wave_grid.append(wave_grid[count] + step)
        #    count += 1

#        wave_grid = np.asarray(wave_grid)

    elif wave_method == 'pixel': # Constant Angstrom
        if A_pix is None:
            msgs.error("Need to provide pixel size with A_pix for with this method")
        #
        wave_grid_min = np.min(waves)
        wave_grid_max = np.max(waves)

        wave_grid = np.arange(wave_grid_min, wave_grid_max + A_pix, A_pix)

    elif wave_method == 'concatenate':  # Concatenate
        # Setup
        loglam = np.log10(waves) # This deals with padding (0's) just fine, i.e. they get masked..
        nspec = waves.shape[0]
        newloglam = loglam[iref, :].compressed()  # Deals with mask
        # Loop
        for j in range(nspec):
            if j == iref:
                continue
            #
            iloglam = loglam[j,:].compressed()
            dloglam_0 = (newloglam[1]-newloglam[0])
            dloglam_n =  (newloglam[-1] - newloglam[-2]) # Assumes sorted
            if (newloglam[0] - iloglam[0]) > dloglam_0:
                kmin = np.argmin(np.abs(iloglam - newloglam[0] - dloglam_0))
                newloglam = np.concatenate([iloglam[:kmin], newloglam])
            #
            if (iloglam[-1] - newloglam[-1]) > dloglam_n:
                kmin = np.argmin(np.abs(iloglam - newloglam[-1] - dloglam_n))
                newloglam = np.concatenate([newloglam, iloglam[kmin:]])
        # Finish
        wave_grid = 10**newloglam
    elif wave_method == 'iref':  # Concatenate
        wave_grid = waves[iref, :].compressed()
    else:
        msgs.error("Bad method for scaling: {:s}".format(wave_method))
    # Concatenate of any wavelengths in other indices that may extend beyond that of wavelengths[0]?

    return wave_grid


def gauss1(x, parameters):
    """ Simple Gaussian
    Parameters
    ----------
    x : ndarray
    parameters : ??

    Returns
    -------

    """
    sz = x.shape[0]
    
    if sz+1 == 5:
        smax = float(26)
    else:
        smax = 13.
    
    if len(parameters) >= 3:
        norm = parameters[2]
    else:
        norm = 1.
        
    u = ( (x - parameters[0]) / max(np.abs(parameters[1]), 1e-20) )**2.
    
    x_mask = np.where(u < smax**2)[0]
    norm = norm / (np.sqrt(2. * np.pi)*parameters[1])
                   
    return norm * x_mask * np.exp(-0.5 * u * x_mask)

def unpack_spec(spectra, all_wave=False):
    """ Unpack the spectra.  Default is to give only one wavelength array

    Parameters
    ----------
    spectra
    all_wave : bool, optional
      Return all the wavelength arrays

    Returns
    -------
    fluxes : ndarray (nspec, npix)
      Any masked values (there should be none) are set to 0.
    sigs : ndarray (nspec, npix)
    wave : ndarray (npix)

    """
    fluxes = spectra.data['flux'].filled(0.)
    sigs = spectra.data['sig'].filled(0.)
    if all_wave:
        wave = spectra.data['wave'].filled(0.)
    else:
        wave = np.array(spectra.data['wave'][0,:])

    # Return
    return fluxes, sigs, wave


def sn_weight(spectra, smask, debug=False):
    """ Calculate the S/N of each input spectrum and
    create an array of weights by which to weight the
    spectra by in coadding.

    Parameters
    ----------
    spectra : XSpectrum1D
        New wavelength grid
    smask : ndarray
        Bool mask of spectra

    Returns
    -------
    sn2 : array
        Mean S/N^2 value for each input spectra
    weights : ndarray
        Weights to be applied to the spectra
    """
    # Setup
    fluxes, sigs, wave = unpack_spec(spectra)
    # Mask locally
    fluxes = np.ma.array(fluxes, mask=smask)
    sigs = np.ma.array(sigs, mask=smask)

    # Calculate
    sn_val = fluxes*(1./sigs)  # Taking flux**2 biases negative values
    sn_sigclip = astropy.stats.sigma_clip(sn_val, sigma=3, iters=5)
    sn = np.mean(sn_sigclip, axis=1).compressed()
    sn2 = sn**2 #S/N^2 value for each spectrum

    rms_sn = np.sqrt(np.mean(sn2)) # Root Mean S/N**2 value for all spectra

    if rms_sn <= 4.0:
        msgs.info("Using constant weights for coadding, RMS S/N = {:g}".format(rms_sn))
        weights = np.ma.outer(np.asarray(sn2), np.ones(fluxes.shape[1]))
    else:
        msgs.info("Using wavelength dependent weights for coadding")
        msgs.warn("If your spectra have very different dispersion, this is *not* accurate")
        sn_med1 = np.ones_like(fluxes) #((fluxes.shape[0], fluxes.shape[1]))
        weights = np.ones_like(fluxes) #((fluxes.shape[0], fluxes.shape[1]))

        bkspace = (10000.0/3.0e5) / (np.log(10.0))
        med_width = wave.shape[0] / ((np.max(wave) - np.min(wave)) / bkspace)
        sig_res = max(med_width, 3)
        nhalf = int(sig_res) * 4
        xkern = np.arange(0, 2*nhalf+2, dtype='float64')-nhalf

        for spec in range(fluxes.shape[0]):
            sn_med1[spec] = medfilt(sn_val[spec], kernel_size = 3)
        
        yvals = gauss1(xkern, [0.0, sig_res, 1, 0])

        for spec in range(fluxes.shape[0]):
            weights[spec] = scipy.ndimage.filters.convolve(sn_med1[spec], yvals)**2

    # Give weights the same mask
    weights.mask = smask
    # and then fill with zeros
    weights = weights.filled(0.)

    # Finish
    return sn2, weights


def grow_mask(initial_mask, n_grow=1):
    """ Grows sigma-clipped mask by n_grow pixels on each side

    Parameters
    ----------
    initial_mask : ndarray
        Initial mask for the flux + variance arrays
    n_grow : int, optional
        Number of pixels to grow the initial mask by
        on each side. Defaults to 1 pixel

    Returns
    -------
    grow_mask : ndarray
        Final mask for the flux + variance arrays
    """
    if not isinstance(n_grow, int):
        msgs.error("n_grow must be an integer")
    # Init
    grow_mask = np.ma.copy(initial_mask)
    npix = grow_mask.size

    # Loop on spectra
    bad_pix = np.where(initial_mask)[0]
    for idx in bad_pix:
        msk_p = idx + np.arange(-1*n_grow, n_grow+1)
        # Restrict
        gdp = (msk_p >= 0) & (msk_p < npix)
        # Apply
        grow_mask[msk_p[gdp]] = True
    # Return
    return grow_mask


def median_ratio_flux(spec, smask, ispec, iref, nsig=3., niter=5, **kwargs):
    """ Calculate the median ratio between two spectra
    Parameters
    ----------
    spec
    smask
    ispec
    iref
    nsig
    niter
    kwargs

    Returns
    -------
    med_scale : float
      Median of reference spectrum to input spectrum
    """
    # Setup
    fluxes, sigs, wave = unpack_spec(spec)
    # Mask
    okm = ~smask[iref,:] & ~smask[ispec,:]
    # Insist on positive values
    okf = (fluxes[iref,:] > 0.) & (fluxes[ispec,:] > 0)
    allok = okm & okf
    # Ratio
    med_flux = fluxes[iref,allok] / fluxes[ispec,allok]
    # Clip
    mn_scale, med_scale, std_scale = astropy.stats.sigma_clipped_stats(med_flux, sigma=nsig, iters=niter, **kwargs)
    # Return
    return med_scale


'''
def median_flux(spec, smask, nsig=3., niter=5, **kwargs):
    """ Calculate the characteristic, median flux of a spectrum

    Parameters
    ----------
    spec : XSpectrum1D
    mask : ndarray, optional
      Additional input mask with True = masked
      This needs to have the same size as the masked spectrum
    nsig : float, optional
      Clip sigma
    niter : int, optional
      Number of clipping iterations
    **kwargs : optional
      Passed to each call of sigma_clipped_stats

    Returns
    -------
    med_spec, std_spec
    """
    debugger.set_trace()   # This routine is not so useful
    # Setup
    fluxes, sigs, wave = unpack_spec(spec)
    # Mask locally
    mfluxes = np.ma.array(fluxes, mask=smask)
    #goodpix = WHERE(refivar GT 0.0 AND finite(refflux) AND finite(refivar) $
    #            AND refmask EQ 1 AND refivar LT 1.0d8)
    mean_spec, med_spec, std_spec = astropy.stats.sigma_clipped_stats(mfluxes, sigma=nsig, iters=niter, **kwargs)
    # Clip a bit
    #badpix = np.any([spec.flux.value < 0.5*np.abs(med_spec)])
    badpix = mfluxes.filled(0.) < 0.5*np.abs(med_spec)
    mean_spec, med_spec, std_spec = astropy.stats.sigma_clipped_stats(mfluxes.filled(0.), mask=badpix,
                                                        sigma=nsig, iters=niter, **kwargs)
    debugger.set_trace()
    # Return
    return med_spec, std_spec

'''

def scale_spectra(spectra, smask, sn2, iref=0, scale_method='auto', hand_scale=None,
                  SN_MAX_MEDSCALE=2., SN_MIN_MEDSCALE=0.5, **kwargs):
    """
    Parameters
    ----------
    spectra : XSpectrum1D
      Rebinned spectra
      These should be registered, i.e. pixel 0 has the same wavelength for all
    sn2 : ndarray
      S/N**2 estimates for each spectrum
    iref : int, optional
      Index of reference spectrum
    scale_method : str, optional
      Method for scaling
       'auto' -- Use automatic method based on RMS of S/N
       'hand' -- Use input scale factors
       'median' -- Use calcualted median value
    SN_MIN_MEDSCALE : float, optional
      Maximum RMS S/N allowed to automatically apply median scaling
    SN_MAX_MEDSCALE : float, optional
      Maximum RMS S/N allowed to automatically apply median scaling

    Returns
    -------
    scales : list of float or ndarray
      Scale value (or arrays) that was applied to the data
    omethod : str
      Method applied (mainly useful if auto was adopted)
       'hand'
       'median'
       'none_SN'
    """
    # Init
    med_ref = None
    rms_sn = np.sqrt(np.mean(sn2)) # Root Mean S/N**2 value for all spectra
    # Check for wavelength registration
    #gdp = np.all(~spectra.data['flux'].mask, axis=0)
    #gidx = np.where(gdp)[0]
    #if not np.isclose(spectra.data['wave'][0,gidx[0]],spectra.data['wave'][1,gidx[0]]):
    #    msgs.error("Input spectra are not registered!")
    # Loop on exposures
    scales = []
    for qq in range(spectra.nspec):
        if scale_method == 'hand':
            omethod = 'hand'
            # Input?
            if hand_scale is None:
                msgs.error("Need to provide hand_scale parameter, one value per spectrum")
            spectra.data['flux'][qq,:] *= hand_scale[qq]
            spectra.data['sig'][qq,:] *= hand_scale[qq]
            #arrsky[*, j] = HAND_SCALE[j]*sclsky[*, j]
            scales.append(hand_scale[qq])
            #
        elif ((rms_sn <= SN_MAX_MEDSCALE) and (rms_sn > SN_MIN_MEDSCALE)) or scale_method=='median':
            omethod = 'median_flux'
            if qq == iref:
                scales.append(1.)
                continue
            # Median ratio (reference to spectrum)
            med_scale = median_ratio_flux(spectra, smask, qq, iref)
            # Apply
            med_scale= np.minimum(med_scale, 10.0)
            spectra.data['flux'][qq,:] *= med_scale
            spectra.data['sig'][qq,:] *= med_scale
            #
            scales.append(med_scale)
        elif rms_sn <= SN_MIN_MEDSCALE:
            omethod = 'none_SN'
        elif (rms_sn > SN_MAX_MEDSCALE) or scale_method=='poly':
            msgs.work("Should be using poly here, not median")
            omethod = 'median_flux'
            if qq == iref:
                scales.append(1.)
                continue
            # Median ratio (reference to spectrum)
            med_scale = median_ratio_flux(spectra, smask, qq, iref)
            # Apply
            med_scale= np.minimum(med_scale, 10.0)
            spectra.data['flux'][qq,:] *= med_scale
            spectra.data['sig'][qq,:] *= med_scale
            #
            scales.append(med_scale)
        else:
            msgs.error("Scale method not recognized! Check documentation for available options")
    # Finish
    return scales, omethod


def bspline_cr(spectra, n_grow_mask=1, cr_nsig=5., debug=False):
    """ Experimental and not so successful..

    Parameters
    ----------
    spectra
    n_grow_mask
    cr_nsig

    Returns
    -------

    """
    # Unpack
    fluxes, sigs, wave = unpack_spec(spectra, all_wave=True)

    # Concatenate
    all_f = fluxes.flatten()
    all_s = sigs.flatten()
    all_w = wave.flatten()

    # Sort
    srt = np.argsort(all_w)

    # Bad pix
    goodp = all_s[srt] > 0.

    # Fit
    mask, bspl = utils.robust_polyfit(all_w[srt][goodp], all_f[srt][goodp], 3,
                                        function='bspline', sigma=cr_nsig, everyn=2*spectra.nspec,
                                        weights=1./np.sqrt(all_s[srt][goodp]), maxone=False)
    # Plot?
    if debug:
        from matplotlib import pyplot as plt
        plt.clf()
        ax = plt.gca()
        ax.scatter(all_w[srt][goodp], all_f[srt][goodp], color='k')
        #
        x = np.linspace(np.min(all_w), np.max(all_w), 30000)
        y = utils.func_val(bspl, x, 'bspline')
        ax.plot(x,y)
        # Masked
        ax.scatter(all_w[srt][goodp][mask==1], all_f[srt][goodp][mask==1], color='r')
        # Range
        stdf = np.std(all_f[srt][goodp])
        ax.set_ylim(-2*stdf, 3*stdf)
        plt.show()
        debugger.set_trace()


def clean_cr(spectra, smask, n_grow_mask=1, cr_nsig=7., nrej_low=5.,
    debug=False, cr_everyn=6, cr_bsigma=5., cr_two_alg='bspline', **kwargs):
    """ Sigma-clips the flux arrays to remove obvious CR

    Parameters
    ----------
    spectra :
    smask : ndarray
      Data mask
    n_grow_mask : int, optional
        Number of pixels to grow the initial mask by
        on each side. Defaults to 1 pixel
    cr_nsig : float, optional
      Number of sigma for rejection for CRs

    Returns
    -------
    """
    # Init
    fluxes, sigs, wave = unpack_spec(spectra)
    npix = wave.size

    def rej_bad(smask, badchi, n_grow_mask, ispec):
        # Grow?
        if n_grow_mask > 0:
            badchi = grow_mask(badchi, n_grow=n_grow_mask)
        # Mask
        smask[ispec,badchi] = True
        msgs.info("Rejecting {:d} CRs in exposure {:d}".format(np.sum(badchi),ispec))
        return

    if spectra.nspec == 2:
        msgs.info("Only 2 exposures.  Using custom procedure")
        if cr_two_alg == 'diff':
            diff = fluxes[0,:] - fluxes[1,:]
            # Robust mean/median
            med, mad = utils.robust_meanstd(diff)
            # Spec0?
            cr0 = (diff-med) > cr_nsig*mad
            if n_grow_mask > 0:
                cr0 = grow_mask(cr0, n_grow=n_grow_mask)
            msgs.info("Rejecting {:d} CRs in exposure 0".format(np.sum(cr0)))
            smask[0,cr0] = True
            if debug:
                debugger.plot1d(wave, fluxes[0,:], xtwo=wave[cr0], ytwo=fluxes[0,cr0], mtwo='s')
            # Spec1?
            cr1 = (-1*(diff-med)) > cr_nsig*mad
            if n_grow_mask > 0:
                cr1 = grow_mask(cr1, n_grow=n_grow_mask)
            smask[1,cr1] = True
            if debug:
                debugger.plot1d(wave, fluxes[1,:], xtwo=wave[cr1], ytwo=fluxes[1,cr1], mtwo='s')
            msgs.info("Rejecting {:d} CRs in exposure 1".format(np.sum(cr1)))
        elif cr_two_alg == 'ratio':
            diff = fluxes[0,:] - fluxes[1,:]
            rtio = fluxes[0,:] / fluxes[1,:]
            # Robust mean/median
            rmed, rmad = utils.robust_meanstd(rtio)
            dmed, dmad = utils.robust_meanstd(diff)
            # Spec0?            med, mad = utils.robust_meanstd(diff)
            cr0 = ((rtio-rmed) > cr_nsig*rmad) & ((diff-dmed) > cr_nsig*dmad)
            if n_grow_mask > 0:
                cr0 = grow_mask(cr0, n_grow=n_grow_mask)
            msgs.info("Rejecting {:d} CRs in exposure 0".format(np.sum(cr0)))
            smask[0,cr0] = True
            if debug:
                debugger.plot1d(wave, fluxes[0,:], xtwo=wave[cr0], ytwo=fluxes[0,cr0], mtwo='s')
            # Spec1?
            cr1 = (-1*(rtio-rmed) > cr_nsig*rmad) & (-1*(diff-dmed) > cr_nsig*dmad)
            if n_grow_mask > 0:
                cr1 = grow_mask(cr1, n_grow=n_grow_mask)
            smask[1,cr1] = True
            if debug:
                debugger.plot1d(wave, fluxes[1,:], xtwo=wave[cr1], ytwo=fluxes[1,cr1], mtwo='s')
            msgs.info("Rejecting {:d} CRs in exposure 1".format(np.sum(cr1)))
        elif cr_two_alg == 'bspline':
            # Package Data for convenience
            waves = spectra.data['wave'].flatten()  # Packed 0,1
            flux = fluxes.flatten()
            sig = sigs.flatten()
            #
            gd = np.where(sig > 0.)[0]
            srt = np.argsort(waves[gd])
            idx = gd[srt]
            # The following may eliminate bright, narrow emission lines
            mask, spl = utils.robust_polyfit(waves[idx], flux[idx], 3, function='bspline',
                    weights=1./sig[gd][srt], sigma=cr_bsigma, maxone=False, everyn=cr_everyn)
            # Reject CR (with grow)
            spec_fit = utils.func_val(spl, wave, 'bspline')
            for ii in range(2):
                diff = fluxes[ii,:] - spec_fit
                cr = (diff > cr_nsig*sigs[ii,:]) & (sigs[ii,:]>0.)
                if debug:
                    debugger.plot1d(spectra.data['wave'][0,:], spectra.data['flux'][ii,:], spec_fit, xtwo=spectra.data['wave'][0,cr], ytwo=spectra.data['flux'][ii,cr], mtwo='s')
                if n_grow_mask > 0:
                    cr = grow_mask(cr, n_grow=n_grow_mask)
                # Mask
                smask[ii,cr] = True
                msgs.info("Cleaning {:d} CRs in exposure {:d}".format(np.sum(cr),ii))
            # Reject Low
            if nrej_low > 0.:
                for ii in range(2):
                    diff = spec_fit - fluxes[ii,:]
                    rej_low = (diff > nrej_low*sigs[ii,:]) & (sigs[ii,:]>0.)
                    if False:
                        debugger.plot1d(spectra.data['wave'][0,:], spectra.data['flux'][ii,:], spec_fit, xtwo=spectra.data['wave'][0,rej_low], ytwo=spectra.data['flux'][ii,rej_low], mtwo='s')
                    msgs.info("Removing {:d} low values in exposure {:d}".format(np.sum(rej_low),ii))
                    smask[ii,rej_low] = True
            else:
                msgs.error("Bad algorithm for combining two spectra!")
        # Check
        if debug:
            gd0 = ~smask[0,:]
            gd1 = ~smask[1,:]
            debugger.plot1d(wave[gd0], fluxes[0,gd0], xtwo=wave[gd1], ytwo=fluxes[1,gd1])
            debugger.set_trace()

    else:
        # Median of the masked array -- Best for 3 or more spectra
        mflux = np.ma.array(fluxes, mask=smask)
        refflux = np.ma.median(mflux,axis=0)
        diff = fluxes - refflux.filled(0.)

        # Loop on spectra
        for ispec in range(spectra.nspec):
            # Generate ivar
            gds = (~smask[ispec,:]) & (sigs[ispec,:] > 0.)
            ivar = np.zeros(npix)
            ivar[gds] = 1./sigs[ispec,gds]**2
            # Single pixel events
            chi2 = diff[ispec]**2 * ivar
            badchi = (ivar > 0.0) & (chi2 > cr_nsig**2)
            if np.any(badchi) > 0:
                rej_bad(smask, badchi, n_grow_mask, ispec)
            # Dual pixels [CRs usually affect 2 (or more) pixels]
            tchi2 = chi2 + np.roll(chi2,1)
            badchi = (ivar > 0.0) & (tchi2 > 2*cr_nsig**2)
            if np.any(badchi) > 0:
                rej_bad(smask, badchi, n_grow_mask, ispec)
    # Return
    return


def one_d_coadd(spectra, smask, weights, debug=False, **kwargs):
    """ Performs a weighted coadd of the spectra in 1D.

    Parameters
    ----------
    spectra : XSpectrum1D
    weights : ndarray
      Should be masked

    Returns
    -------
    coadd : XSpectrum1D

    """
    # Setup
    fluxes, sigs, wave = unpack_spec(spectra)
    variances = (sigs > 0.) * sigs**2
    inv_variances = (sigs > 0.)/(sigs**2 + (sigs==0.))

    # Sum weights
    mweights = np.ma.array(weights, mask=smask)
    sum_weights = np.ma.sum(mweights, axis=0).filled(0.)


    # Coadd
    new_flux = np.ma.sum(mweights*fluxes, axis=0) / (sum_weights + (sum_weights == 0.0).astype(int))
    var = (variances != 0.0).astype(float) / (inv_variances + (inv_variances == 0.0).astype(float))
    new_var = np.ma.sum((mweights**2.)*var, axis=0) / ((sum_weights + (sum_weights == 0.0).astype(int))**2.)

    # Replace masked values with zeros
    new_flux = new_flux.filled(0.)
    new_sig = np.sqrt(new_var.filled(0.))

    # New obj (for passing around)
    new_spec = XSpectrum1D.from_tuple((wave, new_flux, new_sig), masking='none')

    if False:
        debugger.plot1d(wave, new_flux, new_sig)
        debugger.set_trace()
    # Return
    return new_spec


def load_spec(files, iextensions=None, extract='OPT', flux=True):
    """ Load a list of spectra into one XSpectrum1D object

    Parameters
    ----------
    files : list
      List of filenames
    iextensions : int or list, optional
      List of extensions, 1 per filename
      or an int which is the extension in each file
    extract : str, optional
      Extraction method ('opt', 'box')
    flux : bool, optional
      Apply to fluxed spectra?

    Returns
    -------
    spectra : XSpectrum1D
      -- All spectra are collated in this one object
    """
    # Extensions
    if iextensions is None:
        msgs.warn("Extensions not provided.  Assuming first extension for all")
        extensions = np.ones(len(files), dtype='int8')
    elif isinstance(iextensions, int):
        extensions = np.ones(len(files), dtype='int8') * iextensions
    else:
        extensions = np.array(iextensions)

    # Load spectra
    spectra_list = []
    for ii, fname in enumerate(files):
        msgs.info("Loading extension {:d} of spectrum {:s}".format(extensions[ii], fname))
        spectrum = load.load_1dspec(fname, exten=extensions[ii], extract=extract, flux=flux)
        # Polish a bit -- Deal with NAN, inf, and *very* large values that will exceed
        #   the floating point precision of float32 for var which is sig**2 (i.e. 1e38)
        bad_flux = np.any([np.isnan(spectrum.flux), np.isinf(spectrum.flux),
                           np.abs(spectrum.flux) > 1e30,
                           spectrum.sig**2 > 1e10,
                           ], axis=0)
        if np.sum(bad_flux):
            msgs.warn("There are some bad flux values in this spectrum.  Will zero them out and mask them (not ideal)")
            spectrum.data['flux'][spectrum.select][bad_flux] = 0.
            spectrum.data['sig'][spectrum.select][bad_flux] = 0.
        # Append
        spectra_list.append(spectrum)
    # Join into one XSpectrum1D object
    spectra = collate(spectra_list)
    # Return
    return spectra


def get_std_dev(irspec, rmask, ispec1d, s2n_min=2., wvmnx=None, **kwargs):
    """
    Parameters
    ----------
    irspec : XSpectrum1D
      Array of spectra
    ispec1d : XSpectrum1D
      Coadded spectum
    rmask : ndarray
    s2n_min : float, optional
      Minimum S/N for calculating std_dev
    wvmnx : tuple, optional
      Limit analysis to a wavelength interval

    Returns
    -------
    std_dev : float
      Standard devitation in good pixels
      TODO : Should restrict to higher S/N pixels
    dev_sig: ndarray
      Deviate, relative to sigma
    """
    # Setup
    fluxes, sigs, wave = unpack_spec(irspec)
    iflux = ispec1d.data['flux'][0,:].filled(0.)
    isig = ispec1d.data['sig'][0,:].filled(0.)
    cmask = rmask.copy()  # Starting mask
    # Mask locally
    mfluxes = np.ma.array(fluxes, mask=rmask)
    msigs = np.ma.array(sigs, mask=rmask)
    #
    msgs.work("We should restrict this to high S/N regions in the spectrum")
    # Mask on S/N_min
    bad_s2n = np.where(mfluxes/msigs < s2n_min)
    cmask[bad_s2n] = True
    # Limit by wavelength?
    if wvmnx is not None:
        msgs.info("Restricting std_dev calculation to wavelengths {}".format(wvmnx))
        bad_wv = np.any([(wave < wvmnx[0]), (wave > wvmnx[1])], axis=0)
        cmask[bad_wv] = True
    # Only calculate on regions with 2 or more spectra
    sum_msk = np.sum(~cmask, axis=0)
    gdp = (sum_msk > 1) & (isig > 0.)
    if not np.any(gdp):
        msgs.warn("No pixels satisfying s2n_min in std_dev")
        return 1., None
    # Here we go
    dev_sig = (fluxes[:,gdp] - iflux[gdp]) / np.sqrt(sigs[:,gdp]**2 + isig[gdp]**2)
    std_dev = np.std(astropy.stats.sigma_clip(dev_sig, sigma=5, iters=2))
    return std_dev, dev_sig


def coadd_spectra(spectra, wave_grid_method='concatenate', niter=5,
                  scale_method='auto', do_offset=False, sigrej_final=3.,
                  do_var_corr=True, qafile=None, outfile=None,
                  do_cr=True, **kwargs):
    """
    Parameters
    ----------
    spectra : XSpectrum1D
    wave_grid_method :

    Returns
    -------
    spec1d : XSpectrum1D

    """
    # Init
    if niter <= 0:
        msgs.error('Not prepared for zero iterations')

    # Single spectrum?
    if spectra.nspec == 1:
        msgs.info('Only one spectrum.  Writing, as desired, and ending..')
        if outfile is not None:
            write_to_disk(spectra, outfile)
        return spectra

    # Final wavelength array
    new_wave = new_wave_grid(spectra.data['wave'], wave_method=wave_grid_method, **kwargs)

    # Rebin
    rspec = spectra.rebin(new_wave*units.AA, all=True, do_sig=True, grow_bad_sig=True,
                          masking='none')

    # Define mask -- THIS IS THE ONLY ONE TO USE
    rmask = rspec.data['sig'].filled(0.) <= 0.

    # S/N**2, weights
    sn2, weights = sn_weight(rspec, rmask)

    # Scale (modifies rspec in place)
    scales, omethod = scale_spectra(rspec, rmask, sn2, scale_method=scale_method, **kwargs)

    # Clean bad CR :: Should be run *after* scaling
    if do_cr:
        clean_cr(rspec, rmask, **kwargs)

    # Initial coadd
    spec1d = one_d_coadd(rspec, rmask, weights)

    # Init standard deviation
    std_dev, _ = get_std_dev(rspec, rmask, spec1d, **kwargs)
    msgs.info("Initial std_dev = {:g}".format(std_dev))

    iters = 0
    std_dev = 0.
    var_corr = 1.

    # Scale the standard deviation
    while np.absolute(std_dev - 1.) >= 0.1 and iters < niter:
        iters += 1
        msgs.info("Iterating on coadding... iter={:d}".format(iters))

        # Setup (strip out masks, if any)
        tspec = spec1d.copy()
        tspec.unmask()
        newvar = tspec.data['sig'][0,:].filled(0.)**2  # JFH Interpolates over bad values?
        newflux = tspec.data['flux'][0,:].filled(0.)
        newflux_now = newflux  # JFH interpolates
        # Convenient for coadding
        uspec = rspec.copy()
        uspec.unmask()

        # Loop on images to update noise model for rejection
        for qq in range(rspec.nspec):

            # Grab full spectrum (unmasked)
            flux = uspec.data['flux'][qq,:].filled(0.)
            sig = uspec.data['sig'][qq,:].filled(0.)
            ivar = np.zeros_like(sig)
            gd = sig > 0.
            ivar[gd] = 1./sig[gd]**2

            # var_tot
            var_tot = newvar + utils.calc_ivar(ivar)
            ivar_real = utils.calc_ivar(var_tot)
            # smooth out possible outliers in noise
            var_med = medfilt(var_tot, 5)
            var_smooth = medfilt(var_tot, 99)#, boundary = 'reflect')
            # conservatively always take the largest variance
            var_final = np.maximum(var_med, var_smooth)
            ivar_final = utils.calc_ivar(var_final)
            # Cap S/N ratio at SN_MAX to prevent overly aggressive rejection
            SN_MAX = 20.0
            ivar_cap = np.minimum(ivar_final,
                                  (SN_MAX/newflux_now + (newflux_now <= 0.0))**2)
            #; adjust rejection to reflect the statistics of the distribtuion
            #; of errors. This fixes cases where for not totally understood
            #; reasons the noise model is not quite right and
            #; many pixels are rejected.

            #; Is the model offset relative to the data? If so take it out
            if do_offset:
                diff1 = flux-newflux_now
                #idum = np.where(arrmask[*, j] EQ 0, nnotmask)
                debugger.set_trace() # GET THE MASK RIGHT!
                nnotmask = np.sum(~mask)
                nmed_diff = np.maximum(nnotmask//20, 10)
                #; take out the smoothly varying piece
                #; JXP -- This isnt going to work well if the data has a bunch of
                #; null values in it
                w = np.ones(5, 'd')
                diff_sm = np.convolve(w/w.sum(),
                                      medfilt(diff1*(~mask), nmed_diff), mode='same')
                chi2 = (diff1-diff_sm)**2*ivar_real
#                debugger.set_trace()
                goodchi = (~mask) & (ivar_real > 0.0) & (chi2 <= 36.0) # AND masklam, ngd)
                if np.sum(goodchi) == 0:
                    goodchi = np.array([True]*flux.size)
#                debugger.set_trace()  # Port next line to Python to use this
                #djs_iterstat, (arrflux[goodchi, j]-newflux_now[goodchi]) $
                #   , invvar = ivar_real[goodchi], mean = offset_mean $
                #   , median = offset $
            else:
                offset = 0.
            chi2 = (flux-newflux_now - offset)**2*ivar_real
            goodchi = (~rmask[qq,:]) & (ivar_real > 0.0) & (chi2 <= 36.0) # AND masklam, ngd)
            ngd = np.sum(goodchi)
            if ngd == 0:
                goodchi = np.array([True]*flux.size)
            #; evalute statistics of chi2 for good pixels and excluding
            #; extreme 6-sigma outliers
            chi2_good = chi2[goodchi]
            chi2_srt = chi2_good.copy()
            chi2_srt.sort()
            #; evaluate at 1-sigma and then scale
            gauss_prob = 1.0 - 2.0*(1.-scipy.stats.norm.cdf(1.)) #gaussint(-double(1.0d))
            sigind = int(np.round(gauss_prob*ngd))
            chi2_sigrej = chi2_srt[sigind]
            one_sigma = np.minimum(np.maximum(np.sqrt(chi2_sigrej),1.0),5.0)
            sigrej_eff = sigrej_final*one_sigma
            chi2_cap = (flux-newflux_now - offset)**2*ivar_cap
            # Grow??
            chi_mask = (chi2_cap > sigrej_eff**2) & (~rmask[qq,:])
            nrej = np.sum(chi_mask)
            # Apply
            if nrej > 0:
                msgs.info("Rejecting {:d} pixels in exposure {:d}".format(nrej,qq))
                print(rspec.data['wave'][qq,chi_mask])
                rmask[qq,chi_mask] = True
                #rspec.select = qq
                #rspec.add_to_mask(chi_mask)
            #outmask[*, j] = (arrmask[*, j] EQ 1) OR (chi2_cap GT sigrej_eff^2)

        # Incorporate saving of each dev/sig panel onto one page? Currently only saves last fit
        #qa_plots(wavelengths, masked_fluxes, masked_vars, new_wave, new_flux, new_var)

        # Coadd anew
        spec1d = one_d_coadd(rspec, rmask, weights, **kwargs)
        # Calculate std_dev
        std_dev, _ = get_std_dev(rspec, rmask, spec1d, **kwargs)
        #var_corr = var_corr * std_dev
        msgs.info("Desired variance correction: {:g}".format(var_corr))
        msgs.info("New standard deviation: {:g}".format(std_dev))
        if do_var_corr:
            msgs.info("Correcting variance")
            for ispec in range(rspec.nspec):
                rspec.data['sig'][ispec] *= np.sqrt(std_dev)
            spec1d = one_d_coadd(rspec, rmask, weights)

    if iters == 0:
        msgs.warn("No iterations on coadding done")
        #qa_plots(wavelengths, masked_fluxes, masked_vars, new_wave, new_flux, new_var)
    else: #if iters > 0:
        msgs.info("Final correction to initial variances: {:g}".format(var_corr))

    # QA
    if qafile is not None:
        msgs.info("Writing QA file: {:s}".format(qafile))
        coaddspec_qa(spectra, rspec, rmask, spec1d, qafile=qafile)

    # Write to disk?
    if outfile is not None:
        write_to_disk(spec1d, outfile)
    return spec1d


def write_to_disk(spec1d, outfile):
    """ Small method to write file to disk
    """
    msgs.work("Need to include header info")
    if '.hdf5' in outfile:
        spec1d.write_to_hdf5(outfile)
    elif '.fits' in outfile:
        spec1d.write_to_fits(outfile)
    return



def coaddspec_qa(ispectra, rspec, rmask, spec1d, qafile=None, yscale=2.):
    """  QA plot for 1D coadd of spectra

    Parameters
    ----------
    ispectra : XSpectrum1D
      Multi-spectra object
    rspec : XSpectrum1D
      Rebinned spectra with updated variance
    spec1d : XSpectrum1D
      Final coadd
    yscale : float, optional
      Scale median flux by this parameter for the spectral plot

    """

    plt.rcdefaults()
    plt.rcParams['font.family']= 'times new roman'

    if qafile is not None:
        pp = PdfPages(qafile)

    plt.clf()
    plt.figure()
    gs = gridspec.GridSpec(1,2)

    # Deviate
    std_dev, dev_sig = get_std_dev(rspec, rmask, spec1d)
    #dev_sig = (rspec.data['flux'] - spec1d.flux) / (rspec.data['sig']**2 + spec1d.sig**2)
    #std_dev = np.std(sigma_clip(dev_sig, sigma=5, iters=2))
    if dev_sig is not None:
        flat_dev_sig = dev_sig.flatten()

    xmin = -10
    xmax = 10
    n_bins = 100

    # Deviation
    ax = plt.subplot(gs[0])
    if dev_sig is not None:
        hist, edges = np.histogram(flat_dev_sig, range=(xmin, xmax), bins=n_bins)
        area = len(flat_dev_sig)*((xmax-xmin)/float(n_bins))
        xppf = np.linspace(scipy.stats.norm.ppf(0.0001), scipy.stats.norm.ppf(0.9999), 100)
        ax.plot(xppf, area*scipy.stats.norm.pdf(xppf), color='black', linewidth=2.0)
        ax.bar(edges[:-1], hist, width=((xmax-xmin)/float(n_bins)), alpha=0.5)

    # Coadd on individual
    # yrange
    medf = np.median(spec1d.flux)
    ylim = (medf/10., yscale*medf)
    # Plot
    ax = plt.subplot(gs[1])
    for idx in range(ispectra.nspec):
        ispectra.select = idx
        ax.plot(ispectra.wavelength, ispectra.flux, alpha=0.5)#, label='individual exposure')

    ax.plot(spec1d.wavelength, spec1d.flux, color='black', label='coadded spectrum')
    ax.set_ylim(ylim)
    debug=False
    if debug:
        ax.set_ylim(0., 180.)
        ax.set_xlim(3840, 3860.)
    plt.legend()
    plt.title('Coadded + Original Spectra')

    plt.tight_layout(pad=0.2,h_pad=0.,w_pad=0.2)
    if qafile is not None:
        pp.savefig(bbox_inches='tight')
        pp.close()
        msgs.info("Wrote coadd QA: {:s}".format(qafile))
    plt.close()

    plt.rcdefaults()

    return




