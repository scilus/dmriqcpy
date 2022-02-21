#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
from functools import partial
import os
import shutil

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
    generate_report_package,
    generate_metric_reports_parallel,
    get_generic_qa_stats_and_graph,
)
from dmriqcpy.viz.screenshot import screenshot_fa_peaks
from dmriqcpy.viz.utils import dataframe_to_html

DESCRIPTION = """
Compute the DTI report in HTML format.
"""


def _build_arg_parser():
    p = argparse.ArgumentParser(
        description=DESCRIPTION, formatter_class=argparse.RawTextHelpFormatter
    )

    p.add_argument("output_report", help="HTML report")

    p.add_argument(
        "--fa", nargs="+", required=True, help="Folder or list of FA images in Nifti format"
    )

    p.add_argument(
        "--md", nargs="+", required=True, help="Folder or list of MD images in Nifti format"
    )

    p.add_argument(
        "--rd", nargs="+", required=True, help="Folder or list of RD images in Nifti format"
    )

    p.add_argument(
        "--ad", nargs="+", required=True, help="Folder or list of AD images in Nifti format"
    )

    p.add_argument(
        "--residual",
        nargs="+",
        required=True,
        help="Folder or list of residual images in Nifti format",
    )
    p.add_argument(
        "--evecs_v1",
        nargs="+",
        required=True,
        help="Folder or list of evecs v1 images in Nifti format",
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

    images = [
        list_files_from_paths(args.fa)
        list_files_from_paths(args.md)
        list_files_from_paths(args.rd)
        list_files_from_paths(args.ad)
        list_files_from_paths(args.residual)
        list_files_from_paths(args.evecs_v1)
        list_files_from_paths(args.wm)
        list_files_from_paths(args.gm)
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
        [args.fa, "FA"],
        [args.md, "MD"],
        [args.rd, "RD"],
        [args.ad, "AD"],
        [args.residual, "Residual"],
    ]:
        summary, stats, qa_report, qa_graph = get_generic_qa_stats_and_graph(
            metrics, name, args.online
        )
        warning_dict[name] = qa_report
        summary_dict[name] = dataframe_to_html(stats)
        graphs.append(qa_graph)

        cmap = "hot" if name == "Residual" else None
        metrics_dict[name] = generate_metric_reports_parallel(
            zip(metrics),
            args.nb_threads,
            len(metrics) // args.nb_threads,
            report_package_generation_fn=partial(
                generate_report_package,
                stats_summary=summary,
                skip=args.skip,
                nb_columns=args.nb_columns,
                cmap=cmap,
            ),
        )

    metrics_dict["Peaks"] = {
        os.path.basename(evecs).split('.')[0]: {
            "screenshot": screenshot_fa_peaks(fa, evecs, "data")
        }
        for fa, evecs in zip(args.fa, args.evecs_v1)
    }

    nb_subjects = len(fa)
    report = Report(args.output_report)
    report.generate(
        title="Quality Assurance DTI metrics",
        nb_subjects=nb_subjects,
        summary_dict=summary_dict,
        graph_array=graphs,
        metrics_dict=metrics_dict,
        warning_dict=warning_dict,
        online=args.online,
    )


if __name__ == "__main__":
    main()
