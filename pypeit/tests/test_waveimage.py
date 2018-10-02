# Module to run tests on WaveImage class
#   Requires files in Development suite and an Environmental variable
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

# TEST_UNICODE_LITERALS

import os

import pytest
import glob
import numpy as np

from pypeit.tests import tstutils
from pypeit import waveimage

# These tests are not run on Travis
if os.getenv('PYPEIT_DEV') is None:
    skip_test=True
else:
    skip_test=False

def chk_for_files(root):
    files = glob.glob(root+'*')
    if len(files) == 0:
        return False
    else:
        return True

def data_path(filename):
    data_dir = os.path.join(os.path.dirname(__file__), 'files')
    return os.path.join(data_dir, filename)


def test_build_me():
    if skip_test:
        assert True
        return
    # Masters
    spectrograph, TSlits, tilts_dict, wv_calib \
            = tstutils.load_kast_blue_masters(get_spectrograph=True, tslits=True, tilts=True,
                                              wvcalib=True)
    # Instantiate
    setup = 'A_01_aa'
    root_path = data_path('MF') if os.getenv('PYPEIT_DEV') is None \
                    else os.path.join(os.getenv('PYPEIT_DEV'), 'Cooked', 'MF')
    master_dir = root_path+'_'+spectrograph.spectrograph
    mode = 'reuse'
    maskslits = np.zeros(TSlits.nslit, dtype=bool)
    wvImg = waveimage.WaveImage(TSlits.slitpix, tilts_dict['tilts'], wv_calib, setup=setup, maskslits=maskslits,
                                master_dir=master_dir, mode=mode)
    # Build
    wave = wvImg._build_wave()
    assert int(np.max(wave)) == 5516
