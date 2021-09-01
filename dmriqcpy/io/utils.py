# -*- coding: utf-8 -*-
"""
Some functions comes from
https://github.com/scilus/scilpy/blob/master/scilpy/io/utils.py
"""

import os


def add_overwrite_arg(parser):
    """
    Add overwrite option to the parser.

    Parameters
    ----------
    parser: argparse.ArgumentParser object
    """
    parser.add_argument(
        '-f', dest='overwrite', action='store_true',
        help='Force overwriting of the output files.')


def assert_inputs_exist(parser, required, optional=None,
                        are_directories=False):
    """
    Assert that all inputs exist. If not, print parser's usage and exit.

    Parameters
    ----------
    parser: argparse.ArgumentParser object
    required: string or list of paths
    optional: string or list of paths.
        Each element will be ignored if None
    are_directories: bool
    """
    def check(path, are_directories):
        if not os.path.isfile(path) and not are_directories:
            parser.error('Input file {} does not exist'.format(path))
        elif are_directories and not os.path.isdir(path):
            parser.error('Input directory {} does not exist'.format(path))

    if isinstance(required, str):
        required = [required]

    if isinstance(optional, str):
        optional = [optional]

    for required_file in required:
        check(required_file, are_directories)
    for optional_file in optional or []:
        if optional_file is not None:
            check(optional_file, are_directories)


def assert_outputs_exist(parser, args, required, optional=None):
    """
    Assert that all outputs don't exist or that if they exist, -f was used.
    If not, print parser's usage and exit.

    Parameters
    ----------
    parser: argparse.ArgumentParser object
    args: argparse namespace
    required: string or list of paths
    optional: string or list of paths.
        Each element will be ignored if None
    """
    def check(path):
        if os.path.isfile(path) and not args.overwrite:
            parser.error('Output file {} exists. Use -f to force '
                         'overwriting'.format(path))

    if isinstance(required, str):
        required = [required]

    if isinstance(optional, str):
        optional = [optional]

    for required_file in required:
        check(required_file)
    for optional_file in optional or []:
        if optional_file is not None:
            check(optional_file)


def add_online_arg(parser):
    parser.add_argument('--online', action='store_true',
                        help='If set, the script will use the internet '
                             'connexion to grab the needed libraries.')
