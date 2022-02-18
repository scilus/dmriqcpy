#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import os
import shutil

import numpy as np

from dmriqcpy.analysis.stats import stats_frf
from dmriqcpy.io.report import Report
from dmriqcpy.io.utils import (
    add_online_arg,
    add_overwrite_arg,
    assert_inputs_exist,
    assert_outputs_exist,
    list_files_from_paths,
)
from dmriqcpy.viz.graph import graph_frf_eigen, graph_frf_b0
from dmriqcpy.viz.utils import analyse_qa, dataframe_to_html


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

    if os.path.exists("libs"):
        shutil.rmtree("libs")

    name = "FRF"
    metrics_names = ["Mean Eigen value 1", "Mean Eigen value 2", "Mean B0"]

    warning_dict = {}
    summary, stats = stats_frf(metrics_names, frf)
    warning_dict[name] = analyse_qa(summary, stats, metrics_names)
    warning_list = np.concatenate(
        [filenames for filenames in warning_dict[name].values()]
    )
    warning_dict[name]["nb_warnings"] = len(set(warning_list))

    graphs = []
    graphs.append(graph_frf_eigen("EigenValues", metrics_names, summary,
                                  args.online))
    graphs.append(graph_frf_b0("Mean B0", metrics_names, summary, args.online))


    summary_dict = {}
    stats_html = dataframe_to_html(stats)
    summary_dict[name] = stats_html

    metrics_dict = {}
    subjects_dict = {}
    for subj_metric in frf:
        curr_subj = os.path.basename(subj_metric).split('.')[0]
        summary_html = dataframe_to_html(summary.loc[curr_subj].to_frame())
        subjects_dict[curr_subj] = {}
        subjects_dict[curr_subj]["stats"] = summary_html
    metrics_dict[name] = subjects_dict

    nb_subjects = len(frf)
    report = Report(args.output_report)
    report.generate(
        title="Quality Assurance FRF",
        nb_subjects=nb_subjects,
        summary_dict=summary_dict,
        graph_array=graphs,
        metrics_dict=metrics_dict,
        warning_dict=warning_dict,
        online=args.online,
    )


if __name__ == "__main__":
    main()
