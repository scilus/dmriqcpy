#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import os
import shutil

import itertools
from functools import partial
import numpy as np

from dmriqcpy.io.report import Report
from dmriqcpy.io.utils import (
    add_online_arg,
    add_overwrite_arg,
    assert_inputs_exist,
    assert_outputs_exist,
    list_files_from_paths,
    add_skip_arg,
    add_nb_columns_arg,
    add_nb_threads_arg,
    assert_list_arguments_equal_size,
    clean_output_directories,
)
from dmriqcpy.reporting.report import (
    generate_metric_reports_parallel,
    generate_report_package,
    get_generic_qa_stats_and_graph,
)
from dmriqcpy.viz.utils import dataframe_to_html


DESCRIPTION = """
Compute the brain extraction report in HTML format.
"""


def _build_arg_parser():
    p = argparse.ArgumentParser(
        description=DESCRIPTION, formatter_class=argparse.RawTextHelpFormatter
    )

    p.add_argument("image_type", help="Type of image (e.g. B0).")
    p.add_argument("output_report", help="Filename of QC report (in html format).")
    p.add_argument(
        "--no_bet",
        nargs="+",
        required=True,
        help="A folder or a list of images with the skull in Nifti format.",
    )
    p.add_argument(
        "--bet_mask",
        nargs="+",
        required=True,
        help="A folder or a list of images of brain extraction masks in Nifti format.",
    )

    add_skip_arg(p)
    add_nb_columns_arg(p)
    add_nb_threads_arg(p)
    add_online_arg(p)
    add_overwrite_arg(p)

    return p


def main():
    parser = _build_arg_parser()
    args = parser.parse_args()

    images_no_bet = list_files_from_paths(args.no_bet)
    images_bet_mask = list_files_from_paths(args.bet_mask)
    assert_list_arguments_equal_size(parser, images_no_bet, images_bet_mask)

    all_images = np.concatenate([images_no_bet, images_bet_mask])
    assert_inputs_exist(parser, all_images)
    assert_outputs_exist(parser, args, [args.output_report, "data", "libs"])
    clean_output_directories()

    metrics, name = images_no_bet, args.image_type
    nb_subjects = len(args.images_no_bet)

    summary, stats, qa_report, qa_graphs = get_generic_qa_stats_and_graph(
        metrics, name, args.online
    )
    warning_dict = {name: qa_report}
    summary_dict = {name: dataframe_to_html(stats)}

    metrics_dict = {
        name: generate_metric_reports_parallel(
            zip(images_no_bet, images_bet_mask),
            args.nb_threads,
            nb_subjects // args.nb_threads,
            report_package_generation_fn=partial(
                generate_report_package,
                stats_summary=summary,
                skip=args.skip,
                nb_columns=args.nb_columns,
                blend_is_mask=True,
            ),
        )
    }

    report = Report(args.output_report)
    report.generate(
        title="Quality Assurance BET " + args.image_type,
        nb_subjects=nb_subjects,
        summary_dict=summary_dict,
        graph_array=[qa_graphs],
        metrics_dict=metrics_dict,
        warning_dict=warning_dict,
        online=args.online,
    )


if __name__ == "__main__":
    main()
