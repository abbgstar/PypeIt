# encoding: utf-8
"""
Defines parameter sets used to set the behavior for core pypeit
functionality.

For more details on the full parameter hierarchy and a tabulated
description of the keywords in each parameter set, see :ref:`pypeitpar`.

For examples of how to change the parameters for a run of pypeit using
the pypeit input file, see :ref:`pypeit_file`.

**New Parameters**:

To add a new parameter, let's call it `foo`, to any of the provided
parameter sets:

    - Add ``foo=None`` to the ``__init__`` method of the relevant
      parameter set.  E.g.::
        
        def __init__(self, existing_par=None, foo=None):

    - Add any default value (the default value is ``None`` unless you set
      it), options list, data type, and description to the body of the
      ``__init__`` method.  E.g.::

        defaults['foo'] = 'bar'
        options['foo'] = [ 'bar', 'boo', 'fighters' ]
        dtypes['foo'] = str
        descr['foo'] = 'foo? who you callin a foo!  ' \
                       'Options are: {0}'.format(', '.join(options['foo']))

    - Add the parameter to the ``from_dict`` method:
    
        - If the parameter is something that does not require
          instantiation, add the keyword to the ``parkeys`` list in the
          ``from_dict`` method.  E.g.::

            parkeys = [ 'existing_par', 'foo' ]
            kwargs = {}
            for pk in parkeys:
                kwargs[pk] = cfg[pk] if pk in k else None

        - If the parameter is another ParSet or requires instantiation,
          provide the instantiation.  For example, see how the
          :class:`ProcessImagesPar` parameter set is defined in the
          :class:`FrameGroupPar` class.  E.g.::

            pk = 'foo'
            kwargs[pk] = FooPar.from_dict(cfg[pk]) if pk in k else None

**New Parameter Sets:**

To add an entirely new parameter set, use one of the existing parameter
sets as a template, then add the parameter set to :class:`PypeItPar`,
assuming you want it to be accessed throughout the code.

----
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
from __future__ import unicode_literals

import os
import glob
import warnings
from pkg_resources import resource_filename
import inspect

from collections import OrderedDict

import numpy

from configobj import ConfigObj
from astropy.time import Time

from pypeit.par.parset import ParSet
from pypeit.par import util

# Needs this to determine the valid spectrographs TODO: This causes a
# circular import.  Spectrograph specific parameter sets and where they
# go needs to be rethought.
#from ..spectrographs.util import valid_spectrographs

#-----------------------------------------------------------------------------
# Reduction ParSets

# TODO: Create child classes for each allowed frame type?  E.g.:
#
# class BiasPar(FrameGroupPar):
#    def __init__(self, useframe=None, number=None, overscan=None, combine=None, lacosmic=None):
#        # Set frame-specific defaults
#        _number = 5 if number is None else number
#        super(BiasPar, self).__init(frametype='bias', useframe=useframe, number=_number,
#                                    overscan=overscan, combine=combine, lacosmic=lacosmic)

class FrameGroupPar(ParSet):
    """
    An abstracted group of parameters that defines how specific types of
    frames should be grouped and combined.

    For a table with the current keywords, defaults, and descriptions,
    see :ref:`pypeitpar`.
    """
    def __init__(self, frametype=None, useframe=None, number=None, exprng=None, process=None):
        # Grab the parameter names and values from the function
        # arguments
        args, _, _, values = inspect.getargvalues(inspect.currentframe())
        pars = OrderedDict([(k,values[k]) for k in args[1:]])

        # Initialize the other used specifications for this parameter
        # set
        defaults = OrderedDict.fromkeys(pars.keys())
        options = OrderedDict.fromkeys(pars.keys())
        dtypes = OrderedDict.fromkeys(pars.keys())
        descr = OrderedDict.fromkeys(pars.keys())

        # Fill out parameter specifications.  Only the values that are
        # *not* None (i.e., the ones that are defined) need to be set
        defaults['frametype'] = 'bias'
        options['frametype'] = FrameGroupPar.valid_frame_types()
        dtypes['frametype'] = str
        descr['frametype'] = 'Frame type.  ' \
                             'Options are: {0}'.format(', '.join(options['frametype']))

        dtypes['useframe'] = str
        descr['useframe'] = 'A master calibrations file to use if it exists.'

        defaults['number'] = 0
        dtypes['number'] = int
        descr['number'] = 'Used in matching calibration frames to science frames.  This sets ' \
                          'the number of frames to use of this type'

        defaults['exprng'] = [None, None]
        dtypes['exprng'] = list
        descr['exprng'] = 'Used in identifying frames of this type.  This sets the minimum ' \
                          'and maximum allowed exposure times.  There must be two items in ' \
                          'the list.  Use None to indicate no limit; i.e., to select exposures ' \
                          'with any time greater than 30 sec, use exprng = [30, None].'

        defaults['process'] = ProcessImagesPar()
        dtypes['process'] = [ ParSet, dict ]
        descr['process'] = 'Parameters used for basic image processing'

        # Instantiate the parameter set
        super(FrameGroupPar, self).__init__(list(pars.keys()),
                                            values=list(pars.values()),
                                            defaults=list(defaults.values()),
                                            options=list(options.values()),
                                            dtypes=list(dtypes.values()),
                                            descr=list(descr.values()))

        self.validate()

    @classmethod
    def from_dict(cls, frametype, cfg):
        k = cfg.keys()
        parkeys = [ 'useframe', 'number', 'exprng' ]
        kwargs = {}
        for pk in parkeys:
            kwargs[pk] = cfg[pk] if pk in k else None
        pk = 'process'
        kwargs[pk] = ProcessImagesPar.from_dict(cfg[pk]) if pk in k else None
        return cls(frametype=frametype, **kwargs)

    @staticmethod
    def valid_frame_types():
        """
        Return the list of valid frame types.
        """
        return [ 'bias', 'dark', 'pixelflat', 'arc', 'pinhole', 'trace', 'standard', 'science',
                 'all' ]

    def validate(self):
        if self.data['useframe'] is None:
            self.data['useframe'] = self.data['frametype']
        if len(self.data['exprng']) != 2:
            raise ValueError('exprng must be a list with two items.')


class ProcessImagesPar(ParSet):
    """
    The parameters needed to perform basic image processing.

    These parameters are primarily used by
    :class:`pypeit.processimages.ProcessImages`, the base class of many
    of the pypeit objects.

    For a table with the current keywords, defaults, and descriptions,
    see :ref:`pypeitpar`.
    """
    def __init__(self, overscan=None, overscan_par=None, match=None, combine=None, satpix=None,
                 sigrej=None, n_lohi=None, sig_lohi=None, replace=None, lamaxiter=None, grow=None,
                 rmcompact=None, sigclip=None, sigfrac=None, objlim=None):

        # Grab the parameter names and values from the function
        # arguments
        args, _, _, values = inspect.getargvalues(inspect.currentframe())
        pars = OrderedDict([(k,values[k]) for k in args[1:]])

        # Initialize the other used specifications for this parameter
        # set
        defaults = OrderedDict.fromkeys(pars.keys())
        options = OrderedDict.fromkeys(pars.keys())
        dtypes = OrderedDict.fromkeys(pars.keys())
        descr = OrderedDict.fromkeys(pars.keys())

        # Fill out parameter specifications.  Only the values that are
        # *not* None (i.e., the ones that are defined) need to be set
        defaults['overscan'] = 'savgol'
        options['overscan'] = ProcessImagesPar.valid_overscan()
        dtypes['overscan'] = str
        descr['overscan'] = 'Method used to fit the overscan.  ' \
                            'Options are: {0}'.format(', '.join(options['overscan']))
        
        defaults['overscan_par'] = [5, 65]
        dtypes['overscan_par'] = [int, list]
        descr['overscan_par'] = 'Parameters for the overscan subtraction.  For ' \
                                '\'polynomial\', set overcan_par = order, number of pixels, ' \
                                'number of repeats ; for \'savgol\', set overscan_par = ' \
                                'order, window size ; for \'median\', set overscan_par = ' \
                                'None or omit the keyword.'

        defaults['match'] = -1
        dtypes['match'] = [int, float]
        descr['match'] = '(Deprecate?) Match frames with pixel counts that are within N-sigma ' \
                         'of one another, where match=N below.  If N < 0, nothing is matched.'

        defaults['combine'] = 'weightmean'
        options['combine'] = ProcessImagesPar.valid_combine_methods()
        dtypes['combine'] = str
        descr['combine'] = 'Method used to combine frames.  Options are: {0}'.format(
                                       ', '.join(options['combine']))

        defaults['satpix'] = 'reject'
        options['satpix'] = ProcessImagesPar.valid_saturation_handling()
        dtypes['satpix'] = str
        descr['satpix'] = 'Handling of saturated pixels.  Options are: {0}'.format(
                                       ', '.join(options['satpix']))

        defaults['sigrej'] = 20.0
        dtypes['sigrej'] = [int, float]
        descr['sigrej'] = 'Sigma level to reject cosmic rays (<= 0.0 means no CR removal)'

        defaults['n_lohi'] = [0, 0]
        dtypes['n_lohi'] = list
        descr['n_lohi'] = 'Number of pixels to reject at the lowest and highest ends of the ' \
                          'distribution; i.e., n_lohi = low, high.  Use None for no limit.'

        defaults['sig_lohi'] = [3.0, 3.0]
        dtypes['sig_lohi'] = list
        descr['sig_lohi'] = 'Sigma-clipping level at the low and high ends of the distribution; ' \
                            'i.e., sig_lohi = low, high.  Use None for no limit.'

        defaults['replace'] = 'maxnonsat'
        options['replace'] = ProcessImagesPar.valid_rejection_replacements()
        dtypes['replace'] = str
        descr['replace'] = 'If all pixels are rejected, replace them using this method.  ' \
                           'Options are: {0}'.format(', '.join(options['replace']))

        defaults['lamaxiter'] = 1
        dtypes['lamaxiter'] = int
        descr['lamaxiter'] = 'Maximum number of iterations for LA cosmics routine.'

        defaults['grow'] = 1.5
        dtypes['grow'] = [int, float]
        descr['grow'] = 'Factor by which to expand regions with cosmic rays detected by the ' \
                        'LA cosmics routine.'

        defaults['rmcompact'] = True
        dtypes['rmcompact'] = bool
        descr['rmcompact'] = 'Remove compact detections in LA cosmics routine'

        defaults['sigclip'] = 5.0
        dtypes['sigclip'] = [int, float]
        descr['sigclip'] = 'Sigma level for rejection in LA cosmics routine'

        defaults['sigfrac'] = 0.3
        dtypes['sigfrac'] = [int, float]
        descr['sigfrac'] = 'Fraction for the lower clipping threshold in LA cosmics routine.'

        defaults['objlim'] = 5.0
        dtypes['objlim'] = [int, float]
        descr['objlim'] = 'Object detection limit in LA cosmics routine'

        # Instantiate the parameter set
        super(ProcessImagesPar, self).__init__(list(pars.keys()),
                                               values=list(pars.values()),
                                               defaults=list(defaults.values()),
                                               options=list(options.values()),
                                               dtypes=list(dtypes.values()),
                                               descr=list(descr.values()))

        # Check the parameters match the method requirements
        self.validate()

    @classmethod
    def from_dict(cls, cfg):
        k = cfg.keys()
        parkeys = [ 'overscan', 'overscan_par', 'match', 'combine', 'satpix', 'sigrej', 'n_lohi',
                    'sig_lohi', 'replace', 'lamaxiter', 'grow', 'rmcompact', 'sigclip', 'sigfrac',
                    'objlim' ]
        kwargs = {}
        for pk in parkeys:
            kwargs[pk] = cfg[pk] if pk in k else None
        return cls(**kwargs)

    @staticmethod
    def valid_overscan():
        """
        Return the valid overscan methods.
        """
        return [ 'polynomial', 'savgol', 'median' ]

    @staticmethod
    def valid_combine_methods():
        """
        Return the valid methods for combining frames.
        """
        return [ 'mean', 'median', 'weightmean' ]

    @staticmethod
    def valid_saturation_handling():
        """
        Return the valid approachs to handling saturated pixels.
        """
        return [ 'reject', 'force', 'nothing' ]

    @staticmethod
    def valid_rejection_replacements():
        """
        Return the valid replacement methods for rejected pixels.
        """
        return [ 'min', 'max', 'mean', 'median', 'weightmean', 'maxnonsat' ]

    def validate(self):
        """
        Check the parameters are valid for the provided method.
        """

        if self.data['n_lohi'] is not None and len(self.data['n_lohi']) != 2:
            raise ValueError('n_lohi must be a list of two numbers.')
        if self.data['sig_lohi'] is not None and len(self.data['sig_lohi']) != 2:
            raise ValueError('n_lohi must be a list of two numbers.')

        if self.data['overscan'] is None:
            return
        if self.data['overscan_par'] is None:
            raise ValueError('No overscan method parameters defined!')

        # Convert param to list
        if isinstance(self.data['overscan_par'], int):
            self.data['overscan_par'] = [self.data['overscan_par']]
        
        if self.data['overscan'] == 'polynomial' and len(self.data['overscan_par']) != 3:
            raise ValueError('For polynomial overscan method, set overscan_par = order, '
                             'number of pixels, number of repeats')

        if self.data['overscan'] == 'savgol' and len(self.data['overscan_par']) != 2:
            raise ValueError('For savgol overscan method, set overscan_par = order, window size')
            
        if self.data['overscan'] == 'median' and self.data['overscan_par'] is not None:
            warnings.warn('No parameters necessary for median overscan method.  Ignoring input.')

    def to_header(self, hdr):
        """
        Write the parameters to a header object.
        """
        hdr['OSCANMET'] = (self.data['overscan'], 'Method used for overscan subtraction')
        hdr['OSCANPAR'] = (','.join([ '{0:d}'.format(p) for p in self.data['overscan_par'] ]),
                                'Overscan method parameters')
        hdr['COMBMAT'] = ('{0}'.format(self.data['match']), 'Frame combination matching')
        hdr['COMBMETH'] = (self.data['combine'], 'Method used to combine frames')
        hdr['COMBSATP'] = (self.data['satpix'], 'Saturated pixel handling when combining frames')
        hdr['COMBSIGR'] = ('{0}'.format(self.data['sigrej']),
                                'Cosmic-ray sigma rejection when combining')
        hdr['COMBNLH'] = (','.join([ '{0}'.format(n) for n in self.data['n_lohi']]),
                                'N low and high pixels rejected when combining')
        hdr['COMBSLH'] = (','.join([ '{0:.1f}'.format(s) for s in self.data['sig_lohi']]),
                                'Low and high sigma rejection when combining')
        hdr['COMBREPL'] = (self.data['replace'], 'Method used to replace pixels when combining')
        hdr['LACMAXI'] = ('{0}'.format(self.data['lamaxiter']), 'Max iterations for LA cosmic')
        hdr['LACGRW'] = ('{0:.1f}'.format(self.data['grow']), 'Growth radius for LA cosmic')
        hdr['LACRMC'] = (str(self.data['rmcompact']), 'Compact objects removed by LA cosmic')
        hdr['LACSIGC'] = ('{0:.1f}'.format(self.data['sigclip']), 'Sigma clip for LA cosmic')
        hdr['LACSIGF'] = ('{0:.1f}'.format(self.data['sigfrac']),
                            'Lower clip threshold for LA cosmic')
        hdr['LACOBJL'] = ('{0:.1f}'.format(self.data['objlim']),
                            'Object detect limit for LA cosmic')

    @classmethod
    def from_header(cls, hdr):
        """
        Instantiate the object from parameters read from a fits header.
        """
        return cls(overscan=hdr['OSCANMET'],
                   overscan_par=[int(p) for p in hdr['OSCANPAR'].split(',')],
                   match=eval(hdr['COMBMAT']),
                   combine=hdr['COMBMETH'], satpix=hdr['COMBSATP'],
                   sigrej=eval(hdr['COMBSIGR']),
                   n_lohi=[int(p) for p in hdr['COMBNLH'].split(',')],
                   sig_lohi=[float(p) for p in hdr['COMBSLH'].split(',')],
                   replace=hdr['COMBREPL'],
                   lamaxiter=int(hdr['LACMAXI']), grow=float(hdr['LACGRW']),
                   rmcompact=eval(hdr['LACRMC']), sigclip=float(hdr['LACSIGC']),
                   sigfrac=float(hdr['LACSIGF']), objlim=float(hdr['LACOBJL']))


class FlatFieldPar(ParSet):
    """
    A parameter set holding the arguments for how to perform the field
    flattening.

    For a table with the current keywords, defaults, and descriptions,
    see :ref:`pypeitpar`.
    """
    def __init__(self, frame=None, illumflatten=None, tweak_slits=None, method=None): #, params=None, twodpca=None):
    
        # Grab the parameter names and values from the function
        # arguments
        args, _, _, values = inspect.getargvalues(inspect.currentframe())
        pars = OrderedDict([(k,values[k]) for k in args[1:]])

        # Initialize the other used specifications for this parameter
        # set
        defaults = OrderedDict.fromkeys(pars.keys())
        options = OrderedDict.fromkeys(pars.keys())
        dtypes = OrderedDict.fromkeys(pars.keys())
        descr = OrderedDict.fromkeys(pars.keys())

        # Fill out parameter specifications.  Only the values that are
        # *not* None (i.e., the ones that are defined) need to be set

        # TODO: Provide a list of valid masters to use as options?
        defaults['frame'] = 'pixelflat'
        dtypes['frame'] = str
        descr['frame'] = 'Frame to use for field flattening.  Options are: "pixelflat", ' \
                         'or a specified calibration filename.'

        defaults['illumflatten'] = True
        dtypes['illumflatten'] = bool
        descr['illumflatten'] = 'Use the flat field to determine the illumination profile of each slit.'

        defaults['tweak_slits'] = True
        dtypes['tweak_slits'] = bool
        descr['tweak_slits'] = 'Use the illumination flat field to tweak the slit edges. illumflatten must be set to true for this to work'

        # ToDO This method keyword is defunct now
        defaults['method'] = 'bspline'
        options['method'] = FlatFieldPar.valid_methods()
        dtypes['method'] = str
        descr['method'] = 'Method used to flat field the data; use None to skip flat-fielding.  ' \
                          'Options are: None, {0}'.format(', '.join(options['method']))

        # Instantiate the parameter set
        super(FlatFieldPar, self).__init__(list(pars.keys()),
                                           values=list(pars.values()),
                                           defaults=list(defaults.values()),
                                           options=list(options.values()),
                                           dtypes=list(dtypes.values()),
                                           descr=list(descr.values()))

        # Check the parameters match the method requirements
        self.validate()

    @classmethod
    def from_dict(cls, cfg):
        k = cfg.keys()
        parkeys = [ 'frame', 'illumflatten', 'tweak_slits', 'method'] #', 'params', 'twodpca' ]
        kwargs = {}
        for pk in parkeys:
            kwargs[pk] = cfg[pk] if pk in k else None
        return cls(**kwargs)

    @staticmethod
    def valid_frames():
        """
        Return the valid frame types.
        """

        # ToDO JFH So won't this fail if the user tries to provide a filename?
        return ['pixelflat'] # , 'pinhole'] disabling this for now, we don't seem to be using it. JFH

    @staticmethod
    def valid_methods():
        """
        Return the valid flat-field methods
        """
        return ['bspline'] # [ 'PolyScan', 'bspline' ]. Same here. Not sure what PolyScan is

    def validate(self):
        """
        Check the parameters are valid for the provided method.
        """
        # Convert param to list
        #if isinstance(self.data['params'], int):
        #    self.data['params'] = [self.data['params']]
        
        # Check that there are the correct number of parameters
        #if self.data['method'] == 'PolyScan' and len(self.data['params']) != 3:
        #    raise ValueError('For PolyScan method, set params = order, number of '
        #                     'pixels, number of repeats')
        #if self.data['method'] == 'bspline' and len(self.data['params']) != 1:
        #    raise ValueError('For bspline method, set params = spacing (integer).')
        if self.data['frame'] in FlatFieldPar.valid_frames() or self.data['frame'] is None:
            return

        # Check the frame exists
        if not os.path.isfile(self.data['frame']):
            raise ValueError('Provided frame file name does not exist: {0}'.format(
                                self.data['frame']))

        # Check that if tweak slits is true that illumflatten is alwo true
        if self.data['tweak_slits'] and not self.data['illumflatten']:
            raise ValueError('In order to tweak slits illumflatten must be set to True')



class FlexurePar(ParSet):
    """
    A parameter set holding the arguments for how to perform the flexure
    correction.

    For a table with the current keywords, defaults, and descriptions,
    see :ref:`pypeitpar`.
    """
    def __init__(self, method=None, maxshift=None, spectrum=None):

        # Grab the parameter names and values from the function
        # arguments
        args, _, _, values = inspect.getargvalues(inspect.currentframe())
        pars = OrderedDict([(k,values[k]) for k in args[1:]])

        # Initialize the other used specifications for this parameter
        # set
        defaults = OrderedDict.fromkeys(pars.keys())
        options = OrderedDict.fromkeys(pars.keys())
        dtypes = OrderedDict.fromkeys(pars.keys())
        descr = OrderedDict.fromkeys(pars.keys())

        # Fill out parameter specifications.  Only the values that are
        # *not* None (i.e., the ones that are defined) need to be set
        defaults['method'] = 'boxcar'
        options['method'] = FlexurePar.valid_methods()
        dtypes['method'] = str
        descr['method'] = 'Method used to correct for flexure. Use None for no correction.  If ' \
                          'slitcen is used, the flexure correction is performed before the ' \
                          'extraction of objects.  ' \
                          'Options are: None, {0}'.format(', '.join(options['method']))

        defaults['maxshift'] = 20
        dtypes['maxshift'] = [int, float]
        descr['maxshift'] = 'Maximum allowed flexure shift in pixels.'

        # TODO: THIS IS NOT USED!
        dtypes['spectrum'] = str
        descr['spectrum'] = 'Archive sky spectrum to be used for the flexure correction.'

        # Instantiate the parameter set
        super(FlexurePar, self).__init__(list(pars.keys()),
                                         values=list(pars.values()),
                                         defaults=list(defaults.values()),
                                         options=list(options.values()),
                                         dtypes=list(dtypes.values()),
                                         descr=list(descr.values()))
        self.validate()

    @classmethod
    def from_dict(cls, cfg):
        k = cfg.keys()
        parkeys = [ 'method', 'maxshift', 'spectrum' ]
        kwargs = {}
        for pk in parkeys:
            kwargs[pk] = cfg[pk] if pk in k else None
        return cls(**kwargs)

    @staticmethod
    def valid_frames():
        """
        Return the valid frame types.
        """
        return ['pixelflat', 'pinhole']

    @staticmethod
    def valid_methods():
        """
        Return the valid flat-field methods
        """
        return [ 'boxcar', 'slitcen', 'skip' ]

    def validate(self):
        """
        Check the parameters are valid for the provided method.
        """
        pass
        # TODO: This has to check both the local directory and the
        # directory in the source distribution
#        if self.data['spectrum'] is not None and not os.path.isfile(self.data['spectrum']):
#            raise ValueError('Provided archive spectrum does not exist: {0}.'.format(
#                             self.data['spectrum']))


class FluxCalibrationPar(ParSet):
    """
    A parameter set holding the arguments for how to perform the flux
    calibration.

    For a table with the current keywords, defaults, and descriptions,
    see :ref:`pypeitpar`.
    """
    def __init__(self, nonlinear=None, sensfunc=None):

        # Grab the parameter names and values from the function
        # arguments
        args, _, _, values = inspect.getargvalues(inspect.currentframe())
        pars = OrderedDict([(k,values[k]) for k in args[1:]])

        # Initialize the other used specifications for this parameter
        # set
        defaults = OrderedDict.fromkeys(pars.keys())
        dtypes = OrderedDict.fromkeys(pars.keys())
        descr = OrderedDict.fromkeys(pars.keys())

        # Fill out parameter specifications.  Only the values that are
        # *not* None (i.e., the ones that are defined) need to be set
        # TODO: I don't think this is used anywhere
        defaults['nonlinear'] = False
        dtypes['nonlinear'] = bool
        descr['nonlinear'] = 'Perform a non-linear correction.  Requires a series of ' \
                             'pixelflats of the same lamp and setup and with a variety of ' \
                             'exposure times and count rates in every pixel.'

        dtypes['sensfunc'] = str
        descr['sensfunc'] = 'YAML file with an existing calibration function'

        # Instantiate the parameter set
        super(FluxCalibrationPar, self).__init__(list(pars.keys()),
                                                 values=list(pars.values()),
                                                 defaults=list(defaults.values()),
                                                 dtypes=list(dtypes.values()),
                                                 descr=list(descr.values()))
        self.validate()

    @classmethod
    def from_dict(cls, cfg):
        k = cfg.keys()
        parkeys = [ 'nonlinear', 'sensfunc' ]
        kwargs = {}
        for pk in parkeys:
            kwargs[pk] = cfg[pk] if pk in k else None
        return cls(**kwargs)

    def validate(self):
        """
        Check the parameters are valid for the provided method.
        """
        if self.data['sensfunc'] is not None and not os.path.isfile(self.data['sensfunc']):
            raise ValueError('Provided sensitivity function does not exist: {0}.'.format(
                             self.data['sensfunc']))

# JFH TODO this parset is now deprecated
# TODO: What other parameters should there be?
class SkySubtractionPar(ParSet):
    """
    A parameter set holding the arguments for how to perform the sky
    subtraction.

    For a table with the current keywords, defaults, and descriptions,
    see :ref:`pypeitpar`.
    """
    def __init__(self, bspline_spacing=None, nodding=None): #method=None, params=None):

        # Grab the parameter names and values from the function
        # arguments
        args, _, _, values = inspect.getargvalues(inspect.currentframe())
        pars = OrderedDict([(k,values[k]) for k in args[1:]])

        # Initialize the other used specifications for this parameter
        # set
        defaults = OrderedDict.fromkeys(pars.keys())
        options = OrderedDict.fromkeys(pars.keys())
        dtypes = OrderedDict.fromkeys(pars.keys())
        descr = OrderedDict.fromkeys(pars.keys())

        # Fill out parameter specifications.  Only the values that are
        # *not* None (i.e., the ones that are defined) need to be set

        defaults['bspline_spacing'] = 0.6
        dtypes['bspline_spacing'] = [int, float]
        descr['bspline_spacing'] = 'Break-point spacing for the bspline fit'

        defaults['nodding'] = False
        dtypes['nodding'] = bool
        descr['nodding'] = 'Use the nodded frames to perform the sky subtraction'

#        defaults['method'] = 'bspline'
#        options['method'] = SkySubtractionPar.valid_methods()
#        dtypes['method'] = str
#        descr['method'] = 'Method used to for sky subtraction.  ' \
#                          'Options are: None, {0}'.format(', '.join(options['method']))
#
#        defaults['params'] = 20
#        dtypes['params'] = int
#        descr['params'] = 'Sky-subtraction method parameters.  For bspline, set params = spacing.'

        # Instantiate the parameter set
        super(SkySubtractionPar, self).__init__(list(pars.keys()),
                                                values=list(pars.values()),
                                                defaults=list(defaults.values()),
                                                options=list(options.values()),
                                                dtypes=list(dtypes.values()),
                                                descr=list(descr.values()))
        self.validate()

    @classmethod
    def from_dict(cls, cfg):
        k = cfg.keys()
        parkeys = [ 'bspline_spacing', 'nodding' ] #'method', 'params' ]
        kwargs = {}
        for pk in parkeys:
            kwargs[pk] = cfg[pk] if pk in k else None
        return cls(**kwargs)

#    @staticmethod
#    def valid_methods():
#        """
#        Return the valid sky-subtraction methods
#        """
#        return [ 'bspline' ]

    def validate(self):
        pass

