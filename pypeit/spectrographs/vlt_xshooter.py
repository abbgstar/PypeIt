""" Module for VLT X-Shooter
"""
from __future__ import absolute_import, division, print_function

import glob

import numpy as np
from astropy.io import fits

from pypeit import msgs
from pypeit import telescopes
from pypeit.core import parse
from pypeit.core import framematch
from pypeit.par import pypeitpar
from pypeit.spectrographs import spectrograph

from pypeit import debugger

class VLTXShooterSpectrograph(spectrograph.Spectrograph):
    """
    Child to handle VLT/XSHOOTER specific code
    """
    def __init__(self):
        # Get it started
        super(VLTXShooterSpectrograph, self).__init__()
        self.spectrograph = 'vlt_xshooter_base'
        self.telescope = telescopes.VLTTelescopePar()

    @property
    def pypeline(self):
        return 'MultiSlit'

    @staticmethod
    def default_pypeit_par():
        """
        Set default parameters for VLT XSHOOTER reductions.
        """
        par = pypeitpar.PypeItPar()
        # Correct for flexure using the default approach
        par['flexure'] = pypeitpar.FlexurePar()
        return par

    def header_keys(self):
        hdr_keys = {}
        hdr_keys[0] = {}

        # The keyword that identifies the frame type (i.e. bias, flat, etc.)
        hdr_keys[0]['idname']  = 'HIERARCH ESO DPR CATG'
        # Header keyword for the name given by the observer to a given frame
        hdr_keys[0]['target']  = 'OBJECT'
        # The time stamp of the observation (i.e. decimal MJD)
        hdr_keys[0]['time']    = 'MJD-OBS'
        # The UT date of the observation which is used for heliocentric
        # (in the format YYYY-MM-DD  or  YYYY-MM-DDTHH:MM:SS.SS)
        #hdr_keys[0]['date']    = 'DATE-OBS'
        # Right Ascension of the target
        hdr_keys[0]['ra']      = 'RA'
        # Declination of the target
        hdr_keys[0]['dec']     = 'DEC'
        # Airmass at start of observation
        hdr_keys[0]['airmass'] = 'HIERARCH ESO TEL AIRM START'
        # Exposure time keyword
        hdr_keys[0]['exptime'] = 'EXPTIME'
        hdr_keys[0]['naxis0']  = 'NAXIS2'
        hdr_keys[0]['naxis1']  = 'NAXIS1'
        # Binning along SPATIAL axis
        hdr_keys[0]['binning_x'] = 'HIERARCH ESO DET WIN1 BINX'
        # Binning along SPECTRAL axis
        hdr_keys[0]['binning_y'] = 'HIERARCH ESO DET WIN1 BINY'
        # UTC, decker are arm dependent
        return hdr_keys

    def validate_metadata(self, fitstbl):
        indx = fitstbl['binning_x'] == 'None'
        fitstbl['binning_x'][indx] = 1
        indx = fitstbl['binning_y'] == 'None'
        fitstbl['binning_y'][indx] = 1
        fitstbl['binning'] = np.array(['{0},{1}'.format(bx,by)
                                for bx,by in zip(fitstbl['binning_x'], fitstbl['binning_y'])])

    def metadata_keys(self):
        return ['filename', 'date', 'frametype', 'idname', 'target', 'exptime', 'decker',
                'binning']

    def check_frame_type(self, ftype, fitstbl, exprng=None):
        """
        Check for frames of the provided type.
        """
        good_exp = framematch.check_frame_exptime(fitstbl['exptime'], exprng)
        # TODO: Allow for 'sky' frame type, for now include sky in
        # 'science' category
        if ftype == 'science':
            return good_exp & ((fitstbl['idname'] == 'SCIENCE')
                                | (fitstbl['target'] == 'STD,TELLURIC')
                                | (fitstbl['target'] == 'STD,SKY'))
        if ftype == 'standard':
            return good_exp & (fitstbl['target'] == 'STD,FLUX')
        if ftype == 'bias':
            return good_exp & (fitstbl['target'] == 'BIAS')
        if ftype == 'dark':
            return good_exp & (fitstbl['target'] == 'DARK')
        if ftype == 'pixelflat' or ftype == 'trace':
            # Flats and trace frames are typed together
            return good_exp & ((fitstbl['target'] == 'LAMP,DFLAT')
                               | (fitstbl['target'] == 'LAMP,QFLAT')
                               | (fitstbl['target'] == 'LAMP,FLAT'))
        if ftype == 'pinhole':
            # Don't type pinhole
            return np.zeros(len(fitstbl), dtype=bool)
        if ftype == 'arc':
            return good_exp & (fitstbl['target'] == 'LAMP,WAVE')

        msgs.warn('Cannot determine if frames are of type {0}.'.format(ftype))
        return np.zeros(len(fitstbl), dtype=bool)

    def get_match_criteria(self):
        # TODO: Matching needs to be looked at...
        match_criteria = {}
        for key in framematch.FrameTypeBitMask().keys():
            match_criteria[key] = {}
        #
        match_criteria['standard']['match'] = {}
        match_criteria['standard']['match']['binning'] = ''
        # Bias
        match_criteria['bias']['match'] = {}
        match_criteria['bias']['match']['binning'] = ''
        # Pixelflat
        match_criteria['pixelflat']['match'] = match_criteria['standard']['match'].copy()
        # Traceflat
        match_criteria['trace']['match'] = match_criteria['standard']['match'].copy()
        # Arc
        match_criteria['arc']['match'] = match_criteria['bias']['match'].copy()

        # Return
        return match_criteria


