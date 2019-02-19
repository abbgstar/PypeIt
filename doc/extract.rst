.. highlight:: rest

*****************
Object Extraction
*****************


Overview
========

The code identifies and extracts objects significantly detected
by PypeIt. See :ref:`object_finding` for more details on PypeIt's
object finding algorithm.

The following describes how the user can interact and specify
details for the extraction process.


Maximum number of objects
-------------------------

The user can specify the maximum number of science
objects to be extracted per raw science target grouping
by including the following in the PypeIt reduction file::

    [[sciengeimage]]
        maxnumber = 2


Manual Extraction
-----------------

In the case where the science target is faint and likely
to not be automatically decected by PypeIt's object
finding algorithm, the user can specify one or more
locations where a desired spectrum is to be extracted
'manually'.

This can be done by adding a new column titled
'manual_extract' to the :ref:`data block` of the PypeIt
reduction file. In this column, the user must provide
four values for each object/location that the user
wishes for a manual extraction. The values are::

    detector #:spatial pixel location:spectral pixel location:FWHM of Gaussian profile


PypeIt will force a spectrum to be extracted which
passes through the location indicated by the
(spatial, spectral) pixel, in the given detector.
The optimal extraction will have a Gaussian profile
of the specified FWHM.

Multiple 'manually' extracted objects can be given,
separated by a comma.

An example of how this fits into the :ref:`data block`::

    data read
     path /Users/thsyu/Dropbox/BCDs/data/nirspec/apr13_2016
    |                  filename |          frametype |        ra |      dec |         target | dispname |   decker | binning |         mjd | airmass | exptime |                    calib | comb_id | bkg_id |                      manual_extract |
    | NS.20160414.02604.fits.gz |    trace,pixelflat |       0.0 |      0.0 |                |      low | 42x0.760 |     1,1 | 57492.03014 | 1.41291 |    3.28 |  36,37,38,39,40,41,42,43 |       1 |     -1 |                                None |
    | NS.20160414.02620.fits.gz |    trace,pixelflat |       0.0 |      0.0 |                |      low | 42x0.760 |     1,1 | 57492.03033 | 1.41291 |    3.28 |  36,37,38,39,40,41,42,43 |       1 |     -1 |                                None |
    | NS.20160414.02637.fits.gz |    trace,pixelflat |       0.0 |      0.0 |                |      low | 42x0.760 |     1,1 | 57492.03052 | 1.41291 |    3.28 |  36,37,38,39,40,41,42,43 |       1 |     -1 |                                None |
    | NS.20160414.52519.fits.gz |        arc,science | 253.91361 | 63.61965 | OFF_J1655p6337 |      low | 42x0.760 |     1,1 | 57492.60787 | 1.40117 |   250.0 |                       36 |      21 |     22 |   1:757.0:656.5:8.5,-1:746.:757:8.5 |
    | NS.20160414.52795.fits.gz |        arc,science | 253.91328 | 63.61548 | OFF_J1655p6337 |      low | 42x0.760 |     1,1 | 57492.61106 | 1.40481 |   250.0 |                       37 |      22 |     21 |                   1:746.0:759.5:8.5 |
    | NS.20160414.53056.fits.gz |        arc,science | 253.91328 | 63.61548 | OFF_J1655p6337 |      low | 42x0.760 |     1,1 | 57492.61408 | 1.40873 |   250.0 |                       38 |      22 |     21 |                   1:746.0:759.5:8.5 |
    | NS.20160414.53331.fits.gz |        arc,science | 253.91361 | 63.61965 | OFF_J1655p6337 |      low | 42x0.760 |     1,1 | 57492.61727 | 1.41317 |   250.0 |                       39 |      21 |     22 |                   1:757.5:655.5:8.5 |
    | NS.20160414.53666.fits.gz |        arc,science | 253.91361 | 63.61965 | OFF_J1655p6337 |      low | 42x0.760 |     1,1 | 57492.62115 | 1.41905 |   250.0 |                       40 |      26 |     27 |                   1:757.0:657.0:8.5 |
    | NS.20160414.53947.fits.gz |        arc,science | 253.91328 | 63.61548 | OFF_J1655p6337 |      low | 42x0.760 |     1,1 | 57492.62439 | 1.42428 |   250.0 |                       41 |      27 |     26 |                   1:746.0:759.0:8.5 |
    | NS.20160414.54209.fits.gz |        arc,science | 253.91328 | 63.61548 | OFF_J1655p6337 |      low | 42x0.760 |     1,1 | 57492.62743 | 1.42961 |   250.0 |                       42 |      27 |     26 |                   1:746.0:759.0:8.5 |
    | NS.20160414.54487.fits.gz |        arc,science | 253.91361 | 63.61965 | OFF_J1655p6337 |      low | 42x0.760 |     1,1 | 57492.63064 | 1.43567 |   250.0 |                       43 |      26 |     27 |                   1:757.0:656.0:8.5 |
    | NS.20160414.55193.fits.gz |           standard | 279.38983 | 62.52908 | CAL_J1655p6337 |      low | 42x0.760 |     1,1 | 57492.63882 |  1.3586 |     1.0 |                       43 |      24 |     25 |                                None |
    | NS.20160414.55223.fits.gz |           standard | 279.38964 | 62.52491 | CAL_J1655p6337 |      low | 42x0.760 |     1,1 | 57492.63916 | 1.35847 |     1.0 |                       43 |      25 |     24 |                                None |
    | NS.20160414.55235.fits.gz |           standard |  279.3897 | 62.52491 | CAL_J1655p6337 |      low | 42x0.760 |     1,1 |  57492.6393 | 1.35844 |     1.0 |                       43 |      25 |     24 |                                None |
    | NS.20160414.55260.fits.gz |           standard | 279.38995 | 62.52907 | CAL_J1655p6337 |      low | 42x0.760 |     1,1 |  57492.6396 |  1.3585 |     1.0 |                       43 |      24 |     25 |                                None |
    data end