#        """
#        Check the parameters are valid for the provided method.
#        """
#        if self.data['method'] == 'bspline' and not isinstance(self.data['params'], int):
#            raise ValueError('For bspline sky-subtraction method, set params = spacing (integer).')


class ManualExtractionPar(ParSet):
    """
    A parameter set holding the arguments for how to perform the
    manual extraction of a spectrum.

    A list of these objects can be included in an instance of
    :class:`ExtractObjectsPar` to perform a set of user-defined
    extractions.

    For an example of how to define a series of manual extractions in
    the pypeit input file, see :ref:`pypeit_file`.

    Args:
        frame (:obj:`str`):
            The name of the fits file for a manual extraction
        spec = List of spectral positions to hand extract
        spat = List of spatial positions to hand extract
        det = List of detectors for hand extraction. This must be a list aligned with spec and spat lists, or a single integer
             which will be used for all members of that list
        fwhm = List of FWHM for hand extraction. This must be a list aligned with spec and spat lists, or a single number which will
             be used for all members of that list'


    """
    def __init__(self, frame=None, spec=None, spat = None, det = None, fwhm = None):

        # Grab the parameter names and values from the function
        # arguments
        args, _, _, values = inspect.getargvalues(inspect.currentframe())
        pars = OrderedDict([(k,values[k]) for k in args[1:]])

        # Initialize the other used specifications for this parameter
        # set
        dtypes = OrderedDict.fromkeys(pars.keys())
        descr = OrderedDict.fromkeys(pars.keys())

        # Fill out parameter specifications.  Only the values that are
        # *not* None (i.e., the ones that are defined) need to be set
        dtypes['frame'] = str
        descr['frame'] = 'The name of the fits file for a manual extraction'

        dtypes['spec'] = [list, float, int]
        descr['spec'] = 'List of spectral positions to hand extract '

        dtypes['spat'] = [list, float, int]
        descr['spat'] = 'List of spatial positions to hand extract '

        dtypes['det'] = [list, int]
        descr['det'] = 'List of detectors for hand extraction. This must be a list aligned with spec and spat lists, or a single integer which will be used for all members of that list'
        dtypes['fwhm'] = [list, int,float]
        descr['fwhm'] = 'List of FWHM for hand extraction. This must be a list aligned with spec and spat lists, or a single number which will be used for all members of that list'

        # Instantiate the parameter set
        super(ManualExtractionPar, self).__init__(list(pars.keys()),
                                                  values=list(pars.values()),
                                                  dtypes=list(dtypes.values()),
                                                  descr=list(descr.values()))
        self.validate()

    @classmethod
    def from_dict(cls, cfg):
        k = cfg.keys()
        parkeys = [ 'frame', 'spec','spat','det','fwhm']
        kwargs = {}
        for pk in parkeys:
            kwargs[pk] = cfg[pk] if pk in k else None
        return cls(**kwargs)

    def validate(self):
        pass