class VLTXShooterNIRSpectrograph(VLTXShooterSpectrograph):
    """
    Child to handle VLT/XSHOOTER specific code
    """
    def __init__(self):
        # Get it started
        super(VLTXShooterNIRSpectrograph, self).__init__()
        self.spectrograph = 'vlt_xshooter_nir'
        self.camera = 'XShooter_NIR'
        self.detector = [
                # Detector 1
                pypeitpar.DetectorPar(
                            dataext         = 0,
                            dispaxis        = 1,
                            dispflip        = False,
                            xgap            = 0.,
                            ygap            = 0.,
                            ysize           = 1.,
                            platescale      = 0.197, # average between order 11 & 30, see manual
                            darkcurr        = 0.0,
                            saturation      = 65535.,
                            nonlinear       = 0.86,
                            numamplifiers   = 1,
                            gain            = 2.12,
                            ronoise         = 8.0, # ?? more precise value?
                            datasec         = '[20:,4:2044]',
                            oscansec        = '[4:20,4:2044]',
                            suffix          = '_NIR'
                            )]
        self.numhead = 1

    @staticmethod
    def default_pypeit_par():
        """
        Set default parameters for XSHOOTER NIR reductions.
        """
        par = VLTXShooterSpectrograph.default_pypeit_par()
        par['rdx']['spectrograph'] = 'vlt_xshooter_nir'

        # Adjustments to slit and tilts for NIR
        par['calibrations']['slits']['sigdetect'] = 700.
        par['calibrations']['slits']['polyorder'] = 5
        par['calibrations']['slits']['maxshift'] = 0.5
        par['calibrations']['slits']['pcatype'] = 'pixel'
        par['calibrations']['tilts']['tracethresh'] = [10,10,10,10,10,10,10,10,10, 10, 10, 20, 20, 20,20,10]
        # Always correct for flexure, starting with default parameters
        par['flexure'] = pypeitpar.FlexurePar()
        par['scienceframe']['process']['sigclip'] = 20.0
        par['scienceframe']['process']['satpix'] ='nothing'

        return par

    def check_headers(self, headers):
        """
        Check headers match expectations for an VLT/XSHOOTER exposure.

        See also
        :func:`pypeit.spectrographs.spectrograph.Spectrograph.check_headers`.

        Args:
            headers (list):
                A list of headers read from a fits file
        """
        expected_values = { '0.INSTRUME': 'XSHOOTER',
                            '0.HIERARCH ESO SEQ ARM': 'NIR',
                            '0.NAXIS': 2 }
        super(VLTXShooterNIRSpectrograph, self).check_headers(headers,
                                                              expected_values=expected_values)

    def header_keys(self):
        hdr_keys = super(VLTXShooterNIRSpectrograph, self).header_keys()
        hdr_keys[0]['decker'] = 'HIERARCH ESO INS OPTI5 NAME'
        hdr_keys[0]['utc'] = 'HIERARCH ESO DET EXP UTC'
        return hdr_keys

    def setup_arcparam(self, arcparam, msarc_shape=None, 
                       disperser=None, **null_kwargs):
        """
        Setup the arc parameters

        TODO: disperser can't be required because it's never used

        Args:
            arcparam: dict
            disperser: str, REQUIRED
            **null_kwargs:
              Captured and never used

        Returns:
            arcparam is modified in place

        """
        #debugger.set_trace() # THIS NEEDS TO BE DEVELOPED
        arcparam['lamps'] = ['OH_XSHOOTER'] # Line lamps on
        arcparam['nonlinear_counts'] = self.detector[0]['nonlinear']*self.detector[0]['saturation'] # lines abovet this are masked
        arcparam['min_nsig'] = 50.0         # Min significance for arc lines to be used
        arcparam['lowest_nsig'] = 10.0         # Min significance for arc lines to be used
        arcparam['wvmnx'] = [8000.,26000.]  # Guess at wavelength range
        # These parameters influence how the fts are done by pypeit.core.wavecal.fitting.iterative_fitting
        arcparam['match_toler'] = 3 # 3 was default, 1 seems to work better        # Matcing tolerance (pixels)
        arcparam['func'] = 'legendre'       # Function for fitting
        arcparam['n_first'] = 2             # Order of polynomial for first fit
        arcparam['n_final'] = 4  #was default    # Order of polynomial for final fit
        arcparam['nsig_rej'] = 2            # Number of sigma for rejection
        arcparam['nsig_rej_final'] = 3.0    # Number of sigma for rejection (final fit)




