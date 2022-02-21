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
    get_qa_stats_and_graph_in_tissues,
)
from dmriqcpy.viz.utils import dataframe_to_html


DESCRIPTION = """
Compute the registration report in HTML format.
"""


def _build_arg_parser():
    p = argparse.ArgumentParser(
        description=DESCRIPTION, formatter_class=argparse.RawTextHelpFormatter
    )

    p.add_argument("output_report", help="HTML report")
    p.add_argument(
        "--t1_warped",
        nargs="+",
        required=True,
        help="Folder or list of T1 registered images in Nifti format",
    )

    p.add_argument(
        "--rgb", nargs="+", required=True, help="Folder or list of RGB images in Nifti format"
    )

    p.add_argument(
        "--wm", nargs="+", required=True, help="Folder or list of WM mask in Nifti format"
    )

    p.add_argument(
        "--gm", nargs="+", required=True, help="Folder or list of GM mask in Nifti format"
    )

    p.add_argument(
        "--csf", nargs="+", required=True, help="Folder or list of CSF mask in Nifti format"
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

    t1_warped = list_files_from_paths(args.t1_warped)
    rgb = list_files_from_paths(args.rgb)
    wm = list_files_from_paths(args.wm)
    gm = list_files_from_paths(args.gm)
    csf = list_files_from_paths(args.csf)

    assert_list_arguments_equal_size(parser, t1_warped, rgb, wm, gm, csf)
    all_images = np.concatenate([t1_warped, rgb, wm, gm, csf])
    assert_inputs_exist(parser, all_images)
    assert_outputs_exist(parser, args, [args.output_report, "data", "libs"])
    clean_output_directories()

    name = "Register T1"
    nb_subjects = len(t1_warped)

    summary, stats, qa_report, qa_graph = get_qa_stats_and_graph_in_tissues(
        t1_warped, name, wm, gm, csf, args.online
    )

    warning_dict = {name: qa_report}
    summary_dict = {name: dataframe_to_html(stats)}

    metrics_dict = {
        name: generate_metric_reports_parallel(
            zip(t1_warped, rgb),
            args.nb_threads,
            nb_subjects // args.nb_threads,
            report_package_generation_fn=partial(
                generate_report_package,
                stats_summary=summary,
                skip=args.skip,
                nb_columns=args.nb_columns,
            ),
        )
    }

    report = Report(args.output_report)
    report.generate(
        title="Quality Assurance registration",
        nb_subjects=nb_subjects,
        summary_dict=summary_dict,
        graph_array=[qa_graph],
        metrics_dict=metrics_dict,
        warning_dict=warning_dict,
        online=args.online,
    )


if __name__ == "__main__":
    main()