class ManualExtractionParOld(ParSet):
    """
    A parameter set holding the arguments for how to perform the
    manual extraction of a spectrum.

    A list of these objects can be included in an instance of
    :class:`ExtractObjectsPar` to perform a set of user-defined
    extractions.

    For an example of how to define a series of manual extractions in
    the pypeit input file, see :ref:`pypeit_file`.

    Args:
        frame (:obj:`str`):
            The name of the fits file for a manual extraction

        params (:obj:`list`):
            Parameters of the manual extraction.  For example, params =
            1,1000,500,10,10 specifies the following behavior: 1 is the
            detector number, 1000 is the spatial location that the trace
            must go through, 500 is the spectral location that the trace
            must go through, and the last two numbers (10,10) are the
            widths around the stated (spatial,spectral) location that
            should also be in the trace.'
    """
    def __init__(self, frame=None, params=None):

        # Grab the parameter names and values from the function
        # arguments
        args, _, _, values = inspect.getargvalues(inspect.currentframe())
        pars = OrderedDict([(k,values[k]) for k in args[1:]])

        # Initialize the other used specifications for this parameter
        # set
        dtypes = OrderedDict.fromkeys(pars.keys())
        descr = OrderedDict.fromkeys(pars.keys())

        # Fill out parameter specifications.  Only the values that are
        # *not* None (i.e., the ones that are defined) need to be set
        dtypes['frame'] = str
        descr['frame'] = 'The name of the fits file for a manual extraction'

        dtypes['params'] = list
        descr['params'] = 'Parameters of the manual extraction.  For example, params = ' \
                          '1,1000,500,10,10 specifies the following behavior: 1 is the ' \
                          'detector number, 1000 is the spatial location that the trace must ' \
                          'go through, 500 is the spectral location that the trace must go ' \
                          'through, and the last two numbers (10,10) are the widths around the ' \
                          'stated (spatial,spectral) location that should also be in the trace.'

        # Instantiate the parameter set
        super(ManualExtractionPar, self).__init__(list(pars.keys()),
                                                  values=list(pars.values()),
                                                  dtypes=list(dtypes.values()),
                                                  descr=list(descr.values()))
        self.validate()

    @classmethod
    def from_dict(cls, cfg):
        k = cfg.keys()
        parkeys = [ 'frame', 'params' ]
        kwargs = {}
        for pk in parkeys:
            kwargs[pk] = cfg[pk] if pk in k else None
        return cls(**kwargs)

    def validate(self):
        """
        Check the parameters are valid for the provided method.
        """
        if self.data['params'] is not None and len(self.data['params']) != 5:
            raise ValueError('There must be 5 manual extraction parameters.')
        if self.data['frame'] is not None and not os.path.isfile(self.data['frame']):
            raise FileNotFoundError('Manual extraction frame does not exist: {0}'.format(
                                    self.data['frame']))



class ReducePar(ParSet):
    """
    The parameter set used to hold arguments for functionality relevant
    to the overal reduction of the the data.
    
    Critically, this parameter set defines the spectrograph that was
    used to collect the data and the overall pipeline used in the
    reductions.
    
    For a table with the current keywords, defaults, and descriptions,
    see :ref:`pypeitpar`.
    """
    def __init__(self, spectrograph=None, detnum=None, sortroot=None, calwin=None, scidir=None,
                 qadir=None, redux_path=None):

        # Grab the parameter names and values from the function
        # arguments
        args, _, _, values = inspect.getargvalues(inspect.currentframe())
        pars = OrderedDict([(k,values[k]) for k in args[1:]])      # "1:" to skip 'self'

        # Initialize the other used specifications for this parameter
        # set
        defaults = OrderedDict.fromkeys(pars.keys())
        options = OrderedDict.fromkeys(pars.keys())
        dtypes = OrderedDict.fromkeys(pars.keys())
        descr = OrderedDict.fromkeys(pars.keys())

        # Fill out parameter specifications.  Only the values that are
        # *not* None (i.e., the ones that are defined) need to be set
        options['spectrograph'] = ReducePar.valid_spectrographs()
        dtypes['spectrograph'] = str
        descr['spectrograph'] = 'Spectrograph that provided the data to be reduced.  ' \
                                'Options are: {0}'.format(', '.join(options['spectrograph']))

        dtypes['detnum'] = [int, list]
        descr['detnum'] = 'Restrict reduction to a list of detector indices'

        dtypes['sortroot'] = str
        descr['sortroot'] = 'A filename given to output the details of the sorted files.  If ' \
                            'None, the default is the root name of the pypeit file.  If off, ' \
                            'no output is produced.'

        defaults['calwin'] = 0
        dtypes['calwin']   = [int, float]
        descr['calwin'] = 'The window of time in hours to search for calibration frames for a ' \
                          'science frame'

        defaults['scidir'] = 'Science'
        dtypes['scidir'] = str
        descr['scidir'] = 'Directory relative to calling directory to write science files.'

        defaults['qadir'] = 'QA'
        dtypes['qadir'] = str
        descr['qadir'] = 'Directory relative to calling directory to write quality ' \
                         'assessment files.'

        defaults['redux_path'] = os.getcwd()
        dtypes['redux_path'] = str
        descr['redux_path'] = 'Path to folder for performing reductions.'

        # Instantiate the parameter set
        super(ReducePar, self).__init__(list(pars.keys()),
                                        values=list(pars.values()),
                                        defaults=list(defaults.values()),
                                        options=list(options.values()),
                                        dtypes=list(dtypes.values()),
                                        descr=list(descr.values()))
        self.validate()

    @classmethod
    def from_dict(cls, cfg):
        k = cfg.keys()

        # Basic keywords
        parkeys = [ 'spectrograph', 'detnum', 'sortroot', 'calwin', 'scidir', 'qadir',
                    'redux_path']
        kwargs = {}
        for pk in parkeys:
            kwargs[pk] = cfg[pk] if pk in k else None
        return cls(**kwargs)

    @staticmethod
    def valid_spectrographs():
        # WARNING: Needs this to determine the valid spectrographs.
        # Should use pypeit.spectrographs.util.valid_spectrographs
        # instead, but it causes a circular import.  Spectrographs have
        # to be redefined here.   To fix this, spectrograph specific
        # parameter sets (like DetectorPar) and where they go needs to
        # be rethought.
        return ['gemini_gnirs','keck_deimos', 'keck_lris_blue', 'keck_lris_red', 'keck_nires', 'keck_nirspec',
                'shane_kast_blue', 'shane_kast_red', 'shane_kast_red_ret', 'tng_dolores',
                'wht_isis_blue', 'vlt_fors2_chip1', 'vlt_xshooter_uvb', 'vlt_xshooter_vis',
                'vlt_xshooter_nir', 'gemini_gmos_south', 'gemini_gmos_north_e2v', 'gemini_gmos_north_ham']

    def validate(self):
        pass

    
