""" Routine for Echelle coaddition
"""
import numpy as np
from astropy import stats
from astropy.io import fits
from astropy import units
import matplotlib.pyplot as plt

from pypeit.core import coadd
from pypeit.core import load
from pypeit import msgs

from linetools.spectra.utils import collate
from linetools.spectra.xspectrum1d import XSpectrum1D
from pkg_resources import resource_filename

## ToDo: change it to a CLASS and modify coadd_1dspec.py

# setting plot parameters
plt.rcdefaults()
plt.rcParams['font.family'] = 'times new roman'
plt.rcParams["xtick.top"] = True
plt.rcParams["ytick.right"] = True
plt.rcParams["xtick.minor.visible"] = True
plt.rcParams["ytick.minor.visible"] = True
plt.rcParams["ytick.direction"] = 'in'
plt.rcParams["xtick.direction"] = 'in'
plt.rcParams["xtick.labelsize"] = 17
plt.rcParams["ytick.labelsize"] = 17
plt.rcParams["axes.labelsize"] = 17

def spec_from_array(wave,flux,sig,**kwargs):
    """
    return spectrum from arrays of wave, flux and sigma
    """

    ituple = (wave, flux, sig)
    spectrum = XSpectrum1D.from_tuple(ituple, **kwargs)
    # Polish a bit -- Deal with NAN, inf, and *very* large values that will exceed
    #   the floating point precision of float32 for var which is sig**2 (i.e. 1e38)
    bad_flux = np.any([np.isnan(spectrum.flux), np.isinf(spectrum.flux),
                       np.abs(spectrum.flux) > 1e30,
                       spectrum.sig ** 2 > 1e10,
                       ], axis=0)
    if np.sum(bad_flux):
        msgs.warn("There are some bad flux values in this spectrum.  Will zero them out and mask them (not ideal)")
        spectrum.data['flux'][spectrum.select][bad_flux] = 0.
        spectrum.data['sig'][spectrum.select][bad_flux] = 0.
    return spectrum


def median_echelle_scale(spectra, smask, sn2, nsig=3.0, niter=5, SN_MIN_MEDSCALE=0.5, overlapfrac=0.03, debug=False):
    '''
    Scale different orders.
    ToDo: clean up the docs
    :param spectra:
    :param smask:
    :param sn2:
    :param nsig:
    :param niter:
    :param SN_MIN_MEDSCALE:
    :param overlapfrac:
    :param debug:
    :return:
    '''
    norder = spectra.nspec
    rms_sn = np.sqrt(np.mean(sn2))  # Root Mean S/N**2 value for all spectra
    fluxes, sigs, wave = coadd.unpack_spec(spectra, all_wave=False)
    fluxes_raw = fluxes.copy()

    # scaling spectrum order by order. We use the reddest order as the reference since slit loss in redder is smaller
    for i in range(norder - 1):
        iord = norder - i - 1
        sn_iord_iref = fluxes[iord] * (1. / sigs[iord])
        sn_iord_scale = fluxes[iord - 1] * (1. / sigs[iord - 1])
        allok = (sigs[iord - 1, :] > 0) & (sigs[iord, :] > 0) & (sn_iord_iref > SN_MIN_MEDSCALE) & (
        sn_iord_scale > SN_MIN_MEDSCALE)
        if sum(allok) > np.maximum(10., len(wave) * overlapfrac):
            # Ratio
            med_flux = spectra.data['flux'][iord, allok] / spectra.data['flux'][iord - 1, allok]
            # Clip
            mn_scale, med_scale, std_scale = stats.sigma_clipped_stats(med_flux, sigma=nsig, iters=niter)
            med_scale = np.minimum(med_scale, 5.0)
            ## testing
            #if iord == 4:
            #    med_scale = 1.0
            spectra.data['flux'][iord - 1, :] *= med_scale
            spectra.data['sig'][iord - 1, :] *= med_scale
            msgs.info('Scaled %s order by a factor of %s'%(iord,str(med_scale)))

            if debug:
                plt.plot(wave, spectra.data['flux'][iord], 'r-', label='reference spectrum')
                plt.plot(wave, fluxes_raw[iord - 1], 'k-', label='raw spectrum')
                plt.plot(spectra.data['wave'][iord - 1, :], spectra.data['flux'][iord - 1, :], 'b-',
                         label='scaled spectrum')
                mny, medy, stdy = stats.sigma_clipped_stats(fluxes[iord, allok], sigma=nsig, iters=niter)
                plt.ylim([0.1 * medy, 4.0 * medy])
                plt.xlim([np.min(wave[sigs[iord - 1, :] > 0]), np.max(wave[sigs[iord, :] > 0])])
                plt.legend()
                plt.xlabel('wavelength')
                plt.ylabel('Flux')
                plt.show()
        else:
            msgs.warn('Not enough overlap region for sticking different orders.')