#        arcparam['nonlinear_counts'] = self.detector[0]['nonlinear']*self.detector[0]['saturation']
#        arcparam['disp'] = 0.6                                 # Ang/unbinned pixel
#        arcparam['b1'] = 1./ arcparam['disp'] / msarc_shape[0] # Pixel fit term (binning independent)
#        arcparam['b2'] = 0.                                    # Pixel fit term
#        arcparam['lamps'] = ['OH_triplespec']                  # Line lamps on
#        arcparam['wv_cen']=17370.                              # Estimate of central wavelength
#        arcparam['disp_toler'] = 0.1                           # 10% tolerance
#        arcparam['match_toler'] = 3.                           # Matching tolerance (pixels)
#        arcparam['min_ampl'] = 1000.                           # Minimum amplitude
#        arcparam['func'] = 'legendre'                          # Function for fitting
#        arcparam['n_first'] = 1                                # Order of polynomial for first fit
#        arcparam['n_final'] = 3                                # Order of polynomial for final fit
#        arcparam['nsig_rej'] = 5.                              # Number of sigma for rejection
#        arcparam['nsig_rej_final'] = 5.0                       # Number of sigma for rejection (final fit)
#        arcparam['Nstrong'] = 20                               # Number of lines for auto-analysis

    def bpm(self, shape=None, filename=None, det=None, **null_kwargs):
        """
        Override parent bpm function with BPM specific to X-ShooterNIR.

        .. todo::
            Allow for binning changes.

        Parameters
        ----------
        det : int, REQUIRED
        **null_kwargs:
            Captured and never used

        Returns
        -------
        bpix : ndarray
          0 = ok; 1 = Mask

        """

        self.empty_bpm(shape=shape, filename=filename, det=det)
        return self.bpm_img


