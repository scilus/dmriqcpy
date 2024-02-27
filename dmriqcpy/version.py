# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function
import glob

# Format expected by setup.py and doc/source/conf.py: string of form "X.Y.Z"
_version_major = 0
_version_minor = 1
_version_micro = 7  # use '' for first of series, number for 1 and above
_version_extra = ''  # Uncomment this for full releases

# Construct full version string from these.
_ver = [_version_major, _version_minor]
if _version_micro:
    _ver.append(_version_micro)
if _version_extra:
    _ver.append(_version_extra)

__version__ = '.'.join(map(str, _ver))

CLASSIFIERS = ["Development Status :: 3 - Alpha",
               "Environment :: Console",
               "Intended Audience :: Science/Research",
               "License :: OSI Approved :: MIT License",
               "Operating System :: OS Independent",
               "Programming Language :: Python",
               "Topic :: Scientific/Engineering"]

# Description should be a one-liner:
description = "Diffusion MRI Quality Check in python "
# Long description will go up on the pypi page
long_description = """
"""

NAME = "dmriqcpy"
MAINTAINER = "Guillaume Theaud"
MAINTAINER_EMAIL = "guillaume.theaud@gmail.com"
DESCRIPTION = description
LONG_DESCRIPTION = long_description
URL = "https://github.com/GuillaumeTh/dmriqcpy"
DOWNLOAD_URL = ""
LICENSE = "MIT"
AUTHOR = "The developers"
AUTHOR_EMAIL = ""
PLATFORMS = "OS Independent"
MAJOR = _version_major
MINOR = _version_minor
MICRO = _version_micro
VERSION = __version__
REQUIRES = ['numpy (>=1.23,<1.24)', 'jinja2 (>=2.10.1)', 'pandas (>=0.25.1)',
            'nibabel (>=4.0,<4.1)', 'plotly (>=5.18,<5.19)',
            'vtk (>=9.2,<9.3)', 'pillow (>=10.0,<10.1)', 'fury (>=0.8,<0.9)',
            'dipy (>=1.7,<1.8)', 'matplotlib (>=3.6,<3.7)',
            'scipy (>=1.9,<2.0)']
SCRIPTS = glob.glob("scripts/*.py")
