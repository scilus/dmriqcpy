# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function
import glob

# Format expected by setup.py and doc/source/conf.py: string of form "X.Y.Z"
_version_major = 0
_version_minor = 1
_version_micro = ''  # use '' for first of series, number for 1 and above
_version_extra = 'dev'
# _version_extra = ''  # Uncomment this for full releases

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
REQUIRES = ['numpy (>=1.18)', 'jinja2 (>=2.10.1)', 'pandas (>=0.25.1)',
            'nibabel (>=3.0)', 'plotly (>=3.0.0)', 'vtk (>=8.1.2)',
            'pillow (>=6.2.0)', 'fury (>=0.2.0)',
            'matplotlib (>=2.2.0)', 'scipy (>=1.4.1)']
SCRIPTS = glob.glob("scripts/*.py")