class VLTXShooterVISSpectrograph(VLTXShooterSpectrograph):
    """
    Child to handle VLT/XSHOOTER specific code
    """
    def __init__(self):
        # Get it started
        super(VLTXShooterVISSpectrograph, self).__init__()
        self.spectrograph = 'vlt_xshooter_vis'
        self.camera = 'XShooter_VIS'
        self.detector = [
                # Detector 1
                pypeitpar.DetectorPar(
                            dataext         = 0,
                            dispaxis        = 0,
                            dispflip        = False,
                            xgap            = 0.,
                            ygap            = 0.,
                            ysize           = 1.,
                            platescale      = 0.16, # average from order 17 and order 30, see manual
                            darkcurr        = 0.0,
                            saturation      = 65535.,
                            nonlinear       = 0.86,
                            numamplifiers   = 1,
                            gain            = 0.595,
                            ronoise         = 3.1,
                            datasec         = '[1:2000,10:2058]',
                            oscansec        = '[1:2000, 2060:2106]',
                            suffix          = '_VIS'
                            )]
        self.numhead = 1

    @staticmethod
    def default_pypeit_par():
        """
        Set default parameters for VLT XSHOOTER VIS reductions.
        """
        par = VLTXShooterSpectrograph.default_pypeit_par()
        par['rdx']['spectrograph'] = 'vlt_xshooter_vis'

        # Adjustments to slit and tilts for VIS
        par['calibrations']['arcframe']['process']['overscan'] = 'median'
        par['calibrations']['traceframe']['process']['overscan'] = 'median'
        par['calibrations']['slits']['sigdetect'] = 2.0
        par['calibrations']['slits']['pcatype'] = 'order'
        par['calibrations']['slits']['polyorder'] = 5
        par['calibrations']['slits']['maxshift'] = 0.5
        par['calibrations']['slits']['number'] = 15
        par['calibrations']['slits']['fracignore'] = 0.0001

        par['calibrations']['tilts']['tracethresh'] = [ 20., 100., 100., 100., 100., 100., 100.,
                                                       100., 500., 500., 500., 500., 500., 500.,
                                                       500.]

#       par['calibrations']['slits']['pcapar'] = [3,2,1,0]

        return par

    def check_headers(self, headers):
        """
        Check headers match expectations for a VLT/XSHOOTER exposure.

        See also
        :func:`pypeit.spectrographs.spectrograph.Spectrograph.check_headers`.

        Args:
            headers (list):
                A list of headers read from a fits file
        """
        expected_values = { '0.INSTRUME': 'XSHOOTER',
                            '0.HIERARCH ESO SEQ ARM': 'VIS',
                            '0.NAXIS': 2 }
        super(VLTXShooterVISSpectrograph, self).check_headers(headers,
                                                              expected_values=expected_values)

    def header_keys(self):
        hdr_keys = super(VLTXShooterVISSpectrograph, self).header_keys()
        hdr_keys[0]['decker'] = 'HIERARCH ESO INS OPTI4 NAME'
        hdr_keys[0]['utc'] = 'UTC'      # Some have UTC, most do not
        return hdr_keys

    def setup_arcparam(self, arcparam, disperser=None, **null_kwargs):
        """
        Setup the arc parameters

        Args:
            arcparam: dict
            disperser: str, REQUIRED
            **null_kwargs:
              Captured and never used

        Returns:
            arcparam is modified in place

        """
        ## debugger.set_trace() # THIS NEEDS TO BE DEVELOPED
        arcparam['disp'] = 0.1              # Ang/unbinned pixel
        arcparam['b1'] = 10.                # Pixel fit term (binning independent)
                                            # pix = b0 + b1*lambda + b2*lambda**2
        arcparam['b2'] = 0.                 # Pixel fit term pix = b0 + b1*lambda + b2*lambda**2
        arcparam['lamps'] = ['ThAr']        # Line lamps on
        arcparam['wv_cen'] = 7900.          # Guess at central wavelength
        arcparam['wvmnx'] = [5545.,10250]   # Guess at wavelength range
        arcparam['disp_toler'] = 0.1        # 10% tolerance
        arcparam['match_toler'] = 3.        # Matcing tolerance (pixels)
        arcparam['min_ampl'] = 500.         # Minimum amplitude
        arcparam['func'] = 'legendre'       # Function for fitting
        arcparam['n_first'] = 0             # Order of polynomial for first fit
        arcparam['n_final'] = 1             # Order of polynomial for final fit
        arcparam['nsig_rej'] = 2.           # Number of sigma for rejection
        arcparam['nsig_rej_final'] = 3.     # Number of sigma for rejection (final fit)
        arcparam['Nstrong'] = 20            # Number of lines for auto-analysis

        # non linear regime
        arcparam['nonlinear_counts'] = self.detector[0]['nonlinear']*self.detector[0]['saturation']

    def bpm(self, shape=None, filename=None, det=None, **null_kwargs):
        """
        Override parent bpm function with BPM specific to X-Shooter VIS.

        .. todo::
            Allow for binning changes.

        Parameters
        ----------
        det : int, REQUIRED
        **null_kwargs:
            Captured and never used

        Returns
        -------
        bpix : ndarray
          0 = ok; 1 = Mask

        """
        self.empty_bpm(shape=shape, filename=filename, det=det)
        if det == 1:
            self.bpm_img[1456:, 841:845] = 1.

        return self.bpm_img


