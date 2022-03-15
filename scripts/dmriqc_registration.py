#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import os
import shutil

import itertools
from multiprocessing import Pool
import numpy as np


from dmriqcpy.analysis.stats import stats_mean_in_tissues
from dmriqcpy.io.report import Report
from dmriqcpy.io.utils import (add_online_arg, add_overwrite_arg,
                               assert_inputs_exist, assert_outputs_exist,
                               get_files_from_folder)
from dmriqcpy.viz.graph import graph_mean_in_tissues
from dmriqcpy.viz.screenshot import screenshot_mosaic_blend
from dmriqcpy.viz.utils import analyse_qa, dataframe_to_html


DESCRIPTION = """
Compute the registration report in HTML format.
"""


def _build_arg_parser():
    p = argparse.ArgumentParser(description=DESCRIPTION,
                                formatter_class=argparse.RawTextHelpFormatter)

    p.add_argument('output_report',
                   help='HTML report')

    p.add_argument('--t1_warped', nargs='+', required=True,
                   help='Folder or list of T1 registered images '
                        'in Nifti format.')

    p.add_argument('--rgb', nargs='+', required=True,
                   help='Folder or list of RGB images in Nifti format.')

    p.add_argument('--wm', nargs='+', required=True,
                   help='Folder or list of WM mask in Nifti format.')

    p.add_argument('--gm', nargs='+', required=True,
                   help='Folder or list of GM mask in Nifti format.')

    p.add_argument('--csf', nargs='+', required=True,
                   help='Folder or list of CSF mask in Nifti format.')

    p.add_argument('--skip', default=2, type=int,
                   help='Number of images skipped to build the '
                        'mosaic. [%(default)s]')

    p.add_argument('--nb_columns', default=12, type=int,
                   help='Number of columns for the mosaic. [%(default)s]')

    p.add_argument('--nb_threads', type=int, default=1,
                   help='Number of threads. [%(default)s]')

    add_online_arg(p)
    add_overwrite_arg(p)

    return p


def _subj_parralel(t1_metric, rgb_metric, summary, name, skip, nb_columns):
    subjects_dict = {}
    screenshot_path = screenshot_mosaic_blend(t1_metric, rgb_metric,
                                              output_prefix=name,
                                              directory="data",
                                              blend_val=0.5,
                                              skip=skip, nb_columns=nb_columns)

    summary_html = dataframe_to_html(summary.loc[t1_metric])
    subjects_dict[t1_metric] = {}
    subjects_dict[t1_metric]['screenshot'] = screenshot_path
    subjects_dict[t1_metric]['stats'] = summary_html
    return subjects_dict


def main():
    parser = _build_arg_parser()
    args = parser.parse_args()

    t1_warped = get_files_from_folder(args.t1_warped)
    rgb = get_files_from_folder(args.rgb)
    wm = get_files_from_folder(args.wm)
    gm = get_files_from_folder(args.gm)
    csf = get_files_from_folder(args.csf)

    if not len(t1_warped) == len(rgb) == len(wm) ==\
            len(gm) == len(csf):
        parser.error("Not the same number of images in input.")

    all_images = np.concatenate([t1_warped, rgb, wm, gm, csf])
    assert_inputs_exist(parser, all_images)
    assert_outputs_exist(parser, args, [args.output_report, "data", "libs"])

    if os.path.exists("data"):
        shutil.rmtree("data")
    os.makedirs("data")

    if os.path.exists("libs"):
        shutil.rmtree("libs")

    name = "Register T1"
    curr_metrics = ['Mean {} in WM'.format(name),
                    'Mean {} in GM'.format(name),
                    'Mean {} in CSF'.format(name),
                    'Max {} in WM'.format(name)]

    warning_dict = {}
    summary, stats = stats_mean_in_tissues(curr_metrics, t1_warped,
                                           wm, gm, csf)
    warning_dict[name] = analyse_qa(summary, stats, curr_metrics[:3])
    warning_list = np.concatenate([filenames for filenames in warning_dict[name].values()])
    warning_dict[name]['nb_warnings'] = len(np.unique(warning_list))

    graphs = []
    graph = graph_mean_in_tissues('Mean {}'.format(name), curr_metrics[:3],
                                  summary, args.online)
    graphs.append(graph)

    stats_html = dataframe_to_html(stats)
    summary_dict = {}
    summary_dict[name] = stats_html

    pool = Pool(args.nb_threads)
    subjects_dict_pool = pool.starmap(_subj_parralel,
                                      zip(t1_warped,
                                          rgb,
                                          itertools.repeat(summary),
                                          itertools.repeat(name),
                                          itertools.repeat(args.skip),
                                          itertools.repeat(args.nb_columns)))
    pool.close()
    pool.join()

    metrics_dict = {}
    subjects_dict = {}
    for dict_sub in subjects_dict_pool:
        for key in dict_sub:
            subjects_dict[key] = dict_sub[key]
    metrics_dict[name] = subjects_dict

    nb_subjects = len(t1_warped)
    report = Report(args.output_report)
    report.generate(title="Quality Assurance registration",
                    nb_subjects=nb_subjects, summary_dict=summary_dict,
                    graph_array=graphs, metrics_dict=metrics_dict,
                    warning_dict=warning_dict,
                    online=args.online)


if __name__ == '__main__':
    main()
