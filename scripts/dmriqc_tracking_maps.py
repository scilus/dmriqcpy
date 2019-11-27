#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import os
import shutil

import itertools
from multiprocessing import Pool
import numpy as np

from dmriqcpy.io.report import Report
from dmriqcpy.viz.graph import graph_mask_volume
from dmriqcpy.analysis.stats import stats_mask_volume
from dmriqcpy.viz.screenshot import screenshot_mosaic_wrapper
from dmriqcpy.viz.utils import analyse_qa, dataframe_to_html
from dmriqcpy.io.utils import add_overwrite_arg, assert_inputs_exist,\
                              assert_outputs_exist

DESCRIPTION = """
Compute the tracking maps report in HTML format.
 """


def _build_arg_parser():
    p = argparse.ArgumentParser(description=DESCRIPTION,
                                formatter_class=argparse.RawTextHelpFormatter)

    p.add_argument('tracking_type', choices=["pft", "local"],
                   help='Tracking type')

    p.add_argument('output_report',
                   help='HTML report')

    p.add_argument('--seeding_mask', nargs='+', required=True,
                   help='Seeding mask in Nifti format')

    p.add_argument('--tracking_mask', nargs='+',
                   help='Tracking mask in Nifti format')

    p.add_argument('--map_include', nargs='+',
                   help='Map include in Nifti format')

    p.add_argument('--map_exclude', nargs='+',
                   help='Map exlude in Nifti format')

    p.add_argument('--skip', default=2, type=int,
                   help='Number of images skipped to build the mosaic. [%(default)s]')

    p.add_argument('--nb_columns', default=12, type=int,
                   help='Number of columns for the mosaic. [%(default)s]')

    p.add_argument('--nb_threads', type=int, default=1,
                   help='Number of threads. [%(default)s]')

    add_overwrite_arg(p)

    return p


def _subj_parralel(subj_metric, summary, name, skip, nb_columns):
    subjects_dict = {}
    screenshot_path = screenshot_mosaic_wrapper(subj_metric, output_prefix=name,
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

    if args.tracking_type == "local":
        if not len(args.seeding_mask) == len(args.tracking_mask):
            parser.error("Not the same number of images in input.")
        all_images = np.concatenate([args.seeding_mask, args.tracking_mask])
    else:
        if not len(args.seeding_mask) == len(args.map_include) ==\
            len(args.map_exclude):
            parser.error("Not the same number of images in input.")
        all_images = np.concatenate([args.seeding_mask, args.map_include,
                                     args.map_exclude])

    assert_inputs_exist(parser, all_images)
    assert_outputs_exist(parser, args, [args.output_report, "data", "libs"])

    if os.path.exists("data"):
        shutil.rmtree("data")
    os.makedirs("data")

    if os.path.exists("libs"):
        shutil.rmtree("libs")

    if args.tracking_type == "local":
        metrics_names = [[args.seeding_mask, 'Seeding mask'],
                         [args.tracking_mask, 'Tracking mask']]
    else:
        metrics_names = [[args.seeding_mask, 'Seeding mask'],
                         [args.map_include, 'Map include'],
                         [args.map_exclude, 'Maps exclude']]
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
                                  columns,
                                  summary)
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
                subjects_dict[key] = dict_sub[key]
        metrics_dict[name] = subjects_dict

    nb_subjects = len(args.seeding_mask)
    report = Report(args.output_report)
    report.generate(title="Quality Assurance tracking maps",
                    nb_subjects=nb_subjects, summary_dict=summary_dict,
                    graph_array=graphs, metrics_dict=metrics_dict,
                    warning_dict=warning_dict)


if __name__ == '__main__':
    main()