class VLTXShooterUVBSpectrograph(VLTXShooterSpectrograph):
    """
    Child to handle VLT/XSHOOTER specific code
    """
    def __init__(self):
        # Get it started
        super(VLTXShooterUVBSpectrograph, self).__init__()
        self.spectrograph = 'vlt_xshooter_uvb'
        self.camera = 'XShooter_UVB'
        self.detector = [
                # Detector 1
                pypeitpar.DetectorPar(
                            dataext         = 0,
                            dispaxis        = 0,
                            dispflip        = True,
                            xgap            = 0.,
                            ygap            = 0.,
                            ysize           = 1.,
                            # average from order 14 and order 24, see manual
                            platescale      = 0.161,
                            darkcurr        = 0.0,
                            saturation      = 65000.,
                            nonlinear       = 0.86,
                            numamplifiers   = 1,
                            gain            = 1.61,
                            ronoise         = 2.60,
                            datasec         = '[49:,1:]', # '[49:2000,1:2999]',
                            oscansec        = '[1:48,1:]', # '[1:48, 1:2999]',
                            suffix          = '_UVB'
                            )]
        self.numhead = 1

    @staticmethod
    def default_pypeit_par():
        """
        Set default parameters for VLT XSHOOTER UVB reductions.
        """
        par = VLTXShooterSpectrograph.default_pypeit_par()
        par['rdx']['spectrograph'] = 'vlt_xshooter_uvb'

        # Adjustments to slit and tilts for UVB
        par['calibrations']['slits']['sigdetect'] = 20.
        par['calibrations']['slits']['pcatype'] = 'pixel'
        par['calibrations']['slits']['polyorder'] = 5
        par['calibrations']['slits']['maxshift'] = 0.5
        par['calibrations']['slits']['number'] = -1

        par['calibrations']['arcframe']['process']['overscan'] = 'median'
        par['calibrations']['traceframe']['process']['overscan'] = 'median'

        return par

    def check_headers(self, headers):
        """
        Check headers match expectations for a VLT/XSHOOTER exposure.

        See also
        :func:`pypeit.spectrographs.spectrograph.Spectrograph.check_headers`.

        Args:
            headers (list):
                A list of headers read from a fits file
        """
        expected_values = { '0.INSTRUME': 'XSHOOTER',
                            '0.HIERARCH ESO SEQ ARM': 'UVB',
                               '0.NAXIS': 2 }
        super(VLTXShooterUVBSpectrograph, self).check_headers(headers,
                                                              expected_values=expected_values)

    def header_keys(self):
        hdr_keys = super(VLTXShooterUVBSpectrograph, self).header_keys()
        hdr_keys[0]['decker'] = 'HIERARCH ESO INS OPTI3 NAME'
        # TODO: UVB does not have a utc keyword?
        return hdr_keys

    def setup_arcparam(self, arcparam, disperser=None, **null_kwargs):
        """
        Setup the arc parameters

        Args:
            arcparam: dict
            disperser: str, REQUIRED
            **null_kwargs:
              Captured and never used

        Returns:
            arcparam is modified in place

        """
        ## debugger.set_trace() # THIS NEEDS TO BE DEVELOPED
        arcparam['lamps'] = ['ThAr']
        arcparam['n_first']=2 
        arcparam['disp']=0.2 # Ang per pixel (unbinned)
        arcparam['b1']= 0.
        arcparam['b2']= 0.
        arcparam['wvmnx'] = [2950.,5650.]
        arcparam['wv_cen'] = 4300.

    def bpm(self, shape=None, filename=None, det=None, **null_kwargs):
        """
        Override parent bpm function with BPM specific to X-Shooter UVB.

        .. todo::
            Allow for binning changes.

        Parameters
        ----------
        det : int, REQUIRED
        **null_kwargs:
            Captured and never used

        Returns
        -------
        bpix : ndarray
          0 = ok; 1 = Mask

        """
        self.empty_bpm(shape=shape, filename=filename, det=det)
        if det == 1:
            self.bpm_img[1456:, 841:845] = 1.

        return self.bpm_img



