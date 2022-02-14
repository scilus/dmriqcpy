#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import os
import shutil

import itertools
from multiprocessing import Pool
import numpy as np

from dmriqcpy.io.report import Report
from dmriqcpy.io.utils import (add_online_arg, add_overwrite_arg,
                               assert_inputs_exist, assert_outputs_exist,
                               list_files_from_paths, add_skip_arg,
                               add_nb_columns_arg, add_nb_threads_arg)
from dmriqcpy.viz.screenshot import screenshot_mosaic_blend


DESCRIPTION = """
Compute the labels report in HTML format.

Using LUT like:
#No. Label Name:                            R   G   B
"""


def _build_arg_parser():
    p = argparse.ArgumentParser(description=DESCRIPTION,
                                formatter_class=argparse.RawTextHelpFormatter)

    p.add_argument('output_report',
                   help='HTML report.')

    p.add_argument('--t1', nargs='+', required=True,
                   help='Folder or list of T1 images in Nifti format.')

    p.add_argument('--label', nargs='+', required=True,
                   help='Folder or list of label images in Nifti format.')

    p.add_argument('--lut', nargs=1, default="",
                   help='Look Up Table for RGB.')

    p.add_argument('--compute_lut', action='store_true',
                   help='Compute Look Up Table for RGB.')

    add_skip_arg(p)
    add_nb_columns_arg(p)
    add_nb_threads_arg(p)
    add_online_arg(p)
    add_overwrite_arg(p)

    return p


def _subj_parralel(t1, label, name, skip, nb_columns, lut, compute_lut):
    subjects_dict = {}
    if not lut:
        lut = None

    screenshot_path = screenshot_mosaic_blend(t1, label,
                                              output_prefix=name,
                                              directory="data",
                                              blend_val=0.4,
                                              skip=skip, nb_columns=nb_columns,
                                              lut=lut,
                                              compute_lut=compute_lut)

    key = os.path.basename(t1).split('.')[0]

    subjects_dict[key] = {}
    subjects_dict[key]['screenshot'] = screenshot_path
    return subjects_dict


def main():
    parser = _build_arg_parser()
    args = parser.parse_args()

    t1 = list_files_from_paths(args.t1)
    label = list_files_from_paths(args.label)

    if not len(t1) == len(label) and len(label) != 1:
        parser.error("Not the same number of images in input.")

    if len(label) == 1:
        label = label * len(args.t1)

    all_images = np.concatenate([t1, label])
    if args.lut:
        all_images = np.concatenate(all_images, args.lut)

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
                                      zip(t1,
                                          label,
                                          itertools.repeat(name),
                                          itertools.repeat(args.skip),
                                          itertools.repeat(args.nb_columns),
                                          itertools.repeat(args.lut),
                                          itertools.repeat(args.compute_lut)))
    pool.close()
    pool.join()

    metrics_dict = {}
    subjects_dict = {}
    for dict_sub in subjects_dict_pool:
        for key in dict_sub:
            curr_key = os.path.basename(key).split('.')[0]
            subjects_dict[curr_key] = dict_sub[curr_key]
    metrics_dict[name] = subjects_dict

    nb_subjects = len(t1)
    report = Report(args.output_report)
    report.generate(title="Quality Assurance labels",
                    nb_subjects=nb_subjects, metrics_dict=metrics_dict,
                    online=args.online)


if __name__ == '__main__':
    main()