class WavelengthSolutionPar(ParSet):
    """
    The parameter set used to hold arguments for the determination of
    wavelength solution.
    
    For a table with the current keywords, defaults, and descriptions,
    see :ref:`pypeitpar`.
    """
    def __init__(self, reference=None, method=None, lamps=None, rms_threshold=None, numsearch=None,
                 nfitpix=None, IDpixels=None, IDwaves=None, medium=None, frame=None, min_nsig=None, lowest_nsig=None):
        # Grab the parameter names and values from the function
        # arguments
        args, _, _, values = inspect.getargvalues(inspect.currentframe())
        pars = OrderedDict([(k,values[k]) for k in args[1:]])

        # Initialize the other used specifications for this parameter
        # set
        defaults = OrderedDict.fromkeys(pars.keys())
        options = OrderedDict.fromkeys(pars.keys())
        dtypes = OrderedDict.fromkeys(pars.keys())
        descr = OrderedDict.fromkeys(pars.keys())

        # Fill out parameter specifications.  Only the values that are
        # *not* None (i.e., the ones that are defined) need to be set
        # TODO: Only test for 'pixel' is ever used. I.e. 'arc' or 'sky'
        # does not make a difference.
        defaults['reference'] = 'arc'
        options['reference'] = WavelengthSolutionPar.valid_reference()
        dtypes['reference'] = str
        descr['reference'] = 'Perform wavelength calibration with an arc, sky frame.  Use ' \
                             '\'pixel\' for no wavelength solution.'

        defaults['method'] = 'arclines'
        options['method'] = WavelengthSolutionPar.valid_methods()
        dtypes['method'] = str
        descr['method'] = 'Method to use to fit the individual arc lines.  ' \
                          '\'fit\' is likely more accurate, but \'simple\' uses a polynomial ' \
                          'fit (to the log of a gaussian) and is fast and reliable.  ' \
                          '\'arclines\' uses the arclines python package.' \
                          'Options are: {0}'.format(', '.join(options['method']))

        # TODO: Not used
        # Force lamps to be a list
        if pars['lamps'] is not None and not isinstance(pars['lamps'], list):
            pars['lamps'] = [pars['lamps']]
        options['lamps'] = WavelengthSolutionPar.valid_lamps()
        dtypes['lamps'] = list
        descr['lamps'] = 'Name of one or more ions used for the wavelength calibration.  Use ' \
                         'None for no calibration.  ' \
                         'Options are: {0}'.format(', '.join(options['lamps']))

        defaults['rms_threshold'] = 0.15
        dtypes['rms_threshold'] = float
        descr['rms_threshold'] = 'Minimum RMS for keeping a slit solution'

        defaults['min_nsig'] = 5.
        dtypes['min_nsig'] = float
        descr['min_nsig'] = 'Detection threshold for arc lines for "standard" lines'

        defaults['lowest_nsig'] = 5.
        dtypes['lowest_nsig'] = float
        descr['lowest_nsig'] = 'Detection threshold for arc lines for "weakest" lines'

        # TODO: Not used
        defaults['numsearch'] = 20
        dtypes['numsearch'] = int
        descr['numsearch'] = 'Number of brightest arc lines to search for in preliminary ' \
                             'identification'

        defaults['nfitpix'] = 5
        dtypes['nfitpix'] = int
        descr['nfitpix'] = 'Number of pixels to fit when deriving the centroid of the arc ' \
                           'lines (an odd number is best)'

        dtypes['IDpixels'] = [int, float, list]
        descr['IDpixels'] = 'One or more pixels at which to manually identify a line'

        dtypes['IDwaves'] = [int, float, list]
        descr['IDwaves'] = 'Wavelengths of the manually identified lines'

        # TODO: Not used
        defaults['medium'] = 'vacuum'
        options['medium'] = WavelengthSolutionPar.valid_media()
        dtypes['medium'] = str
        descr['medium'] = 'Medium used when wavelength calibrating the data.  ' \
                          'Options are: {0}'.format(', '.join(options['medium']))

        # TODO: What should the default be?  None or 'heliocentric'?
        defaults['frame'] = 'heliocentric'
        options['frame'] = WavelengthSolutionPar.valid_reference_frames()
        dtypes['frame'] = str
        descr['frame'] = 'Frame of reference for the wavelength calibration.  ' \
                         'Options are: {0}'.format(', '.join(options['frame']))


        # Instantiate the parameter set
        super(WavelengthSolutionPar, self).__init__(list(pars.keys()),
                                                    values=list(pars.values()),
                                                    defaults=list(defaults.values()),
                                                    options=list(options.values()),
                                                    dtypes=list(dtypes.values()),
                                                    descr=list(descr.values()))
        self.validate()

    @classmethod
    def from_dict(cls, cfg):
        k = cfg.keys()
        parkeys = [ 'reference', 'method', 'lamps', 'rms_threshold', 'numsearch', 'nfitpix',
                    'IDpixels', 'IDwaves', 'medium', 'frame', 'min_nsig', 'lowest_nsig' ]
        kwargs = {}
        for pk in parkeys:
            kwargs[pk] = cfg[pk] if pk in k else None
        return cls(**kwargs)

    @staticmethod
    def valid_reference():
        """
        Return the valid wavelength solution methods.
        """
        return [ 'arc', 'sky', 'pixel' ]

    @staticmethod
    def valid_methods():
        """
        Return the valid wavelength solution methods.
        """
        return [ 'simple', 'fit', 'arclines' ]

    @staticmethod
    def valid_lamps():
        """
        Return the valid lamp ions
        """
        return [ 'ArI', 'CdI', 'HgI', 'HeI', 'KrI', 'NeI', 'XeI', 'ZnI', 'ThAr' ]

    @staticmethod
    def valid_media():
        """
        Return the valid media for the wavelength calibration.
        """
        return [ 'vacuum', 'air' ]

    @staticmethod
    def valid_reference_frames():
        """
        Return the valid reference frames for the wavelength calibration
        """
        return [ 'heliocentric', 'barycentric' ]

    def validate(self):
        pass


class TraceSlitsPar(ParSet):
    """
    The parameter set used to hold arguments for tracing the slit
    positions along the dispersion axis.
    
    For a table with the current keywords, defaults, and descriptions,
    see :ref:`pypeitpar`.
    """
    def __init__(self, function=None, polyorder=None, medrep=None, number=None, trim=None,
                 maxgap=None, maxshift=None, pad=None, sigdetect=None, fracignore=None,
                 min_slit_width = None,
                 diffpolyorder=None, single=None, sobel_mode=None, pcatype=None, pcapar=None,
                 pcaextrap=None):

        # Grab the parameter names and values from the function
        # arguments
        args, _, _, values = inspect.getargvalues(inspect.currentframe())
        pars = OrderedDict([(k,values[k]) for k in args[1:]])      # "1:" to skip 'self'

        # Initialize the other used specifications for this parameter
        # set
        defaults = OrderedDict.fromkeys(pars.keys())
        options = OrderedDict.fromkeys(pars.keys())
        dtypes = OrderedDict.fromkeys(pars.keys())
        descr = OrderedDict.fromkeys(pars.keys())

        # Fill out parameter specifications.  Only the values that are
        # *not* None (i.e., the ones that are defined) need to be set

        defaults['function'] = 'legendre'
        options['function'] = TraceSlitsPar.valid_functions()
        dtypes['function'] = str
        descr['function'] = 'Function use to trace the slit center.  ' \
                            'Options are: {0}'.format(', '.join(options['function']))

        defaults['polyorder'] = 3
        dtypes['polyorder'] = int
        descr['polyorder'] = 'Order of the function to use.'

        defaults['medrep'] = 0
        dtypes['medrep'] = int
        descr['medrep'] = 'Number of times to median smooth a trace image prior to analysis ' \
                          'for slit/order edges'

        # Force number to be an integer
        if values['number'] == 'auto':
            values['number'] = -1
        defaults['number'] = -1
        dtypes['number'] = int
        descr['number'] = 'Manually set the number of slits to identify (>=1). \'auto\' or -1 ' \
                          'will automatically identify the number of slits.'

        # Force trim to be a tuple
        if pars['trim'] is not None and not isinstance(pars['trim'], tuple):
            try:
                pars['trim'] = tuple(pars['trim'])
            except:
                raise TypeError('Could not convert provided trim to a tuple.')
        defaults['trim'] = (3,3)
        dtypes['trim'] = tuple
        descr['trim'] = 'How much to trim off each edge of each slit'

        dtypes['maxgap'] = int
        descr['maxgap'] = 'Maximum number of pixels to allow for the gap between slits.  Use ' \
                          'None if the neighbouring slits are far apart or of similar ' \
                          'illumination.'

        defaults['maxshift'] = 0.15
        dtypes['maxshift'] = [int, float]
        descr['maxshift'] = 'Maximum shift in trace crude'

        defaults['pad'] = 0
        dtypes['pad'] = int
        descr['pad'] = 'Integer number of pixels to consider beyond the slit edges.'

        defaults['sigdetect'] = 20.0
        dtypes['sigdetect'] = [int, float]
        descr['sigdetect'] = 'Sigma detection threshold for edge detection'
    
        defaults['fracignore'] = 0.01
        dtypes['fracignore'] = float
        descr['fracignore'] = 'If a slit spans less than this fraction over the spectral size ' \
                              'of the detector, it will be ignored (and reconstructed when/if ' \
                              'an \'order\' PCA analysis is performed).'

        defaults['min_slit_width'] = 6.0  # arcseconds!
        dtypes['min_slit_width'] = float
        descr['min_slit_width'] = 'If a slit spans less than this number of arcseconds over the spatial ' \
                                  'direction of the detector, it will be ignored. Use this option to prevent the ' \
                                  'of alignment (box) slits from multislit reductions, which typically cannot be reduced ' \
                                  'without a significant struggle'

        defaults['diffpolyorder'] = 2
        dtypes['diffpolyorder'] = int
        descr['diffpolyorder'] = 'Order of the 2D function used to fit the 2d solution for the ' \
                                 'spatial size of all orders.'

        defaults['single'] = []
        dtypes['single'] = list
        descr['single'] = 'Add a single, user-defined slit based on its location on each ' \
                          'detector.  Syntax is a list of values, 2 per detector, that define ' \
                          'the slit according to column values.  The second value (for the ' \
                          'right edge) must be greater than 0 to be applied.  LRISr example: ' \
                          'setting single = -1, -1, 7, 295 means the code will skip the ' \
                          'user-definition for the first detector but adds one for the second. ' \
                          ' None means no user-level slits defined.'

        defaults['sobel_mode'] = 'nearest'
        options['sobel_mode'] = TraceSlitsPar.valid_sobel_modes()
        dtypes['sobel_mode'] = str
        descr['sobel_mode'] = 'Mode for Sobel filtering.  Default is \'nearest\' but the ' \
                              'developers find \'constant\' works best for DEIMOS.'

        defaults['pcatype'] = 'pixel'
        options['pcatype'] = TraceSlitsPar.valid_pca_types()
        dtypes['pcatype'] = str
        descr['pcatype'] = 'Select to perform the PCA using the pixel position (pcatype=pixel) ' \
                           'or by spectral order (pcatype=order).  Pixel positions can be used ' \
                           'for multi-object spectroscopy where the gap between slits is ' \
                           'irregular.  Order is used for echelle spectroscopy or for slits ' \
                           'with separations that are a smooth function of the slit number.'

        defaults['pcapar'] = [ 3, 2, 1, 0]
        dtypes['pcapar'] = list
        descr['pcapar'] = 'Order of the polynomials to be used to fit the principle ' \
                          'components.  The list length must be equal to or less than polyorder+1. ' \
                          'TODO: Provide more explanation'

        defaults['pcaextrap'] = [0, 0]
        dtypes['pcaextrap'] = list
        descr['pcaextrap'] = 'The number of extra orders to predict in the negative (first ' \
                             'number) and positive (second number) direction.  Must be two ' \
                             'numbers in the list and they must be integers.'

        # Instantiate the parameter set
        super(TraceSlitsPar, self).__init__(list(pars.keys()),
                                            values=list(pars.values()),
                                            defaults=list(defaults.values()),
                                            options=list(options.values()),
                                            dtypes=list(dtypes.values()),
                                            descr=list(descr.values()))
        self.validate()

    @classmethod
    def from_dict(cls, cfg):
        k = cfg.keys()
        parkeys = [ 'function', 'polyorder', 'medrep', 'number', 'trim', 'maxgap', 'maxshift',
                    'pad', 'sigdetect', 'fracignore', 'min_slit_width', 'diffpolyorder', 'single', 'sobel_mode',
                    'pcatype', 'pcapar', 'pcaextrap' ]
        kwargs = {}
        for pk in parkeys:
            kwargs[pk] = cfg[pk] if pk in k else None
        return cls(**kwargs)

    @staticmethod
    def valid_functions():
        """
        Return the list of valid functions to use for slit tracing.
        """
        return [ 'polynomial', 'legendre', 'chebyshev' ]

    @staticmethod
    def valid_sobel_modes():
        """Return the valid sobel modes."""
        return [ 'nearest', 'constant' ]

    @staticmethod
    def valid_pca_types():
        """
        Return the valid PCA types.
        """
        return ['pixel', 'order']

    def validate(self):
        if self.data['number'] == 0:
            raise ValueError('Number of slits must be -1 for automatic identification or '
                             'greater than 0')
        if len(self.data['pcaextrap']) != 2:
            raise ValueError('PCA extrapolation parameters must be a list with two values.')
        for e in self.data['pcaextrap']:
            if not isinstance(e, int):
                raise ValueError('PCA extrapolation values must be integers.')

