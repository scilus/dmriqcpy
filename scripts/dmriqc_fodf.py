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
Compute the FODF report in HTML format.
"""


def _build_arg_parser():
    p = argparse.ArgumentParser(
        description=DESCRIPTION, formatter_class=argparse.RawTextHelpFormatter
    )

    p.add_argument("output_report", help="HTML report")
    p.add_argument(
        "--afd_max",
        nargs="+",
        required=True,
        help="Folder or list of AFD max images in Nifti format",
    )
    p.add_argument(
        "--afd_sum",
        nargs="+",
        required=True,
        help="Folder or list of AFD sum images in Nifti format",
    )
    p.add_argument(
        "--afd_total",
        nargs="+",
        required=True,
        help="Folder or list of AFD total images in Nifti format",
    )
    p.add_argument(
        "--nufo",
        nargs="+",
        required=True,
        help="Folder or list of NUFO max images in Nifti format",
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

    (
        afd_max,
        afd_sum,
        afd_total,
        nufo,
        wm,
        gm,
        csf
    ) = images = [
        list_files_from_paths(args.afd_max),
        list_files_from_paths(args.afd_sum),
        list_files_from_paths(args.afd_total),
        list_files_from_paths(args.nufo),
        list_files_from_paths(args.wm),
        list_files_from_paths(args.gm),
        list_files_from_paths(args.csf)
    ]

    assert_list_arguments_equal_size(parser, *images)
    all_images = np.concatenate(images)
    assert_inputs_exist(parser, all_images)
    assert_outputs_exist(parser, args, [args.output_report, "data", "libs"])
    clean_output_directories()

    metrics_dict = {}
    summary_dict = {}
    graphs = []
    warning_dict = {}
    for metrics, name in [
        [afd_max, "AFD_max"],
        [afd_sum, "AFD_sum"],
        [afd_total, "AFD_total"],
        [nufo, "NUFO"],
    ]:
        summary, stats, qa_report, qa_graph = get_qa_stats_and_graph_in_tissues(
            metrics, name, wm, gm, csf, args.online
        )
        warning_dict[name] = qa_report
        summary_dict[name] = dataframe_to_html(stats)
        graphs.append(qa_graph)

        metrics_dict[name] = generate_metric_reports_parallel(
            zip(metrics),
            args.nb_threads,
            len(metrics) // args.nb_threads,
            report_package_generation_fn=partial(
                generate_report_package,
                stats_summary=summary,
                skip=args.skip,
                nb_columns=args.nb_columns,
            ),
        )

    nb_subjects = len(afd_max)
    report = Report(args.output_report)
    report.generate(
        title="Quality Assurance FODF metrics",
        nb_subjects=nb_subjects,
        summary_dict=summary_dict,
        graph_array=graphs,
        metrics_dict=metrics_dict,
        warning_dict=warning_dict,
        online=args.online,
    )


if __name__ == "__main__":
    main()
