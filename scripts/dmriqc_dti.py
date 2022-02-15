#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import itertools
from multiprocessing import Pool
import os
import shutil

import numpy as np

from dmriqcpy.analysis.stats import stats_mean_in_tissues
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
)
from dmriqcpy.viz.graph import graph_mean_in_tissues
from dmriqcpy.viz.screenshot import (
    screenshot_fa_peaks,
    screenshot_mosaic_wrapper,
)
from dmriqcpy.viz.utils import analyse_qa, dataframe_to_html

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


def _subj_parralel(subj_metric, summary, name, skip, nb_columns):
    subjects_dict = {}
    curr_key = os.path.basename(subj_metric).split('.')[0]
    cmap = None
    if name == "Residual":
        cmap = "hot"
    screenshot_path = screenshot_mosaic_wrapper(
        subj_metric,
        output_prefix=name,
        directory="data",
        skip=skip,
        nb_columns=nb_columns,
        cmap=cmap,
    )

    summary_html = dataframe_to_html(summary.loc[curr_key].to_frame())
    subjects_dict[curr_key] = {}
    subjects_dict[curr_key]["screenshot"] = screenshot_path
    subjects_dict[curr_key]["stats"] = summary_html
    return subjects_dict


def main():
    parser = _build_arg_parser()
    args = parser.parse_args()

    fa = list_files_from_paths(args.fa)
    md = list_files_from_paths(args.md)
    rd = list_files_from_paths(args.rd)
    ad = list_files_from_paths(args.ad)
    residual = list_files_from_paths(args.residual)
    evecs_v1 = list_files_from_paths(args.evecs_v1)
    wm = list_files_from_paths(args.wm)
    gm = list_files_from_paths(args.gm)
    csf = list_files_from_paths(args.csf)

    if (
        not len(fa)
        == len(md)
        == len(rd)
        == len(ad)
        == len(residual)
        == len(evecs_v1)
        == len(wm)
        == len(gm)
        == len(csf)
    ):
        parser.error("Not the same number of images in input.")

    all_images = np.concatenate(
        [
            fa,
            md,
            rd,
            ad,
            residual,
            evecs_v1,
            wm,
            gm,
            csf,
        ]
    )
    assert_inputs_exist(parser, all_images)
    assert_outputs_exist(parser, args, [args.output_report, "data", "libs"])

    if os.path.exists("data"):
        shutil.rmtree("data")
    os.makedirs("data")

    if os.path.exists("libs"):
        shutil.rmtree("libs")

    metrics_names = [
        [fa, "FA"],
        [md, "MD"],
        [rd, "RD"],
        [ad, "AD"],
        [residual, "Residual"],
    ]
    metrics_dict = {}
    summary_dict = {}
    graphs = []
    warning_dict = {}
    for metrics, name in metrics_names:
        subjects_dict = {}
        curr_metrics = [
            "Mean {} in WM".format(name),
            "Mean {} in GM".format(name),
            "Mean {} in CSF".format(name),
            "Max {} in WM".format(name),
        ]

        summary, stats = stats_mean_in_tissues(
            curr_metrics, metrics, wm, gm, csf
        )

        warning_dict[name] = analyse_qa(summary, stats, curr_metrics[:3])
        warning_list = np.concatenate(
            [filenames for filenames in warning_dict[name].values()]
        )
        warning_dict[name]["nb_warnings"] = len(np.unique(warning_list))

        graph = graph_mean_in_tissues(
            "Mean {}".format(name), curr_metrics[:3], summary, args.online
        )
        graphs.append(graph)

        stats_html = dataframe_to_html(stats)
        summary_dict[name] = stats_html

        pool = Pool(args.nb_threads)
        subjects_dict_pool = pool.starmap(
            _subj_parralel,
            zip(
                metrics,
                itertools.repeat(summary),
                itertools.repeat(name),
                itertools.repeat(args.skip),
                itertools.repeat(args.nb_columns),
            ),
        )

        pool.close()
        pool.join()

        for dict_sub in subjects_dict_pool:
            for key in dict_sub:
                subjects_dict[key] = dict_sub[key]
        metrics_dict[name] = subjects_dict

    subjects_dict = {}
    name = "Peaks"
    for curr_fa, curr_evecs in zip(fa, evecs_v1):
        evecs_filename = os.path.basename(curr_evecs).split('.')[0]
        screenshot_path = screenshot_fa_peaks(curr_fa, curr_evecs, "data")

        subjects_dict[evecs_filename] = {}
        subjects_dict[evecs_filename]["screenshot"] = screenshot_path
    metrics_dict[name] = subjects_dict

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