class WaveTiltsPar(ParSet):
    """
    The parameter set used to hold arguments for tracing the
    monochromatic tilt along the slit.
    
    For a table with the current keywords, defaults, and descriptions,
    see :ref:`pypeitpar`.

    .. todo::
        Changed to reflect wavetilts.py settings.  Was `yorder`
        previously `disporder`?  If so, I think I prefer the generality
        of `disporder`...
    """
    def __init__(self, idsonly=None, tracethresh=None, order=None, function=None, yorder=None,
                 func2D=None, method=None, params=None):


        # Grab the parameter names and values from the function
        # arguments
        args, _, _, values = inspect.getargvalues(inspect.currentframe())
        pars = OrderedDict([(k,values[k]) for k in args[1:]])      # "1:" to skip 'self'

        # Initialize the other used specifications for this parameter
        # set
        defaults = OrderedDict.fromkeys(pars.keys())
        options = OrderedDict.fromkeys(pars.keys())
        dtypes = OrderedDict.fromkeys(pars.keys())
        descr = OrderedDict.fromkeys(pars.keys())

        # Fill out parameter specifications.  Only the values that are
        # *not* None (i.e., the ones that are defined) need to be set

        defaults['idsonly'] = False
        dtypes['idsonly'] = bool
        descr['idsonly'] = 'Only use the arc lines that have an identified wavelength to trace ' \
                           'tilts'

        defaults['tracethresh'] = 20.
        dtypes['tracethresh'] = [int, float, list, numpy.ndarray]
        descr['tracethresh'] = 'Significance threshold for arcs to be used in tracing wavelength tilts.'

        defaults['order'] = 2
        dtypes['order'] = int
        descr['order'] = 'Order of the polynomial function to be used for the tilt of an ' \
                         'individual arc line.  Must be 1 for echelle data (Echelle pipeline).'

        defaults['function'] = 'legendre'
        # TODO: Allowed values?
        dtypes['function'] = str
        descr['function'] = 'Type of function for arc line fits'

        defaults['yorder'] = 4
        dtypes['yorder'] = int
        descr['yorder'] = 'Order of the polynomial function to be used to fit the tilts ' \
                          'along the y direction.'

        defaults['func2D'] = 'legendre'
        # TODO: Allowed values?
        dtypes['func2D'] = str
        descr['func2D'] = 'Type of function for 2D fit'

        defaults['method'] = 'spca'
        options['method'] = WaveTiltsPar.valid_methods()
        dtypes['method'] = str
        descr['method'] = 'Method used to trace the tilt of the slit along an order.  ' \
                          'Options are: {0}'.format(', '.join(options['method']))

        # TODO: Need to add checks that check params against method
        defaults['params'] = [ 1, 1, 0 ]
        dtypes['params'] = [ int, list ]
        descr['params'] = 'Parameters to use for the provided method.  TODO: Need more explanation'

        # Instantiate the parameter set
        super(WaveTiltsPar, self).__init__(list(pars.keys()),
                                            values=list(pars.values()),
                                            defaults=list(defaults.values()),
                                            options=list(options.values()),
                                            dtypes=list(dtypes.values()),
                                            descr=list(descr.values()))
        self.validate()

    @classmethod
    def from_dict(cls, cfg):
        k = cfg.keys()
        parkeys = [ 'idsonly', 'tracethresh', 'order', 'function', 'yorder', 'func2D',
                    'method', 'params' ]
        kwargs = {}
        for pk in parkeys:
            kwargs[pk] = cfg[pk] if pk in k else None
        return cls(**kwargs)

    @staticmethod
    def valid_methods():
        """
        Return the valid methods to use for tilt tracing.
        """
        return [ 'pca', 'spca', 'spline', 'interp', 'perp', 'zero' ]

    def validate(self):
        # Convert param to list
        if isinstance(self.data['params'], int):
            self.data['params'] = [self.data['params']]
        pass

# TODO: JFH. This parameter class is now deprecated
# From artrace.trace_objects_in_slit
#       trim=2, triml=None, trimr=None, sigmin=2.0, bgreg=None
class TraceObjectsPar(ParSet):
    """
    The parameter set used to hold arguments for tracing one or more
    objects within a slit.
    
    For a table with the current keywords, defaults, and descriptions,
    see :ref:`pypeitpar`.
    """
    def __init__(self, function=None, order=None, find=None, nsmooth=None, xedge=None, method=None,
                 params=None):

        # Grab the parameter names and values from the function
        # arguments
        args, _, _, values = inspect.getargvalues(inspect.currentframe())
        pars = OrderedDict([(k,values[k]) for k in args[1:]])      # "1:" to skip 'self'

        # Initialize the other used specifications for this parameter
        # set
        defaults = OrderedDict.fromkeys(pars.keys())
        options = OrderedDict.fromkeys(pars.keys())
        dtypes = OrderedDict.fromkeys(pars.keys())
        descr = OrderedDict.fromkeys(pars.keys())

        # Fill out parameter specifications.  Only the values that are
        # *not* None (i.e., the ones that are defined) need to be set
        defaults['function'] = 'legendre'
        options['function'] = TraceObjectsPar.valid_functions()
        dtypes['function'] = str
        descr['function'] = 'Function to use to trace the object in each slit.  ' \
                            'Options are: {0}'.format(options['function'])

        defaults['order'] = 2
        dtypes['order'] = int
        descr['order'] = 'Order of the function to use to fit the object trace in each slit'

        defaults['find'] = 'standard'
        options['find'] = TraceObjectsPar.valid_detection_algorithms()
        dtypes['find'] = str
        descr['find'] = 'Algorithm to use for finding objects.' \
                        'Options are: {0}'.format(', '.join(options['find']))

        defaults['nsmooth'] = 3
        dtypes['nsmooth'] = [int, float]
        descr['nsmooth'] = 'Parameter for Gaussian smoothing when find=nminima.'

        defaults['xedge'] = 0.03
        dtypes['xedge'] = float
        descr['xedge'] = 'Ignore any objects within xedge of the edge of the slit'

        defaults['method'] = 'pca'
        options['method'] = TraceObjectsPar.valid_methods()
        dtypes['method'] = str
        descr['method'] = 'Method to use for tracing each object; only used with Echelle ' \
                          'pipeline.  Options are: {0}'.format(', '.join(options['method']))

        defaults['params'] = [1, 0]
        dtypes['params'] = [int, list]
        descr['params'] = 'Parameters for the requested method.  For pca, params is a list ' \
                          'containing the order of the polynomials that should be used to fit ' \
                          'the object trace principal components. For example, params = 1, 0 ' \
                          'will fit 2 principal components, the first PC will be fit with a ' \
                          'first order polynomial, the second PC will be fit with a zeroth ' \
                          'order polynomial. TODO: What about the other methods?'

        # Instantiate the parameter set
        super(TraceObjectsPar, self).__init__(list(pars.keys()),
                                              values=list(pars.values()),
                                              defaults=list(defaults.values()),
                                              options=list(options.values()),
                                              dtypes=list(dtypes.values()),
                                              descr=list(descr.values()))
        self.validate()

    @classmethod
    def from_dict(cls, cfg):
        k = cfg.keys()
        parkeys = [ 'function', 'order', 'find', 'nsmooth', 'xedge', 'method', 'params' ]
        kwargs = {}
        for pk in parkeys:
            kwargs[pk] = cfg[pk] if pk in k else None
        return cls(**kwargs)

    @staticmethod
    def valid_functions():
        """
        Return the list of valid functions to use for object tracing.
        """
        return [ 'polynomial', 'legendre', 'chebyshev' ]

    @staticmethod
    def valid_detection_algorithms():
        """
        Return the list of valid algorithms for detecting objects.
        """
        return [ 'standard', 'nminima' ]

    @staticmethod
    def valid_methods():
        """
        Return the valid methods to use for tilt tracing.
        """
        return [ 'pca', 'spca', 'spline', 'interp', 'perp', 'zero' ]

    def validate(self):
        # Convert param to list
        if isinstance(self.data['params'], int):
            self.data['params'] = [self.data['params']]
        pass

# TODO JFH This parset is now deprecated.
class ExtractObjectsPar(ParSet):
    """
    The parameter set used to hold arguments for extracting object
    spectra.
    
    For a table with the current keywords, defaults, and descriptions,
    see :ref:`pypeitpar`.
    """
    def __init__(self, pixelmap=None, pixelwidth=None, reuse=None, profile=None, maxnumber=None,
                 manual=None):

        # Grab the parameter names and values from the function
        # arguments
        args, _, _, values = inspect.getargvalues(inspect.currentframe())
        pars = OrderedDict([(k,values[k]) for k in args[1:]])      # "1:" to skip 'self'

        # Check the manual input
        if manual is not None:
            if not isinstance(manual, (ParSet, dict, list)):
                raise TypeError('Manual extraction input must be a ParSet, dictionary, or list.')
            _manual = [manual] if isinstance(manual, (ParSet,dict)) else manual
            pars['manual'] = _manual

        # Initialize the other used specifications for this parameter
        # set
        defaults = OrderedDict.fromkeys(pars.keys())
        options = OrderedDict.fromkeys(pars.keys())
        dtypes = OrderedDict.fromkeys(pars.keys())
        descr = OrderedDict.fromkeys(pars.keys())

        # Fill out parameter specifications.  Only the values that are
        # *not* None (i.e., the ones that are defined) need to be set
        dtypes['pixelmap'] = str
        descr['pixelmap'] = 'If desired, a fits file can be specified (of the appropriate form)' \
                            'to specify the locations of the pixels on the detector (in ' \
                            'physical space).  TODO: Where is "appropriate form" specified?'

        defaults['pixelwidth'] = 2.5
        dtypes['pixelwidth'] = [int, float]
        descr['pixelwidth'] = 'The size of the extracted pixels (as an scaled number of Arc ' \
                              'FWHM), -1 will not resample'

        defaults['reuse'] = False
        dtypes['reuse'] = bool
        descr['reuse'] = 'If the extraction has previously been performed and saved, load the ' \
                         'previous result'

        defaults['profile'] = 'gaussian'
        options['profile'] = ExtractObjectsPar.valid_profiles()
        dtypes['profile'] = str
        descr['profile'] = 'Fitting function used to extract science data, only if the ' \
                           'extraction is 2D.  NOTE: options with suffix \'func\' fits a ' \
                           'function to the pixels whereas those without this suffix take into ' \
                           'account the integration of the function over the pixel (and is ' \
                           'closer to truth).   ' \
                           'Options are: {0}'.format(', '.join(options['profile']))

        dtypes['maxnumber'] = int
        descr['maxnumber'] = 'Maximum number of objects to extract in a science frame.  Use ' \
                             'None for no limit.'

        dtypes['manual'] = list
        descr['manual'] = 'List of manual extraction parameter sets'

        # Instantiate the parameter set
        super(ExtractObjectsPar, self).__init__(list(pars.keys()),
                                                values=list(pars.values()),
                                                defaults=list(defaults.values()),
                                                options=list(options.values()),
                                                dtypes=list(dtypes.values()),
                                                descr=list(descr.values()))
        self.validate()

    @classmethod
    def from_dict(cls, cfg):
        k = cfg.keys()
        parkeys = [ 'pixelmap', 'pixelwidth', 'reuse', 'profile', 'maxnumber' ]
        kwargs = {}
        for pk in parkeys:
            kwargs[pk] = cfg[pk] if pk in k else None
        kwargs['manual'] = util.get_parset_list(cfg, 'manual', ManualExtractionPar)
        return cls(**kwargs)

    @staticmethod
    def valid_profiles():
        """
        Return the list of valid functions to use for object tracing.
        """
        return [ 'gaussian', 'gaussfunc', 'moffat', 'moffatfunc' ]

    def validate(self):
        pass

