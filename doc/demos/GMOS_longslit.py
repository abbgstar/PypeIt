{
 "cells": [
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "# Demo of PYPIT on LRISr Longslit [v1.1]"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 1,
   "metadata": {
    "collapsed": true
   },
   "outputs": [],
   "source": [
    "# import\n",
    "from importlib import reload\n",
    "import os\n",
    "import glob\n",
    "import numpy as np\n",
    "\n",
    "# A few core routines\n",
    "from pypit.core import arsetup\n",
    "from pypit.core import arsort\n",
    "from pypit import arpixels\n",
    "from pypit.core import arprocimg\n",
    "from pypit.core import arwave\n",
    "from pypit.core import arsave\n",
    "from pypit import arutils\n",
    "from pypit import arload\n",
    "\n",
    "# Classes\n",
    "from pypit import arcimage\n",
    "from pypit import biasframe\n",
    "from pypit import bpmimage\n",
    "from pypit import flatfield\n",
    "from pypit import fluxspec\n",
    "from pypit import pypitsetup\n",
    "from pypit import scienceimage\n",
    "from pypit import traceimage\n",
    "from pypit import traceslits\n",
    "from pypit import wavecalib\n",
    "from pypit import waveimage\n",
    "from pypit import wavetilts"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "## To play along, you need the Development suite and the $PYPIT_DEV environmental variable pointed at it"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 2,
   "metadata": {},
   "outputs": [
    {
     "data": {
      "text/plain": [
       "'/home/xavier/local/Python/PYPIT-development-suite/'"
      ]
     },
     "execution_count": 2,
     "metadata": {},
     "output_type": "execute_result"
    }
   ],
   "source": [
    "os.getenv('PYPIT_DEV')"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "## Kuldge for settings"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 3,
   "metadata": {
    "collapsed": true
   },
   "outputs": [],
   "source": [
    "spectrograph='keck_lris_red'"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 4,
   "metadata": {},
   "outputs": [
    {
     "name": "stderr",
     "output_type": "stream",
     "text": [
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marparse.py 75 load_file()\u001b[0m - Loading default settings\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marparse.py 87 load_file()\u001b[0m - Loading base settings from settings.baseargflag\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marparse.py 1393 run_ncpus()\u001b[0m - Setting 7 CPUs\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marparse.py 75 load_file()\u001b[0m - Loading default settings\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marparse.py 75 load_file()\u001b[0m - Loading default settings\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marparse.py 87 load_file()\u001b[0m - Loading base settings from settings.basespect\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marparse.py 75 load_file()\u001b[0m - Loading default settings\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marparse.py 75 load_file()\u001b[0m - Loading default settings\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marparse.py 87 load_file()\u001b[0m - Loading base settings from settings.basespect\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marparse.py 75 load_file()\u001b[0m - Loading default settings\n"
     ]
    }
   ],
   "source": [
    "from pypit import arparse as settings\n",
    "settings.dummy_settings(spectrograph=spectrograph)\n",
    "settings.argflag['reduce']['masters']['setup'] = 'C_01_aa'\n",
    "#\n",
    "# Load default spectrograph settings\n",
    "spect = settings.get_spect_class(('ARMS', 'keck_lris_red', 'pypit'))# '.'.join(redname.split('.')[:-1])))\n",
    "lines = spect.load_file(base=True)  # Base spectrograph settings\n",
    "spect.set_paramlist(lines)\n",
    "lines = spect.load_file()  # Instrument specific\n",
    "spect.set_paramlist(lines)"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "## Build the fitstbl"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 5,
   "metadata": {},
   "outputs": [
    {
     "data": {
      "text/plain": [
       "23"
      ]
     },
     "execution_count": 5,
     "metadata": {},
     "output_type": "execute_result"
    }
   ],
   "source": [
    "keck_lris_files = glob.glob(os.getenv('PYPIT_DEV')+'RAW_DATA/Keck_LRIS_red/long_600_7500_d560/LR*')\n",
    "len(keck_lris_files)"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 6,
   "metadata": {
    "collapsed": true
   },
   "outputs": [],
   "source": [
    "# Init\n",
    "setupc = pypitsetup.PypitSetup(settings.argflag, settings.spect)"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 7,
   "metadata": {},
   "outputs": [
    {
     "name": "stderr",
     "output_type": "stream",
     "text": [
      "\u001b[1;31m[WARNING] ::\u001b[0m \u001b[1;34marload.py 159 load_headers()\u001b[0m - TARGNAME keyword not in header. Setting to None\n",
      "\u001b[1;31m[WARNING] ::\u001b[0m \u001b[1;34marload.py 159 load_headers()\u001b[0m - RA keyword not in header. Setting to None\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marload.py 194 load_headers()\u001b[0m - Successfully loaded headers for file:\n",
      "             /home/xavier/local/Python/PYPIT-development-suite/RAW_DATA/Keck_LRIS_red/long_600_7500_d560/LR.20160216.05709.fits\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marload.py 194 load_headers()\u001b[0m - Successfully loaded headers for file:\n",
      "             /home/xavier/local/Python/PYPIT-development-suite/RAW_DATA/Keck_LRIS_red/long_600_7500_d560/LR.20160216.14244.fits\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marload.py 194 load_headers()\u001b[0m - Successfully loaded headers for file:\n",
      "             /home/xavier/local/Python/PYPIT-development-suite/RAW_DATA/Keck_LRIS_red/long_600_7500_d560/LR.20160216.05649.fits\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marload.py 194 load_headers()\u001b[0m - Successfully loaded headers for file:\n",
      "             /home/xavier/local/Python/PYPIT-development-suite/RAW_DATA/Keck_LRIS_red/long_600_7500_d560/LR.20160216.07587.fits\n",
      "\u001b[1;31m[WARNING] ::\u001b[0m \u001b[1;34marload.py 159 load_headers()\u001b[0m - TARGNAME keyword not in header. Setting to None\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marload.py 194 load_headers()\u001b[0m - Successfully loaded headers for file:\n",
      "             /home/xavier/local/Python/PYPIT-development-suite/RAW_DATA/Keck_LRIS_red/long_600_7500_d560/LR.20160216.07348.fits\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marload.py 194 load_headers()\u001b[0m - Successfully loaded headers for file:\n",
      "             /home/xavier/local/Python/PYPIT-development-suite/RAW_DATA/Keck_LRIS_red/long_600_7500_d560/LR.20160216.07529.fits\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marload.py 194 load_headers()\u001b[0m - Successfully loaded headers for file:\n",
      "             /home/xavier/local/Python/PYPIT-development-suite/RAW_DATA/Keck_LRIS_red/long_600_7500_d560/LR.20160216.05529.fits\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marload.py 194 load_headers()\u001b[0m - Successfully loaded headers for file:\n",
      "             /home/xavier/local/Python/PYPIT-development-suite/RAW_DATA/Keck_LRIS_red/long_600_7500_d560/LR.20160216.40478.fits\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marload.py 194 load_headers()\u001b[0m - Successfully loaded headers for file:\n",
      "             /home/xavier/local/Python/PYPIT-development-suite/RAW_DATA/Keck_LRIS_red/long_600_7500_d560/LR.20160216.14090.fits\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marload.py 194 load_headers()\u001b[0m - Successfully loaded headers for file:\n",
      "             /home/xavier/local/Python/PYPIT-development-suite/RAW_DATA/Keck_LRIS_red/long_600_7500_d560/LR.20160216.07762.fits\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marload.py 194 load_headers()\u001b[0m - Successfully loaded headers for file:\n",
      "             /home/xavier/local/Python/PYPIT-development-suite/RAW_DATA/Keck_LRIS_red/long_600_7500_d560/LR.20160216.07646.fits\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marload.py 194 load_headers()\u001b[0m - Successfully loaded headers for file:\n",
      "             /home/xavier/local/Python/PYPIT-development-suite/RAW_DATA/Keck_LRIS_red/long_600_7500_d560/LR.20160216.14399.fits\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marload.py 194 load_headers()\u001b[0m - Successfully loaded headers for file:\n",
      "             /home/xavier/local/Python/PYPIT-development-suite/RAW_DATA/Keck_LRIS_red/long_600_7500_d560/LR.20160216.07820.fits\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marload.py 194 load_headers()\u001b[0m - Successfully loaded headers for file:\n",
      "             /home/xavier/local/Python/PYPIT-development-suite/RAW_DATA/Keck_LRIS_red/long_600_7500_d560/LR.20160216.07937.fits\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marload.py 194 load_headers()\u001b[0m - Successfully loaded headers for file:\n",
      "             /home/xavier/local/Python/PYPIT-development-suite/RAW_DATA/Keck_LRIS_red/long_600_7500_d560/LR.20160216.07878.fits\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marload.py 194 load_headers()\u001b[0m - Successfully loaded headers for file:\n",
      "             /home/xavier/local/Python/PYPIT-development-suite/RAW_DATA/Keck_LRIS_red/long_600_7500_d560/LR.20160216.05589.fits\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marload.py 194 load_headers()\u001b[0m - Successfully loaded headers for file:\n",
      "             /home/xavier/local/Python/PYPIT-development-suite/RAW_DATA/Keck_LRIS_red/long_600_7500_d560/LR.20160216.07412.fits\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marload.py 194 load_headers()\u001b[0m - Successfully loaded headers for file:\n",
      "             /home/xavier/local/Python/PYPIT-development-suite/RAW_DATA/Keck_LRIS_red/long_600_7500_d560/LR.20160216.14322.fits\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marload.py 194 load_headers()\u001b[0m - Successfully loaded headers for file:\n",
      "             /home/xavier/local/Python/PYPIT-development-suite/RAW_DATA/Keck_LRIS_red/long_600_7500_d560/LR.20160216.13991.fits\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marload.py 194 load_headers()\u001b[0m - Successfully loaded headers for file:\n",
      "             /home/xavier/local/Python/PYPIT-development-suite/RAW_DATA/Keck_LRIS_red/long_600_7500_d560/LR.20160216.07703.fits\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marload.py 194 load_headers()\u001b[0m - Successfully loaded headers for file:\n",
      "             /home/xavier/local/Python/PYPIT-development-suite/RAW_DATA/Keck_LRIS_red/long_600_7500_d560/LR.20160216.14167.fits\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marload.py 194 load_headers()\u001b[0m - Successfully loaded headers for file:\n",
      "             /home/xavier/local/Python/PYPIT-development-suite/RAW_DATA/Keck_LRIS_red/long_600_7500_d560/LR.20160216.07470.fits\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marload.py 194 load_headers()\u001b[0m - Successfully loaded headers for file:\n",
      "             /home/xavier/local/Python/PYPIT-development-suite/RAW_DATA/Keck_LRIS_red/long_600_7500_d560/LR.20160216.17613.fits\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marload.py 197 load_headers()\u001b[0m - Checking spectrograph settings for required header information\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marload.py 206 load_headers()\u001b[0m - Headers loaded for 23 files successfully\n"
     ]
    }
   ],
   "source": [
    "fitstbl = setupc.build_fitstbl(keck_lris_files)"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 8,
   "metadata": {},
   "outputs": [
    {
     "data": {
      "text/html": [
       "<i>Table length=5</i>\n",
       "<table id=\"table140122373421992\" class=\"table-striped table-bordered table-condensed\">\n",
       "<thead><tr><th>directory</th><th>filename</th><th>utc</th><th>target</th><th>idname</th><th>time</th><th>date</th><th>equinox</th><th>ra</th><th>dec</th><th>airmass</th><th>naxis0</th><th>naxis1</th><th>binning</th><th>exptime</th><th>filter1</th><th>filter2</th><th>hatch</th><th>shutopen</th><th>shutclose</th><th>decker</th><th>lamps</th><th>slitwid</th><th>slitlen</th><th>detrot</th><th>dichroic</th><th>dispname</th><th>dispangle</th><th>lampname01</th><th>lampstat01</th><th>lampname02</th><th>lampstat02</th><th>lampname03</th><th>lampstat03</th><th>lampname04</th><th>lampstat04</th><th>lampname05</th><th>lampstat05</th><th>lampname06</th><th>lampstat06</th><th>lampname07</th><th>lampstat07</th><th>lampname08</th><th>lampstat08</th><th>lampname09</th><th>lampstat09</th><th>lampname10</th><th>lampstat10</th><th>lampname11</th><th>lampstat11</th><th>lampname12</th><th>lampstat12</th><th>wavecen</th><th>instrume</th></tr></thead>\n",
       "<thead><tr><th>str92</th><th>str22</th><th>str11</th><th>str14</th><th>str4</th><th>float64</th><th>str19</th><th>str4</th><th>str11</th><th>str11</th><th>float64</th><th>str4</th><th>str4</th><th>str3</th><th>int64</th><th>str5</th><th>str4</th><th>str6</th><th>str4</th><th>str4</th><th>str8</th><th>str4</th><th>str4</th><th>str4</th><th>str4</th><th>str3</th><th>str8</th><th>float64</th><th>str7</th><th>str3</th><th>str4</th><th>str3</th><th>str5</th><th>str3</th><th>str7</th><th>str3</th><th>str4</th><th>str3</th><th>str7</th><th>str3</th><th>str5</th><th>str3</th><th>str7</th><th>str3</th><th>str9</th><th>str3</th><th>str6</th><th>str3</th><th>str6</th><th>str3</th><th>str7</th><th>str3</th><th>float64</th><th>str13</th></tr></thead>\n",
       "<tr><td>/home/xavier/local/Python/PYPIT-development-suite/RAW_DATA/Keck_LRIS_red/long_600_7500_d560/</td><td>LR.20160216.05529.fits</td><td>01:32:09.90</td><td></td><td>dark</td><td>1378417.5361</td><td>2016-02-16T01:32:11</td><td>None</td><td>00:00:00.00</td><td>+00:00:00.0</td><td>1.41294028</td><td>None</td><td>None</td><td>2,2</td><td>1</td><td>clear</td><td>None</td><td>closed</td><td>None</td><td>None</td><td>long_0.7</td><td>None</td><td>None</td><td>None</td><td>None</td><td>560</td><td>600/7500</td><td>27.0812645</td><td>MERCURY</td><td>on</td><td>NEON</td><td>on</td><td>ARGON</td><td>on</td><td>CADMIUM</td><td>on</td><td>ZINC</td><td>on</td><td>KRYPTON</td><td>on</td><td>XENON</td><td>on</td><td>FEARGON</td><td>off</td><td>DEUTERIUM</td><td>off</td><td>FLAMP1</td><td>off</td><td>FLAMP2</td><td>off</td><td>HALOGEN</td><td>off</td><td>7150.0078125</td><td>keck_lris_red</td></tr>\n",
       "<tr><td>/home/xavier/local/Python/PYPIT-development-suite/RAW_DATA/Keck_LRIS_red/long_600_7500_d560/</td><td>LR.20160216.05589.fits</td><td>01:33:09.40</td><td></td><td>dark</td><td>1378417.55263</td><td>2016-02-16T01:33:11</td><td>None</td><td>00:00:00.00</td><td>+00:00:00.0</td><td>1.41294028</td><td>None</td><td>None</td><td>2,2</td><td>1</td><td>clear</td><td>None</td><td>closed</td><td>None</td><td>None</td><td>long_0.7</td><td>None</td><td>None</td><td>None</td><td>None</td><td>560</td><td>600/7500</td><td>27.0812645</td><td>MERCURY</td><td>on</td><td>NEON</td><td>on</td><td>ARGON</td><td>on</td><td>CADMIUM</td><td>on</td><td>ZINC</td><td>on</td><td>KRYPTON</td><td>on</td><td>XENON</td><td>on</td><td>FEARGON</td><td>off</td><td>DEUTERIUM</td><td>off</td><td>FLAMP1</td><td>off</td><td>FLAMP2</td><td>off</td><td>HALOGEN</td><td>off</td><td>7150.0078125</td><td>keck_lris_red</td></tr>\n",
       "<tr><td>/home/xavier/local/Python/PYPIT-development-suite/RAW_DATA/Keck_LRIS_red/long_600_7500_d560/</td><td>LR.20160216.05649.fits</td><td>01:34:09.64</td><td></td><td>dark</td><td>1378417.56936</td><td>2016-02-16T01:34:11</td><td>None</td><td>00:00:00.00</td><td>+00:00:00.0</td><td>1.41294028</td><td>None</td><td>None</td><td>2,2</td><td>1</td><td>clear</td><td>None</td><td>closed</td><td>None</td><td>None</td><td>long_0.7</td><td>None</td><td>None</td><td>None</td><td>None</td><td>560</td><td>600/7500</td><td>27.0812645</td><td>MERCURY</td><td>on</td><td>NEON</td><td>on</td><td>ARGON</td><td>on</td><td>CADMIUM</td><td>on</td><td>ZINC</td><td>on</td><td>KRYPTON</td><td>on</td><td>XENON</td><td>on</td><td>FEARGON</td><td>off</td><td>DEUTERIUM</td><td>off</td><td>FLAMP1</td><td>off</td><td>FLAMP2</td><td>off</td><td>HALOGEN</td><td>off</td><td>7150.0078125</td><td>keck_lris_red</td></tr>\n",
       "<tr><td>/home/xavier/local/Python/PYPIT-development-suite/RAW_DATA/Keck_LRIS_red/long_600_7500_d560/</td><td>LR.20160216.05709.fits</td><td>01:35:09.44</td><td>None</td><td>dark</td><td>1378417.58597</td><td>2016-02-16T01:35:11</td><td>None</td><td>None</td><td>+00:00:00.0</td><td>1.41294028</td><td>None</td><td>None</td><td>2,2</td><td>1</td><td>clear</td><td>None</td><td>closed</td><td>None</td><td>None</td><td>long_0.7</td><td>None</td><td>None</td><td>None</td><td>None</td><td>560</td><td>600/7500</td><td>27.0812645</td><td>MERCURY</td><td>on</td><td>NEON</td><td>on</td><td>ARGON</td><td>on</td><td>CADMIUM</td><td>on</td><td>ZINC</td><td>on</td><td>KRYPTON</td><td>on</td><td>XENON</td><td>on</td><td>FEARGON</td><td>off</td><td>DEUTERIUM</td><td>off</td><td>FLAMP1</td><td>off</td><td>FLAMP2</td><td>off</td><td>HALOGEN</td><td>off</td><td>7150.0078125</td><td>keck_lris_red</td></tr>\n",
       "<tr><td>/home/xavier/local/Python/PYPIT-development-suite/RAW_DATA/Keck_LRIS_red/long_600_7500_d560/</td><td>LR.20160216.07348.fits</td><td>02:02:28.34</td><td>None</td><td>dark</td><td>1378418.04122</td><td>2016-02-16T02:02:28</td><td>None</td><td>15:20:00.00</td><td>+45:00:00.0</td><td>1.41309745</td><td>None</td><td>None</td><td>2,2</td><td>0</td><td>clear</td><td>None</td><td>closed</td><td>None</td><td>None</td><td>long_0.7</td><td>None</td><td>None</td><td>None</td><td>None</td><td>560</td><td>600/7500</td><td>27.0812645</td><td>MERCURY</td><td>off</td><td>NEON</td><td>off</td><td>ARGON</td><td>off</td><td>CADMIUM</td><td>off</td><td>ZINC</td><td>off</td><td>KRYPTON</td><td>off</td><td>XENON</td><td>off</td><td>FEARGON</td><td>off</td><td>DEUTERIUM</td><td>off</td><td>FLAMP1</td><td>off</td><td>FLAMP2</td><td>off</td><td>HALOGEN</td><td>on</td><td>7150.0078125</td><td>keck_lris_red</td></tr>\n",
       "</table>"
      ],
      "text/plain": [
       "<Table length=5>\n",
       "                                         directory                                           ...\n",
       "                                           str92                                             ...\n",
       "-------------------------------------------------------------------------------------------- ...\n",
       "/home/xavier/local/Python/PYPIT-development-suite/RAW_DATA/Keck_LRIS_red/long_600_7500_d560/ ...\n",
       "/home/xavier/local/Python/PYPIT-development-suite/RAW_DATA/Keck_LRIS_red/long_600_7500_d560/ ...\n",
       "/home/xavier/local/Python/PYPIT-development-suite/RAW_DATA/Keck_LRIS_red/long_600_7500_d560/ ...\n",
       "/home/xavier/local/Python/PYPIT-development-suite/RAW_DATA/Keck_LRIS_red/long_600_7500_d560/ ...\n",
       "/home/xavier/local/Python/PYPIT-development-suite/RAW_DATA/Keck_LRIS_red/long_600_7500_d560/ ..."
      ]
     },
     "execution_count": 8,
     "metadata": {},
     "output_type": "execute_result"
    }
   ],
   "source": [
    "fitstbl[0:5]"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "## Image type\n",
    "    Classifies the images\n",
    "    Adds image type columns to the fitstbl"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 9,
   "metadata": {},
   "outputs": [
    {
     "name": "stderr",
     "output_type": "stream",
     "text": [
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marsort.py 110 type_data()\u001b[0m - Typing files\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marsort.py 169 type_data()\u001b[0m - Making forced file identification changes\n",
      "\u001b[1;31m[WARNING] ::\u001b[0m \u001b[1;34marsort.py 170 type_data()\u001b[0m - Note that the image will have *only* the specified type\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marsort.py 188 type_data()\u001b[0m - Couldn't identify the following files:\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marsort.py 190 type_data()\u001b[0m - LR.20160216.07348.fits\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marsort.py 202 type_data()\u001b[0m - Typing completed!\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34mpypitsetup.py 228 type_data()\u001b[0m - Adding file type information to the fitstbl\n"
     ]
    }
   ],
   "source": [
    "filetypes = setupc.type_data(flag_unknown=True)"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "### Show"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 10,
   "metadata": {},
   "outputs": [
    {
     "data": {
      "text/html": [
       "<i>Table length=23</i>\n",
       "<table id=\"table140122373288288\" class=\"table-striped table-bordered table-condensed\">\n",
       "<thead><tr><th>filename</th><th>arc</th><th>bias</th><th>pixelflat</th><th>science</th><th>standard</th><th>unknown</th></tr></thead>\n",
       "<thead><tr><th>str22</th><th>bool</th><th>bool</th><th>bool</th><th>bool</th><th>bool</th><th>bool</th></tr></thead>\n",
       "<tr><td>LR.20160216.05529.fits</td><td>True</td><td>False</td><td>False</td><td>False</td><td>False</td><td>False</td></tr>\n",
       "<tr><td>LR.20160216.05589.fits</td><td>True</td><td>False</td><td>False</td><td>False</td><td>False</td><td>False</td></tr>\n",
       "<tr><td>LR.20160216.05649.fits</td><td>True</td><td>False</td><td>False</td><td>False</td><td>False</td><td>False</td></tr>\n",
       "<tr><td>LR.20160216.05709.fits</td><td>True</td><td>False</td><td>False</td><td>False</td><td>False</td><td>False</td></tr>\n",
       "<tr><td>LR.20160216.07348.fits</td><td>False</td><td>False</td><td>False</td><td>False</td><td>False</td><td>True</td></tr>\n",
       "<tr><td>LR.20160216.07412.fits</td><td>False</td><td>True</td><td>False</td><td>False</td><td>False</td><td>False</td></tr>\n",
       "<tr><td>LR.20160216.07470.fits</td><td>False</td><td>True</td><td>False</td><td>False</td><td>False</td><td>False</td></tr>\n",
       "<tr><td>LR.20160216.07529.fits</td><td>False</td><td>True</td><td>False</td><td>False</td><td>False</td><td>False</td></tr>\n",
       "<tr><td>LR.20160216.07587.fits</td><td>False</td><td>True</td><td>False</td><td>False</td><td>False</td><td>False</td></tr>\n",
       "<tr><td>LR.20160216.07646.fits</td><td>False</td><td>True</td><td>False</td><td>False</td><td>False</td><td>False</td></tr>\n",
       "<tr><td>...</td><td>...</td><td>...</td><td>...</td><td>...</td><td>...</td><td>...</td></tr>\n",
       "<tr><td>LR.20160216.07878.fits</td><td>False</td><td>True</td><td>False</td><td>False</td><td>False</td><td>False</td></tr>\n",
       "<tr><td>LR.20160216.07937.fits</td><td>False</td><td>True</td><td>False</td><td>False</td><td>False</td><td>False</td></tr>\n",
       "<tr><td>LR.20160216.13991.fits</td><td>False</td><td>False</td><td>True</td><td>False</td><td>False</td><td>False</td></tr>\n",
       "<tr><td>LR.20160216.14090.fits</td><td>False</td><td>False</td><td>True</td><td>False</td><td>False</td><td>False</td></tr>\n",
       "<tr><td>LR.20160216.14167.fits</td><td>False</td><td>False</td><td>True</td><td>False</td><td>False</td><td>False</td></tr>\n",
       "<tr><td>LR.20160216.14244.fits</td><td>False</td><td>False</td><td>True</td><td>False</td><td>False</td><td>False</td></tr>\n",
       "<tr><td>LR.20160216.14322.fits</td><td>False</td><td>False</td><td>True</td><td>False</td><td>False</td><td>False</td></tr>\n",
       "<tr><td>LR.20160216.14399.fits</td><td>False</td><td>False</td><td>True</td><td>False</td><td>False</td><td>False</td></tr>\n",
       "<tr><td>LR.20160216.17613.fits</td><td>False</td><td>False</td><td>False</td><td>False</td><td>True</td><td>False</td></tr>\n",
       "<tr><td>LR.20160216.40478.fits</td><td>False</td><td>False</td><td>False</td><td>True</td><td>False</td><td>False</td></tr>\n",
       "</table>"
      ],
      "text/plain": [
       "<Table length=23>\n",
       "       filename         arc   bias pixelflat science standard unknown\n",
       "        str22           bool  bool    bool     bool    bool     bool \n",
       "---------------------- ----- ----- --------- ------- -------- -------\n",
       "LR.20160216.05529.fits  True False     False   False    False   False\n",
       "LR.20160216.05589.fits  True False     False   False    False   False\n",
       "LR.20160216.05649.fits  True False     False   False    False   False\n",
       "LR.20160216.05709.fits  True False     False   False    False   False\n",
       "LR.20160216.07348.fits False False     False   False    False    True\n",
       "LR.20160216.07412.fits False  True     False   False    False   False\n",
       "LR.20160216.07470.fits False  True     False   False    False   False\n",
       "LR.20160216.07529.fits False  True     False   False    False   False\n",
       "LR.20160216.07587.fits False  True     False   False    False   False\n",
       "LR.20160216.07646.fits False  True     False   False    False   False\n",
       "                   ...   ...   ...       ...     ...      ...     ...\n",
       "LR.20160216.07878.fits False  True     False   False    False   False\n",
       "LR.20160216.07937.fits False  True     False   False    False   False\n",
       "LR.20160216.13991.fits False False      True   False    False   False\n",
       "LR.20160216.14090.fits False False      True   False    False   False\n",
       "LR.20160216.14167.fits False False      True   False    False   False\n",
       "LR.20160216.14244.fits False False      True   False    False   False\n",
       "LR.20160216.14322.fits False False      True   False    False   False\n",
       "LR.20160216.14399.fits False False      True   False    False   False\n",
       "LR.20160216.17613.fits False False     False   False     True   False\n",
       "LR.20160216.40478.fits False False     False    True    False   False"
      ]
     },
     "execution_count": 10,
     "metadata": {},
     "output_type": "execute_result"
    }
   ],
   "source": [
    "setupc.fitstbl[['filename','arc','bias','pixelflat','science','standard','unknown' ]]"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "## Match to science"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 11,
   "metadata": {},
   "outputs": [
    {
     "name": "stderr",
     "output_type": "stream",
     "text": [
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marsort.py 964 match_to_science()\u001b[0m - Matching calibrations to Science frames\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marsort.py 973 match_to_science()\u001b[0m - =================================================\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marsort.py 975 match_to_science()\u001b[0m - Matching calibrations to OFF_J1044p6306: LR.20160216.40478.fits\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marsort.py 1025 match_to_science()\u001b[0m -   Found 4 arc frame for OFF_J1044p6306 (1 required)\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marsort.py 1025 match_to_science()\u001b[0m -   Found 10 bias frame for OFF_J1044p6306 (5 required)\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marsort.py 988 match_to_science()\u001b[0m -   Dark frames not required.  Not matching..\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marsort.py 1002 match_to_science()\u001b[0m -    No pinhole frames are required.  Not matching..\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marsort.py 1025 match_to_science()\u001b[0m -   Found 6 pixelflat frame for OFF_J1044p6306 (3 required)\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marsort.py 1025 match_to_science()\u001b[0m -   Found 1 standard frame for OFF_J1044p6306 (1 required)\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marsort.py 1025 match_to_science()\u001b[0m -   Found 6 trace frame for OFF_J1044p6306 (3 required)\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marsort.py 1047 match_to_science()\u001b[0m - Science frames successfully matched to calibration frames\n"
     ]
    }
   ],
   "source": [
    "fitstbl = setupc.match_to_science()"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "### Setup dict"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 12,
   "metadata": {
    "collapsed": true
   },
   "outputs": [],
   "source": [
    "setup_dict = setupc.build_setup_dict()"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 13,
   "metadata": {},
   "outputs": [
    {
     "data": {
      "text/plain": [
       "{'A': {'--': {'dichroic': '560',\n",
       "   'disperser': {'angle': 27.0812645, 'name': '600/7500'},\n",
       "   'slit': {'decker': 'long_0.7', 'slitlen': 'None', 'slitwid': 'None'}},\n",
       "  '01': {'binning': '2,2', 'det': 1, 'namp': 2},\n",
       "  '02': {'binning': '2,2', 'det': 2, 'namp': 2},\n",
       "  'aa': {'arc': ['LR.20160216.05709.fits'],\n",
       "   'bias': ['LR.20160216.07703.fits',\n",
       "    'LR.20160216.07762.fits',\n",
       "    'LR.20160216.07820.fits',\n",
       "    'LR.20160216.07878.fits',\n",
       "    'LR.20160216.07937.fits'],\n",
       "   'pixelflat': ['LR.20160216.14244.fits',\n",
       "    'LR.20160216.14322.fits',\n",
       "    'LR.20160216.14399.fits'],\n",
       "   'science': ['LR.20160216.40478.fits'],\n",
       "   'trace': ['LR.20160216.14244.fits',\n",
       "    'LR.20160216.14322.fits',\n",
       "    'LR.20160216.14399.fits']}}}"
      ]
     },
     "execution_count": 13,
     "metadata": {},
     "output_type": "execute_result"
    }
   ],
   "source": [
    "setup_dict"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 14,
   "metadata": {},
   "outputs": [
    {
     "data": {
      "text/html": [
       "<i>Table length=23</i>\n",
       "<table id=\"table140122365398544\" class=\"table-striped table-bordered table-condensed\">\n",
       "<thead><tr><th>filename</th><th>arc</th><th>bias</th><th>pixelflat</th><th>science</th><th>standard</th><th>sci_ID</th></tr></thead>\n",
       "<thead><tr><th>str22</th><th>bool</th><th>bool</th><th>bool</th><th>bool</th><th>bool</th><th>int64</th></tr></thead>\n",
       "<tr><td>LR.20160216.05529.fits</td><td>True</td><td>False</td><td>False</td><td>False</td><td>False</td><td>0</td></tr>\n",
       "<tr><td>LR.20160216.05589.fits</td><td>True</td><td>False</td><td>False</td><td>False</td><td>False</td><td>0</td></tr>\n",
       "<tr><td>LR.20160216.05649.fits</td><td>True</td><td>False</td><td>False</td><td>False</td><td>False</td><td>0</td></tr>\n",
       "<tr><td>LR.20160216.05709.fits</td><td>True</td><td>False</td><td>False</td><td>False</td><td>False</td><td>1</td></tr>\n",
       "<tr><td>LR.20160216.07348.fits</td><td>False</td><td>False</td><td>False</td><td>False</td><td>False</td><td>0</td></tr>\n",
       "<tr><td>LR.20160216.07412.fits</td><td>False</td><td>True</td><td>False</td><td>False</td><td>False</td><td>0</td></tr>\n",
       "<tr><td>LR.20160216.07470.fits</td><td>False</td><td>True</td><td>False</td><td>False</td><td>False</td><td>0</td></tr>\n",
       "<tr><td>LR.20160216.07529.fits</td><td>False</td><td>True</td><td>False</td><td>False</td><td>False</td><td>0</td></tr>\n",
       "<tr><td>LR.20160216.07587.fits</td><td>False</td><td>True</td><td>False</td><td>False</td><td>False</td><td>0</td></tr>\n",
       "<tr><td>LR.20160216.07646.fits</td><td>False</td><td>True</td><td>False</td><td>False</td><td>False</td><td>0</td></tr>\n",
       "<tr><td>...</td><td>...</td><td>...</td><td>...</td><td>...</td><td>...</td><td>...</td></tr>\n",
       "<tr><td>LR.20160216.07878.fits</td><td>False</td><td>True</td><td>False</td><td>False</td><td>False</td><td>1</td></tr>\n",
       "<tr><td>LR.20160216.07937.fits</td><td>False</td><td>True</td><td>False</td><td>False</td><td>False</td><td>1</td></tr>\n",
       "<tr><td>LR.20160216.13991.fits</td><td>False</td><td>False</td><td>True</td><td>False</td><td>False</td><td>0</td></tr>\n",
       "<tr><td>LR.20160216.14090.fits</td><td>False</td><td>False</td><td>True</td><td>False</td><td>False</td><td>0</td></tr>\n",
       "<tr><td>LR.20160216.14167.fits</td><td>False</td><td>False</td><td>True</td><td>False</td><td>False</td><td>0</td></tr>\n",
       "<tr><td>LR.20160216.14244.fits</td><td>False</td><td>False</td><td>True</td><td>False</td><td>False</td><td>1</td></tr>\n",
       "<tr><td>LR.20160216.14322.fits</td><td>False</td><td>False</td><td>True</td><td>False</td><td>False</td><td>1</td></tr>\n",
       "<tr><td>LR.20160216.14399.fits</td><td>False</td><td>False</td><td>True</td><td>False</td><td>False</td><td>1</td></tr>\n",
       "<tr><td>LR.20160216.17613.fits</td><td>False</td><td>False</td><td>False</td><td>False</td><td>True</td><td>1</td></tr>\n",
       "<tr><td>LR.20160216.40478.fits</td><td>False</td><td>False</td><td>False</td><td>True</td><td>False</td><td>1</td></tr>\n",
       "</table>"
      ],
      "text/plain": [
       "<Table length=23>\n",
       "       filename         arc   bias pixelflat science standard sci_ID\n",
       "        str22           bool  bool    bool     bool    bool   int64 \n",
       "---------------------- ----- ----- --------- ------- -------- ------\n",
       "LR.20160216.05529.fits  True False     False   False    False      0\n",
       "LR.20160216.05589.fits  True False     False   False    False      0\n",
       "LR.20160216.05649.fits  True False     False   False    False      0\n",
       "LR.20160216.05709.fits  True False     False   False    False      1\n",
       "LR.20160216.07348.fits False False     False   False    False      0\n",
       "LR.20160216.07412.fits False  True     False   False    False      0\n",
       "LR.20160216.07470.fits False  True     False   False    False      0\n",
       "LR.20160216.07529.fits False  True     False   False    False      0\n",
       "LR.20160216.07587.fits False  True     False   False    False      0\n",
       "LR.20160216.07646.fits False  True     False   False    False      0\n",
       "                   ...   ...   ...       ...     ...      ...    ...\n",
       "LR.20160216.07878.fits False  True     False   False    False      1\n",
       "LR.20160216.07937.fits False  True     False   False    False      1\n",
       "LR.20160216.13991.fits False False      True   False    False      0\n",
       "LR.20160216.14090.fits False False      True   False    False      0\n",
       "LR.20160216.14167.fits False False      True   False    False      0\n",
       "LR.20160216.14244.fits False False      True   False    False      1\n",
       "LR.20160216.14322.fits False False      True   False    False      1\n",
       "LR.20160216.14399.fits False False      True   False    False      1\n",
       "LR.20160216.17613.fits False False     False   False     True      1\n",
       "LR.20160216.40478.fits False False     False    True    False      1"
      ]
     },
     "execution_count": 14,
     "metadata": {},
     "output_type": "execute_result"
    }
   ],
   "source": [
    "setupc.fitstbl[['filename','arc','bias','pixelflat','science','standard','sci_ID']]"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "## Setup :: command line\n",
    "    pypit_setup /home/xavier/local/Python/PYPIT-development-suite/RAW_DATA/Keck_LRIS_red/long_600_7500_d560/LR.20160216 keck_lris_red -c"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 15,
   "metadata": {
    "collapsed": true
   },
   "outputs": [],
   "source": [
    "cols = ['filename', 'target']+setupc.ftypes+['failures', 'sci_ID']"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 16,
   "metadata": {},
   "outputs": [
    {
     "data": {
      "text/html": [
       "<i>Table length=23</i>\n",
       "<table id=\"table140122365396752\" class=\"table-striped table-bordered table-condensed\">\n",
       "<thead><tr><th>filename</th><th>target</th><th>arc</th><th>bias</th><th>dark</th><th>pinhole</th><th>pixelflat</th><th>science</th><th>standard</th><th>trace</th><th>unknown</th><th>failures</th><th>sci_ID</th></tr></thead>\n",
       "<thead><tr><th>str22</th><th>str14</th><th>bool</th><th>bool</th><th>bool</th><th>bool</th><th>bool</th><th>bool</th><th>bool</th><th>bool</th><th>bool</th><th>bool</th><th>int64</th></tr></thead>\n",
       "<tr><td>LR.20160216.05529.fits</td><td></td><td>True</td><td>False</td><td>False</td><td>False</td><td>False</td><td>False</td><td>False</td><td>False</td><td>False</td><td>False</td><td>0</td></tr>\n",
       "<tr><td>LR.20160216.05589.fits</td><td></td><td>True</td><td>False</td><td>False</td><td>False</td><td>False</td><td>False</td><td>False</td><td>False</td><td>False</td><td>False</td><td>0</td></tr>\n",
       "<tr><td>LR.20160216.05649.fits</td><td></td><td>True</td><td>False</td><td>False</td><td>False</td><td>False</td><td>False</td><td>False</td><td>False</td><td>False</td><td>False</td><td>0</td></tr>\n",
       "<tr><td>LR.20160216.05709.fits</td><td>None</td><td>True</td><td>False</td><td>False</td><td>False</td><td>False</td><td>False</td><td>False</td><td>False</td><td>False</td><td>False</td><td>1</td></tr>\n",
       "<tr><td>LR.20160216.07348.fits</td><td>None</td><td>False</td><td>False</td><td>False</td><td>False</td><td>False</td><td>False</td><td>False</td><td>False</td><td>True</td><td>False</td><td>0</td></tr>\n",
       "<tr><td>LR.20160216.07412.fits</td><td>unknown</td><td>False</td><td>True</td><td>False</td><td>False</td><td>False</td><td>False</td><td>False</td><td>False</td><td>False</td><td>False</td><td>0</td></tr>\n",
       "<tr><td>LR.20160216.07470.fits</td><td>unknown</td><td>False</td><td>True</td><td>False</td><td>False</td><td>False</td><td>False</td><td>False</td><td>False</td><td>False</td><td>False</td><td>0</td></tr>\n",
       "<tr><td>LR.20160216.07529.fits</td><td>unknown</td><td>False</td><td>True</td><td>False</td><td>False</td><td>False</td><td>False</td><td>False</td><td>False</td><td>False</td><td>False</td><td>0</td></tr>\n",
       "<tr><td>LR.20160216.07587.fits</td><td>unknown</td><td>False</td><td>True</td><td>False</td><td>False</td><td>False</td><td>False</td><td>False</td><td>False</td><td>False</td><td>False</td><td>0</td></tr>\n",
       "<tr><td>LR.20160216.07646.fits</td><td>unknown</td><td>False</td><td>True</td><td>False</td><td>False</td><td>False</td><td>False</td><td>False</td><td>False</td><td>False</td><td>False</td><td>0</td></tr>\n",
       "<tr><td>...</td><td>...</td><td>...</td><td>...</td><td>...</td><td>...</td><td>...</td><td>...</td><td>...</td><td>...</td><td>...</td><td>...</td><td>...</td></tr>\n",
       "<tr><td>LR.20160216.07878.fits</td><td>unknown</td><td>False</td><td>True</td><td>False</td><td>False</td><td>False</td><td>False</td><td>False</td><td>False</td><td>False</td><td>False</td><td>1</td></tr>\n",
       "<tr><td>LR.20160216.07937.fits</td><td>unknown</td><td>False</td><td>True</td><td>False</td><td>False</td><td>False</td><td>False</td><td>False</td><td>False</td><td>False</td><td>False</td><td>1</td></tr>\n",
       "<tr><td>LR.20160216.13991.fits</td><td>unknown</td><td>False</td><td>False</td><td>False</td><td>False</td><td>True</td><td>False</td><td>False</td><td>True</td><td>False</td><td>False</td><td>0</td></tr>\n",
       "<tr><td>LR.20160216.14090.fits</td><td>unknown</td><td>False</td><td>False</td><td>False</td><td>False</td><td>True</td><td>False</td><td>False</td><td>True</td><td>False</td><td>False</td><td>0</td></tr>\n",
       "<tr><td>LR.20160216.14167.fits</td><td>unknown</td><td>False</td><td>False</td><td>False</td><td>False</td><td>True</td><td>False</td><td>False</td><td>True</td><td>False</td><td>False</td><td>0</td></tr>\n",
       "<tr><td>LR.20160216.14244.fits</td><td>unknown</td><td>False</td><td>False</td><td>False</td><td>False</td><td>True</td><td>False</td><td>False</td><td>True</td><td>False</td><td>False</td><td>1</td></tr>\n",
       "<tr><td>LR.20160216.14322.fits</td><td>unknown</td><td>False</td><td>False</td><td>False</td><td>False</td><td>True</td><td>False</td><td>False</td><td>True</td><td>False</td><td>False</td><td>1</td></tr>\n",
       "<tr><td>LR.20160216.14399.fits</td><td>unknown</td><td>False</td><td>False</td><td>False</td><td>False</td><td>True</td><td>False</td><td>False</td><td>True</td><td>False</td><td>False</td><td>1</td></tr>\n",
       "<tr><td>LR.20160216.17613.fits</td><td>G1910B2B</td><td>False</td><td>False</td><td>False</td><td>False</td><td>False</td><td>False</td><td>True</td><td>False</td><td>False</td><td>False</td><td>1</td></tr>\n",
       "<tr><td>LR.20160216.40478.fits</td><td>OFF_J1044p6306</td><td>False</td><td>False</td><td>False</td><td>False</td><td>False</td><td>True</td><td>False</td><td>False</td><td>False</td><td>False</td><td>1</td></tr>\n",
       "</table>"
      ],
      "text/plain": [
       "<Table length=23>\n",
       "       filename            target      arc   bias ... unknown failures sci_ID\n",
       "        str22              str14       bool  bool ...   bool    bool   int64 \n",
       "---------------------- -------------- ----- ----- ... ------- -------- ------\n",
       "LR.20160216.05529.fits                 True False ...   False    False      0\n",
       "LR.20160216.05589.fits                 True False ...   False    False      0\n",
       "LR.20160216.05649.fits                 True False ...   False    False      0\n",
       "LR.20160216.05709.fits           None  True False ...   False    False      1\n",
       "LR.20160216.07348.fits           None False False ...    True    False      0\n",
       "LR.20160216.07412.fits        unknown False  True ...   False    False      0\n",
       "LR.20160216.07470.fits        unknown False  True ...   False    False      0\n",
       "LR.20160216.07529.fits        unknown False  True ...   False    False      0\n",
       "LR.20160216.07587.fits        unknown False  True ...   False    False      0\n",
       "LR.20160216.07646.fits        unknown False  True ...   False    False      0\n",
       "                   ...            ...   ...   ... ...     ...      ...    ...\n",
       "LR.20160216.07878.fits        unknown False  True ...   False    False      1\n",
       "LR.20160216.07937.fits        unknown False  True ...   False    False      1\n",
       "LR.20160216.13991.fits        unknown False False ...   False    False      0\n",
       "LR.20160216.14090.fits        unknown False False ...   False    False      0\n",
       "LR.20160216.14167.fits        unknown False False ...   False    False      0\n",
       "LR.20160216.14244.fits        unknown False False ...   False    False      1\n",
       "LR.20160216.14322.fits        unknown False False ...   False    False      1\n",
       "LR.20160216.14399.fits        unknown False False ...   False    False      1\n",
       "LR.20160216.17613.fits       G1910B2B False False ...   False    False      1\n",
       "LR.20160216.40478.fits OFF_J1044p6306 False False ...   False    False      1"
      ]
     },
     "execution_count": 16,
     "metadata": {},
     "output_type": "execute_result"
    }
   ],
   "source": [
    "setupc.fitstbl[cols]"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "----"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {
    "collapsed": true
   },
   "source": [
    "## Setup + datasec"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 17,
   "metadata": {
    "collapsed": true
   },
   "outputs": [],
   "source": [
    "# Image IDs\n",
    "sci_ID = 1  # First exposure ID\n",
    "det = 2     # Slitb for LRIS\n",
    "dnum = 'det02'"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 18,
   "metadata": {},
   "outputs": [
    {
     "data": {
      "text/plain": [
       "22"
      ]
     },
     "execution_count": 18,
     "metadata": {},
     "output_type": "execute_result"
    }
   ],
   "source": [
    "# Index in fitstbl\n",
    "scidx = np.where((fitstbl['sci_ID'] == sci_ID) & fitstbl['science'])[0][0]\n",
    "scidx"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "### Settings"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 19,
   "metadata": {
    "collapsed": true
   },
   "outputs": [],
   "source": [
    "settings_det = settings.spect[dnum].copy()  # Should include naxis0, naxis1 in this"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 20,
   "metadata": {},
   "outputs": [
    {
     "data": {
      "text/plain": [
       "{'darkcurr': 0.0,\n",
       " 'gain': [1.191, 1.162],\n",
       " 'nonlinear': 0.76,\n",
       " 'numamplifiers': 2,\n",
       " 'platescale': 0.135,\n",
       " 'ronoise': [4.54, 4.62],\n",
       " 'saturation': 65535.0,\n",
       " 'suffix': '_02red',\n",
       " 'xgap': 0.0,\n",
       " 'ygap': 0.0,\n",
       " 'ysize': 1.0}"
      ]
     },
     "execution_count": 20,
     "metadata": {},
     "output_type": "execute_result"
    }
   ],
   "source": [
    "settings_det"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 21,
   "metadata": {
    "collapsed": true
   },
   "outputs": [],
   "source": [
    "# Ugliness\n",
    "settings_det['binning'] = fitstbl['binning'][0]\n",
    "#\n",
    "settings.spect[dnum] = settings_det.copy()  # Used internally..\n",
    "#\n",
    "tsettings = settings.argflag.copy()\n",
    "tsettings['detector'] = settings.spect[settings.get_dnum(det)]\n",
    "tsettings['detector']['dataext'] = None\n",
    "tsettings['detector']['dispaxis'] = settings.argflag['trace']['dispersion']['direction']"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "### Setup"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 22,
   "metadata": {},
   "outputs": [
    {
     "data": {
      "text/plain": [
       "'A_02_aa'"
      ]
     },
     "execution_count": 22,
     "metadata": {},
     "output_type": "execute_result"
    }
   ],
   "source": [
    "setup = arsetup.instr_setup(sci_ID, det, fitstbl, setup_dict, settings_det['numamplifiers'], must_exist=True)\n",
    "setup"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "### datasec"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 23,
   "metadata": {
    "collapsed": true
   },
   "outputs": [],
   "source": [
    "scifile = os.path.join(fitstbl['directory'][scidx],fitstbl['filename'][scidx])"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 24,
   "metadata": {},
   "outputs": [
    {
     "name": "stderr",
     "output_type": "stream",
     "text": [
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marprocimg.py 174 get_datasec()\u001b[0m - Parsing datasec and oscansec from headers\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marlris.py 48 read_lris()\u001b[0m - Reading LRIS file: /home/xavier/local/Python/PYPIT-development-suite/RAW_DATA/Keck_LRIS_red/long_600_7500_d560/LR.20160216.40478.fits\n"
     ]
    }
   ],
   "source": [
    "datasec_img, naxis0, naxis1 = arprocimg.get_datasec_trimmed(\n",
    "    spectrograph, scifile, det, settings_det,\n",
    "    naxis0=fitstbl['naxis0'][scidx],\n",
    "    naxis1=fitstbl['naxis1'][scidx])"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 25,
   "metadata": {},
   "outputs": [
    {
     "data": {
      "text/plain": [
       "((2048, 1024), 2068, 1110)"
      ]
     },
     "execution_count": 25,
     "metadata": {},
     "output_type": "execute_result"
    }
   ],
   "source": [
    "datasec_img.shape, naxis0, naxis1"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 26,
   "metadata": {
    "collapsed": true
   },
   "outputs": [],
   "source": [
    "fitstbl['naxis0'][scidx] = naxis0\n",
    "fitstbl['naxis1'][scidx] = naxis1"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "----"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "## Bias"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 27,
   "metadata": {
    "collapsed": true
   },
   "outputs": [],
   "source": [
    "tsettings['bias']['combine']['reject']['cosmics'] = 3."
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 28,
   "metadata": {
    "collapsed": true
   },
   "outputs": [],
   "source": [
    "biasFrame = biasframe.BiasFrame(settings=tsettings, setup=setup,\n",
    "                                    det=det, fitstbl=fitstbl, sci_ID=sci_ID)"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 29,
   "metadata": {},
   "outputs": [
    {
     "name": "stderr",
     "output_type": "stream",
     "text": [
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marload.py 327 load_raw_frame()\u001b[0m - Loading raw_file: /home/xavier/local/Python/PYPIT-development-suite/RAW_DATA/Keck_LRIS_red/long_600_7500_d560/LR.20160216.07703.fits\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marlris.py 48 read_lris()\u001b[0m - Reading LRIS file: /home/xavier/local/Python/PYPIT-development-suite/RAW_DATA/Keck_LRIS_red/long_600_7500_d560/LR.20160216.07703.fits\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marload.py 327 load_raw_frame()\u001b[0m - Loading raw_file: /home/xavier/local/Python/PYPIT-development-suite/RAW_DATA/Keck_LRIS_red/long_600_7500_d560/LR.20160216.07762.fits\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marlris.py 48 read_lris()\u001b[0m - Reading LRIS file: /home/xavier/local/Python/PYPIT-development-suite/RAW_DATA/Keck_LRIS_red/long_600_7500_d560/LR.20160216.07762.fits\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marload.py 327 load_raw_frame()\u001b[0m - Loading raw_file: /home/xavier/local/Python/PYPIT-development-suite/RAW_DATA/Keck_LRIS_red/long_600_7500_d560/LR.20160216.07820.fits\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marlris.py 48 read_lris()\u001b[0m - Reading LRIS file: /home/xavier/local/Python/PYPIT-development-suite/RAW_DATA/Keck_LRIS_red/long_600_7500_d560/LR.20160216.07820.fits\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marload.py 327 load_raw_frame()\u001b[0m - Loading raw_file: /home/xavier/local/Python/PYPIT-development-suite/RAW_DATA/Keck_LRIS_red/long_600_7500_d560/LR.20160216.07878.fits\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marlris.py 48 read_lris()\u001b[0m - Reading LRIS file: /home/xavier/local/Python/PYPIT-development-suite/RAW_DATA/Keck_LRIS_red/long_600_7500_d560/LR.20160216.07878.fits\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marload.py 327 load_raw_frame()\u001b[0m - Loading raw_file: /home/xavier/local/Python/PYPIT-development-suite/RAW_DATA/Keck_LRIS_red/long_600_7500_d560/LR.20160216.07937.fits\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marlris.py 48 read_lris()\u001b[0m - Reading LRIS file: /home/xavier/local/Python/PYPIT-development-suite/RAW_DATA/Keck_LRIS_red/long_600_7500_d560/LR.20160216.07937.fits\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marprocimg.py 174 get_datasec()\u001b[0m - Parsing datasec and oscansec from headers\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marlris.py 48 read_lris()\u001b[0m - Reading LRIS file: /home/xavier/local/Python/PYPIT-development-suite/RAW_DATA/Keck_LRIS_red/long_600_7500_d560/LR.20160216.07703.fits\n",
      "\u001b[1;31m[WARNING] ::\u001b[0m \u001b[1;34mprocessimages.py 385 process()\u001b[0m - Your images have not been bias subtracted!\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marcomb.py 94 core_comb_frames()\u001b[0m - Combining 5 bias frames\n",
      "\u001b[1;30m[WORK IN ]::\u001b[0m\n",
      "\u001b[1;33m[PROGRESS]::\u001b[0m \u001b[1;34marcomb.py 98 core_comb_frames()\u001b[0m - lscomb feature has not been included here yet...\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marcomb.py 162 core_comb_frames()\u001b[0m - Finding saturated and non-linear pixels\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marcomb.py 189 core_comb_frames()\u001b[0m - Rejecting cosmic rays\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marcomb.py 231 core_comb_frames()\u001b[0m - Not rejecting any low/high pixels\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marcomb.py 235 core_comb_frames()\u001b[0m - Rejecting deviant pixels\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marcomb.py 256 core_comb_frames()\u001b[0m - Combining frames with a mean operation\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marcomb.py 294 core_comb_frames()\u001b[0m - Replacing completely masked pixels with the median value of the input frames\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marcomb.py 307 core_comb_frames()\u001b[0m - 5 bias frames combined successfully!\n"
     ]
    }
   ],
   "source": [
    "msbias = biasFrame.build_image()"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 30,
   "metadata": {},
   "outputs": [
    {
     "data": {
      "text/plain": [
       "(2068, 1110)"
      ]
     },
     "execution_count": 30,
     "metadata": {},
     "output_type": "execute_result"
    }
   ],
   "source": [
    "msbias.shape"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 31,
   "metadata": {
    "collapsed": true
   },
   "outputs": [],
   "source": [
    "biasFrame.show()"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "----"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "## Arc Image frame"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 32,
   "metadata": {
    "collapsed": true
   },
   "outputs": [],
   "source": [
    "arcImage = arcimage.ArcImage([], spectrograph=spectrograph,\n",
    "                             settings=tsettings, det=det, setup=setup,\n",
    "                             sci_ID=sci_ID, msbias=msbias, fitstbl=fitstbl)"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 33,
   "metadata": {},
   "outputs": [
    {
     "name": "stderr",
     "output_type": "stream",
     "text": [
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marload.py 327 load_raw_frame()\u001b[0m - Loading raw_file: /home/xavier/local/Python/PYPIT-development-suite/RAW_DATA/Keck_LRIS_red/long_600_7500_d560/LR.20160216.05709.fits\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marlris.py 48 read_lris()\u001b[0m - Reading LRIS file: /home/xavier/local/Python/PYPIT-development-suite/RAW_DATA/Keck_LRIS_red/long_600_7500_d560/LR.20160216.05709.fits\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marprocimg.py 174 get_datasec()\u001b[0m - Parsing datasec and oscansec from headers\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marlris.py 48 read_lris()\u001b[0m - Reading LRIS file: /home/xavier/local/Python/PYPIT-development-suite/RAW_DATA/Keck_LRIS_red/long_600_7500_d560/LR.20160216.05709.fits\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34mprocessimages.py 272 bias_subtract()\u001b[0m - Bias subtracting your image(s)\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marprocimg.py 77 bias_subtract()\u001b[0m - Subtracting bias image from raw frame\n"
     ]
    }
   ],
   "source": [
    "msarc = arcImage.build_image()"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 34,
   "metadata": {
    "collapsed": true
   },
   "outputs": [],
   "source": [
    "arcImage.show()"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "----"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "## Bad pixel mask"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 35,
   "metadata": {
    "collapsed": true
   },
   "outputs": [],
   "source": [
    "bpmImage = bpmimage.BPMImage(spectrograph=spectrograph,\n",
    "                             settings=tsettings, det=det,\n",
    "                             shape=msarc.shape,\n",
    "                             binning=fitstbl['binning'][scidx],\n",
    "                             reduce_badpix=False,\n",
    "                             msbias=msbias)"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 36,
   "metadata": {},
   "outputs": [
    {
     "name": "stderr",
     "output_type": "stream",
     "text": [
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marlris.py 384 bpm()\u001b[0m - Using hard-coded BPM for det=2 on LRISr\n"
     ]
    }
   ],
   "source": [
    "msbpm = bpmImage.build()"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 37,
   "metadata": {},
   "outputs": [
    {
     "data": {
      "text/plain": [
       "(2048, 1024)"
      ]
     },
     "execution_count": 37,
     "metadata": {},
     "output_type": "execute_result"
    }
   ],
   "source": [
    "msbpm.shape"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "----"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "## pixlocn"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 38,
   "metadata": {},
   "outputs": [
    {
     "name": "stderr",
     "output_type": "stream",
     "text": [
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marpixels.py 66 core_gen_pixloc()\u001b[0m - Deriving physical pixel locations on the detector\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marpixels.py 69 core_gen_pixloc()\u001b[0m - Pixel gap in the dispersion direction = 0.000\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marpixels.py 70 core_gen_pixloc()\u001b[0m - Pixel size in the dispersion direction = 1.000\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marpixels.py 73 core_gen_pixloc()\u001b[0m - Pixel gap in the spatial direction = 0.000\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marpixels.py 74 core_gen_pixloc()\u001b[0m - Pixel size in the spatial direction = 1.000\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marpixels.py 79 core_gen_pixloc()\u001b[0m - Saving pixel locations\n"
     ]
    }
   ],
   "source": [
    "pixlocn = arpixels.gen_pixloc(msarc.shape, det, settings.argflag)"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "----"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "## Trace slit(s)"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 39,
   "metadata": {
    "collapsed": true
   },
   "outputs": [],
   "source": [
    "# Settings\n",
    "ts_settings = dict(trace=settings.argflag['trace'], masters=settings.argflag['reduce']['masters'])"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 40,
   "metadata": {
    "collapsed": true
   },
   "outputs": [],
   "source": [
    "# Instantiate (without mstrace)\n",
    "traceSlits = traceslits.TraceSlits(None, pixlocn, settings=ts_settings,\n",
    "                                   det=det, setup=setup, binbpx=msbpm)"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "### Build the trace image first"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 41,
   "metadata": {},
   "outputs": [
    {
     "name": "stderr",
     "output_type": "stream",
     "text": [
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marload.py 327 load_raw_frame()\u001b[0m - Loading raw_file: /home/xavier/local/Python/PYPIT-development-suite/RAW_DATA/Keck_LRIS_red/long_600_7500_d560/LR.20160216.14244.fits\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marlris.py 48 read_lris()\u001b[0m - Reading LRIS file: /home/xavier/local/Python/PYPIT-development-suite/RAW_DATA/Keck_LRIS_red/long_600_7500_d560/LR.20160216.14244.fits\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marload.py 327 load_raw_frame()\u001b[0m - Loading raw_file: /home/xavier/local/Python/PYPIT-development-suite/RAW_DATA/Keck_LRIS_red/long_600_7500_d560/LR.20160216.14322.fits\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marlris.py 48 read_lris()\u001b[0m - Reading LRIS file: /home/xavier/local/Python/PYPIT-development-suite/RAW_DATA/Keck_LRIS_red/long_600_7500_d560/LR.20160216.14322.fits\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marload.py 327 load_raw_frame()\u001b[0m - Loading raw_file: /home/xavier/local/Python/PYPIT-development-suite/RAW_DATA/Keck_LRIS_red/long_600_7500_d560/LR.20160216.14399.fits\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marlris.py 48 read_lris()\u001b[0m - Reading LRIS file: /home/xavier/local/Python/PYPIT-development-suite/RAW_DATA/Keck_LRIS_red/long_600_7500_d560/LR.20160216.14399.fits\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marprocimg.py 174 get_datasec()\u001b[0m - Parsing datasec and oscansec from headers\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marlris.py 48 read_lris()\u001b[0m - Reading LRIS file: /home/xavier/local/Python/PYPIT-development-suite/RAW_DATA/Keck_LRIS_red/long_600_7500_d560/LR.20160216.14244.fits\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34mprocessimages.py 272 bias_subtract()\u001b[0m - Bias subtracting your image(s)\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marprocimg.py 77 bias_subtract()\u001b[0m - Subtracting bias image from raw frame\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marprocimg.py 77 bias_subtract()\u001b[0m - Subtracting bias image from raw frame\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marprocimg.py 77 bias_subtract()\u001b[0m - Subtracting bias image from raw frame\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marcomb.py 94 core_comb_frames()\u001b[0m - Combining 3 trace_image frames\n",
      "\u001b[1;30m[WORK IN ]::\u001b[0m\n",
      "\u001b[1;33m[PROGRESS]::\u001b[0m \u001b[1;34marcomb.py 98 core_comb_frames()\u001b[0m - lscomb feature has not been included here yet...\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marcomb.py 162 core_comb_frames()\u001b[0m - Finding saturated and non-linear pixels\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marcomb.py 189 core_comb_frames()\u001b[0m - Rejecting cosmic rays\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marcomb.py 231 core_comb_frames()\u001b[0m - Not rejecting any low/high pixels\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marcomb.py 235 core_comb_frames()\u001b[0m - Rejecting deviant pixels\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marcomb.py 256 core_comb_frames()\u001b[0m - Combining frames with a weightmean operation\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marcomb.py 294 core_comb_frames()\u001b[0m - Replacing completely masked pixels with the maxnonsat value of the input frames\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marcomb.py 307 core_comb_frames()\u001b[0m - 3 trace_image frames combined successfully!\n",
      "\u001b[1;31m[WARNING] ::\u001b[0m \u001b[1;34marprocimg.py 505 gain_frame()\u001b[0m - Should probably be measuring the gain across the amplifier boundary\n"
     ]
    }
   ],
   "source": [
    "trace_image_files = arsort.list_of_files(fitstbl, 'trace', sci_ID)\n",
    "Timage = traceimage.TraceImage(trace_image_files,\n",
    "                               spectrograph=spectrograph,\n",
    "                               settings=tsettings, det=det,\n",
    "                               datasec_img=datasec_img)\n",
    "mstrace = Timage.process(bias_subtract=msbias, trim=True, apply_gain=True)"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 42,
   "metadata": {
    "collapsed": true
   },
   "outputs": [],
   "source": [
    "Timage.show()"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "### Now trace"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 43,
   "metadata": {},
   "outputs": [
    {
     "name": "stderr",
     "output_type": "stream",
     "text": [
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34martraceslits.py 826 edgearr_from_binarr()\u001b[0m - Detecting slit edges in the mstrace image\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34martraceslits.py 888 edgearr_from_binarr()\u001b[0m - Applying bad pixel mask\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34martraceslits.py 946 edgearr_add_left_right()\u001b[0m - 1 left edge and 1 right edge were found in the trace\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34martraceslits.py 972 edgearr_add_left_right()\u001b[0m - Assigning slit edge traces\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34mtraceslits.py 363 _assign_edges()\u001b[0m - Assigning left slit edges\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34mtraceslits.py 369 _assign_edges()\u001b[0m - Assigning right slit edges\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34martraceslits.py 1160 edgearr_final_left_right()\u001b[0m - 1 left edge and 1 right edge were found in the trace\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34martraceslits.py 574 edgearr_tcrude()\u001b[0m - Crude tracing the edges\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34martraceslits.py 1329 fit_edges()\u001b[0m - Fitting left slit traces\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34martraceslits.py 1331 fit_edges()\u001b[0m - Fitting right slit traces\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34mtraceslits.py 392 _chk_for_longslit()\u001b[0m - Only one slit was identified. Should be a longslit.\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34mtraceslits.py 521 _make_pixel_arrays()\u001b[0m - Converting physical trace locations to nearest pixel\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34mtraceslits.py 528 _make_pixel_arrays()\u001b[0m - Identifying the pixels belonging to each slit\n"
     ]
    }
   ],
   "source": [
    "# Load up and get ready\n",
    "traceSlits.mstrace = mstrace\n",
    "_ = traceSlits.make_binarr()\n",
    "# Now we go forth\n",
    "tslits_dict = traceSlits.run(arms=True)\n",
    "# QA\n",
    "traceSlits._qa()"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 44,
   "metadata": {
    "collapsed": true
   },
   "outputs": [],
   "source": [
    "traceSlits.show('edges')"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 45,
   "metadata": {
    "collapsed": true
   },
   "outputs": [],
   "source": [
    "# Initialize maskslits\n",
    "nslits = tslits_dict['lcen'].shape[1]\n",
    "maskslits = np.zeros(nslits, dtype=bool)"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "----"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "## Wavelength Calibration"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 46,
   "metadata": {
    "collapsed": true
   },
   "outputs": [],
   "source": [
    "# Settings\n",
    "wvc_settings = dict(calibrate=settings.argflag['arc']['calibrate'], masters=settings.argflag['reduce']['masters'])"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 47,
   "metadata": {
    "collapsed": true
   },
   "outputs": [],
   "source": [
    "# Instantiate\n",
    "waveCalib = wavecalib.WaveCalib(msarc, spectrograph=spectrograph,\n",
    "                                settings=wvc_settings, det=det,\n",
    "                                setup=setup, fitstbl=fitstbl, sci_ID=sci_ID)"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 48,
   "metadata": {},
   "outputs": [
    {
     "name": "stderr",
     "output_type": "stream",
     "text": [
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34mararc.py 85 get_censpec()\u001b[0m - Extracting an approximate arc spectrum at the centre of each slit\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34mararc.py 439 setup_param()\u001b[0m - Loading line list using ArI,NeI,HgI,KrI,XeI lamps\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34mararclines.py 68 load_arcline_list()\u001b[0m - Rejecting select ArI lines\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34mararclines.py 68 load_arcline_list()\u001b[0m - Rejecting select NeI lines\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34mararclines.py 68 load_arcline_list()\u001b[0m - Rejecting select HgI lines\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34mararclines.py 76 load_arcline_list()\u001b[0m - Cutting down line list by wvmnx: 2900,11000\n"
     ]
    },
    {
     "name": "stdout",
     "output_type": "stream",
     "text": [
      "---------------------------------------------------\n",
      "Report:\n",
      "::   Number of lines recovered    = 83\n",
      "::   Number of lines analyzed     = 83\n",
      "::   Number of acceptable matches = 81\n",
      "::   Best central wavelength      = 7174.84A\n",
      "::   Best dispersion              = 1.59702A/pix\n",
      "::   Best solution used pix_tol   = 1.0\n",
      "::   Best solution had unknown    = True\n",
      "---------------------------------------------------\n"
     ]
    }
   ],
   "source": [
    "# Run\n",
    "wv_calib, _ = waveCalib.run(tslits_dict['lcen'], tslits_dict['rcen'],\n",
    "                                    pixlocn, nonlinear=settings_det['nonlinear'])"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 49,
   "metadata": {},
   "outputs": [
    {
     "data": {
      "text/plain": [
       "{'Nstrong': 13,\n",
       " 'b1': 0.00030517578125,\n",
       " 'b2': 0.0,\n",
       " 'disp': 1.6,\n",
       " 'disp_toler': 0.1,\n",
       " 'func': 'legendre',\n",
       " 'lamps': ['ArI', 'NeI', 'HgI', 'KrI', 'XeI'],\n",
       " 'match_toler': 3.0,\n",
       " 'min_ampl': 300.0,\n",
       " 'n_final': 4,\n",
       " 'n_first': 3,\n",
       " 'nsig_rej': 2.0,\n",
       " 'nsig_rej_final': 3.0,\n",
       " 'wv_cen': 7150.0078125,\n",
       " 'wvmnx': [2900.0, 11000.0]}"
      ]
     },
     "execution_count": 49,
     "metadata": {},
     "output_type": "execute_result"
    }
   ],
   "source": [
    "wv_calib['arcparam']"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 50,
   "metadata": {},
   "outputs": [
    {
     "data": {
      "text/plain": [
       "dict_keys(['fitc', 'function', 'xfit', 'yfit', 'ions', 'fmin', 'fmax', 'xnorm', 'xrej', 'yrej', 'mask', 'spec', 'nrej', 'shift', 'tcent', 'rms'])"
      ]
     },
     "execution_count": 50,
     "metadata": {},
     "output_type": "execute_result"
    }
   ],
   "source": [
    "wv_calib['0'].keys()"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "----"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "## Wave Tilts"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 51,
   "metadata": {
    "collapsed": true
   },
   "outputs": [],
   "source": [
    "# Settings kludges\n",
    "tilt_settings = dict(tilts=settings.argflag['trace']['slits']['tilts'].copy(),\n",
    "                     masters=settings.argflag['reduce']['masters'])\n",
    "tilt_settings['tilts']['function'] = settings.argflag['trace']['slits']['function']"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 52,
   "metadata": {
    "collapsed": true
   },
   "outputs": [],
   "source": [
    "# Instantiate\n",
    "waveTilts = wavetilts.WaveTilts(msarc, settings=tilt_settings,\n",
    "                                    det=det, setup=setup,\n",
    "                                    tslits_dict=tslits_dict, settings_det=settings_det,\n",
    "                                    pixlocn=pixlocn)"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 53,
   "metadata": {},
   "outputs": [
    {
     "name": "stderr",
     "output_type": "stream",
     "text": [
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34mararc.py 85 get_censpec()\u001b[0m - Extracting an approximate arc spectrum at the centre of each slit\n",
      "\u001b[1;30m[WORK IN ]::\u001b[0m\n",
      "\u001b[1;33m[PROGRESS]::\u001b[0m \u001b[1;34martracewave.py 205 trace_tilt()\u001b[0m - Detecting lines for slit 1\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34mararc.py 177 detect_lines()\u001b[0m - Detecting lines\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34mararc.py 203 detect_lines()\u001b[0m - Detecting the strongest, nonsaturated lines\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34martracewave.py 263 trace_tilt()\u001b[0m - Modelling arc line tilts with 51 arc lines\n",
      "\u001b[1;30m[WORK IN ]::\u001b[0m\n",
      "\u001b[1;33m[PROGRESS]::\u001b[0m \u001b[1;34martracewave.py 269 trace_tilt()\u001b[0m - This next step could be multiprocessed to speed up the reduction\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34martracewave.py 437 trace_tilt()\u001b[0m - Completed spectral tilt tracing\n",
      "\u001b[1;31m[WARNING] ::\u001b[0m \u001b[1;34mwavetilts.py 192 _analyze_lines()\u001b[0m - There were 13 additional arc lines that should have been traced\n",
      "             (perhaps lines were saturated?). Check the spectral tilt solution\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34martracewave.py 780 fit_tilts()\u001b[0m - Fitting tilts with a low order, 2D legendre\n",
      "\u001b[1;30m[WORK IN ]::\u001b[0m\n",
      "\u001b[1;33m[PROGRESS]::\u001b[0m \u001b[1;34marutils.py 811 polyfit2d_general()\u001b[0m - Generalize to different polynomial types\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34martracewave.py 799 fit_tilts()\u001b[0m - RMS (pixels): 0.004461452134072074\n"
     ]
    }
   ],
   "source": [
    "# Run\n",
    "mstilts, wt_maskslits = waveTilts.run(maskslits=maskslits, wv_calib=wv_calib)"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 54,
   "metadata": {},
   "outputs": [
    {
     "name": "stderr",
     "output_type": "stream",
     "text": [
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34mwavetilts.py 429 show()\u001b[0m - Green = ok line;  red=not used\n"
     ]
    }
   ],
   "source": [
    "waveTilts.show('fweight', slit=0)"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 55,
   "metadata": {},
   "outputs": [
    {
     "name": "stderr",
     "output_type": "stream",
     "text": [
      "\u001b[1;31m[WARNING] ::\u001b[0m \u001b[1;34mwavetilts.py 464 show()\u001b[0m - Display via tilts is not exact\n"
     ]
    }
   ],
   "source": [
    "waveTilts.show('tilts', slit=0)"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "----"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "## Pixel Flat Field"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 56,
   "metadata": {
    "collapsed": true
   },
   "outputs": [],
   "source": [
    "# Settings\n",
    "flat_settings = dict(flatfield=settings.argflag['reduce']['flatfield'].copy(),\n",
    "                     slitprofile=settings.argflag['reduce']['slitprofile'].copy(),\n",
    "                     combine=settings.argflag['pixelflat']['combine'].copy(),\n",
    "                     masters=settings.argflag['reduce']['masters'].copy(),\n",
    "                     detector=settings.spect[dnum])"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 57,
   "metadata": {
    "collapsed": true
   },
   "outputs": [],
   "source": [
    "# Instantiate\n",
    "pixflat_image_files = arsort.list_of_files(fitstbl, 'pixelflat', sci_ID)\n",
    "flatField = flatfield.FlatField(file_list=pixflat_image_files, msbias=msbias,\n",
    "                                spectrograph=spectrograph,\n",
    "                                settings=flat_settings,\n",
    "                                tslits_dict=tslits_dict,\n",
    "                                tilts=mstilts, det=det, setup=setup,\n",
    "                                datasec_img=datasec_img)"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 58,
   "metadata": {},
   "outputs": [
    {
     "name": "stderr",
     "output_type": "stream",
     "text": [
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marload.py 327 load_raw_frame()\u001b[0m - Loading raw_file: /home/xavier/local/Python/PYPIT-development-suite/RAW_DATA/Keck_LRIS_red/long_600_7500_d560/LR.20160216.14244.fits\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marlris.py 48 read_lris()\u001b[0m - Reading LRIS file: /home/xavier/local/Python/PYPIT-development-suite/RAW_DATA/Keck_LRIS_red/long_600_7500_d560/LR.20160216.14244.fits\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marload.py 327 load_raw_frame()\u001b[0m - Loading raw_file: /home/xavier/local/Python/PYPIT-development-suite/RAW_DATA/Keck_LRIS_red/long_600_7500_d560/LR.20160216.14322.fits\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marlris.py 48 read_lris()\u001b[0m - Reading LRIS file: /home/xavier/local/Python/PYPIT-development-suite/RAW_DATA/Keck_LRIS_red/long_600_7500_d560/LR.20160216.14322.fits\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marload.py 327 load_raw_frame()\u001b[0m - Loading raw_file: /home/xavier/local/Python/PYPIT-development-suite/RAW_DATA/Keck_LRIS_red/long_600_7500_d560/LR.20160216.14399.fits\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marlris.py 48 read_lris()\u001b[0m - Reading LRIS file: /home/xavier/local/Python/PYPIT-development-suite/RAW_DATA/Keck_LRIS_red/long_600_7500_d560/LR.20160216.14399.fits\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marprocimg.py 174 get_datasec()\u001b[0m - Parsing datasec and oscansec from headers\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marlris.py 48 read_lris()\u001b[0m - Reading LRIS file: /home/xavier/local/Python/PYPIT-development-suite/RAW_DATA/Keck_LRIS_red/long_600_7500_d560/LR.20160216.14244.fits\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34mprocessimages.py 272 bias_subtract()\u001b[0m - Bias subtracting your image(s)\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marprocimg.py 77 bias_subtract()\u001b[0m - Subtracting bias image from raw frame\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marprocimg.py 77 bias_subtract()\u001b[0m - Subtracting bias image from raw frame\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marprocimg.py 77 bias_subtract()\u001b[0m - Subtracting bias image from raw frame\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marcomb.py 94 core_comb_frames()\u001b[0m - Combining 3 pixelflat frames\n",
      "\u001b[1;30m[WORK IN ]::\u001b[0m\n",
      "\u001b[1;33m[PROGRESS]::\u001b[0m \u001b[1;34marcomb.py 98 core_comb_frames()\u001b[0m - lscomb feature has not been included here yet...\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marcomb.py 162 core_comb_frames()\u001b[0m - Finding saturated and non-linear pixels\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marcomb.py 189 core_comb_frames()\u001b[0m - Rejecting cosmic rays\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marcomb.py 231 core_comb_frames()\u001b[0m - Not rejecting any low/high pixels\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marcomb.py 235 core_comb_frames()\u001b[0m - Rejecting deviant pixels\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marcomb.py 256 core_comb_frames()\u001b[0m - Combining frames with a weightmean operation\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marcomb.py 294 core_comb_frames()\u001b[0m - Replacing completely masked pixels with the maxnonsat value of the input frames\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marcomb.py 307 core_comb_frames()\u001b[0m - 3 pixelflat frames combined successfully!\n",
      "\u001b[1;31m[WARNING] ::\u001b[0m \u001b[1;34marprocimg.py 505 gain_frame()\u001b[0m - Should probably be measuring the gain across the amplifier boundary\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34mflatfield.py 297 run()\u001b[0m - Setting pixels outside of slits to 1. in the flat.\n"
     ]
    }
   ],
   "source": [
    "# Run\n",
    "mspixflatnrm, slitprof = flatField.run(armed=False)"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 59,
   "metadata": {
    "collapsed": true
   },
   "outputs": [],
   "source": [
    "flatField.show('norm')"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "----"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "## Wavelength Image"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 60,
   "metadata": {
    "collapsed": true
   },
   "outputs": [],
   "source": [
    "# Settings\n",
    "wvimg_settings = dict(masters=settings.argflag['reduce']['masters'].copy())"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 61,
   "metadata": {
    "collapsed": true
   },
   "outputs": [],
   "source": [
    "# Instantiate\n",
    "waveImage = waveimage.WaveImage(mstilts, wv_calib, settings=wvimg_settings,\n",
    "                                    setup=setup, maskslits=maskslits,\n",
    "                                    slitpix=tslits_dict['slitpix'])"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 62,
   "metadata": {
    "collapsed": true
   },
   "outputs": [],
   "source": [
    "# Build\n",
    "mswave = waveImage._build_wave()"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 63,
   "metadata": {
    "collapsed": true
   },
   "outputs": [],
   "source": [
    "waveImage.show('wave')"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "----"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "## Science Image"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "### File list"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 64,
   "metadata": {
    "collapsed": true
   },
   "outputs": [],
   "source": [
    "sci_image_files = arsort.list_of_files(fitstbl, 'science', sci_ID)"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 65,
   "metadata": {
    "collapsed": true
   },
   "outputs": [],
   "source": [
    "# Settings\n",
    "sci_settings = tsettings.copy()"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "### Instantiate"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 66,
   "metadata": {
    "collapsed": true
   },
   "outputs": [],
   "source": [
    "# Instantiate\n",
    "sciI = scienceimage.ScienceImage(file_list=sci_image_files, datasec_img=datasec_img,\n",
    "                                 bpm=msbpm, det=det, setup=setup, settings=sci_settings,\n",
    "                                 maskslits=maskslits, pixlocn=pixlocn, tslits_dict=tslits_dict,\n",
    "                                 tilts=mstilts, fitstbl=fitstbl, scidx=scidx)"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "### Name, time"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 67,
   "metadata": {},
   "outputs": [
    {
     "data": {
      "text/plain": [
       "'OFF_J1044p6306_LRISr_2016Feb16T112439'"
      ]
     },
     "execution_count": 67,
     "metadata": {},
     "output_type": "execute_result"
    }
   ],
   "source": [
    "# Names and time\n",
    "obstime, basename = sciI.init_time_names(settings.spect['mosaic']['camera'],\n",
    "                timeunit=settings.spect[\"fits\"][\"timeunit\"])\n",
    "basename"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "### Process"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 68,
   "metadata": {},
   "outputs": [
    {
     "name": "stderr",
     "output_type": "stream",
     "text": [
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marload.py 327 load_raw_frame()\u001b[0m - Loading raw_file: /home/xavier/local/Python/PYPIT-development-suite/RAW_DATA/Keck_LRIS_red/long_600_7500_d560/LR.20160216.40478.fits\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marlris.py 48 read_lris()\u001b[0m - Reading LRIS file: /home/xavier/local/Python/PYPIT-development-suite/RAW_DATA/Keck_LRIS_red/long_600_7500_d560/LR.20160216.40478.fits\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marprocimg.py 174 get_datasec()\u001b[0m - Parsing datasec and oscansec from headers\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marlris.py 48 read_lris()\u001b[0m - Reading LRIS file: /home/xavier/local/Python/PYPIT-development-suite/RAW_DATA/Keck_LRIS_red/long_600_7500_d560/LR.20160216.40478.fits\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34mprocessimages.py 272 bias_subtract()\u001b[0m - Bias subtracting your image(s)\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marprocimg.py 77 bias_subtract()\u001b[0m - Subtracting bias image from raw frame\n",
      "\u001b[1;31m[WARNING] ::\u001b[0m \u001b[1;34marprocimg.py 505 gain_frame()\u001b[0m - Should probably be measuring the gain across the amplifier boundary\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34mprocessimages.py 430 build_rawvarframe()\u001b[0m - Generate raw variance frame (from detected counts [flat fielded])\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marprocimg.py 236 lacosmic()\u001b[0m - Detecting cosmic rays with the L.A.Cosmic algorithm\n",
      "\u001b[1;30m[WORK IN ]::\u001b[0m\n",
      "\u001b[1;33m[PROGRESS]::\u001b[0m \u001b[1;34marprocimg.py 237 lacosmic()\u001b[0m - Include these parameters in the settings files to be adjusted by the user\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marprocimg.py 259 lacosmic()\u001b[0m - Convolving image with Laplacian kernel\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marprocimg.py 267 lacosmic()\u001b[0m - Creating noise model\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marprocimg.py 274 lacosmic()\u001b[0m - Calculating Laplacian signal to noise ratio\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marprocimg.py 282 lacosmic()\u001b[0m - Selecting candidate cosmic rays\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marprocimg.py 287 lacosmic()\u001b[0m - 80163 candidate pixels\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marprocimg.py 291 lacosmic()\u001b[0m - Masking saturated pixels\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marprocimg.py 295 lacosmic()\u001b[0m - 80161 candidate pixels not part of saturated stars\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marprocimg.py 297 lacosmic()\u001b[0m - Building fine structure image\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marprocimg.py 306 lacosmic()\u001b[0m - Removing suspected compact bright objects\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marprocimg.py 316 lacosmic()\u001b[0m - 49554 remaining candidate pixels\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marprocimg.py 320 lacosmic()\u001b[0m - Finding neighboring pixels affected by cosmic rays\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marprocimg.py 336 lacosmic()\u001b[0m - Masking saturated stars\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marprocimg.py 341 lacosmic()\u001b[0m - 109612 pixels detected as cosmics\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marprocimg.py 350 lacosmic()\u001b[0m - Iteration 1 -- 109612 pixels identified as cosmic rays (109612 new)\n",
      "\u001b[1;30m[WORK IN ]::\u001b[0m\n",
      "\u001b[1;33m[PROGRESS]::\u001b[0m \u001b[1;34marprocimg.py 353 lacosmic()\u001b[0m - The following algorithm would be better on the rectified, tilts-corrected image\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marprocimg.py 408 lacosmic()\u001b[0m - Growing cosmic ray mask by 1 pixel\n"
     ]
    }
   ],
   "source": [
    "# Process (includes Variance image and CRs)\n",
    "dnoise = (settings_det['darkcurr'] * float(fitstbl[\"exptime\"][scidx])/3600.0)\n",
    "sciframe, rawvarframe, crmask = sciI._process(\n",
    "    msbias, mspixflatnrm, apply_gain=True, dnoise=dnoise)"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 69,
   "metadata": {
    "collapsed": true
   },
   "outputs": [],
   "source": [
    "sciI.show('sci')"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "### Global sky sub"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 70,
   "metadata": {},
   "outputs": [
    {
     "name": "stderr",
     "output_type": "stream",
     "text": [
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34mscienceimage.py 459 global_skysub()\u001b[0m - Working on slit: 0\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marutils.py 198 bspline_profile()\u001b[0m - Fitting npoly =  1 profile basis functions, nx=584071 pixels\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marutils.py 199 bspline_profile()\u001b[0m - ****************************  Iter  Chi^2  # rejected  Rel. fact   ****************************\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marutils.py 200 bspline_profile()\u001b[0m -                               ----  -----  ----------  --------- \n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marutils.py 281 bspline_profile()\u001b[0m -                                 1   0.003        0        1.00\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marutils.py 286 bspline_profile()\u001b[0m - ***********************************************************************************************\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marutils.py 289 bspline_profile()\u001b[0m - Final fit after  1 iterations: reduced_chi =    0.003, rejected =       0, relative_factor =   1.00\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marutils.py 198 bspline_profile()\u001b[0m - Fitting npoly =  1 profile basis functions, nx=584197 pixels\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marutils.py 199 bspline_profile()\u001b[0m - ****************************  Iter  Chi^2  # rejected  Rel. fact   ****************************\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marutils.py 200 bspline_profile()\u001b[0m -                               ----  -----  ----------  --------- \n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marutils.py 281 bspline_profile()\u001b[0m -                                 1   1.242     4682        1.00\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marutils.py 286 bspline_profile()\u001b[0m - ***********************************************************************************************\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marutils.py 289 bspline_profile()\u001b[0m - Final fit after  1 iterations: reduced_chi =    1.242, rejected =    4682, relative_factor =   1.00\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34mscienceimage.py 469 global_skysub()\u001b[0m - Building model variance from the Sky frame\n"
     ]
    }
   ],
   "source": [
    "# Global skysub\n",
    "settings_skysub = {}\n",
    "settings_skysub['skysub'] = settings.argflag['reduce']['skysub'].copy()\n",
    "global_sky, modelvarframe = sciI.global_skysub(settings_skysub)"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 71,
   "metadata": {
    "collapsed": true
   },
   "outputs": [],
   "source": [
    "sciI.show('skysub')"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "### Find objects"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 72,
   "metadata": {},
   "outputs": [
    {
     "name": "stderr",
     "output_type": "stream",
     "text": [
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34martrace.py 285 trace_objects_in_slit()\u001b[0m - Rectifying science frame\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34martrace.py 306 trace_objects_in_slit()\u001b[0m - Estimating object profiles\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34martrace.py 375 trace_objects_in_slit()\u001b[0m - Identifying objects that are significantly detected\n",
      "\u001b[1;31m[WARNING] ::\u001b[0m \u001b[1;34martrace.py 430 trace_objects_in_slit()\u001b[0m - Removed objects near the slit edges\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34martrace.py 461 trace_objects_in_slit()\u001b[0m - Found 4 objects\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34martrace.py 462 trace_objects_in_slit()\u001b[0m - Tracing 4 objects\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34martrace.py 498 trace_objects_in_slit()\u001b[0m - Performing global trace to all objects\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34martrace.py 501 trace_objects_in_slit()\u001b[0m - Constructing a trace for all objects\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34martrace.py 509 trace_objects_in_slit()\u001b[0m - Converting object traces to detector pixels\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34martrace.py 90 trace_objbg_image()\u001b[0m - Creating an image weighted by object pixels for 4 objects\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34martrace.py 99 trace_objbg_image()\u001b[0m - Creating an image weighted by background pixels\n"
     ]
    }
   ],
   "source": [
    "_, nobj = sciI.find_objects()"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "### Repeat the last 2 steps"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 73,
   "metadata": {},
   "outputs": [
    {
     "name": "stderr",
     "output_type": "stream",
     "text": [
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34mscienceimage.py 459 global_skysub()\u001b[0m - Working on slit: 0\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marutils.py 198 bspline_profile()\u001b[0m - Fitting npoly =  1 profile basis functions, nx=519297 pixels\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marutils.py 199 bspline_profile()\u001b[0m - ****************************  Iter  Chi^2  # rejected  Rel. fact   ****************************\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marutils.py 200 bspline_profile()\u001b[0m -                               ----  -----  ----------  --------- \n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marutils.py 281 bspline_profile()\u001b[0m -                                 1   0.003        0        1.00\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marutils.py 286 bspline_profile()\u001b[0m - ***********************************************************************************************\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marutils.py 289 bspline_profile()\u001b[0m - Final fit after  1 iterations: reduced_chi =    0.003, rejected =       0, relative_factor =   1.00\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marutils.py 198 bspline_profile()\u001b[0m - Fitting npoly =  1 profile basis functions, nx=519420 pixels\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marutils.py 199 bspline_profile()\u001b[0m - ****************************  Iter  Chi^2  # rejected  Rel. fact   ****************************\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marutils.py 200 bspline_profile()\u001b[0m -                               ----  -----  ----------  --------- \n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marutils.py 281 bspline_profile()\u001b[0m -                                 1   1.287     4524        1.00\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marutils.py 286 bspline_profile()\u001b[0m - ***********************************************************************************************\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marutils.py 289 bspline_profile()\u001b[0m - Final fit after  1 iterations: reduced_chi =    1.287, rejected =    4524, relative_factor =   1.00\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34mscienceimage.py 469 global_skysub()\u001b[0m - Building model variance from the Sky frame\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34martrace.py 285 trace_objects_in_slit()\u001b[0m - Rectifying science frame\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34martrace.py 306 trace_objects_in_slit()\u001b[0m - Estimating object profiles\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34martrace.py 375 trace_objects_in_slit()\u001b[0m - Identifying objects that are significantly detected\n",
      "\u001b[1;31m[WARNING] ::\u001b[0m \u001b[1;34martrace.py 430 trace_objects_in_slit()\u001b[0m - Removed objects near the slit edges\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34martrace.py 461 trace_objects_in_slit()\u001b[0m - Found 4 objects\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34martrace.py 462 trace_objects_in_slit()\u001b[0m - Tracing 4 objects\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34martrace.py 498 trace_objects_in_slit()\u001b[0m - Performing global trace to all objects\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34martrace.py 501 trace_objects_in_slit()\u001b[0m - Constructing a trace for all objects\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34martrace.py 509 trace_objects_in_slit()\u001b[0m - Converting object traces to detector pixels\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34martrace.py 90 trace_objbg_image()\u001b[0m - Creating an image weighted by object pixels for 4 objects\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34martrace.py 99 trace_objbg_image()\u001b[0m - Creating an image weighted by background pixels\n"
     ]
    }
   ],
   "source": [
    "# Mask the objects\n",
    "global_sky, modelvarframe = sciI.global_skysub(settings_skysub, use_tracemask=True)\n",
    "# Another round of finding objects\n",
    "_, nobj = sciI.find_objects()  "
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "### Extraction -- New algorithm in development"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 74,
   "metadata": {},
   "outputs": [
    {
     "name": "stderr",
     "output_type": "stream",
     "text": [
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34mscienceimage.py 278 boxcar()\u001b[0m - Performing boxcar extraction\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marextract.py 80 boxcar()\u001b[0m - Performing boxcar extraction of object 1/4 in slit 1/1\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marextract.py 89 boxcar()\u001b[0m -    Fitting the background\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marextract.py 166 boxcar()\u001b[0m -    Summing object counts\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marextract.py 169 boxcar()\u001b[0m -    Summing variance array\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marextract.py 80 boxcar()\u001b[0m - Performing boxcar extraction of object 2/4 in slit 1/1\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marextract.py 89 boxcar()\u001b[0m -    Fitting the background\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marextract.py 166 boxcar()\u001b[0m -    Summing object counts\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marextract.py 169 boxcar()\u001b[0m -    Summing variance array\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marextract.py 80 boxcar()\u001b[0m - Performing boxcar extraction of object 3/4 in slit 1/1\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marextract.py 89 boxcar()\u001b[0m -    Fitting the background\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marextract.py 166 boxcar()\u001b[0m -    Summing object counts\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marextract.py 169 boxcar()\u001b[0m -    Summing variance array\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marextract.py 80 boxcar()\u001b[0m - Performing boxcar extraction of object 4/4 in slit 1/1\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marextract.py 89 boxcar()\u001b[0m -    Fitting the background\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marextract.py 166 boxcar()\u001b[0m -    Summing object counts\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marextract.py 169 boxcar()\u001b[0m -    Summing variance array\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34mscienceimage.py 306 original_optimal()\u001b[0m - Attempting optimal extraction with model profile\n",
      "\u001b[1;30m[WORK IN ]::\u001b[0m\n",
      "\u001b[1;33m[PROGRESS]::\u001b[0m \u001b[1;34marextract.py 259 obj_profiles()\u001b[0m - Should probably loop on S/N\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marextract.py 261 obj_profiles()\u001b[0m - Deriving spatial profile of object 1/4 in slit 1/1\n",
      "\u001b[1;30m[WORK IN ]::\u001b[0m\n",
      "\u001b[1;33m[PROGRESS]::\u001b[0m \u001b[1;34martrace.py 1819 slit_image()\u001b[0m - Use 2D spline to evaluate tilts\n",
      "\u001b[1;30m[WORK IN ]::\u001b[0m\n",
      "\u001b[1;33m[PROGRESS]::\u001b[0m \u001b[1;34martrace.py 1824 slit_image()\u001b[0m - Should worry about changing plate scale\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marextract.py 284 obj_profiles()\u001b[0m - Good S/N for profile\n",
      "\u001b[1;30m[WORK IN ]::\u001b[0m\n",
      "\u001b[1;33m[PROGRESS]::\u001b[0m \u001b[1;34marextract.py 294 obj_profiles()\u001b[0m - Weight by S/N in boxcar extraction? [avoid CRs; smooth?]\n",
      "\u001b[1;30m[WORK IN ]::\u001b[0m\n",
      "\u001b[1;33m[PROGRESS]::\u001b[0m \u001b[1;34marextract.py 303 obj_profiles()\u001b[0m - Might give our own guess here instead of using default\n",
      "\u001b[1;30m[WORK IN ]::\u001b[0m\n",
      "\u001b[1;33m[PROGRESS]::\u001b[0m \u001b[1;34marextract.py 323 obj_profiles()\u001b[0m - Consider flagging/removing CRs here\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marextract.py 261 obj_profiles()\u001b[0m - Deriving spatial profile of object 2/4 in slit 1/1\n",
      "\u001b[1;30m[WORK IN ]::\u001b[0m\n",
      "\u001b[1;33m[PROGRESS]::\u001b[0m \u001b[1;34martrace.py 1819 slit_image()\u001b[0m - Use 2D spline to evaluate tilts\n",
      "\u001b[1;30m[WORK IN ]::\u001b[0m\n",
      "\u001b[1;33m[PROGRESS]::\u001b[0m \u001b[1;34martrace.py 1824 slit_image()\u001b[0m - Should worry about changing plate scale\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marextract.py 284 obj_profiles()\u001b[0m - Good S/N for profile\n",
      "\u001b[1;30m[WORK IN ]::\u001b[0m\n",
      "\u001b[1;33m[PROGRESS]::\u001b[0m \u001b[1;34marextract.py 294 obj_profiles()\u001b[0m - Weight by S/N in boxcar extraction? [avoid CRs; smooth?]\n",
      "\u001b[1;30m[WORK IN ]::\u001b[0m\n",
      "\u001b[1;33m[PROGRESS]::\u001b[0m \u001b[1;34marextract.py 303 obj_profiles()\u001b[0m - Might give our own guess here instead of using default\n",
      "\u001b[1;30m[WORK IN ]::\u001b[0m\n",
      "\u001b[1;33m[PROGRESS]::\u001b[0m \u001b[1;34marextract.py 323 obj_profiles()\u001b[0m - Consider flagging/removing CRs here\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marextract.py 261 obj_profiles()\u001b[0m - Deriving spatial profile of object 3/4 in slit 1/1\n",
      "\u001b[1;30m[WORK IN ]::\u001b[0m\n",
      "\u001b[1;33m[PROGRESS]::\u001b[0m \u001b[1;34martrace.py 1819 slit_image()\u001b[0m - Use 2D spline to evaluate tilts\n",
      "\u001b[1;30m[WORK IN ]::\u001b[0m\n",
      "\u001b[1;33m[PROGRESS]::\u001b[0m \u001b[1;34martrace.py 1824 slit_image()\u001b[0m - Should worry about changing plate scale\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marextract.py 284 obj_profiles()\u001b[0m - Good S/N for profile\n",
      "\u001b[1;30m[WORK IN ]::\u001b[0m\n",
      "\u001b[1;33m[PROGRESS]::\u001b[0m \u001b[1;34marextract.py 294 obj_profiles()\u001b[0m - Weight by S/N in boxcar extraction? [avoid CRs; smooth?]\n",
      "\u001b[1;30m[WORK IN ]::\u001b[0m\n",
      "\u001b[1;33m[PROGRESS]::\u001b[0m \u001b[1;34marextract.py 303 obj_profiles()\u001b[0m - Might give our own guess here instead of using default\n",
      "\u001b[1;30m[WORK IN ]::\u001b[0m\n",
      "\u001b[1;33m[PROGRESS]::\u001b[0m \u001b[1;34marextract.py 323 obj_profiles()\u001b[0m - Consider flagging/removing CRs here\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marextract.py 261 obj_profiles()\u001b[0m - Deriving spatial profile of object 4/4 in slit 1/1\n",
      "\u001b[1;30m[WORK IN ]::\u001b[0m\n",
      "\u001b[1;33m[PROGRESS]::\u001b[0m \u001b[1;34martrace.py 1819 slit_image()\u001b[0m - Use 2D spline to evaluate tilts\n",
      "\u001b[1;30m[WORK IN ]::\u001b[0m\n",
      "\u001b[1;33m[PROGRESS]::\u001b[0m \u001b[1;34martrace.py 1824 slit_image()\u001b[0m - Should worry about changing plate scale\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marextract.py 284 obj_profiles()\u001b[0m - Good S/N for profile\n",
      "\u001b[1;30m[WORK IN ]::\u001b[0m\n",
      "\u001b[1;33m[PROGRESS]::\u001b[0m \u001b[1;34marextract.py 294 obj_profiles()\u001b[0m - Weight by S/N in boxcar extraction? [avoid CRs; smooth?]\n",
      "\u001b[1;30m[WORK IN ]::\u001b[0m\n",
      "\u001b[1;33m[PROGRESS]::\u001b[0m \u001b[1;34marextract.py 303 obj_profiles()\u001b[0m - Might give our own guess here instead of using default\n",
      "\u001b[1;30m[WORK IN ]::\u001b[0m\n",
      "\u001b[1;33m[PROGRESS]::\u001b[0m \u001b[1;34marextract.py 323 obj_profiles()\u001b[0m - Consider flagging/removing CRs here\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marextract.py 465 optimal_extract()\u001b[0m - Performing optimal extraction of object 1/4 in slit 1/1\n",
      "\u001b[1;30m[WORK IN ]::\u001b[0m\n",
      "\u001b[1;33m[PROGRESS]::\u001b[0m \u001b[1;34martrace.py 1819 slit_image()\u001b[0m - Use 2D spline to evaluate tilts\n",
      "\u001b[1;30m[WORK IN ]::\u001b[0m\n",
      "\u001b[1;33m[PROGRESS]::\u001b[0m \u001b[1;34martrace.py 1824 slit_image()\u001b[0m - Should worry about changing plate scale\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marextract.py 465 optimal_extract()\u001b[0m - Performing optimal extraction of object 2/4 in slit 1/1\n",
      "\u001b[1;30m[WORK IN ]::\u001b[0m\n",
      "\u001b[1;33m[PROGRESS]::\u001b[0m \u001b[1;34martrace.py 1819 slit_image()\u001b[0m - Use 2D spline to evaluate tilts\n",
      "\u001b[1;30m[WORK IN ]::\u001b[0m\n",
      "\u001b[1;33m[PROGRESS]::\u001b[0m \u001b[1;34martrace.py 1824 slit_image()\u001b[0m - Should worry about changing plate scale\n",
      "\u001b[1;31m[WARNING] ::\u001b[0m \u001b[1;34marextract.py 507 optimal_extract()\u001b[0m - Replacing fully masked regions with mean wavelengths\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marextract.py 465 optimal_extract()\u001b[0m - Performing optimal extraction of object 3/4 in slit 1/1\n",
      "\u001b[1;30m[WORK IN ]::\u001b[0m\n",
      "\u001b[1;33m[PROGRESS]::\u001b[0m \u001b[1;34martrace.py 1819 slit_image()\u001b[0m - Use 2D spline to evaluate tilts\n",
      "\u001b[1;30m[WORK IN ]::\u001b[0m\n",
      "\u001b[1;33m[PROGRESS]::\u001b[0m \u001b[1;34martrace.py 1824 slit_image()\u001b[0m - Should worry about changing plate scale\n",
      "\u001b[1;31m[WARNING] ::\u001b[0m \u001b[1;34marextract.py 507 optimal_extract()\u001b[0m - Replacing fully masked regions with mean wavelengths\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marextract.py 465 optimal_extract()\u001b[0m - Performing optimal extraction of object 4/4 in slit 1/1\n",
      "\u001b[1;30m[WORK IN ]::\u001b[0m\n",
      "\u001b[1;33m[PROGRESS]::\u001b[0m \u001b[1;34martrace.py 1819 slit_image()\u001b[0m - Use 2D spline to evaluate tilts\n",
      "\u001b[1;30m[WORK IN ]::\u001b[0m\n",
      "\u001b[1;33m[PROGRESS]::\u001b[0m \u001b[1;34martrace.py 1824 slit_image()\u001b[0m - Should worry about changing plate scale\n",
      "\u001b[1;31m[WARNING] ::\u001b[0m \u001b[1;34marextract.py 507 optimal_extract()\u001b[0m - Replacing fully masked regions with mean wavelengths\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34mscienceimage.py 360 extraction()\u001b[0m - Update model variance image (and trace?) and repeat\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34mscienceimage.py 306 original_optimal()\u001b[0m - Attempting optimal extraction with model profile\n",
      "\u001b[1;30m[WORK IN ]::\u001b[0m\n",
      "\u001b[1;33m[PROGRESS]::\u001b[0m \u001b[1;34marextract.py 259 obj_profiles()\u001b[0m - Should probably loop on S/N\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marextract.py 261 obj_profiles()\u001b[0m - Deriving spatial profile of object 1/4 in slit 1/1\n",
      "\u001b[1;30m[WORK IN ]::\u001b[0m\n",
      "\u001b[1;33m[PROGRESS]::\u001b[0m \u001b[1;34martrace.py 1819 slit_image()\u001b[0m - Use 2D spline to evaluate tilts\n",
      "\u001b[1;30m[WORK IN ]::\u001b[0m\n",
      "\u001b[1;33m[PROGRESS]::\u001b[0m \u001b[1;34martrace.py 1824 slit_image()\u001b[0m - Should worry about changing plate scale\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marextract.py 284 obj_profiles()\u001b[0m - Good S/N for profile\n",
      "\u001b[1;30m[WORK IN ]::\u001b[0m\n",
      "\u001b[1;33m[PROGRESS]::\u001b[0m \u001b[1;34marextract.py 294 obj_profiles()\u001b[0m - Weight by S/N in boxcar extraction? [avoid CRs; smooth?]\n",
      "\u001b[1;30m[WORK IN ]::\u001b[0m\n",
      "\u001b[1;33m[PROGRESS]::\u001b[0m \u001b[1;34marextract.py 303 obj_profiles()\u001b[0m - Might give our own guess here instead of using default\n"
     ]
    },
    {
     "name": "stderr",
     "output_type": "stream",
     "text": [
      "\u001b[1;30m[WORK IN ]::\u001b[0m\n",
      "\u001b[1;33m[PROGRESS]::\u001b[0m \u001b[1;34marextract.py 323 obj_profiles()\u001b[0m - Consider flagging/removing CRs here\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marextract.py 261 obj_profiles()\u001b[0m - Deriving spatial profile of object 2/4 in slit 1/1\n",
      "\u001b[1;30m[WORK IN ]::\u001b[0m\n",
      "\u001b[1;33m[PROGRESS]::\u001b[0m \u001b[1;34martrace.py 1819 slit_image()\u001b[0m - Use 2D spline to evaluate tilts\n",
      "\u001b[1;30m[WORK IN ]::\u001b[0m\n",
      "\u001b[1;33m[PROGRESS]::\u001b[0m \u001b[1;34martrace.py 1824 slit_image()\u001b[0m - Should worry about changing plate scale\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marextract.py 284 obj_profiles()\u001b[0m - Good S/N for profile\n",
      "\u001b[1;30m[WORK IN ]::\u001b[0m\n",
      "\u001b[1;33m[PROGRESS]::\u001b[0m \u001b[1;34marextract.py 294 obj_profiles()\u001b[0m - Weight by S/N in boxcar extraction? [avoid CRs; smooth?]\n",
      "\u001b[1;30m[WORK IN ]::\u001b[0m\n",
      "\u001b[1;33m[PROGRESS]::\u001b[0m \u001b[1;34marextract.py 303 obj_profiles()\u001b[0m - Might give our own guess here instead of using default\n",
      "\u001b[1;30m[WORK IN ]::\u001b[0m\n",
      "\u001b[1;33m[PROGRESS]::\u001b[0m \u001b[1;34marextract.py 323 obj_profiles()\u001b[0m - Consider flagging/removing CRs here\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marextract.py 261 obj_profiles()\u001b[0m - Deriving spatial profile of object 3/4 in slit 1/1\n",
      "\u001b[1;30m[WORK IN ]::\u001b[0m\n",
      "\u001b[1;33m[PROGRESS]::\u001b[0m \u001b[1;34martrace.py 1819 slit_image()\u001b[0m - Use 2D spline to evaluate tilts\n",
      "\u001b[1;30m[WORK IN ]::\u001b[0m\n",
      "\u001b[1;33m[PROGRESS]::\u001b[0m \u001b[1;34martrace.py 1824 slit_image()\u001b[0m - Should worry about changing plate scale\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marextract.py 284 obj_profiles()\u001b[0m - Good S/N for profile\n",
      "\u001b[1;30m[WORK IN ]::\u001b[0m\n",
      "\u001b[1;33m[PROGRESS]::\u001b[0m \u001b[1;34marextract.py 294 obj_profiles()\u001b[0m - Weight by S/N in boxcar extraction? [avoid CRs; smooth?]\n",
      "\u001b[1;30m[WORK IN ]::\u001b[0m\n",
      "\u001b[1;33m[PROGRESS]::\u001b[0m \u001b[1;34marextract.py 303 obj_profiles()\u001b[0m - Might give our own guess here instead of using default\n",
      "\u001b[1;30m[WORK IN ]::\u001b[0m\n",
      "\u001b[1;33m[PROGRESS]::\u001b[0m \u001b[1;34marextract.py 323 obj_profiles()\u001b[0m - Consider flagging/removing CRs here\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marextract.py 261 obj_profiles()\u001b[0m - Deriving spatial profile of object 4/4 in slit 1/1\n",
      "\u001b[1;30m[WORK IN ]::\u001b[0m\n",
      "\u001b[1;33m[PROGRESS]::\u001b[0m \u001b[1;34martrace.py 1819 slit_image()\u001b[0m - Use 2D spline to evaluate tilts\n",
      "\u001b[1;30m[WORK IN ]::\u001b[0m\n",
      "\u001b[1;33m[PROGRESS]::\u001b[0m \u001b[1;34martrace.py 1824 slit_image()\u001b[0m - Should worry about changing plate scale\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marextract.py 284 obj_profiles()\u001b[0m - Good S/N for profile\n",
      "\u001b[1;30m[WORK IN ]::\u001b[0m\n",
      "\u001b[1;33m[PROGRESS]::\u001b[0m \u001b[1;34marextract.py 294 obj_profiles()\u001b[0m - Weight by S/N in boxcar extraction? [avoid CRs; smooth?]\n",
      "\u001b[1;30m[WORK IN ]::\u001b[0m\n",
      "\u001b[1;33m[PROGRESS]::\u001b[0m \u001b[1;34marextract.py 303 obj_profiles()\u001b[0m - Might give our own guess here instead of using default\n",
      "\u001b[1;30m[WORK IN ]::\u001b[0m\n",
      "\u001b[1;33m[PROGRESS]::\u001b[0m \u001b[1;34marextract.py 323 obj_profiles()\u001b[0m - Consider flagging/removing CRs here\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marextract.py 465 optimal_extract()\u001b[0m - Performing optimal extraction of object 1/4 in slit 1/1\n",
      "\u001b[1;30m[WORK IN ]::\u001b[0m\n",
      "\u001b[1;33m[PROGRESS]::\u001b[0m \u001b[1;34martrace.py 1819 slit_image()\u001b[0m - Use 2D spline to evaluate tilts\n",
      "\u001b[1;30m[WORK IN ]::\u001b[0m\n",
      "\u001b[1;33m[PROGRESS]::\u001b[0m \u001b[1;34martrace.py 1824 slit_image()\u001b[0m - Should worry about changing plate scale\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marextract.py 465 optimal_extract()\u001b[0m - Performing optimal extraction of object 2/4 in slit 1/1\n",
      "\u001b[1;30m[WORK IN ]::\u001b[0m\n",
      "\u001b[1;33m[PROGRESS]::\u001b[0m \u001b[1;34martrace.py 1819 slit_image()\u001b[0m - Use 2D spline to evaluate tilts\n",
      "\u001b[1;30m[WORK IN ]::\u001b[0m\n",
      "\u001b[1;33m[PROGRESS]::\u001b[0m \u001b[1;34martrace.py 1824 slit_image()\u001b[0m - Should worry about changing plate scale\n",
      "\u001b[1;31m[WARNING] ::\u001b[0m \u001b[1;34marextract.py 507 optimal_extract()\u001b[0m - Replacing fully masked regions with mean wavelengths\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marextract.py 465 optimal_extract()\u001b[0m - Performing optimal extraction of object 3/4 in slit 1/1\n",
      "\u001b[1;30m[WORK IN ]::\u001b[0m\n",
      "\u001b[1;33m[PROGRESS]::\u001b[0m \u001b[1;34martrace.py 1819 slit_image()\u001b[0m - Use 2D spline to evaluate tilts\n",
      "\u001b[1;30m[WORK IN ]::\u001b[0m\n",
      "\u001b[1;33m[PROGRESS]::\u001b[0m \u001b[1;34martrace.py 1824 slit_image()\u001b[0m - Should worry about changing plate scale\n",
      "\u001b[1;31m[WARNING] ::\u001b[0m \u001b[1;34marextract.py 507 optimal_extract()\u001b[0m - Replacing fully masked regions with mean wavelengths\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marextract.py 465 optimal_extract()\u001b[0m - Performing optimal extraction of object 4/4 in slit 1/1\n",
      "\u001b[1;30m[WORK IN ]::\u001b[0m\n",
      "\u001b[1;33m[PROGRESS]::\u001b[0m \u001b[1;34martrace.py 1819 slit_image()\u001b[0m - Use 2D spline to evaluate tilts\n",
      "\u001b[1;30m[WORK IN ]::\u001b[0m\n",
      "\u001b[1;33m[PROGRESS]::\u001b[0m \u001b[1;34martrace.py 1824 slit_image()\u001b[0m - Should worry about changing plate scale\n",
      "\u001b[1;31m[WARNING] ::\u001b[0m \u001b[1;34marextract.py 507 optimal_extract()\u001b[0m - Replacing fully masked regions with mean wavelengths\n"
     ]
    }
   ],
   "source": [
    "specobjs, finalvar, finalsky = sciI.extraction(mswave)"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "### Flexure"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 75,
   "metadata": {},
   "outputs": [
    {
     "name": "stderr",
     "output_type": "stream",
     "text": [
      "\u001b[1;30m[WORK IN ]::\u001b[0m\n",
      "\u001b[1;33m[PROGRESS]::\u001b[0m \u001b[1;34marwave.py 281 flexure_obj()\u001b[0m - Consider doing 2 passes in flexure as in LowRedux\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marwave.py 204 flexure_archive()\u001b[0m - Using paranal_sky.fits file for Sky spectrum\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marwave.py 297 flexure_obj()\u001b[0m - Working on flexure in slit (if an object was detected): 0\n",
      "\u001b[1;31m[WARNING] ::\u001b[0m \u001b[1;34marwave.py 44 flex_shift()\u001b[0m - If we use Paranal, cut down on wavelength early on\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34mararc.py 177 detect_lines()\u001b[0m - Detecting lines\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34mararc.py 203 detect_lines()\u001b[0m - Detecting the strongest, nonsaturated lines\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34mararc.py 177 detect_lines()\u001b[0m - Detecting lines\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34mararc.py 203 detect_lines()\u001b[0m - Detecting the strongest, nonsaturated lines\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marwave.py 72 flex_shift()\u001b[0m - Resolution of Archive=34127.6 and Observation=2744.53\n",
      "\u001b[1;30m[WORK IN ]::\u001b[0m\n",
      "\u001b[1;33m[PROGRESS]::\u001b[0m \u001b[1;34marwave.py 137 flex_shift()\u001b[0m - Need to mask bad pixels\n",
      "\u001b[1;30m[WORK IN ]::\u001b[0m\n",
      "\u001b[1;33m[PROGRESS]::\u001b[0m \u001b[1;34marwave.py 140 flex_shift()\u001b[0m - Consider taking median first [5 pixel]\n",
      "\u001b[1;30m[WORK IN ]::\u001b[0m\n",
      "\u001b[1;33m[PROGRESS]::\u001b[0m \u001b[1;34marwave.py 153 flex_shift()\u001b[0m - Consider taking median first [5 pixel]\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marwave.py 172 flex_shift()\u001b[0m - Flexure correction of -2.89474 pixels\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marwave.py 324 flexure_obj()\u001b[0m - Applying flexure correction to boxcar extraction for object:\n",
      "             <SpecObjExp: O221-S1517-D02-I0022 == Setup S-D560-G6007500-T270812645-B22 Object at 0.22065 in Slit at 0.151719 with det=02, scidx=22 and objtype=science>\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marwave.py 324 flexure_obj()\u001b[0m - Applying flexure correction to optimal extraction for object:\n",
      "             <SpecObjExp: O221-S1517-D02-I0022 == Setup S-D560-G6007500-T270812645-B22 Object at 0.22065 in Slit at 0.151719 with det=02, scidx=22 and objtype=science>\n",
      "\u001b[1;31m[WARNING] ::\u001b[0m \u001b[1;34marwave.py 44 flex_shift()\u001b[0m - If we use Paranal, cut down on wavelength early on\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34mararc.py 177 detect_lines()\u001b[0m - Detecting lines\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34mararc.py 203 detect_lines()\u001b[0m - Detecting the strongest, nonsaturated lines\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34mararc.py 177 detect_lines()\u001b[0m - Detecting lines\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34mararc.py 203 detect_lines()\u001b[0m - Detecting the strongest, nonsaturated lines\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marwave.py 72 flex_shift()\u001b[0m - Resolution of Archive=34127.6 and Observation=2765.26\n",
      "\u001b[1;30m[WORK IN ]::\u001b[0m\n",
      "\u001b[1;33m[PROGRESS]::\u001b[0m \u001b[1;34marwave.py 137 flex_shift()\u001b[0m - Need to mask bad pixels\n",
      "\u001b[1;30m[WORK IN ]::\u001b[0m\n",
      "\u001b[1;33m[PROGRESS]::\u001b[0m \u001b[1;34marwave.py 140 flex_shift()\u001b[0m - Consider taking median first [5 pixel]\n",
      "\u001b[1;30m[WORK IN ]::\u001b[0m\n",
      "\u001b[1;33m[PROGRESS]::\u001b[0m \u001b[1;34marwave.py 153 flex_shift()\u001b[0m - Consider taking median first [5 pixel]\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marwave.py 172 flex_shift()\u001b[0m - Flexure correction of -2.89587 pixels\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marwave.py 324 flexure_obj()\u001b[0m - Applying flexure correction to boxcar extraction for object:\n",
      "             <SpecObjExp: O607-S1517-D02-I0022 == Setup S-D560-G6007500-T270812645-B22 Object at 0.60662 in Slit at 0.151719 with det=02, scidx=22 and objtype=science>\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marwave.py 324 flexure_obj()\u001b[0m - Applying flexure correction to optimal extraction for object:\n",
      "             <SpecObjExp: O607-S1517-D02-I0022 == Setup S-D560-G6007500-T270812645-B22 Object at 0.60662 in Slit at 0.151719 with det=02, scidx=22 and objtype=science>\n",
      "\u001b[1;31m[WARNING] ::\u001b[0m \u001b[1;34marwave.py 44 flex_shift()\u001b[0m - If we use Paranal, cut down on wavelength early on\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34mararc.py 177 detect_lines()\u001b[0m - Detecting lines\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34mararc.py 203 detect_lines()\u001b[0m - Detecting the strongest, nonsaturated lines\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34mararc.py 177 detect_lines()\u001b[0m - Detecting lines\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34mararc.py 203 detect_lines()\u001b[0m - Detecting the strongest, nonsaturated lines\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marwave.py 72 flex_shift()\u001b[0m - Resolution of Archive=34127.6 and Observation=2711.16\n",
      "\u001b[1;30m[WORK IN ]::\u001b[0m\n",
      "\u001b[1;33m[PROGRESS]::\u001b[0m \u001b[1;34marwave.py 137 flex_shift()\u001b[0m - Need to mask bad pixels\n",
      "\u001b[1;30m[WORK IN ]::\u001b[0m\n",
      "\u001b[1;33m[PROGRESS]::\u001b[0m \u001b[1;34marwave.py 140 flex_shift()\u001b[0m - Consider taking median first [5 pixel]\n",
      "\u001b[1;30m[WORK IN ]::\u001b[0m\n",
      "\u001b[1;33m[PROGRESS]::\u001b[0m \u001b[1;34marwave.py 153 flex_shift()\u001b[0m - Consider taking median first [5 pixel]\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marwave.py 172 flex_shift()\u001b[0m - Flexure correction of -2.89529 pixels\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marwave.py 324 flexure_obj()\u001b[0m - Applying flexure correction to boxcar extraction for object:\n",
      "             <SpecObjExp: O802-S1517-D02-I0022 == Setup S-D560-G6007500-T270812645-B22 Object at 0.802417 in Slit at 0.151719 with det=02, scidx=22 and objtype=science>\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marwave.py 324 flexure_obj()\u001b[0m - Applying flexure correction to optimal extraction for object:\n",
      "             <SpecObjExp: O802-S1517-D02-I0022 == Setup S-D560-G6007500-T270812645-B22 Object at 0.802417 in Slit at 0.151719 with det=02, scidx=22 and objtype=science>\n",
      "\u001b[1;31m[WARNING] ::\u001b[0m \u001b[1;34marwave.py 44 flex_shift()\u001b[0m - If we use Paranal, cut down on wavelength early on\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34mararc.py 177 detect_lines()\u001b[0m - Detecting lines\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34mararc.py 203 detect_lines()\u001b[0m - Detecting the strongest, nonsaturated lines\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34mararc.py 177 detect_lines()\u001b[0m - Detecting lines\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34mararc.py 203 detect_lines()\u001b[0m - Detecting the strongest, nonsaturated lines\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marwave.py 72 flex_shift()\u001b[0m - Resolution of Archive=34127.6 and Observation=2760.3\n",
      "\u001b[1;30m[WORK IN ]::\u001b[0m\n",
      "\u001b[1;33m[PROGRESS]::\u001b[0m \u001b[1;34marwave.py 137 flex_shift()\u001b[0m - Need to mask bad pixels\n",
      "\u001b[1;30m[WORK IN ]::\u001b[0m\n",
      "\u001b[1;33m[PROGRESS]::\u001b[0m \u001b[1;34marwave.py 140 flex_shift()\u001b[0m - Consider taking median first [5 pixel]\n",
      "\u001b[1;30m[WORK IN ]::\u001b[0m\n",
      "\u001b[1;33m[PROGRESS]::\u001b[0m \u001b[1;34marwave.py 153 flex_shift()\u001b[0m - Consider taking median first [5 pixel]\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marwave.py 172 flex_shift()\u001b[0m - Flexure correction of -2.89537 pixels\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marwave.py 324 flexure_obj()\u001b[0m - Applying flexure correction to boxcar extraction for object:\n",
      "             <SpecObjExp: O845-S1517-D02-I0022 == Setup S-D560-G6007500-T270812645-B22 Object at 0.844828 in Slit at 0.151719 with det=02, scidx=22 and objtype=science>\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marwave.py 324 flexure_obj()\u001b[0m - Applying flexure correction to optimal extraction for object:\n",
      "             <SpecObjExp: O845-S1517-D02-I0022 == Setup S-D560-G6007500-T270812645-B22 Object at 0.844828 in Slit at 0.151719 with det=02, scidx=22 and objtype=science>\n"
     ]
    }
   ],
   "source": [
    "flex_list = arwave.flexure_obj(\n",
    "    specobjs, maskslits, settings.argflag['reduce']['flexure']['method'],\n",
    "    spectrograph,\n",
    "    skyspec_fil = settings.argflag['reduce']['flexure']['spectrum'],\n",
    "    mxshft = settings.argflag['reduce']['flexure']['maxshift'])"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 76,
   "metadata": {
    "collapsed": true
   },
   "outputs": [],
   "source": [
    "# QA \n",
    "arwave.flexure_qa(specobjs, maskslits, basename, det, flex_list)"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "### Heliocentric (optional)"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 77,
   "metadata": {},
   "outputs": [
    {
     "name": "stderr",
     "output_type": "stream",
     "text": [
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marwave.py 403 geomotion_correct()\u001b[0m - Applying heliocentric correction to boxcar extraction for object:\n",
      "             <SpecObjExp: O221-S1517-D02-I0022 == Setup S-D560-G6007500-T270812645-B22 Object at 0.22065 in Slit at 0.151719 with det=02, scidx=22 and objtype=science>\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marwave.py 403 geomotion_correct()\u001b[0m - Applying heliocentric correction to optimal extraction for object:\n",
      "             <SpecObjExp: O221-S1517-D02-I0022 == Setup S-D560-G6007500-T270812645-B22 Object at 0.22065 in Slit at 0.151719 with det=02, scidx=22 and objtype=science>\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marwave.py 403 geomotion_correct()\u001b[0m - Applying heliocentric correction to boxcar extraction for object:\n",
      "             <SpecObjExp: O607-S1517-D02-I0022 == Setup S-D560-G6007500-T270812645-B22 Object at 0.60662 in Slit at 0.151719 with det=02, scidx=22 and objtype=science>\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marwave.py 403 geomotion_correct()\u001b[0m - Applying heliocentric correction to optimal extraction for object:\n",
      "             <SpecObjExp: O607-S1517-D02-I0022 == Setup S-D560-G6007500-T270812645-B22 Object at 0.60662 in Slit at 0.151719 with det=02, scidx=22 and objtype=science>\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marwave.py 403 geomotion_correct()\u001b[0m - Applying heliocentric correction to boxcar extraction for object:\n",
      "             <SpecObjExp: O802-S1517-D02-I0022 == Setup S-D560-G6007500-T270812645-B22 Object at 0.802417 in Slit at 0.151719 with det=02, scidx=22 and objtype=science>\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marwave.py 403 geomotion_correct()\u001b[0m - Applying heliocentric correction to optimal extraction for object:\n",
      "             <SpecObjExp: O802-S1517-D02-I0022 == Setup S-D560-G6007500-T270812645-B22 Object at 0.802417 in Slit at 0.151719 with det=02, scidx=22 and objtype=science>\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marwave.py 403 geomotion_correct()\u001b[0m - Applying heliocentric correction to boxcar extraction for object:\n",
      "             <SpecObjExp: O845-S1517-D02-I0022 == Setup S-D560-G6007500-T270812645-B22 Object at 0.844828 in Slit at 0.151719 with det=02, scidx=22 and objtype=science>\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marwave.py 403 geomotion_correct()\u001b[0m - Applying heliocentric correction to optimal extraction for object:\n",
      "             <SpecObjExp: O845-S1517-D02-I0022 == Setup S-D560-G6007500-T270812645-B22 Object at 0.844828 in Slit at 0.151719 with det=02, scidx=22 and objtype=science>\n"
     ]
    }
   ],
   "source": [
    "vel, vel_corr = arwave.geomotion_correct(specobjs, maskslits, fitstbl, scidx,\n",
    "                                         obstime, settings.spect,\n",
    "                                         settings.argflag['reduce']['calibrate']['refframe'])"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 78,
   "metadata": {
    "collapsed": true
   },
   "outputs": [],
   "source": [
    "sci_dict = {}\n",
    "sci_dict['meta'] = {}\n",
    "sci_dict['meta']['vel_corr'] = vel_corr"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "----"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "## Write"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "### 1D spectra"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 79,
   "metadata": {},
   "outputs": [
    {
     "name": "stderr",
     "output_type": "stream",
     "text": [
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marsave.py 451 save_1d_spectra_fits()\u001b[0m - Wrote 1D spectra to Science/spec1d_OFF_J1044p6306_LRISr_2016Feb16T112439.fits\n"
     ]
    },
    {
     "data": {
      "text/plain": [
       "'Science/spec1d_OFF_J1044p6306_LRISr_2016Feb16T112439.fits'"
      ]
     },
     "execution_count": 79,
     "metadata": {},
     "output_type": "execute_result"
    }
   ],
   "source": [
    "outfile = 'Science/spec1d_{:s}.fits'.format(basename)\n",
    "helio_dict = dict(refframe=settings.argflag['reduce']['calibrate']['refframe'],\n",
    "                  vel_correction=sci_dict['meta']['vel_corr'])\n",
    "arsave.save_1d_spectra_fits([specobjs], fitstbl[scidx], outfile,\n",
    "                                helio_dict=helio_dict, obs_dict=settings.spect['mosaic'])"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "### 2D images"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 80,
   "metadata": {},
   "outputs": [
    {
     "name": "stderr",
     "output_type": "stream",
     "text": [
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marsave.py 727 save_2d_images()\u001b[0m - Wrote: Science//spec2d_OFF_J1044p6306_LRISr_2016Feb16T112439.fits\n"
     ]
    }
   ],
   "source": [
    "# Write 2D images for the Science Frame\n",
    "arsave.save_2d_images(\n",
    "    sci_dict, fitstbl, scidx,\n",
    "    settings.spect['fits']['headext{0:02d}'.format(1)], setup,\n",
    "    settings.argflag['run']['directory']['master']+'_'+spectrograph, # MFDIR\n",
    "    'Science/',  basename)"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "----"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "## Fluxing (optional)"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "### Reduce a standard star"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 81,
   "metadata": {},
   "outputs": [
    {
     "name": "stderr",
     "output_type": "stream",
     "text": [
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marload.py 327 load_raw_frame()\u001b[0m - Loading raw_file: /home/xavier/local/Python/PYPIT-development-suite/RAW_DATA/Keck_LRIS_red/long_600_7500_d560/LR.20160216.17613.fits\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marlris.py 48 read_lris()\u001b[0m - Reading LRIS file: /home/xavier/local/Python/PYPIT-development-suite/RAW_DATA/Keck_LRIS_red/long_600_7500_d560/LR.20160216.17613.fits\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marprocimg.py 174 get_datasec()\u001b[0m - Parsing datasec and oscansec from headers\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marlris.py 48 read_lris()\u001b[0m - Reading LRIS file: /home/xavier/local/Python/PYPIT-development-suite/RAW_DATA/Keck_LRIS_red/long_600_7500_d560/LR.20160216.17613.fits\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34mprocessimages.py 272 bias_subtract()\u001b[0m - Bias subtracting your image(s)\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marprocimg.py 77 bias_subtract()\u001b[0m - Subtracting bias image from raw frame\n",
      "\u001b[1;31m[WARNING] ::\u001b[0m \u001b[1;34marprocimg.py 505 gain_frame()\u001b[0m - Should probably be measuring the gain across the amplifier boundary\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34mprocessimages.py 430 build_rawvarframe()\u001b[0m - Generate raw variance frame (from detected counts [flat fielded])\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marprocimg.py 236 lacosmic()\u001b[0m - Detecting cosmic rays with the L.A.Cosmic algorithm\n",
      "\u001b[1;30m[WORK IN ]::\u001b[0m\n",
      "\u001b[1;33m[PROGRESS]::\u001b[0m \u001b[1;34marprocimg.py 237 lacosmic()\u001b[0m - Include these parameters in the settings files to be adjusted by the user\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marprocimg.py 259 lacosmic()\u001b[0m - Convolving image with Laplacian kernel\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marprocimg.py 267 lacosmic()\u001b[0m - Creating noise model\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marprocimg.py 274 lacosmic()\u001b[0m - Calculating Laplacian signal to noise ratio\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marprocimg.py 282 lacosmic()\u001b[0m - Selecting candidate cosmic rays\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marprocimg.py 287 lacosmic()\u001b[0m - 11894 candidate pixels\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marprocimg.py 291 lacosmic()\u001b[0m - Masking saturated pixels\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marprocimg.py 295 lacosmic()\u001b[0m - 11892 candidate pixels not part of saturated stars\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marprocimg.py 297 lacosmic()\u001b[0m - Building fine structure image\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marprocimg.py 306 lacosmic()\u001b[0m - Removing suspected compact bright objects\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marprocimg.py 316 lacosmic()\u001b[0m -  6297 remaining candidate pixels\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marprocimg.py 320 lacosmic()\u001b[0m - Finding neighboring pixels affected by cosmic rays\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marprocimg.py 336 lacosmic()\u001b[0m - Masking saturated stars\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marprocimg.py 341 lacosmic()\u001b[0m - 14586 pixels detected as cosmics\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marprocimg.py 350 lacosmic()\u001b[0m - Iteration 1 -- 14586 pixels identified as cosmic rays (14586 new)\n",
      "\u001b[1;30m[WORK IN ]::\u001b[0m\n",
      "\u001b[1;33m[PROGRESS]::\u001b[0m \u001b[1;34marprocimg.py 353 lacosmic()\u001b[0m - The following algorithm would be better on the rectified, tilts-corrected image\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marprocimg.py 408 lacosmic()\u001b[0m - Growing cosmic ray mask by 1 pixel\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34mscienceimage.py 459 global_skysub()\u001b[0m - Working on slit: 0\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marutils.py 198 bspline_profile()\u001b[0m - Fitting npoly =  1 profile basis functions, nx=590811 pixels\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marutils.py 199 bspline_profile()\u001b[0m - ****************************  Iter  Chi^2  # rejected  Rel. fact   ****************************\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marutils.py 200 bspline_profile()\u001b[0m -                               ----  -----  ----------  --------- \n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marutils.py 281 bspline_profile()\u001b[0m -                                 1   0.010        0        1.00\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marutils.py 286 bspline_profile()\u001b[0m - ***********************************************************************************************\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marutils.py 289 bspline_profile()\u001b[0m - Final fit after  1 iterations: reduced_chi =    0.010, rejected =       0, relative_factor =   1.00\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marutils.py 198 bspline_profile()\u001b[0m - Fitting npoly =  1 profile basis functions, nx=590811 pixels\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marutils.py 199 bspline_profile()\u001b[0m - ****************************  Iter  Chi^2  # rejected  Rel. fact   ****************************\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marutils.py 200 bspline_profile()\u001b[0m -                               ----  -----  ----------  --------- \n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marutils.py 281 bspline_profile()\u001b[0m -                                 1   1.315     6726        1.00\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marutils.py 286 bspline_profile()\u001b[0m - ***********************************************************************************************\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marutils.py 289 bspline_profile()\u001b[0m - Final fit after  1 iterations: reduced_chi =    1.315, rejected =    6726, relative_factor =   1.00\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34mscienceimage.py 469 global_skysub()\u001b[0m - Building model variance from the Sky frame\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34martrace.py 285 trace_objects_in_slit()\u001b[0m - Rectifying science frame\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34martrace.py 306 trace_objects_in_slit()\u001b[0m - Estimating object profiles\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34martrace.py 375 trace_objects_in_slit()\u001b[0m - Identifying objects that are significantly detected\n",
      "\u001b[1;31m[WARNING] ::\u001b[0m \u001b[1;34martrace.py 430 trace_objects_in_slit()\u001b[0m - Removed objects near the slit edges\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34martrace.py 461 trace_objects_in_slit()\u001b[0m - Found 8 objects\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34martrace.py 462 trace_objects_in_slit()\u001b[0m - Tracing 8 objects\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34martrace.py 498 trace_objects_in_slit()\u001b[0m - Performing global trace to all objects\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34martrace.py 501 trace_objects_in_slit()\u001b[0m - Constructing a trace for all objects\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34martrace.py 509 trace_objects_in_slit()\u001b[0m - Converting object traces to detector pixels\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34martrace.py 90 trace_objbg_image()\u001b[0m - Creating an image weighted by object pixels for 8 objects\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34martrace.py 99 trace_objbg_image()\u001b[0m - Creating an image weighted by background pixels\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34mscienceimage.py 459 global_skysub()\u001b[0m - Working on slit: 0\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marutils.py 198 bspline_profile()\u001b[0m - Fitting npoly =  1 profile basis functions, nx=461991 pixels\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marutils.py 199 bspline_profile()\u001b[0m - ****************************  Iter  Chi^2  # rejected  Rel. fact   ****************************\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marutils.py 200 bspline_profile()\u001b[0m -                               ----  -----  ----------  --------- \n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marutils.py 281 bspline_profile()\u001b[0m -                                 1   0.000        0        1.00\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marutils.py 286 bspline_profile()\u001b[0m - ***********************************************************************************************\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marutils.py 289 bspline_profile()\u001b[0m - Final fit after  1 iterations: reduced_chi =    0.000, rejected =       0, relative_factor =   1.00\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marutils.py 198 bspline_profile()\u001b[0m - Fitting npoly =  1 profile basis functions, nx=461991 pixels\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marutils.py 199 bspline_profile()\u001b[0m - ****************************  Iter  Chi^2  # rejected  Rel. fact   ****************************\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marutils.py 200 bspline_profile()\u001b[0m -                               ----  -----  ----------  --------- \n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marutils.py 281 bspline_profile()\u001b[0m -                                 1   1.193     3310        1.00\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marutils.py 286 bspline_profile()\u001b[0m - ***********************************************************************************************\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marutils.py 289 bspline_profile()\u001b[0m - Final fit after  1 iterations: reduced_chi =    1.193, rejected =    3310, relative_factor =   1.00\n"
     ]
    },
    {
     "name": "stderr",
     "output_type": "stream",
     "text": [
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34mscienceimage.py 469 global_skysub()\u001b[0m - Building model variance from the Sky frame\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34mscienceimage.py 278 boxcar()\u001b[0m - Performing boxcar extraction\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marextract.py 80 boxcar()\u001b[0m - Performing boxcar extraction of object 1/8 in slit 1/1\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marextract.py 89 boxcar()\u001b[0m -    Fitting the background\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marextract.py 166 boxcar()\u001b[0m -    Summing object counts\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marextract.py 169 boxcar()\u001b[0m -    Summing variance array\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marextract.py 80 boxcar()\u001b[0m - Performing boxcar extraction of object 2/8 in slit 1/1\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marextract.py 89 boxcar()\u001b[0m -    Fitting the background\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marextract.py 166 boxcar()\u001b[0m -    Summing object counts\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marextract.py 169 boxcar()\u001b[0m -    Summing variance array\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marextract.py 80 boxcar()\u001b[0m - Performing boxcar extraction of object 3/8 in slit 1/1\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marextract.py 89 boxcar()\u001b[0m -    Fitting the background\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marextract.py 166 boxcar()\u001b[0m -    Summing object counts\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marextract.py 169 boxcar()\u001b[0m -    Summing variance array\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marextract.py 80 boxcar()\u001b[0m - Performing boxcar extraction of object 4/8 in slit 1/1\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marextract.py 89 boxcar()\u001b[0m -    Fitting the background\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marextract.py 166 boxcar()\u001b[0m -    Summing object counts\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marextract.py 169 boxcar()\u001b[0m -    Summing variance array\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marextract.py 80 boxcar()\u001b[0m - Performing boxcar extraction of object 5/8 in slit 1/1\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marextract.py 89 boxcar()\u001b[0m -    Fitting the background\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marextract.py 166 boxcar()\u001b[0m -    Summing object counts\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marextract.py 169 boxcar()\u001b[0m -    Summing variance array\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marextract.py 80 boxcar()\u001b[0m - Performing boxcar extraction of object 6/8 in slit 1/1\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marextract.py 89 boxcar()\u001b[0m -    Fitting the background\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marextract.py 166 boxcar()\u001b[0m -    Summing object counts\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marextract.py 169 boxcar()\u001b[0m -    Summing variance array\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marextract.py 80 boxcar()\u001b[0m - Performing boxcar extraction of object 7/8 in slit 1/1\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marextract.py 89 boxcar()\u001b[0m -    Fitting the background\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marextract.py 166 boxcar()\u001b[0m -    Summing object counts\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marextract.py 169 boxcar()\u001b[0m -    Summing variance array\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marextract.py 80 boxcar()\u001b[0m - Performing boxcar extraction of object 8/8 in slit 1/1\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marextract.py 89 boxcar()\u001b[0m -    Fitting the background\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marextract.py 166 boxcar()\u001b[0m -    Summing object counts\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marextract.py 169 boxcar()\u001b[0m -    Summing variance array\n"
     ]
    }
   ],
   "source": [
    "std_dict = {}\n",
    "# Reduce standard here; only legit if the mask is the same\n",
    "std_idx = arsort.ftype_indices(fitstbl, 'standard', sci_ID)[0]\n",
    "#\n",
    "std_image_files = arsort.list_of_files(fitstbl, 'standard', sci_ID)\n",
    "std_dict[std_idx] = {}\n",
    "\n",
    "# Instantiate for the Standard\n",
    "stdI = scienceimage.ScienceImage(file_list=std_image_files, datasec_img=datasec_img,\n",
    "                                 bpm=msbpm, det=det, setup=setup, settings=sci_settings,\n",
    "                                 maskslits=maskslits, pixlocn=pixlocn, tslits_dict=tslits_dict,\n",
    "                                 tilts=mstilts, fitstbl=fitstbl, scidx=std_idx,\n",
    "                                 objtype='standard')\n",
    "# Names and time\n",
    "_, std_basename = stdI.init_time_names(settings.spect['mosaic']['camera'],\n",
    "                                         timeunit=settings.spect[\"fits\"][\"timeunit\"])\n",
    "# Process (includes Variance image and CRs)\n",
    "stdframe, _, _ = stdI._process(msbias, mspixflatnrm, apply_gain=True, dnoise=dnoise)\n",
    "# Sky\n",
    "_ = stdI.global_skysub(settings_skysub)\n",
    "# Find objects\n",
    "_, nobj = stdI.find_objects()\n",
    "_ = stdI.global_skysub(settings_skysub, use_tracemask=True)\n",
    "# Extract\n",
    "stdobjs, _, _ = stdI.extraction(mswave)\n",
    "# Save for fluxing and output later\n",
    "std_dict[std_idx][det] = {}\n",
    "std_dict[std_idx][det]['basename'] = std_basename\n",
    "std_dict[std_idx][det]['specobjs'] = arutils.unravel_specobjs([stdobjs])\n"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "### Sensitivity function"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 82,
   "metadata": {
    "collapsed": true
   },
   "outputs": [],
   "source": [
    "# Settings\n",
    "fsettings = settings.spect.copy()\n",
    "fsettings['run'] = settings.argflag['run']\n",
    "fsettings['reduce'] = settings.argflag['reduce']"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 83,
   "metadata": {},
   "outputs": [
    {
     "name": "stderr",
     "output_type": "stream",
     "text": [
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marflux.py 442 find_standard()\u001b[0m - Putative standard star <SpecObjExp: O233-S1517-D02-I0021 == Setup S-D560-G6007500-T2708013535-B22 Object at 0.232859 in Slit at 0.151719 with det=02, scidx=21 and objtype=standard> has a median boxcar count of 34232.22224319243\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marflux.py 370 load_extinction_data()\u001b[0m - Using mkoextinct.dat for extinction corrections.\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marflux.py 300 find_standard_file()\u001b[0m - Using standard star G191B2B\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marflux.py 406 load_standard_file()\u001b[0m - Loading standard star file: /home/xavier/local/Python/PYPIT/pypit/data/standards/calspec/g191b2b_mod_005.fits.gz\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marflux.py 407 load_standard_file()\u001b[0m - Fluxes are flambda, normalized to 1e-17\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marflux.py 507 generate_sensfunc()\u001b[0m - Masking edges\n",
      "\u001b[1;31m[WARNING] ::\u001b[0m \u001b[1;34marflux.py 513 generate_sensfunc()\u001b[0m - Should pull resolution from arc line analysis\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marflux.py 517 generate_sensfunc()\u001b[0m - Masking Balmer\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marflux.py 525 generate_sensfunc()\u001b[0m - Masking Telluric\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marflux.py 532 generate_sensfunc()\u001b[0m - Masking Below the atmospheric cutoff\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marflux.py 203 bspline_magfit()\u001b[0m - Difference between fits is 8.8605e-05\n",
      "\u001b[1;30m[WORK IN ]::\u001b[0m\n",
      "\u001b[1;33m[PROGRESS]::\u001b[0m \u001b[1;34marflux.py 206 bspline_magfit()\u001b[0m - Add QA for sensitivity function\n"
     ]
    }
   ],
   "source": [
    "# Build the list of stdobjs\n",
    "reload(fluxspec)\n",
    "all_std_objs = []\n",
    "for det in std_dict[std_idx].keys():\n",
    "    all_std_objs += std_dict[std_idx][det]['specobjs']\n",
    "FxSpec = fluxspec.FluxSpec(settings=fsettings, std_specobjs=all_std_objs,\n",
    "                           setup=setup)  # This takes the last setup run, which is as sensible as any..\n",
    "sensfunc = FxSpec.master(fitstbl[std_idx], save=False)"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 84,
   "metadata": {},
   "outputs": [
    {
     "data": {
      "text/plain": [
       "[<SpecObjExp: O233-S1517-D02-I0021 == Setup S-D560-G6007500-T2708013535-B22 Object at 0.232859 in Slit at 0.151719 with det=02, scidx=21 and objtype=standard>,\n",
       " <SpecObjExp: O394-S1517-D02-I0021 == Setup S-D560-G6007500-T2708013535-B22 Object at 0.393931 in Slit at 0.151719 with det=02, scidx=21 and objtype=standard>,\n",
       " <SpecObjExp: O608-S1517-D02-I0021 == Setup S-D560-G6007500-T2708013535-B22 Object at 0.607527 in Slit at 0.151719 with det=02, scidx=21 and objtype=standard>,\n",
       " <SpecObjExp: O805-S1517-D02-I0021 == Setup S-D560-G6007500-T2708013535-B22 Object at 0.804754 in Slit at 0.151719 with det=02, scidx=21 and objtype=standard>,\n",
       " <SpecObjExp: O846-S1517-D02-I0021 == Setup S-D560-G6007500-T2708013535-B22 Object at 0.845834 in Slit at 0.151719 with det=02, scidx=21 and objtype=standard>,\n",
       " <SpecObjExp: O671-S1517-D02-I0021 == Setup S-D560-G6007500-T2708013535-B22 Object at 0.671486 in Slit at 0.151719 with det=02, scidx=21 and objtype=standard>,\n",
       " <SpecObjExp: O934-S1517-D02-I0021 == Setup S-D560-G6007500-T2708013535-B22 Object at 0.933993 in Slit at 0.151719 with det=02, scidx=21 and objtype=standard>,\n",
       " <SpecObjExp: O942-S1517-D02-I0021 == Setup S-D560-G6007500-T2708013535-B22 Object at 0.942221 in Slit at 0.151719 with det=02, scidx=21 and objtype=standard>]"
      ]
     },
     "execution_count": 84,
     "metadata": {},
     "output_type": "execute_result"
    }
   ],
   "source": [
    "all_std_objs"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 85,
   "metadata": {},
   "outputs": [
    {
     "data": {
      "image/png": "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\ngg==\n",
      "text/plain": [
       "<matplotlib.figure.Figure at 0x7f70c7b4c550>"
      ]
     },
     "metadata": {},
     "output_type": "display_data"
    }
   ],
   "source": [
    "# Show\n",
    "FxSpec.show_sensfunc()"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "### Flux"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 86,
   "metadata": {},
   "outputs": [
    {
     "name": "stderr",
     "output_type": "stream",
     "text": [
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marflux.py 370 load_extinction_data()\u001b[0m - Using mkoextinct.dat for extinction corrections.\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marflux.py 46 apply_sensfunc()\u001b[0m - Fluxing boxcar extraction for:\n",
      "             <SpecObjExp: O221-S1517-D02-I0022 == Setup dum_config Object at 0.221 in Slit at 0.1517 with det=02, scidx=22 and objtype=unknown>\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marflux.py 46 apply_sensfunc()\u001b[0m - Fluxing optimal extraction for:\n",
      "             <SpecObjExp: O221-S1517-D02-I0022 == Setup dum_config Object at 0.221 in Slit at 0.1517 with det=02, scidx=22 and objtype=unknown>\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marflux.py 370 load_extinction_data()\u001b[0m - Using mkoextinct.dat for extinction corrections.\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marflux.py 46 apply_sensfunc()\u001b[0m - Fluxing boxcar extraction for:\n",
      "             <SpecObjExp: O607-S1517-D02-I0022 == Setup dum_config Object at 0.607 in Slit at 0.1517 with det=02, scidx=22 and objtype=unknown>\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marflux.py 46 apply_sensfunc()\u001b[0m - Fluxing optimal extraction for:\n",
      "             <SpecObjExp: O607-S1517-D02-I0022 == Setup dum_config Object at 0.607 in Slit at 0.1517 with det=02, scidx=22 and objtype=unknown>\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marflux.py 370 load_extinction_data()\u001b[0m - Using mkoextinct.dat for extinction corrections.\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marflux.py 46 apply_sensfunc()\u001b[0m - Fluxing boxcar extraction for:\n",
      "             <SpecObjExp: O802-S1517-D02-I0022 == Setup dum_config Object at 0.802 in Slit at 0.1517 with det=02, scidx=22 and objtype=unknown>\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marflux.py 46 apply_sensfunc()\u001b[0m - Fluxing optimal extraction for:\n",
      "             <SpecObjExp: O802-S1517-D02-I0022 == Setup dum_config Object at 0.802 in Slit at 0.1517 with det=02, scidx=22 and objtype=unknown>\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marflux.py 370 load_extinction_data()\u001b[0m - Using mkoextinct.dat for extinction corrections.\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marflux.py 46 apply_sensfunc()\u001b[0m - Fluxing boxcar extraction for:\n",
      "             <SpecObjExp: O845-S1517-D02-I0022 == Setup dum_config Object at 0.845 in Slit at 0.1517 with det=02, scidx=22 and objtype=unknown>\n",
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marflux.py 46 apply_sensfunc()\u001b[0m - Fluxing optimal extraction for:\n",
      "             <SpecObjExp: O845-S1517-D02-I0022 == Setup dum_config Object at 0.845 in Slit at 0.1517 with det=02, scidx=22 and objtype=unknown>\n"
     ]
    }
   ],
   "source": [
    "# Load\n",
    "sci_specobjs, sci_header = arload.load_specobj('Science/spec1d_OFF_J1044p6306_LRISr_2016Feb16T112439.fits')\n",
    "#\n",
    "FxSpec.sci_specobjs = sci_specobjs\n",
    "FxSpec.sci_header = sci_header\n",
    "# Flux\n",
    "FxSpec.flux_science()"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 87,
   "metadata": {},
   "outputs": [
    {
     "name": "stderr",
     "output_type": "stream",
     "text": [
      "\u001b[1;32m[INFO]    ::\u001b[0m \u001b[1;34marsave.py 451 save_1d_spectra_fits()\u001b[0m - Wrote 1D spectra to Science/spec1d_OFF_J1044p6306_LRISr_2016Feb16T112439.fits\n"
     ]
    }
   ],
   "source": [
    "# Write\n",
    "FxSpec.write_science('Science/spec1d_OFF_J1044p6306_LRISr_2016Feb16T112439.fits')"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {
    "collapsed": true
   },
   "outputs": [],
   "source": []
  }
 ],
 "metadata": {
  "kernelspec": {
   "display_name": "Python 3",
   "language": "python",
   "name": "python3"
  },
  "language_info": {
   "codemirror_mode": {
    "name": "ipython",
    "version": 3
   },
   "file_extension": ".py",
   "mimetype": "text/x-python",
   "name": "python",
   "nbconvert_exporter": "python",
   "pygments_lexer": "ipython3",
   "version": "3.6.3"
  }
 },
 "nbformat": 4,
 "nbformat_minor": 2
}