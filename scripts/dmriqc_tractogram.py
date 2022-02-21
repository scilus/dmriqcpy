#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import os
import shutil
from functools import partial

import numpy as np

from dmriqcpy.io.report import Report
from dmriqcpy.io.utils import (
    add_online_arg,
    add_overwrite_arg,
    assert_inputs_exist,
    assert_outputs_exist,
    assert_list_arguments_equal_size,
    add_nb_threads_arg,
    clean_output_directories,
    list_files_from_paths,
)
from dmriqcpy.reporting.report import (
    generate_metric_reports_parallel,
    generate_report_package,
    get_tractogram_qa_stats_and_graph,
)
from dmriqcpy.viz.utils import dataframe_to_html


DESCRIPTION = """
Compute the tractogram report in HTML format.
"""


def _build_arg_parser():
    p = argparse.ArgumentParser(
        description=DESCRIPTION, formatter_class=argparse.RawTextHelpFormatter
    )

    p.add_argument("output_report", help="HTML report")
    p.add_argument(
        "--tractograms",
        nargs="+",
        required=True,
        help="Tractograms in format supported by Nibabel",
    )
    p.add_argument("--t1", nargs="+", required=True, help="Folder or list of T1 images in Nifti format")

    add_online_arg(p)
    add_nb_threads_arg(p)
    add_overwrite_arg(p)

    return p


def main():
    parser = _build_arg_parser()
    args = parser.parse_args()

    t1 = list_files_from_paths(args.t1)
    tractograms = list_files_from_paths(args.tractograms)

    assert_list_arguments_equal_size(parser, t1, tractograms)
    all_images = np.concatenate([tractograms, t1])
    assert_inputs_exist(parser, all_images)
    assert_outputs_exist(parser, args, [args.output_report, "data", "libs"])
    clean_output_directories()

    name = "Tracking"
    nb_subjects = len(tractograms)

    summary, stats, qa_report, qa_graph = get_tractogram_qa_stats_and_graph(
        tractograms, args.online
    )

    warning_dict = {name: qa_report}
    summary_dict = {name: dataframe_to_html(stats)}

    metrics_dict = {
        name: generate_metric_reports_parallel(
            zip(tractograms, t1),
            args.nb_threads,
            nb_subjects // args.nb_threads,
            report_package_generation_fn=partial(
                generate_report_package,
                stats_summary=summary,
                metric_is_tracking=True
            ),
        )
    }

    report = Report(args.output_report)
    report.generate(
        title="Quality Assurance tractograms",
        nb_subjects=nb_subjects,
        summary_dict=summary_dict,
        graph_array=[qa_graph],
        metrics_dict=metrics_dict,
        warning_dict=warning_dict,
        online=args.online,
    )


if __name__ == "__main__":
    main()