# ToDO place holder to be updated by JFH
class ScienceImagePar(ParSet):
    """
    The parameter set used to hold arguments for sky subtraction, object
    finding and extraction in the ScienceImage class

    For a table with the current keywords, defaults, and descriptions,
    see :ref:`pypeitpar`.
    """

    def __init__(self, bspline_spacing=None, maxnumber=None, manual=None, nodding=None):

        # Grab the parameter names and values from the function
        # arguments
        args, _, _, values = inspect.getargvalues(inspect.currentframe())
        pars = OrderedDict([(k, values[k]) for k in args[1:]])  # "1:" to skip 'self'

        # Check the manual input
        if manual is not None:
            if not isinstance(manual, (ParSet, dict, list)):
                raise TypeError('Manual extraction input must be a ParSet, dictionary, or list.')
            _manual = [manual] if isinstance(manual, (ParSet, dict)) else manual
            pars['manual'] = _manual

        # Initialize the other used specifications for this parameter
        # set
        defaults = OrderedDict.fromkeys(pars.keys())
        options = OrderedDict.fromkeys(pars.keys())
        dtypes = OrderedDict.fromkeys(pars.keys())
        descr = OrderedDict.fromkeys(pars.keys())

        # Fill out parameter specifications.  Only the values that are
        # *not* None (i.e., the ones that are defined) need to be set

        defaults['bspline_spacing'] = 0.6
        dtypes['bspline_spacing'] = [int, float]
        descr['bspline_spacing'] = 'Break-point spacing for the bspline fit'

        dtypes['maxnumber'] = int
        descr['maxnumber'] = 'Maximum number of objects to extract in a science frame.  Use ' \
                             'None for no limit.'

        # Place holder for NIR maybe in the future
        defaults['nodding'] = False
        dtypes['nodding'] = bool
        descr['nodding'] = 'Use the nodded frames to perform the sky subtraction'

        dtypes['manual'] = list
        descr['manual'] = 'List of manual extraction parameter sets'

        # Instantiate the parameter set
        super(ScienceImagePar, self).__init__(list(pars.keys()),
                                              values=list(pars.values()),
                                              defaults=list(defaults.values()),
                                              options=list(options.values()),
                                              dtypes=list(dtypes.values()),
                                              descr=list(descr.values()))
        self.validate()

    @classmethod
    def from_dict(cls, cfg):
        k = cfg.keys()
        #ToDO change to updated param list
        parkeys = ['bspline_spacing', 'maxnumber', 'nodding']
        kwargs = {}
        for pk in parkeys:
            kwargs[pk] = cfg[pk] if pk in k else None
        kwargs['manual'] = util.get_parset_list(cfg, 'manual', ManualExtractionPar)
        return cls(**kwargs)

    def validate(self):
        pass


class CalibrationsPar(ParSet):
    """
    The superset of parameters used to calibrate the science data.
    
    Note that there are specific defaults for each frame group that are
    different from the defaults of the abstracted :class:`FrameGroupPar`
    class.

    For a table with the current keywords, defaults, and descriptions,
    see :ref:`pypeitpar`.
    """
    def __init__(self, caldir=None, masters=None, setup=None, trim=None, badpix=None,
                 biasframe=None, darkframe=None, arcframe=None, pixelflatframe=None,
                 pinholeframe=None, traceframe=None, standardframe=None, flatfield=None,
                 wavelengths=None, slits=None, tilts=None):

        # Grab the parameter names and values from the function
        # arguments
        args, _, _, values = inspect.getargvalues(inspect.currentframe())
        pars = OrderedDict([(k,values[k]) for k in args[1:]])      # "1:" to skip 'self'

        # Initialize the other used specifications for this parameter
        # set
        defaults = OrderedDict.fromkeys(pars.keys())
        options = OrderedDict.fromkeys(pars.keys())
        dtypes = OrderedDict.fromkeys(pars.keys())
        descr = OrderedDict.fromkeys(pars.keys())

        # Fill out parameter specifications.  Only the values that are
        # *not* None (i.e., the ones that are defined) need to be set
        defaults['caldir'] = 'MF'
        dtypes['caldir'] = str
        descr['caldir'] = 'Directory relative to calling directory to write master files.'

        options['masters'] = CalibrationsPar.allowed_master_options()
        dtypes['masters'] = str
        descr['masters'] = 'Treatment of master frames.  Use None to select the default ' \
                           'behavior (which is?), \'reuse\' to use any existing masters, and ' \
                           '\'force\' to __only__ use master frames.  ' \
                           'Options are: None, {0}'.format(', '.join(options['masters']))

        dtypes['setup'] = str
        descr['setup'] = 'If masters=\'force\', this is the setup name to be used: e.g., ' \
                         'C_02_aa .  The detector number is ignored but the other information ' \
                         'must match the Master Frames in the master frame folder.'

        defaults['trim'] = True
        dtypes['trim'] = bool
        descr['trim'] = 'Trim the frame to isolate the data'

        defaults['badpix'] = True
        dtypes['badpix'] = bool
        descr['badpix'] = 'Make a bad pixel mask? Bias frames must be provided.'

        defaults['biasframe'] = FrameGroupPar(frametype='bias', number=5)
        dtypes['biasframe'] = [ ParSet, dict ]
        descr['biasframe'] = 'The frames and combination rules for the bias correction'

        defaults['darkframe'] = FrameGroupPar(frametype='bias', number=0)
        dtypes['darkframe'] = [ ParSet, dict ]
        descr['darkframe'] = 'The frames and combination rules for the dark-current correction'

        defaults['pixelflatframe'] = FrameGroupPar(frametype='pixelflat', number=5)
        dtypes['pixelflatframe'] = [ ParSet, dict ]
        descr['pixelflatframe'] = 'The frames and combination rules for the field flattening'

        defaults['pinholeframe'] = FrameGroupPar(frametype='pinhole', number=0)
        dtypes['pinholeframe'] = [ ParSet, dict ]
        descr['pinholeframe'] = 'The frames and combination rules for the pinholes'

        defaults['arcframe'] = FrameGroupPar(frametype='arc', number=1,
                                             process=ProcessImagesPar(sigrej=-1))
        dtypes['arcframe'] = [ ParSet, dict ]
        descr['arcframe'] = 'The frames and combination rules for the wavelength calibration'

        defaults['traceframe'] = FrameGroupPar(frametype='trace', number=3)
        dtypes['traceframe'] = [ ParSet, dict ]
        descr['traceframe'] = 'The frames and combination rules for images used for slit tracing'

        defaults['standardframe'] = FrameGroupPar(frametype='standard', number=1)
        dtypes['standardframe'] = [ ParSet, dict ]
        descr['standardframe'] = 'The frames and combination rules for the spectrophotometric ' \
                                 'standard observations'

        defaults['flatfield'] = FlatFieldPar()
        dtypes['flatfield'] = [ ParSet, dict ]
        descr['flatfield'] = 'Parameters used to set the flat-field procedure'

        defaults['wavelengths'] = WavelengthSolutionPar()
        dtypes['wavelengths'] = [ ParSet, dict ]
        descr['wavelengths'] = 'Parameters used to derive the wavelength solution'

        defaults['slits'] = TraceSlitsPar()
        dtypes['slits'] = [ ParSet, dict ]
        descr['slits'] = 'Define how the slits should be traced using the trace ?PINHOLE? frames'

        defaults['tilts'] = WaveTiltsPar()
        dtypes['tilts'] = [ ParSet, dict ]
        descr['tilts'] = 'Define how to tract the slit tilts using the trace frames'

        # Instantiate the parameter set
        super(CalibrationsPar, self).__init__(list(pars.keys()),
                                              values=list(pars.values()),
                                              defaults=list(defaults.values()),
                                              options=list(options.values()),
                                              dtypes=list(dtypes.values()),
                                              descr=list(descr.values()))
        self.validate()

    @classmethod
    def from_dict(cls, cfg):
        k = cfg.keys()

        # Basic keywords
        parkeys = [ 'caldir', 'masters', 'setup', 'trim', 'badpix' ]
        kwargs = {}
        for pk in parkeys:
            kwargs[pk] = cfg[pk] if pk in k else None

        # Keywords that are ParSets
        pk = 'biasframe'
        kwargs[pk] = FrameGroupPar.from_dict('bias', cfg[pk]) if pk in k else None
        pk = 'darkframe'
        kwargs[pk] = FrameGroupPar.from_dict('dark', cfg[pk]) if pk in k else None
        pk = 'arcframe'
        kwargs[pk] = FrameGroupPar.from_dict('arc', cfg[pk]) if pk in k else None
        pk = 'pixelflatframe'
        kwargs[pk] = FrameGroupPar.from_dict('pixelflat', cfg[pk]) if pk in k else None
        pk = 'pinholeframe'
        kwargs[pk] = FrameGroupPar.from_dict('pinhole', cfg[pk]) if pk in k else None
        pk = 'traceframe'
        kwargs[pk] = FrameGroupPar.from_dict('trace', cfg[pk]) if pk in k else None
        pk = 'standardframe'
        kwargs[pk] = FrameGroupPar.from_dict('standard', cfg[pk]) if pk in k else None
        pk = 'flatfield'
        kwargs[pk] = FlatFieldPar.from_dict(cfg[pk]) if pk in k else None
        pk = 'wavelengths'
        kwargs[pk] = WavelengthSolutionPar.from_dict(cfg[pk]) if pk in k else None
        pk = 'slits'
        kwargs[pk] = TraceSlitsPar.from_dict(cfg[pk]) if pk in k else None
        pk = 'tilts'
        kwargs[pk] = WaveTiltsPar.from_dict(cfg[pk]) if pk in k else None

        return cls(**kwargs)

    @staticmethod
    def allowed_master_options():
        """Return the allowed handling methods for the master frames."""
        return [ 'reuse', 'force' ]

    # TODO: Perform extensive checking that the parameters are valid for
    # the Calibrations class.  May not be necessary because validate will
    # be called for all the sub parameter sets, but this can do higher
    # level checks, if necessary.
    def validate(self):
        if self.data['masters'] == 'force' \
                and (self.data['setup'] is None or len(self.data['setup']) == 0):
            raise ValueError('When forcing use of master frames, you must specify the setup to '
                             'be used using the \'setup\' keyword.')

