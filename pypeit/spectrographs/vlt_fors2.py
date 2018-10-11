""" Module for VLT FORS2
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


class VLTFORS2Spectrograph(spectrograph.Spectrograph):
    """
    Child to handle VLT/FORS2 specific code
    """

    def __init__(self):
        # Get it started
        super(VLTFORS2Spectrograph, self).__init__()
        self.spectrograph = 'vlt_fors2_base'
        self.telescope = telescopes.VLTTelescopePar()

    @staticmethod
    def default_pypeit_par():
        """
        Set default parameters for VLT FORS2 reductions.
        """
        par = pypeitpar.PypeItPar()
        # Frame numbers
        par['calibrations']['standardframe']['number'] = 1
        par['calibrations']['biasframe']['number'] = 5
        par['calibrations']['pixelflatframe']['number'] = 5
        par['calibrations']['traceframe']['number'] = 5
        par['calibrations']['arcframe']['number'] = 1
        # Use bias frames
        par['calibrations']['biasframe']['useframe'] = 'bias'
        # Set wave tilts order
        par['calibrations']['tilts']['order'] = 2
        # Scienceimage default parameters
        par['scienceimage'] = pypeitpar.ScienceImagePar()
        # Always flux calibrate, starting with default parameters
        par['fluxcalib'] = pypeitpar.FluxCalibrationPar()
        # Always correct for flexure, starting with default parameters
        par['flexure'] = pypeitpar.FlexurePar()
        # Set the default exposure time ranges for the frame typing
        par['calibrations']['biasframe']['exprng'] = [None, 1]
        par['calibrations']['darkframe']['exprng'] = [999999, None]  # No dark frames
        par['calibrations']['pinholeframe']['exprng'] = [999999, None]  # No pinhole frames
        par['calibrations']['pixelflatframe']['exprng'] = [0, None]
        par['calibrations']['traceframe']['exprng'] = [0, None]
        par['calibrations']['arcframe']['exprng'] = [None, 100]
        par['calibrations']['standardframe']['exprng'] = [1, 120]
        par['scienceframe']['exprng'] = [1, None]
        return par

    def header_keys(self):
        """
        Provide the relevant header keywords
        """

        hdr_keys = {}
        hdr_keys[0] = {}

        # The keyword that identifies the frame type (i.e. bias, flat, etc.)
        hdr_keys[0]['idname']  = 'HIERARCH ESO DPR TYPE'
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

        hdr_keys[0]['decker'] = 'HIERARCH ESO SEQ SPEC TARG '
        hdr_keys[0]['filter1'] = 'GRISM_N'
        hdr_keys[0]['dispname'] = 'HIERARCH ESO INS GRIS1 NAME'

        hdr_keys[0]['naxis0'] = 'NAXIS2'
        hdr_keys[0]['naxis1'] = 'NAXIS1'

        return hdr_keys

    def validate_metadata(self, fitstbl):
        indx = fitstbl['binning_x'] == 'None'
        fitstbl['binning_x'][indx] = 1
        indx = fitstbl['binning_y'] == 'None'
        fitstbl['binning_y'][indx] = 1
        fitstbl['binning'] = np.array(['{0},{1}'.format(bx,by)
                                for bx,by in zip(fitstbl['binning_x'], fitstbl['binning_y'])])

    def check_frame_type(self, ftype, fitstbl, exprng=None):
        """
        Check for frames of the provided type.
        """
        good_exp = framematch.check_frame_exptime(fitstbl['exptime'], exprng)
        if ftype == 'science':
            return good_exp & (fitstbl['idname'] == 'SKY')
        if ftype == 'standard':
            return good_exp & (fitstbl['idname'] == 'STD')
        if ftype == 'arc':
            return good_exp & (fitstbl['idname'] == 'WAVE,LAMP')
        if ftype == 'pixelflat' or ftype == 'trace':
            return good_exp & (fitstbl['idname'] == 'FLAT,LAMP')
        if ftype == 'bias':
            return good_exp & (fitstbl['idname'] == 'BIAS')

        msgs.warn('Cannot determine if frames are of type {0}.'.format(ftype))
        return np.zeros(len(fitstbl), dtype=bool)


        good_exp = framematch.check_frame_exptime(fitstbl['exptime'], exprng)
        if ftype in ['science', 'standard']:
            return good_exp & self.lamps(fitstbl, 'off')
        #            \
        #                        & np.array([ t not in ['Arcs', 'Bias', 'Dome Flat']
        #                                        for t in fitstbl['target']])
        if ftype == 'bias':
            return good_exp  # & (fitstbl['target'] == 'Bias')
        if ftype == 'pixelflat' or ftype == 'trace':
            # Flats and trace frames are typed together
            return good_exp & self.lamps(fitstbl, 'dome')  # & (fitstbl['target'] == 'Dome Flat')
        if ftype == 'pinhole' or ftype == 'dark':
            # Don't type pinhole or dark frames
            return np.zeros(len(fitstbl), dtype=bool)
        if ftype == 'arc':
            return good_exp & self.lamps(fitstbl, 'arcs')  # & (fitstbl['target'] == 'Arcs')

        msgs.warn('Cannot determine if frames are of type {0}.'.format(ftype))
        return np.zeros(len(fitstbl), dtype=bool)

    def get_match_criteria(self):
        """Set the general matching criteria for VLT FORS2."""
        match_criteria = {}
        for key in framematch.FrameTypeBitMask().keys():
            match_criteria[key] = {}

        match_criteria['standard']['match'] = {}
        match_criteria['standard']['match']['naxis0'] = '=0'
        match_criteria['standard']['match']['naxis1'] = '=0'

        match_criteria['bias']['match'] = {}
        match_criteria['bias']['match']['naxis0'] = '=0'
        match_criteria['bias']['match']['naxis1'] = '=0'

        match_criteria['pixelflat']['match'] = {}
        match_criteria['pixelflat']['match']['naxis0'] = '=0'
        match_criteria['pixelflat']['match']['naxis1'] = '=0'
        match_criteria['pixelflat']['match']['decker'] = ''

        match_criteria['trace']['match'] = {}
        match_criteria['trace']['match']['naxis0'] = '=0'
        match_criteria['trace']['match']['naxis1'] = '=0'
        match_criteria['trace']['match']['decker'] = ''

        match_criteria['arc']['match'] = {}
        match_criteria['arc']['match']['naxis0'] = '=0'
        match_criteria['arc']['match']['naxis1'] = '=0'

        return match_criteria


class VLTFORS2Chip1Spectrograph(VLTFORS2Spectrograph):
    """
    Child to handle VLT/FORS2 chip1 specific code
    """

    def __init__(self):
        # Get it started
        super(VLTFORS2Chip1Spectrograph, self).__init__()
        self.spectrograph = 'vlt_fors2_chip1'
        self.camera = 'FORS2_chip1'
        self.detector = [
            # Detector 1
            pypeitpar.DetectorPar(
                dataext=0,
                dispaxis=1,
                dispflip=False,
                xgap=0.,
                ygap=0.,
                ysize=1.,
                platescale=0.126,
                darkcurr=0.0,
                saturation=65535.,
                nonlinear=0.9,
                numamplifiers=1,
                gain=[1.89],
                ronoise=[3.20],
                datasec=['[:,5:]'],
                oscansec=['[:,:5]'],
                suffix='_chip1'
            )]
        self.numhead = 1
        # Uses timeunit from parent class
        # Uses default primary_hdrext
        self.sky_file = 'sky_kastb_600.fits'


    @staticmethod
    def default_pypeit_par():
        """
        Set default parameters for Shane Kast Blue reductions.
        """
        par = VLTFORS2Spectrograph.default_pypeit_par()
        par['rdx']['spectrograph'] = 'vlt_fors2_chip1'
        return par

    def check_headers(self, headers):
        """
        Check headers match expectations for a Shane Kast blue exposure.

        See also
        :func:`pypeit.spectrographs.spectrograph.Spectrograph.check_headers`.

        Args:
            headers (list):
                A list of headers read from a fits file
        """
        expected_values = {'0.NAXIS': 2,
                           '0.EXTNAME': 'CHIP1',
                           '0.HIERARCH ESO DET CHIP1 NAME': 'EEV, EEV'}
#                           '0.HIERARCH ESO INS MODE': 'LSS'}
        super(VLTFORS2Chip1Spectrograph, self).check_headers(headers,
                                                             expected_values=expected_values)

    def header_keys(self):
        """
        Header keys specific to shane_kast_blue

        Returns:

        """
        hdr_keys = super(VLTFORS2Chip1Spectrograph, self).header_keys()
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
        arcparam['lamps'] = ['CdI', 'HgI', 'HeI', 'NeI']
        arcparam['nonlinear_counts'] = self.detector[0]['nonlinear'] * self.detector[0]['saturation']
        if disperser == 'GRIS_1200B':
            arcparam['disp'] = 2.4
            #arcparam['b1'] = 6.88935788e-04
            #arcparam['b2'] = -2.38634231e-08
            arcparam['wvmnx'][1] = 6000.
            arcparam['wv_cen'] = 4360.
        else:
            msgs.error('Not ready for this disperser {:s}!'.format(disperser))
