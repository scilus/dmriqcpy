# -*- coding: utf-8 -*-
import glob
import os
import shutil

import numpy as np


"""
Some functions comes from
https://github.com/scilus/scilpy/blob/master/scilpy/io/utils.py
"""


def assert_inputs_exist(parser, required, optional=None, are_directories=False):
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
            parser.error("Input file {} does not exist".format(path))
        elif are_directories and not os.path.isdir(path):
            parser.error("Input directory {} does not exist".format(path))

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
            parser.error(
                "Output file {} exists. Use -f to force overwriting".format(
                    path
                )
            )

    if isinstance(required, str):
        required = [required]

    if isinstance(optional, str):
        optional = [optional]

    for required_file in required:
        check(required_file)
    for optional_file in optional or []:
        if optional_file is not None:
            check(optional_file)


def assert_list_arguments_equal_size(parser, *args):
    sizes = [len(arg) for arg in args]
    if len(sizes) == 0:
        parser.error("No input images provided.")
    if not np.allclose(sizes, sizes[0]):
        parser.error("Not the same number of images in input.")


def add_overwrite_arg(parser):
    """
    Add overwrite option to the parser.

    Parameters
    ----------
    parser: argparse.ArgumentParser object
    """
    parser.add_argument(
        "-f",
        dest="overwrite",
        action="store_true",
        help="Force overwriting of the output files.",
    )


def add_online_arg(parser):
    parser.add_argument(
        "--online",
        action="store_true",
        help="If set, opening the generated HTML report will require an "
        "internet connection to dynamically load JS and CSS dependencies",
    )


def add_nb_threads_arg(parser, default=1):
    parser.add_argument(
        "--nb_threads",
        type=int,
        default=default,
        help="Number of threads. [%(default)s]",
    )


def add_skip_arg(parser, default=2):
    parser.add_argument(
        "--skip",
        default=default,
        type=int,
        help="Number of images skipped to build the mosaic. [%(default)s]",
    )


def add_nb_columns_arg(parser, default=12):
    parser.add_argument(
        "--nb_columns",
        default=default,
        type=int,
        help="Number of columns for the mosaic. [%(default)s]",
    )


def clean_output_directories(outputs_data=True):
    if outputs_data:
        if os.path.exists("data"):
            shutil.rmtree("data")
        os.makedirs("data")

    if os.path.exists("libs"):
        shutil.rmtree("libs")


def list_files_from_paths(paths):
    """
    Get all images from folder or list of files

    Parameters
    ----------
    paths: list
        List of folders and images

    Return
    ------
    out_images: list
        List of files sorted
    """
    out_images = []
    for curr_path in paths:
        if os.path.isdir(curr_path):
            curr_images = glob.glob(os.path.join(curr_path, "*"))
        else:
            curr_images = [curr_path]

        out_images = out_images + curr_images

    return sorted(out_images)