#-----------------------------------------------------------------------------
# Parameters superset
class PypeItPar(ParSet):
    """
    The superset of parameters used by PypeIt.
    
    This is a single object used as a container for all the
    user-specified arguments used by PypeIt.
    
    To get the default parameters for a given spectrograph, e.g.::

        from pypeit.spectrographs.util import load_spectrograph

        spectrograph = load_spectrograph('shane_kast_blue')
        par = spectrograph.default_pypeit_par()

    If the user has a set of configuration alterations to be read from a
    pypeit file, e.g.::

        from pypeit.par.util import parse_pypeit_file
        from pypeit.spectrographs.util import load_spectrograph
        from pypeit.par import PypeItPar

        spectrograph = load_spectrograph('shane_kast_blue')
        spec_cfg_lines = spectrograph.default_pypeit_par().to_config()
        user_cfg_lines = parse_pypeit_file('myrdx.pypeit')[0]
        par = PypeItPar.from_cfg_lines(cfg_lines=spec_cfg_lines,
                                      merge_with=user_cfg_lines)

    To write the configuration of a given instance of :class:`PypeItPar`,
    use the :func:`to_config` function::
        
        par.to_config('mypypeitpar.cfg')

    For a table with the current keywords, defaults, and descriptions,
    see :ref:`pypeitpar`.
    """
    def __init__(self, rdx=None, calibrations=None, scienceframe=None, scienceimage=None,
                 flexure=None, fluxcalib=None):

        # Grab the parameter names and values from the function
        # arguments
        args, _, _, values = inspect.getargvalues(inspect.currentframe())
        pars = OrderedDict([(k,values[k]) for k in args[1:]])      # "1:" to skip 'self'

        # Initialize the other used specifications for this parameter
        # set
        defaults = OrderedDict.fromkeys(pars.keys())
        dtypes = OrderedDict.fromkeys(pars.keys())
        descr = OrderedDict.fromkeys(pars.keys())

        # Fill out parameter specifications.  Only the values that are
        # *not* None (i.e., the ones that are defined) need to be set
        defaults['rdx'] = ReducePar()
        dtypes['rdx'] = [ ParSet, dict ]
        descr['rdx'] = 'PypIt reduction rules.'

#        defaults['baseprocess'] = ProcessImagesPar()
#        dtypes['baseprocess'] = [ ParSet, dict ]
#        descr['baseprocess'] = 'Default-level parameters used when processing all images'

        defaults['calibrations'] = CalibrationsPar()
        dtypes['calibrations'] = [ ParSet, dict ]
        descr['calibrations'] = 'Parameters for the calibration algorithms'

        defaults['scienceframe'] = FrameGroupPar(frametype='science')
        dtypes['scienceframe'] = [ ParSet, dict ]
        descr['scienceframe'] = 'The frames and combination rules for the science observations'

        defaults['scienceimage'] = ScienceImagePar()
        dtypes['scienceimage'] = [ParSet, dict]
        descr['scienceimage'] = 'Parameters determining sky-subtraction, object finding, and ' \
                                'extraction'

        # Flexure is turned OFF by default
        dtypes['flexure'] = [ ParSet, dict ]
        descr['flexure'] = 'Parameters used by the flexure-correction procedure.  Flexure ' \
                           'corrections are not performed by default.  To turn on, either ' \
                           'set the parameters in the \'flexure\' parameter group or set ' \
                           '\'flexure = True\' in the \'rdx\' parameter group to use the ' \
                           'default flexure-correction parameters.'

        # Flux calibration is turned OFF by default
        dtypes['fluxcalib'] = [ ParSet, dict ]
        descr['fluxcalib'] = 'Parameters used by the flux-calibration procedure.  Flux ' \
                             'calibration is not performed by default.  To turn on, either ' \
                             'set the parameters in the \'fluxcalib\' parameter group or set ' \
                             '\'fluxcalib = True\' in the \'rdx\' parameter group to use the ' \
                             'default flux-calibration parameters.'
        
        # Instantiate the parameter set
        super(PypeItPar, self).__init__(list(pars.keys()),
                                       values=list(pars.values()),
                                       defaults=list(defaults.values()),
                                       dtypes=list(dtypes.values()),
                                       descr=list(descr.values()))

        self.validate()

#    def update(self, par):
#        """
#        Update the current parameters.
#
#        Likely doesn't work because it isn't recursive ...
#        """
#        if not isinstance(par, PypeItPar):
#            raise TypeError('Parameters can only be updated using another instance of PypeItPar.')
#        self.data.update(par.data)

    @classmethod
    def from_cfg_file(cls, cfg_file=None, merge_with=None, evaluate=True):
        """
        Construct the parameter set using a configuration file.

        Note that::

            default = PypeItPar()
            nofile = PypeItPar.from_cfg_file()
            assert default.data == nofile.data, 'This should always pass.'

        Args:
            cfg_file (:obj:`str`, optional):
                The name of the configuration file that defines the
                default parameters.  This can be used to load a pypeit
                config file from a previous run that was constructed and
                output by pypeit.  This has to contain the full set of
                parameters, not just the subset you want to change.  For
                the latter, use :arg:`merge_with` to provide one or more
                config files to merge with the defaults to construct the
                full parameter set.
            merge_with (:obj:`str`, :obj:`list`, optional):
                One or more config files with the modifications to
                either default parameters (:arg:`cfg_file` is None) or
                the parameters provided by :arg:`cfg_file`.  The
                modifications are performed in series so the list order
                of the config files is important.
            evaluate (:obj:`bool`, optional):
                Evaluate the values in the config object before
                assigning them in the subsequent parameter sets.  The
                parameters in the config file are *always* read as
                strings, so this should almost always be true; however,
                see the warning below.
                
        .. warning::

            When :arg:`evaluate` is true, the function runs `eval()` on
            all the entries in the `ConfigObj` dictionary, done using
            :func:`_recursive_dict_evaluate`.  This has the potential to
            go haywire if the name of a parameter unintentionally
            happens to be identical to an imported or system-level
            function.  Of course, this can be useful by allowing one to
            define the function to use as a parameter, but it also means
            one has to be careful with the values that the parameters
            should be allowed to have.  The current way around this is
            to provide a list of strings that should be ignored during
            the evaluation, done using :func:`_eval_ignore`.

        .. todo::
            Allow the user to add to the ignored strings.

        Returns:
            :class:`pypeit.par.core.PypeItPar`: The instance of the
            parameter set.
        """
        # Get the base parameters in a ConfigObj instance
        cfg = ConfigObj(PypeItPar().to_config() if cfg_file is None else cfg_file)

        # Get the list of other configuration parameters to merge it with
        _merge_with = [] if merge_with is None else \
                        ([merge_with] if isinstance(merge_with, str) else merge_with)
        merge_cfg = ConfigObj()
        for f in _merge_with:
            merge_cfg.merge(ConfigObj(f))

        # Merge with the defaults
        cfg.merge(merge_cfg)

        # Evaluate the strings if requested
        if evaluate:
            cfg = util.recursive_dict_evaluate(cfg)
        
        # Instantiate the object based on the configuration dictionary
        return cls.from_dict(cfg)

    @classmethod
    def from_cfg_lines(cls, cfg_lines=None, merge_with=None, evaluate=True):
        """
        Construct the parameter set using the list of string lines read
        from a config file.

        Note that::

            default = PypeItPar()
            nofile = PypeItPar.from_cfg_lines()
            assert default.data == nofile.data, 'This should always pass.'

        Args:
            cfg_lines (:obj:`list`, optional):
                A list of strings with lines read, or made to look like
                they are, from a configuration file.  This can be used
                to load lines from a previous run of pypeit that was
                constructed and output by pypeit.  This has to contain
                the full set of parameters, not just the subset to
                change.  For the latter, leave this as the default value
                (None) and use :arg:`merge_with` to provide a set of
                lines to merge with the defaults to construct the full
                parameter set.
            merge_with (:obj:`list`, optional):
                A list of strings with lines read, or made to look like
                they are, from a configuration file that should be
                merged with the lines provided by `cfg_lines`, or the
                default parameters.
            evaluate (:obj:`bool`, optional):
                Evaluate the values in the config object before
                assigning them in the subsequent parameter sets.  The
                parameters in the config file are *always* read as
                strings, so this should almost always be true; however,
                see the warning below.
                
        .. warning::

            When :arg:`evaluate` is true, the function runs `eval()` on
            all the entries in the `ConfigObj` dictionary, done using
            :func:`_recursive_dict_evaluate`.  This has the potential to
            go haywire if the name of a parameter unintentionally
            happens to be identical to an imported or system-level
            function.  Of course, this can be useful by allowing one to
            define the function to use as a parameter, but it also means
            one has to be careful with the values that the parameters
            should be allowed to have.  The current way around this is
            to provide a list of strings that should be ignored during
            the evaluation, done using :func:`_eval_ignore`.

        .. todo::
            Allow the user to add to the ignored strings.

        Returns:
            :class:`pypeit.par.core.PypeItPar`: The instance of the
            parameter set.
        """
        # Get the base parameters in a ConfigObj instance
        cfg = ConfigObj(PypeItPar().to_config() if cfg_lines is None else cfg_lines)
        
        # Merge in additional parameters
        if merge_with is not None:
            cfg.merge(ConfigObj(merge_with))

        # Evaluate the strings if requested
        if evaluate:
            cfg = util.recursive_dict_evaluate(cfg)
        
        # Instantiate the object based on the configuration dictionary
        return cls.from_dict(cfg)

    @classmethod
    def from_pypeit_file(cls, ifile, evaluate=True):
        """
        Construct the parameter set using a pypeit file.
        
        Args:
            ifile (str):
                Name of the pypeit file to read.  Expects to find setup
                and data blocks in the file.  See docs.
            evaluate (:obj:`bool`, optional):
                Evaluate the values in the config object before
                assigning them in the subsequent parameter sets.  The
                parameters in the config file are *always* read as
                strings, so this should almost always be true; however,
                see the warning below.
                
        .. warning::

            When :arg:`evaluate` is true, the function runs `eval()` on
            all the entries in the `ConfigObj` dictionary, done using
            :func:`_recursive_dict_evaluate`.  This has the potential to
            go haywire if the name of a parameter unintentionally
            happens to be identical to an imported or system-level
            function.  Of course, this can be useful by allowing one to
            define the function to use as a parameter, but it also means
            one has to be careful with the values that the parameters
            should be allowed to have.  The current way around this is
            to provide a list of strings that should be ignored during
            the evaluation, done using :func:`_eval_ignore`.

        .. todo::
            Allow the user to add to the ignored strings.

        Returns:
            :class:`pypeit.par.core.PypeItPar`: The instance of the
            parameter set.
        """
        # TODO: Need to include instrument-specific defaults somewhere...
        return cls.from_cfg_lines(merge_with=util.pypeit_config_lines(ifile), evaluate=evaluate)

    @classmethod
    def from_dict(cls, cfg):
        k = cfg.keys()
        kwargs = {}

        pk = 'rdx'
        kwargs[pk] = ReducePar.from_dict(cfg[pk]) if pk in k else None

        pk = 'calibrations'
        kwargs[pk] = CalibrationsPar.from_dict(cfg[pk]) if pk in k else None

        pk = 'scienceframe'
        kwargs[pk] = FrameGroupPar.from_dict('science', cfg[pk]) if pk in k else None

        pk = 'scienceimage'
        kwargs[pk] = ScienceImagePar.from_dict(cfg[pk]) if pk in k else None

        # Allow flexure to be turned on using cfg['rdx']
        pk = 'flexure'
        default = FlexurePar()
        kwargs[pk] = FlexurePar.from_dict(cfg[pk]) if pk in k else default

        # Allow flux calibration to be turned on using cfg['rdx']
        pk = 'fluxcalib'
        default = FluxCalibrationPar() \
                        if pk in cfg['rdx'].keys() and cfg['rdx']['fluxcalib'] else None
        kwargs[pk] = FluxCalibrationPar.from_dict(cfg[pk]) if pk in k else default

        if 'baseprocess' not in k:
            return cls(**kwargs)

        # Include any alterations to the basic processing of *all*
        # images
        self = cls(**kwargs)
        baseproc = ProcessImagesPar.from_dict(cfg['baseprocess'])
        self.sync_processing(baseproc)
        return self

    def sync_processing(self, proc_par):
        """
        Sync the processing of all the frame types based on the input
        ProcessImagesPar parameters.

        The parameters are merged in sequence starting from the
        parameter defaults, then including global adjustments provided
        by ``process``, and ending with the parameters that may have
        already been changed for each frame.

        This function can be used at anytime, but is most useful with
        the from_dict method where a ``baseprocess`` group can be
        supplied to change the processing parameters for all frames away
        from the defaults.

        Args:
            proc_par (:class:`ProcessImagesPar`):
                Effectively a new set of default image processing
                parameters for all frames.

        Raises:
            TypeError:
                Raised if the provided parameter set is not an instance
                of :class:`ProcessImagesPar`.
        """
        # Checks
        if not isinstance(proc_par, ProcessImagesPar):
            raise TypeError('Must provide an instance of ProcessImagesPar')
        
        # All the relevant ParSets are already ProcessImagesPar objects,
        # so we can work directly with the internal dictionaries.

        # Find the keys in the input that are different from the default
        default = ProcessImagesPar()
        base_diff = [ k for k in proc_par.keys() if default[k] != proc_par[k] ]

        # Calibration frames
        frames = [ f for f in self['calibrations'].keys() if 'frame' in f ]
        for f in frames:
            # Find the keys in self that are the same as the default
            frame_same = [ k for k in proc_par.keys() 
                            if self['calibrations'][f]['process'].data[k] == default[k] ]
            to_change = list(set(base_diff) & set(frame_same))
            for k in to_change:
                self['calibrations'][f]['process'].data[k] = proc_par[k]
            
        # Science frames
        frame_same = [ k for k in proc_par.keys() 
                            if self['scienceframe']['process'].data[k] == default[k] ]
        to_change = list(set(base_diff) & set(frame_same))
        for k in to_change:
            self['scienceframe']['process'].data[k] = proc_par[k]

    # TODO: Perform extensive checking that the parameters are valid for
    # a full run of PYPIT.  May not be necessary because validate will
    # be called for all the sub parameter sets, but this can do higher
    # level checks, if necessary.
    def validate(self):
        pass

