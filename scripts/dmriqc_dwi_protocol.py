#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import os
import shutil

import numpy as np
import pandas as pd

from dmriqcpy.analysis.utils import (
    dwi_protocol,
    read_protocol,
    identify_shells,
    get_bvecs_from_shells_idxs,
)
from dmriqcpy.io.report import Report
from dmriqcpy.io.utils import (
    add_online_arg,
    add_overwrite_arg,
    assert_inputs_exist,
    assert_outputs_exist,
    assert_list_arguments_equal_size,
    clean_output_directories,
    list_files_from_paths,
)
from dmriqcpy.reporting.report import get_qa_report
from dmriqcpy.viz.graph import (
    graph_directions_per_shells,
    graph_dwi_protocol,
    graph_subjects_per_shells,
)
from dmriqcpy.viz.screenshot import plot_proj_shell
from dmriqcpy.viz.utils import dataframe_to_html

DESCRIPTION = """
Compute DWI protocol report.
"""


def _build_arg_parser():
    p = argparse.ArgumentParser(
        description=DESCRIPTION, formatter_class=argparse.RawTextHelpFormatter
    )

    p.add_argument("output_report", help="Filename of QC report (in html format).")

    p.add_argument(
        "--bval", nargs="+", required=True, help="Folder or list of bval files."
    )

    p.add_argument(
        "--bvec", nargs="+", required=True, help="Folder or list of bvec files."
    )

    p.add_argument(
        "--metadata", nargs="+", help="Folder or list of json files to get the metadata."
    )

    p.add_argument(
        "--dicom_fields",
        nargs="+",
        default=[
            "EchoTime",
            "RepetitionTime",
            "SliceThickness",
            "Manufacturer",
            "ManufacturersModelName",
        ],
        help="DICOM fields used to compare information. %(default)s",
    )
    p.add_argument(
        "--tolerance",
        "-t",
        metavar="INT",
        type=int,
        default=20,
        help="The tolerated gap between the b-values to extract "
        "and the actual b-values. [%(default)s]",
    )

    add_online_arg(p)
    add_overwrite_arg(p)

    return p


def main():
    parser = _build_arg_parser()
    args = parser.parse_args()

    bval = list_files_from_paths(args.bval)
    bvec = list_files_from_paths(args.bvec)
    files_to_validate = [bval, bvec]

    if args.metadata:
        metadata = list_files_from_paths(args.metadata)
        files_to_validate.append(metadata)

    assert_list_arguments_equal_size(parser, *files_to_validate)

    stats_tags = []
    stats_tags_for_graph = []
    stats_tags_for_graph_all = []
    if args.metadata:
        (
            stats_tags,
            stats_tags_for_graph,
            stats_tags_for_graph_all,
        ) = read_protocol(metadata, args.dicom_fields)

    all_data = np.concatenate([bval, bvec])
    assert_inputs_exist(parser, all_data)
    assert_outputs_exist(parser, args, [args.output_report, "data", "libs"])
    clean_output_directories()

    name = "DWI Protocol"
    summary, stats_for_graph, stats_all, shells = dwi_protocol(bval)

    if stats_tags:
        for tag, curr_df in stats_tags:
            if "complete_" in tag:
                metric = curr_df.columns[0]
                for nSub in curr_df.index:
                    currKey = [nKey for nKey in summary.keys() if nSub in nKey]
                    summary[currKey[0]][metric] = curr_df[metric][nSub]

    if not isinstance(stats_tags_for_graph, list):
        stats_for_graph = pd.concat([stats_for_graph, stats_tags_for_graph], axis=1, join="inner")
        stats_all = pd.concat([stats_all, stats_tags_for_graph_all], axis=1, join="inner")

    warning_dict = {name: get_qa_report(stats_for_graph, stats_all, stats_all.columns)}
    summary_dict = {name: dataframe_to_html(stats_all)}

    if args.metadata:
        for curr_tag in stats_tags:
            if "complete_" not in curr_tag[0]:
                summary_dict[curr_tag[0]] = dataframe_to_html(curr_tag[1])

    graphs = [
        graph_directions_per_shells("Nbr directions per shell", shells, not args.online),
        graph_subjects_per_shells("Nbr subjects per shell", shells, not args.online),
    ]
    for c in stats_for_graph.keys():
        graphs.append(graph_dwi_protocol(c, c, stats_for_graph, not args.online))

    subjects_dict = {}
    for curr_bval, curr_bvec in zip(bval, bvec):
        curr_subj = os.path.basename(curr_bval).split('.')[0]
        subjects_dict[curr_subj] = {}
        points = np.genfromtxt(curr_bvec)
        if points.shape[0] == 3:
            points = points.T
        centroids, shell_idx = identify_shells(np.genfromtxt(curr_bval))
        plot_proj_shell(
            get_bvecs_from_shells_idxs(points, shell_idx),
            centroids,
            opacity=0.2,
            ofile=os.path.join(
                "data",
                name.replace(" ", "_") + "_" + curr_subj
            ),
            ores=(800, 800),
        )
        subjects_dict[curr_subj]["screenshot"] = os.path.join(
            "data",
            name.replace(" ", "_") + "_" + curr_subj + ".png"
        )

    for subj in bval:
        curr_subj = os.path.basename(subj).split('.')[0]
        summary_html = dataframe_to_html(summary[subj])
        subjects_dict[curr_subj]["stats"] = summary_html
    metrics_dict = {name: subjects_dict}

    nb_subjects = len(bval)
    report = Report(args.output_report)
    report.generate(
        title="Quality Assurance DWI protocol",
        nb_subjects=nb_subjects,
        metrics_dict=metrics_dict,
        summary_dict=summary_dict,
        graph_array=graphs,
        warning_dict=warning_dict,
        online=args.online,
    )


if __name__ == "__main__":
    main()
