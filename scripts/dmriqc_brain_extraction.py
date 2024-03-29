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
                               list_files_from_paths)
from dmriqcpy.analysis.stats import stats_mean_median
from dmriqcpy.viz.graph import graph_mean_median
from dmriqcpy.viz.screenshot import screenshot_mosaic_blend
from dmriqcpy.viz.utils import analyse_qa, dataframe_to_html


DESCRIPTION = """
Compute the brain extraction report in HTML format.
"""


def _build_arg_parser():
    p = argparse.ArgumentParser(description=DESCRIPTION,
                                formatter_class=argparse.RawTextHelpFormatter)
    p.add_argument('image_type',
                   help='Type of image (e.g. B0).')

    p.add_argument('output_report',
                   help='Filename of QC report (in html format).')

    p.add_argument('--no_bet', nargs='+', required=True,
                   help='A folder or a list of images with the skull in'
                        ' Nifti format.')
    p.add_argument('--bet_mask', nargs='+', required=True,
                   help='Folder or a list of images of brain extraction masks'
                        ' in Nifti format.')

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


def _subj_parralel(images_no_bet, images_bet_mask, name, skip,
                   summary, nb_columns):
    subjects_dict = {}
    for subj_metric, mask in zip(images_no_bet, images_bet_mask):
        curr_key = os.path.basename(subj_metric).split('.')[0]
        screenshot_path = screenshot_mosaic_blend(subj_metric, mask,
                                                  output_prefix=name,
                                                  directory="data",
                                                  blend_val=0.3,
                                                  skip=skip,
                                                  nb_columns=nb_columns,
                                                  is_mask=True)

        summary_html = dataframe_to_html(summary.loc[curr_key].to_frame())
        subjects_dict[curr_key] = {}
        subjects_dict[curr_key]['screenshot'] = screenshot_path
        subjects_dict[curr_key]['stats'] = summary_html
    return subjects_dict


def main():
    parser = _build_arg_parser()
    args = parser.parse_args()

    images_no_bet = list_files_from_paths(args.no_bet)
    images_bet_mask = list_files_from_paths(args.bet_mask)

    if not len(images_no_bet) == len(images_bet_mask):
        parser.error("Not the same number of images in input.")

    all_images = np.concatenate([images_no_bet, images_bet_mask])
    assert_inputs_exist(parser, all_images)
    assert_outputs_exist(parser, args, [args.output_report, "data", "libs"])

    if os.path.exists("data"):
        shutil.rmtree("data")
    os.makedirs("data")

    if os.path.exists("libs"):
        shutil.rmtree("libs")

    metrics = images_no_bet
    name = args.image_type
    curr_metrics = ['Mean {}'.format(name),
                    'Median {}'.format(name)]

    summary, stats = stats_mean_median(curr_metrics, metrics)

    warning_dict = {}
    warning_dict[name] = analyse_qa(summary, stats, curr_metrics)
    warning_images = [filenames for filenames in warning_dict[name].values()]
    warning_list = np.concatenate([warning_images])
    warning_dict[name]['nb_warnings'] = len(np.unique(warning_list))

    graphs = []
    graph = graph_mean_median('Mean {}'.format(name), curr_metrics, summary,
                              args.online)
    graphs.append(graph)

    stats_html = dataframe_to_html(stats)
    summary_dict = {}
    summary_dict[name] = stats_html

    pool = Pool(args.nb_threads)
    subjects_dict_pool = pool.starmap(_subj_parralel,
        zip(np.array_split(np.array(images_no_bet), args.nb_threads),
            np.array_split(np.array(images_bet_mask), args.nb_threads),
            itertools.repeat(name), itertools.repeat(args.skip),
            itertools.repeat(summary), itertools.repeat(args.nb_columns)))

    pool.close()
    pool.join()

    metrics_dict = {}
    subjects_dict = {}
    for dict_sub in subjects_dict_pool:
        for key in dict_sub:
            subjects_dict[key] = dict_sub[key]
    metrics_dict[name] = subjects_dict

    nb_subjects = len(images_no_bet)
    report = Report(args.output_report)
    report.generate(title="Quality Assurance BET " + args.image_type,
                    nb_subjects=nb_subjects, summary_dict=summary_dict,
                    graph_array=graphs, metrics_dict=metrics_dict,
                    warning_dict=warning_dict,
                    online=args.online)


if __name__ == '__main__':
    main()
