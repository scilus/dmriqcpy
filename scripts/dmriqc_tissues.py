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
    get_mask_qa_stats_and_graph,
)
from dmriqcpy.viz.utils import dataframe_to_html


DESCRIPTION = """
Compute the tissue report in HTML format.
 """


def _build_arg_parser():
    p = argparse.ArgumentParser(
        description=DESCRIPTION, formatter_class=argparse.RawTextHelpFormatter
    )

    p.add_argument("output_report", help="HTML report")
    p.add_argument("--wm", nargs="+", required=True, help="WM mask in Nifti format")
    p.add_argument("--gm", nargs="+", required=True, help="GM mask in Nifti format")
    p.add_argument("--csf", nargs="+", required=True, help="CSF mask in Nifti format")

    add_skip_arg(p)
    add_nb_columns_arg(p)
    add_nb_threads_arg(p)
    add_online_arg(p)
    add_overwrite_arg(p)

    return p


def main():
    parser = _build_arg_parser()
    args = parser.parse_args()

    wm = list_files_from_paths(args.wm)
    gm = list_files_from_paths(args.gm)
    csf = list_files_from_paths(args.csf)

    assert_list_arguments_equal_size(parser, wm, gm, csf)
    all_images = np.concatenate([wm, gm, csf])
    assert_inputs_exist(parser, all_images)
    assert_outputs_exist(parser, args, [args.output_report, "data", "libs"])
    clean_output_directories()

    metrics_names = [
        [wm, "WM mask"],
        [gm, "GM mask"],
        [csf, "CSF mask"],
    ]
    metrics_dict = {}
    summary_dict = {}
    graphs = []
    warning_dict = {}
    for metrics, name in [[args.wm, "WM mask"], [args.gm, "GM mask"], [args.csf, "CSF mask"]]:
        summary, stats, qa_report, qa_graph = get_mask_qa_stats_and_graph(
            metrics, name, args.online
        )

        warning_dict[name] = qa_report
        summary_dict[name] = dataframe_to_html(stats)
        graphs.append(qa_graph)

        metrics_dict[name] = generate_metric_reports_parallel(
            zip(metrics),
            args.nb_threads,
            report_package_generation_fn=partial(
                generate_report_package,
                stats_summary=summary,
                skip=args.skip,
                nb_columns=args.nb_columns,
            ),
        )

    nb_subjects = len(wm)
    report = Report(args.output_report)
    report.generate(
        title="Quality Assurance tissue segmentation",
        nb_subjects=nb_subjects,
        summary_dict=summary_dict,
        graph_array=graphs,
        metrics_dict=metrics_dict,
        warning_dict=warning_dict,
        online=args.online,
    )


if __name__ == "__main__":
    main()
