#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import os
import shutil

from dmriqcpy.io.report import Report
from dmriqcpy.io.utils import (
    add_online_arg,
    add_overwrite_arg,
    assert_inputs_exist,
    assert_outputs_exist,
    clean_output_directories,
    list_files_from_paths,
)
from dmriqcpy.reporting.report import get_frf_qa_stats_and_graph
from dmriqcpy.viz.utils import dataframe_to_html


DESCRIPTION = """
Compute the fiber response function (frf) report in HTML format.
"""


def _build_arg_parser():
    p = argparse.ArgumentParser(
        description=DESCRIPTION, formatter_class=argparse.RawTextHelpFormatter
    )

    p.add_argument(
        "frf",
        nargs="+",
        help="Folder or list of fiber response function (frf) files (in txt format).",
    )
    p.add_argument("output_report", help="Filename of QC report (in html format).")

    add_online_arg(p)
    add_overwrite_arg(p)

    return p


def main():
    parser = _build_arg_parser()
    args = parser.parse_args()

    frf = list_files_from_paths(args.frf)

    assert_inputs_exist(parser, frf)
    assert_outputs_exist(parser, args, [args.output_report, "libs"])
    clean_output_directories(False)

    name = "FRF"
    nb_subjects = len(frf)

    summary, stats, qa_report, qa_graph = get_frf_qa_stats_and_graph(frf, args.online)
    warning_dict = {name: qa_report}
    summary_dict = {name: dataframe_to_html(stats)}

    metrics_dict = {
        name: {
            subj_metric: {"stats": dataframe_to_html(summary.loc[subj_metric])}
            for subj_metric in frf
        }
    }

    report = Report(args.output_report)
    report.generate(
        title="Quality Assurance FRF",
        nb_subjects=nb_subjects,
        summary_dict=summary_dict,
        graph_array=[qa_graph],
        metrics_dict=metrics_dict,
        warning_dict=warning_dict,
        online=args.online,
    )


if __name__ == "__main__":
    main()