#-----------------------------------------------------------------------------
# Instrument parameters

# TODO: This should probably get moved to spectrograph.py
class DetectorPar(ParSet):
    """
    The parameters used to define the salient properties of an
    instrument detector.

    These parameters should be *independent* of any specific use of the
    detector, and are used in the definition of the instruments served
    by PypeIt.

    To see the list of instruments served, a table with the the current
    keywords, defaults, and descriptions for the :class:`DetectorPar`
    class, and an explanation of how to define a new instrument, see
    :ref:`instruments`.
    """
    def __init__(self, dataext=None, dispaxis=None, dispflip=None, xgap=None, ygap=None, ysize=None,
                 platescale=None, darkcurr=None, saturation=None, mincounts = None, nonlinear=None,
                 numamplifiers=None, gain=None, ronoise=None, datasec=None, oscansec=None,
                 suffix=None):

        # Grab the parameter names and values from the function
        # arguments
        args, _, _, values = inspect.getargvalues(inspect.currentframe())
        pars = OrderedDict([(k,values[k]) for k in args[1:]])

        # Initialize the other used specifications for this parameter
        # set
        defaults = OrderedDict.fromkeys(pars.keys())
        options = OrderedDict.fromkeys(pars.keys())
        dtypes = OrderedDict.fromkeys(pars.keys())
        descr = OrderedDict.fromkeys(pars.keys())

        # Fill out parameter specifications.  Only the values that are
        # *not* None (i.e., the ones that are defined) need to be set
        defaults['dataext'] = 0
        dtypes['dataext'] = int
        descr['dataext'] = 'Index of fits extension containing data'

        # TODO: Should this be detector-specific, or camera-specific?
        defaults['dispaxis'] = 0
        options['dispaxis'] = [ 0, 1]
        dtypes['dispaxis'] = int
        descr['dispaxis'] = 'Spectra are dispersed along this axis. Allowed values are 0 ' \
                            '(first dimension for a numpy array shape) or 1 (second dimension for numpy array shape)'


        defaults['dispflip'] = False
        dtypes['dispflip'] = bool
        descr['dispflip'] = 'If this is True then the dispersion dimension (specificed by the dispaxis) will be ' \
                            'flipped so that wavelengths are always an increasing function of array index'

        defaults['xgap'] = 0.0
        dtypes['xgap'] = [int, float]
        descr['xgap'] = 'Gap between the square detector pixels (expressed as a fraction of the ' \
                        'x pixel size -- x is predominantly the dispersion axis)'

        defaults['ygap'] = 0.0
        dtypes['ygap'] = [int, float]
        descr['ygap'] = 'Gap between the square detector pixels (expressed as a fraction of the ' \
                        'y pixel size -- x is predominantly the dispersion axis)'

        defaults['ysize'] = 1.0
        dtypes['ysize'] = [int, float]
        descr['ysize'] = 'The size of a pixel in the y-direction as a multiple of the x pixel ' \
                         'size (i.e. xsize = 1.0 -- x is predominantly the dispersion axis)'

        defaults['platescale'] = 0.135
        dtypes['platescale'] = [int, float]
        descr['platescale'] = 'arcsec per pixel in the spatial dimension for an unbinned pixel'

        defaults['darkcurr'] = 0.0
        dtypes['darkcurr'] = [int, float]
        descr['darkcurr'] = 'Dark current (e-/hour)'

        defaults['saturation'] = 65535.0
        dtypes['saturation'] = [ int, float ]
        descr['saturation'] = 'The detector saturation level'

        defaults['mincounts'] = -1000.0
        dtypes['mincounts'] = [ int, float ]
        descr['mincounts'] = 'Counts in a pixel below this value will be ignored as being unphysical'


        defaults['nonlinear'] = 0.86
        dtypes['nonlinear'] = [ int, float ]
        descr['nonlinear'] = 'Percentage of detector range which is linear (i.e. everything ' \
                             'above nonlinear*saturation will be flagged as saturated)'

        # gain, ronoise, datasec, and oscansec must be lists if there is
        # more than one amplifier
        defaults['numamplifiers'] = 1
        dtypes['numamplifiers'] = int
        descr['numamplifiers'] = 'Number of amplifiers'

        defaults['gain'] = 1.0 if pars['numamplifiers'] is None else [1.0]*pars['numamplifiers']
        dtypes['gain'] = [ int, float, list ]
        descr['gain'] = 'Inverse gain (e-/ADU). A list should be provided if a detector ' \
                        'contains more than one amplifier.'

        defaults['gain'] = 4.0 if pars['numamplifiers'] is None else [4.0]*pars['numamplifiers']
        dtypes['ronoise'] = [ int, float, list ]
        descr['ronoise'] = 'Read-out noise (e-). A list should be provided if a detector ' \
                           'contains more than one amplifier.'

        # TODO: Allow for None, such that the entire image is the data
        # section
        defaults['datasec'] = 'DATASEC' if pars['numamplifiers'] is None \
                                        else ['DATASEC']*pars['numamplifiers']
        dtypes['datasec'] = [str, list]
        descr['datasec'] = 'Either the data sections or the header keyword where the valid ' \
                           'data sections can be obtained, one per amplifier. If defined ' \
                           'explicitly should have the format of a numpy array slice'

        # TODO: Allow for None, such that there is no overscan region
        defaults['oscansec'] = 'BIASSEC' if pars['numamplifiers'] is None \
                                        else ['BIASSEC']*pars['numamplifiers']
        dtypes['oscansec'] = [str, list]
        descr['oscansec'] = 'Either the overscan section or the header keyword where the valid ' \
                            'data sections can be obtained, one per amplifier. If defined ' \
                            'explicitly should have the format of a numpy array slice'

        # TODO: Allow this to be None?
        defaults['suffix'] = ''
        dtypes['suffix'] = str
        descr['suffix'] = 'Suffix to be appended to all saved calibration and extraction frames.'

        # Instantiate the parameter set
        super(DetectorPar, self).__init__(list(pars.keys()),
                                          values=list(pars.values()),
                                          defaults=list(defaults.values()),
                                          options=list(options.values()),
                                          dtypes=list(dtypes.values()),
                                          descr=list(descr.values()))
        self.validate()

    @classmethod
    def from_dict(cls, cfg):
        k = cfg.keys()
        parkeys = [ 'dataext', 'dispaxis', 'dispflip', 'xgap', 'ygap', 'ysize', 'platescale', 'darkcurr',
                    'saturation', 'mincounts','nonlinear', 'numamplifiers', 'gain', 'ronoise', 'datasec',
                    'oscansec', 'suffix' ]
        kwargs = {}
        for pk in parkeys:
            kwargs[pk] = cfg[pk] if pk in k else None
        return cls(**kwargs)

    def validate(self):
        """
        Check the parameters are valid for the provided method.
        """
        if self.data['numamplifiers'] > 1:
            keys = [ 'gain', 'ronoise', 'datasec', 'oscansec' ]
            dtype = [ (int, float), (int, float), str, str ]
            for i in range(len(keys)):
                if self.data[keys[i]] is None:
                    continue
                if not isinstance(self.data[keys[i]], list) \
                        or len(self.data[keys[i]]) != self.data['numamplifiers']:
                    raise ValueError('Provided {0} does not match amplifiers.'.format(keys[i]))

            for j in range(self.data['numamplifiers']):
                if self.data[keys[i]] is not None \
                        and not isinstance(self.data[keys[i]][j], dtype[i]):
                    TypeError('Incorrect type for {0}; should be {1}'.format(keys[i], dtype[i]))

# TODO: This should get moved to telescopes.py
class TelescopePar(ParSet):
    """
    The parameters used to define the salient properties of a telescope.

    These parameters should be *independent* of any specific use of the
    telescope.  They and are used by the :mod:`pypeit.telescopes` module
    to define the telescopes served by PypeIt, and kept as part of the
    :class:`pypeit.spectrographs.spectrograph.Spectrograph` definition of
    the instruments served by PypeIt.

    To see the list of instruments served, a table with the the current
    keywords, defaults, and descriptions for the :class:`TelescopePar`
    class, and an explanation of how to define a new instrument, see
    :ref:`instruments`.
    """
    def __init__(self, name=None, longitude=None, latitude=None, elevation=None, fratio=None,
                 diameter=None):

        # Grab the parameter names and values from the function
        # arguments
        args, _, _, values = inspect.getargvalues(inspect.currentframe())
        pars = OrderedDict([(k,values[k]) for k in args[1:]])

        # Initialize the other used specifications for this parameter
        # set
        defaults = OrderedDict.fromkeys(pars.keys())
        options = OrderedDict.fromkeys(pars.keys())
        dtypes = OrderedDict.fromkeys(pars.keys())
        descr = OrderedDict.fromkeys(pars.keys())

        # Fill out parameter specifications.  Only the values that are
        # *not* None (i.e., the ones that are defined) need to be set
        defaults['name'] = 'KECK'
        options['name'] = TelescopePar.valid_telescopes()
        dtypes['name'] = str
        descr['name'] = 'Name of the telescope used to obtain the observations.  ' \
                        'Options are: {0}'.format(', '.join(options['name']))
        
        dtypes['longitude'] = [int, float]
        descr['longitude'] = 'Longitude of the telescope on Earth in degrees.'

        dtypes['latitude'] = [int, float]
        descr['latitude'] = 'Latitude of the telescope on Earth in degrees.'

        dtypes['elevation'] = [int, float]
        descr['elevation'] = 'Elevation of the telescope in m'

        dtypes['fratio'] = [int, float]
        descr['fratio'] = 'f-ratio of the telescope'

        dtypes['diameter'] = [int, float]
        descr['diameter'] = 'Diameter of the telescope in m'

        # Instantiate the parameter set
        super(TelescopePar, self).__init__(list(pars.keys()),
                                           values=list(pars.values()),
                                           defaults=list(defaults.values()),
                                           options=list(options.values()),
                                           dtypes=list(dtypes.values()),
                                           descr=list(descr.values()))

        # Check the parameters match the method requirements
        self.validate()


    @classmethod
    def from_dict(cls, cfg):
        k = cfg.keys()
        parkeys = [ 'name', 'longitude', 'latitude', 'elevation', 'fratio', 'diameter' ]
        kwargs = {}
        for pk in parkeys:
            kwargs[pk] = cfg[pk] if pk in k else None
        return cls(**kwargs)

    @staticmethod
    def valid_telescopes():
        """
        Return the valid telescopes.
        """
        return [ 'GEMINI-N','GEMINI-S', 'KECK', 'SHANE', 'WHT', 'APF', 'TNG', 'VLT' ]

    def validate(self):
        pass

    def platescale(self):
        r"""
        Return the platescale of the telescope in arcsec per mm.

        Calculated as

        .. math::
            p = \frac{206265}{f D},

        where :math:`f` is the f-ratio and :math:`D` is the diameter.
        If either of these is not available, the function returns
        `None`.
        """
        return None if self['fratio'] is None or self['diameter'] is None \
                else 206265/self['fratio']/self['diameter']/1e3


