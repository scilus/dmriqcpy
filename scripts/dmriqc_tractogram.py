#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import os
import shutil

import numpy as np


from dmriqcpy.io.report import Report
from dmriqcpy.io.utils import (add_online_arg, add_overwrite_arg,
                               assert_inputs_exist, assert_outputs_exist)
from dmriqcpy.analysis.stats import stats_tractogram
from dmriqcpy.viz.graph import graph_tractogram
from dmriqcpy.viz.screenshot import screenshot_tracking
from dmriqcpy.viz.utils import analyse_qa, dataframe_to_html


DESCRIPTION = """
Compute the tractogram report in HTML format.
"""


def _build_arg_parser():
    p = argparse.ArgumentParser(description=DESCRIPTION,
                                formatter_class=argparse.RawTextHelpFormatter)

    p.add_argument('output_report',
                   help='HTML report')

    p.add_argument('--tractograms', nargs='+',
                   help='Tractograms in format supported by Nibabel')

    p.add_argument('--t1', nargs='+',
                   help='T1 images in Nifti format')

    add_online_arg(p)
    add_overwrite_arg(p)

    return p


def main():
    parser = _build_arg_parser()
    args = parser.parse_args()

    if not len(args.tractograms) == len(args.t1):
        parser.error("Not the same number of images in input.")

    all_images = np.concatenate([args.tractograms, args.t1])
    assert_inputs_exist(parser, all_images)
    assert_outputs_exist(parser, args, [args.output_report, "data", "libs"])

    if os.path.exists("data"):
        shutil.rmtree("data")
    os.makedirs("data")

    if os.path.exists("libs"):
        shutil.rmtree("libs")

    name = "Tracking"
    columns = ["Nb streamlines"]

    warning_dict = {}
    summary, stats = stats_tractogram(columns, args.tractograms)
    warning_dict[name] = analyse_qa(summary, stats, ["Nb streamlines"])
    warning_list = np.concatenate([filenames for filenames in warning_dict[name].values()])
    warning_dict[name]['nb_warnings'] = len(np.unique(warning_list))

    graphs = []
    graph = graph_tractogram("Tracking", columns, summary, args.online)
    graphs.append(graph)

    summary_dict = {}
    stats_html = dataframe_to_html(stats)
    summary_dict[name] = stats_html

    metrics_dict = {}
    subjects_dict = {}
    for subj_metric, t1 in zip(args.tractograms, args.t1):
        screenshot_path = screenshot_tracking(subj_metric, t1, "data")
        summary_html = dataframe_to_html(summary.loc[subj_metric])
        subjects_dict[subj_metric] = {}
        subjects_dict[subj_metric]['screenshot'] = screenshot_path
        subjects_dict[subj_metric]['stats'] = summary_html
    metrics_dict[name] = subjects_dict

    nb_subjects = len(args.tractograms)
    report = Report(args.output_report)
    report.generate(title="Quality Assurance tractograms",
                    nb_subjects=nb_subjects, summary_dict=summary_dict,
                    graph_array=graphs, metrics_dict=metrics_dict,
                    warning_dict=warning_dict)


if __name__ == '__main__':
    main()
