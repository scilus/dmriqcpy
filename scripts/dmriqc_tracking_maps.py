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
                               list_files_from_paths, add_skip_arg,
                               add_nb_columns_arg, add_nb_threads_arg)
from dmriqcpy.viz.graph import graph_mask_volume
from dmriqcpy.viz.screenshot import screenshot_mosaic_wrapper
from dmriqcpy.viz.utils import analyse_qa, dataframe_to_html


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
                   help='Folder or list of seeding mask in Nifti format')

    p.add_argument('--tracking_mask', nargs='+',
                   help='Folder or list of tracking mask in Nifti format')

    p.add_argument('--map_include', nargs='+',
                   help='Folder or list of map include in Nifti format')

    p.add_argument('--map_exclude', nargs='+',
                   help='Folder or list of map exlude in Nifti format')

    add_skip_arg(p)
    add_nb_columns_arg(p)
    add_nb_threads_arg(p)
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

    summary_html = dataframe_to_html(summary.loc[curr_key].to_frame())
    subjects_dict[curr_key] = {}
    subjects_dict[curr_key]['screenshot'] = screenshot_path
    subjects_dict[curr_key]['stats'] = summary_html
    return subjects_dict


def main():
    parser = _build_arg_parser()
    args = parser.parse_args()

    seeding_mask = list_files_from_paths(args.seeding_mask)

    if args.tracking_type == "local":
        tracking_mask = list_files_from_paths(args.tracking_mask)
        if not len(seeding_mask) == len(tracking_mask):
            parser.error("Not the same number of images in input.")
        all_images = np.concatenate([args.seeding_mask, args.tracking_mask])
    else:
        map_include = list_files_from_paths(args.map_include)
        map_exclude = list_files_from_paths(args.map_exclude)
        if not len(seeding_mask) == len(map_include) ==\
                len(map_exclude):
            parser.error("Not the same number of images in input.")
        all_images = np.concatenate([seeding_mask, map_include,
                                     map_exclude])

    assert_inputs_exist(parser, all_images)
    assert_outputs_exist(parser, args, [args.output_report, "data", "libs"])

    if os.path.exists("data"):
        shutil.rmtree("data")
    os.makedirs("data")

    if os.path.exists("libs"):
        shutil.rmtree("libs")

    if args.tracking_type == "local":
        metrics_names = [[seeding_mask, 'Seeding mask'],
                         [tracking_mask, 'Tracking mask']]
    else:
        metrics_names = [[seeding_mask, 'Seeding mask'],
                         [map_include, 'Map include'],
                         [map_exclude, 'Maps exclude']]
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

    nb_subjects = len(seeding_mask)
    report = Report(args.output_report)
    report.generate(title="Quality Assurance tracking maps",
                    nb_subjects=nb_subjects, summary_dict=summary_dict,
                    graph_array=graphs, metrics_dict=metrics_dict,
                    warning_dict=warning_dict,
                    online=args.online)


if __name__ == '__main__':
    main()