def ech_coadd(files,objids=None,extract='OPT',flux=True,giantcoadd=False,
              wave_grid_method='velocity', niter=5,wave_grid_min=None, wave_grid_max=None,v_pix=None,
              scale_method='auto', do_offset=False, sigrej_final=3.,do_var_corr=False,
              qafile=None, outfile=None,do_cr=True, debug=False,**kwargs):
    """
    routines for coadding spectra observed with echelle spectrograph.
    parameters:
        files (list): file names
        objids (str): objid
        extract (str): 'OPT' or 'BOX'
        flux (bool): fluxed or not
        giantcoadd (bool): coadding order by order or do it at once?
        wave_grid_method (str): default velocity
        niter (int): number of iteration for rejections
        wave_grid_min (float): min wavelength, None means it will find the min value from your spectra
        wave_grid_max (float): max wavelength, None means it will find the max value from your spectra
        v_pix (float): delta velocity, see coadd.py
        scale_method (str): see coadd.py
        do_offset (str): see coadd.py, not implemented yet.
        sigrej_final (float): see coadd.py
        do_var_corr (bool): see coadd.py, default False. It seems True will results in a large error
        qafile (str): name of qafile
        outfile (str): name of coadded spectrum
        do_cr (bool): remove cosmic rays?
        debug (bool): show debug plots?
        kwargs: see coadd.py
    returns:
        spec1d: coadded XSpectrum1D
    """

    nfile = len(files)
    if nfile <=1:
        msgs.info('Only one spectrum exits coadding...')
        return

    fname = files[0]
    ext_final = fits.getheader(fname, -1)
    norder = ext_final['ECHORDER'] + 1
    msgs.info('spectrum {:s} has {:d} orders'.format(fname, norder))
    if norder <= 1:
        msgs.error('The number of orders have to be greater than one for echelle. Longslit data?')

    if giantcoadd:
        msgs.info('Coadding all orders and exposures at once')
        spectra = load.ech_load_spec(files, objid=objids,order=None, extract=extract, flux=flux)
        wave_grid = np.zeros((2,spectra.nspec))
        for i in range(spectra.nspec):
            wave_grid[0, i] = spectra[i].wvmin.value
            wave_grid[1, i] = spectra[i].wvmax.value
        ech_kwargs = {'echelle': True, 'wave_grid_min': np.min(wave_grid), 'wave_grid_max': np.max(wave_grid),
                      'v_pix': v_pix}
        kwargs.update(ech_kwargs)
        # Coadding
        spec1d = coadd.coadd_spectra(spectra, wave_grid_method=wave_grid_method, niter=niter,
                                          scale_method=scale_method, do_offset=do_offset, sigrej_final=sigrej_final,
                                          do_var_corr=do_var_corr, qafile=qafile, outfile=outfile,
                                          do_cr=do_cr, debug=debug,**kwargs)
    else:
        msgs.info('Coadding individual orders first and then merge order')
        spectra_list = []
        # Keywords for Table
        rsp_kwargs = {}
        rsp_kwargs['wave_tag'] = '{:s}_WAVE'.format(extract)
        rsp_kwargs['flux_tag'] = '{:s}_FLAM'.format(extract)
        rsp_kwargs['sig_tag'] = '{:s}_FLAM_SIG'.format(extract)
        #wave_grid = np.zeros((2,norder))
        for iord in range(norder):
            spectra = load.ech_load_spec(files, objid=objids, order=iord, extract=extract, flux=flux)
            ech_kwargs = {'echelle': False, 'wave_grid_min': spectra.wvmin.value, 'wave_grid_max': spectra.wvmax.value, 'v_pix': v_pix}
            #wave_grid[0,iord] = spectra.wvmin.value
            #wave_grid[1,iord] = spectra.wvmax.value
            kwargs.update(ech_kwargs)
            # Coadding the individual orders
            if qafile is not None:
                qafile_iord = qafile+'_%s'%str(iord)
            else:
                qafile_iord =  None
            spec1d_iord = coadd.coadd_spectra(spectra, wave_grid_method=wave_grid_method, niter=niter,
                                       scale_method=scale_method, do_offset=do_offset, sigrej_final=sigrej_final,
                                       do_var_corr=do_var_corr, qafile=qafile_iord, outfile=None,
                                       do_cr=do_cr, debug=debug, **kwargs)
            spectrum = spec_from_array(spec1d_iord.wavelength, spec1d_iord.flux, spec1d_iord.sig,**rsp_kwargs)
            spectra_list.append(spectrum)
        # Join into one XSpectrum1D object
        spectra_coadd = collate(spectra_list)

        ## merge orders
        # Final wavelength array
        kwargs['wave_grid_min'] = np.min(spectra_coadd.data['wave'][spectra_coadd.data['wave']>0])
        kwargs['wave_grid_max'] = np.max(spectra_coadd.data['wave'][spectra_coadd.data['wave']>0])
        wave_final = coadd.new_wave_grid(spectra_coadd.data['wave'], wave_method=wave_grid_method, **kwargs)
        # The rebin function in linetools can not work on collated spectra (i.e. filled 0).
        # Thus I have to rebin the spectra first and then collate again.
        spectra_list_new = []
        for i in range(spectra_coadd.nspec):
            speci = spectra_list[i].rebin(wave_final * units.AA, all=True, do_sig=True, grow_bad_sig=True,
                              masking='none')
            spectra_list_new.append(speci)
        spectra_coadd_rebin = collate(spectra_list_new)
        fluxes, sigs, wave = coadd.unpack_spec(spectra_coadd_rebin,all_wave=False)

        ## scaling different orders
        rmask = spectra_coadd_rebin.data['sig'].filled(0.) > 0.
        sn2, weights = coadd.sn_weight(fluxes, sigs, wave, rmask)
        ## ToDo pasing parameters
        SN_MIN_MEDSCALE = 0.5
        overlapfrac=0.01
        median_echelle_scale(spectra_coadd_rebin, rmask, sn2, nsig=sigrej_final, niter=niter,
                             SN_MIN_MEDSCALE=SN_MIN_MEDSCALE, overlapfrac=overlapfrac, debug=debug)

        ## Merging orders
        ## ToDo: Joe claimed not to use pixel depedent weighting.
        weights = 1.0 / sigs**2
        weights[~np.isfinite(weights)] = 0.0
        weight_combine = np.sum(weights, axis=0)
        weight_norm = weights / weight_combine
        weight_norm[np.isnan(weight_norm)] = 1.0
        flux_final = np.sum(fluxes * weight_norm, axis=0)
        sig_final = np.sqrt(np.sum((weight_norm * sigs) ** 2, axis=0))
        spec1d_final = spec_from_array(wave_final * units.AA,flux_final,sig_final,**rsp_kwargs)

        # plot and save qa
        plt.figure(figsize=(12, 6))
        ax1 = plt.axes([0.07, 0.13, 0.9, 0.4])
        ax2 = plt.axes([0.07, 0.55, 0.9, 0.4])
        plt.setp(ax2.get_xticklabels(), visible=False)

        medf = np.median(spec1d_final.flux)
        ylim = (np.sort([0. - 0.3 * medf, 5 * medf]))
        cmap = plt.get_cmap('RdYlBu_r')
        for idx in range(spectra_coadd_rebin.nspec):
            spectra_coadd_rebin.select = idx
            color = cmap(float(idx) / spectra_coadd_rebin.nspec)
            ind_good = spectra_coadd_rebin.sig > 0
            ax1.plot(spectra_coadd_rebin.wavelength[ind_good], spectra_coadd_rebin.flux[ind_good], color=color)

        if (np.max(spec1d_final.wavelength) > (9000.0 * units.AA)):
            skytrans_file = resource_filename('pypeit', '/data/skisim/atm_transmission_secz1.5_1.6mm.dat')
            skycat = np.genfromtxt(skytrans_file, dtype='float')
            scale = 0.85 * ylim[1]
            ax2.plot(skycat[:, 0] * 1e4, skycat[:, 1] * scale, 'm-', alpha=0.5)

        ax2.plot(spec1d_final.wavelength, spec1d_final.sig, ls='steps-', color='0.7')
        ax2.plot(spec1d_final.wavelength, spec1d_final.flux, ls='steps-', color='b')

        ax1.set_xlim([np.min(spec1d_final.wavelength.value), np.max(spec1d_final.wavelength.value)])
        ax1.set_ylim(ylim)
        ax2.set_xlim([np.min(spec1d_final.wavelength.value), np.max(spec1d_final.wavelength.value)])
        ax2.set_ylim(ylim)
        ax1.set_xlabel('Wavelength (Angstrom)')
        ax1.set_ylabel('Flux')
        ax2.set_ylabel('Flux')

        plt.tight_layout(pad=0.2, h_pad=0., w_pad=0.2)
        if qafile is not None:
            if len(qafile.split('.')) == 1:
                msgs.info("No fomat given for the qafile, save to PDF format.")
                qafile = qafile + '.pdf'
            plt.savefig(qafile)
            msgs.info("Wrote coadd QA: {:s}".format(qafile))
        if debug:
            plt.show()
        plt.close()
        if outfile is not None:
            coadd.write_to_disk(spec1d_final, outfile)

        ### deprecated
        # from IPython import embed
        # embed()
        #kwargs['echelle'] = True
        #kwargs['wave_grid_min'] = np.min(wave_grid)
        #kwargs['wave_grid_max'] = np.max(wave_grid)
        #spec1d_final = coadd.coadd_spectra(spectra_coadd_rebin, wave_grid_method=wave_grid_method, niter=niter,
        #                                  scale_method=scale_method, do_offset=do_offset, sigrej_final=sigrej_final,
        #                                  do_var_corr=do_var_corr, qafile=qafile, outfile=outfile,
        #                                  do_cr=do_cr, debug=debug, **kwargs)

    return spec1d_final
