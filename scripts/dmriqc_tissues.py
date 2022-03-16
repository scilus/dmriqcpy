#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import os
import shutil

import itertools
from multiprocessing import Pool
import numpy as np


from dmriqcpy.analysis.stats import stats_mask_volume
from dmriqcpy.io.report import Report
from dmriqcpy.io.utils import (add_online_arg, add_overwrite_arg,
                               assert_inputs_exist, assert_outputs_exist,
                               list_files_from_paths)
from dmriqcpy.viz.graph import graph_mask_volume
from dmriqcpy.viz.screenshot import screenshot_mosaic_wrapper
from dmriqcpy.viz.utils import analyse_qa, dataframe_to_html


DESCRIPTION = """
Compute the tissue report in HTML format.
 """


def _build_arg_parser():
    p = argparse.ArgumentParser(description=DESCRIPTION,
                                formatter_class=argparse.RawTextHelpFormatter)

    p.add_argument('output_report',
                   help='HTML report')

    p.add_argument('--wm', nargs='+', required=True,
                   help='WM mask in Nifti format')

    p.add_argument('--gm', nargs='+', required=True,
                   help='GM mask in Nifti format')

    p.add_argument('--csf', nargs='+', required=True,
                   help='CSF mask in Nifti format')

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
    curr_key = os.path.basename(subj_metric).split('.')[0]
    screenshot_path = screenshot_mosaic_wrapper(subj_metric,
                                                output_prefix=name,
                                                directory="data", skip=skip,
                                                nb_columns=nb_columns)

    summary_html = dataframe_to_html(summary.loc[curr_key])
    subjects_dict[curr_key] = {}
    subjects_dict[curr_key]['screenshot'] = screenshot_path
    subjects_dict[curr_key]['stats'] = summary_html
    return subjects_dict


def main():
    parser = _build_arg_parser()
    args = parser.parse_args()

    wm = list_files_from_paths(args.wm)
    gm = list_files_from_paths(args.gm)
    csf = list_files_from_paths(args.csf)

    if not len(wm) == len(gm) == len(csf):
        parser.error("Not the same number of images in input.")

    all_images = np.concatenate([wm, gm, csf])
    assert_inputs_exist(parser, all_images)
    assert_outputs_exist(parser, args, [args.output_report, "data", "libs"])

    if os.path.exists("data"):
        shutil.rmtree("data")
    os.makedirs("data")

    if os.path.exists("libs"):
        shutil.rmtree("libs")

    metrics_names = [[wm, 'WM mask'],
                     [gm, 'GM mask'],
                     [csf, 'CSF mask']]
    metrics_dict = {}
    summary_dict = {}
    graphs = []
    warning_dict = {}
    for metrics, name in metrics_names:
        columns = ["{} volume".format(name)]
        summary, stats = stats_mask_volume(columns, metrics)

        warning_dict[name] = analyse_qa(summary, stats, columns)
        warning_list = np.concatenate([filenames for filenames in warning_dict[name].values()])
        warning_dict[name]['nb_warnings'] = len(np.unique(warning_list))

        graph = graph_mask_volume('{} mean volume'.format(name),
                                  columns, summary, args.online)
        graphs.append(graph)

        stats_html = dataframe_to_html(stats)
        summary_dict[name] = stats_html

        subjects_dict = {}
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
                curr_key = os.path.basename(key).split('.')[0]
                subjects_dict[curr_key] = dict_sub[curr_key]
        metrics_dict[name] = subjects_dict

    nb_subjects = len(wm)
    report = Report(args.output_report)
    report.generate(title="Quality Assurance tissue segmentation",
                    nb_subjects=nb_subjects, summary_dict=summary_dict,
                    graph_array=graphs, metrics_dict=metrics_dict,
                    warning_dict=warning_dict,
                    online=args.online)


if __name__ == '__main__':
    main()
