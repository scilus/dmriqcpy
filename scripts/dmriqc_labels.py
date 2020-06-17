#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import os
import shutil

import itertools
from multiprocessing import Pool
import numpy as np

from dmriqcpy.io.report import Report
from dmriqcpy.viz.graph import graph_mean_in_tissues
from dmriqcpy.analysis.stats import stats_mean_in_tissues
from dmriqcpy.viz.screenshot import screenshot_mosaic_blend
from dmriqcpy.viz.utils import analyse_qa, dataframe_to_html
from dmriqcpy.io.utils import add_overwrite_arg, assert_inputs_exist, \
    assert_outputs_exist

DESCRIPTION = """
Compute the labels report in HTML format.

Using LUT like: 
#No. Label Name:                            R   G   B
"""


def _build_arg_parser():
    p = argparse.ArgumentParser(description=DESCRIPTION,
                                formatter_class=argparse.RawTextHelpFormatter)

    p.add_argument('output_report',
                   help='HTML report')

    p.add_argument('lut',
                   help='Look Up Table for RGB')

    p.add_argument('--t1', nargs='+', required=True,
                   help='T1 images in Nifti format')

    p.add_argument('--label', nargs='+', required=True,
                   help='Label images in Nifti format')

    p.add_argument('--skip', default=2, type=int,
                   help='Number of images skipped to build the mosaic. [%(default)s]')

    p.add_argument('--nb_columns', default=12, type=int,
                   help='Number of columns for the mosaic. [%(default)s]')

    p.add_argument('--nb_threads', type=int, default=1,
                   help='Number of threads. [%(default)s]')

    add_overwrite_arg(p)

    return p


def _subj_parralel(t1, label, name, skip, nb_columns, lut):
    subjects_dict = {}
    screenshot_path = screenshot_mosaic_blend(t1, label,
                                              output_prefix=name,
                                              directory="data",
                                              blend_val=0.5,
                                              skip=skip, nb_columns=nb_columns,
                                              lut=lut)

    subjects_dict[t1] = {}
    subjects_dict[t1]['screenshot'] = screenshot_path
    return subjects_dict


def main():
    parser = _build_arg_parser()
    args = parser.parse_args()

    if not len(args.t1) == len(args.label):
        parser.error("Not the same number of images in input.")

    all_images = np.concatenate([args.t1, args.label, [args.lut]])
    assert_inputs_exist(parser, all_images)
    assert_outputs_exist(parser, args, [args.output_report, "data", "libs"])

    if os.path.exists("data"):
        shutil.rmtree("data")
    os.makedirs("data")

    if os.path.exists("libs"):
        shutil.rmtree("libs")

    name = "Labels"

    pool = Pool(args.nb_threads)
    subjects_dict_pool = pool.starmap(_subj_parralel,
                                      zip(args.t1,
                                          args.label,
                                          itertools.repeat(name),
                                          itertools.repeat(args.skip),
                                          itertools.repeat(args.nb_columns),
                                          itertools.repeat(args.lut)))
    pool.close()
    pool.join()

    metrics_dict = {}
    subjects_dict = {}
    for dict_sub in subjects_dict_pool:
        for key in dict_sub:
            subjects_dict[key] = dict_sub[key]
    metrics_dict[name] = subjects_dict

    nb_subjects = len(args.t1)
    report = Report(args.output_report)
    report.generate(title="Quality Assurance labels",
                    nb_subjects=nb_subjects, metrics_dict=metrics_dict)


if __name__ == '__main__':
    main()
