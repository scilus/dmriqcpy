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
from dmriqcpy.viz.screenshot import screenshot_mosaic_wrapper
from dmriqcpy.viz.utils import analyse_qa, dataframe_to_html


DESCRIPTION = """
Compute the FODF report in HTML format.
"""


def _build_arg_parser():
    p = argparse.ArgumentParser(description=DESCRIPTION,
                                formatter_class=argparse.RawTextHelpFormatter)

    p.add_argument('output_report',
                   help='HTML report')

    p.add_argument('--afd_max', nargs='+', required=True,
                   help='Folder or list of AFD max images in Nifti format.')

    p.add_argument('--afd_sum', nargs='+', required=True,
                   help='Folder or list of AFD sum images in Nifti format.')

    p.add_argument('--afd_total', nargs='+', required=True,
                   help='Folder or list of AFD total images in Nifti format.')

    p.add_argument('--nufo', nargs='+', required=True,
                   help='Folder or list of NUFO max images in Nifti format.')

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


def _subj_parralel(subj_metric, summary, name, skip, nb_columns):
    subjects_dict = {}
    screenshot_path = screenshot_mosaic_wrapper(subj_metric,
                                                output_prefix=name,
                                                directory="data", skip=skip,
                                                nb_columns=nb_columns)

    summary_html = dataframe_to_html(summary.loc[subj_metric])
    subjects_dict[subj_metric] = {}
    subjects_dict[subj_metric]['screenshot'] = screenshot_path
    subjects_dict[subj_metric]['stats'] = summary_html
    return subjects_dict


def main():
    parser = _build_arg_parser()
    args = parser.parse_args()

    afd_max = get_files_from_folder(args.afd_max)
    afd_sum = get_files_from_folder(args.afd_sum)
    afd_total = get_files_from_folder(args.afd_total)
    nufo = get_files_from_folder(args.nufo)
    wm = get_files_from_folder(args.wm)
    gm = get_files_from_folder(args.gm)
    csf = get_files_from_folder(args.csf)

    if not len(afd_max) == len(afd_sum) == len(afd_total) ==\
            len(nufo) == len(wm) == len(gm) == len(csf):
        parser.error("Not the same number of images in input.")

    all_images = np.concatenate([afd_max, afd_sum, afd_total,
                                 nufo, wm, gm, csf])
    assert_inputs_exist(parser, all_images)
    assert_outputs_exist(parser, args, [args.output_report, "data", "libs"])

    if os.path.exists("data"):
        shutil.rmtree("data")
    os.makedirs("data")

    if os.path.exists("libs"):
        shutil.rmtree("libs")

    metrics_names = [[afd_max, 'AFD_max'], [afd_sum, 'AFD_sum'],
                     [afd_total, 'AFD_total'], [nufo, 'NUFO']]
    metrics_dict = {}
    summary_dict = {}
    graphs = []
    warning_dict = {}
    for metrics, name in metrics_names:
        subjects_dict = {}
        curr_metrics = ['Mean {} in WM'.format(name),
                        'Mean {} in GM'.format(name),
                        'Mean {} in CSF'.format(name),
                        'Max {} in WM'.format(name)]

        summary, stats = stats_mean_in_tissues(curr_metrics, metrics, wm,
                                               gm, csf)
        warning_dict[name] = analyse_qa(summary, stats, curr_metrics[:3])
        warning_list = np.concatenate([filenames for filenames in warning_dict[name].values()])
        warning_dict[name]['nb_warnings'] = len(np.unique(warning_list))

        graph = graph_mean_in_tissues('Mean {}'.format(name), curr_metrics[:3],
                                      summary, args.online)
        graphs.append(graph)

        stats_html = dataframe_to_html(stats)
        summary_dict[name] = stats_html
        pool = Pool(args.nb_threads)
        subjects_dict_pool = pool.starmap(_subj_parralel,
                                          zip(metrics,
                                              itertools.repeat(summary),
                                              itertools.repeat(name),
                                              itertools.repeat(args.skip),
                                              itertools.repeat(args.nb_columns)))

        pool.close()
        pool.join()

        for dict_sub in subjects_dict_pool:
            for key in dict_sub:
                subjects_dict[key] = dict_sub[key]
        metrics_dict[name] = subjects_dict

    nb_subjects = len(afd_max)
    report = Report(args.output_report)
    report.generate(title="Quality Assurance FODF metrics",
                    nb_subjects=nb_subjects, summary_dict=summary_dict,
                    graph_array=graphs, metrics_dict=metrics_dict,
                    warning_dict=warning_dict,
                    online=args.online)


if __name__ == '__main__':
    main()
