#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import itertools
from multiprocessing import Pool
import os
import shutil

import numpy as np

from dmriqcpy.analysis.stats import stats_mean_in_tissues, stats_mean_median
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
from dmriqcpy.viz.graph import graph_mean_in_tissues, graph_mean_median
from dmriqcpy.viz.screenshot import screenshot_mosaic_wrapper
from dmriqcpy.viz.utils import analyse_qa, dataframe_to_html

DESCRIPTION = """
Compute report in HTML format from images.
"""


def _build_arg_parser():
    p = argparse.ArgumentParser(
        description=DESCRIPTION, formatter_class=argparse.RawTextHelpFormatter
    )

    p.add_argument("image_type", help="Type of image (e.g. B0 resample).")

    p.add_argument("output_report", help="HTML report.")

    p.add_argument(
        "--images",
        nargs="+",
        required=True,
        help="Folder or list of images in Nifti format."
    )

    p.add_argument(
        "--wm",
        nargs="+",
        help="Folder or list of WM mask in Nifti format."
    )

    p.add_argument(
        "--gm",
        nargs="+",
        help="Folder or list of GM mask in Nifti format"
    )

    p.add_argument(
        "--csf",
        nargs="+",
        help="Folder or list of CSF mask in Nifti format."
    )

    p.add_argument(
        "--duration",
        default=100,
        type=int,
        help="Duration of each image in GIF in milliseconds." " [%(default)s]",
    )

    add_skip_arg(p)
    add_nb_columns_arg(p)
    add_nb_threads_arg(p)
    add_online_arg(p)
    add_overwrite_arg(p)

    return p


def _subj_parralel(subj_metric, summary, name, skip, nb_columns, duration):
    subjects_dict = {}
    curr_key = os.path.basename(subj_metric).split('.')[0]
    screenshot_path = screenshot_mosaic_wrapper(
        subj_metric,
        output_prefix=name,
        directory="data",
        skip=skip,
        nb_columns=nb_columns,
        duration=duration,
    )

    summary_html = dataframe_to_html(summary.loc[curr_key].to_frame())
    subjects_dict[curr_key] = {}
    subjects_dict[curr_key]["screenshot"] = screenshot_path
    subjects_dict[curr_key]["stats"] = summary_html
    return subjects_dict


def main():
    parser = _build_arg_parser()
    args = parser.parse_args()

    images = list_files_from_paths(args.images)
    all_images = images

    with_tissues = False
    if args.wm is not None and args.gm is not None and args.csf is not None:
        wm = list_files_from_paths(args.wm)
        gm = list_files_from_paths(args.gm)
        csf = list_files_from_paths(args.csf)
        if not len(images) == len(wm) == len(gm) == len(csf):
            parser.error("Not the same number of images in input.")

        with_tissues = True
        all_images = np.concatenate([images, wm, gm, csf])

    assert_inputs_exist(parser, all_images)
    assert_outputs_exist(parser, args, [args.output_report, "data", "libs"])

    if os.path.exists("data"):
        shutil.rmtree("data")
    os.makedirs("data")

    if os.path.exists("libs"):
        shutil.rmtree("libs")

    name = args.image_type

    if with_tissues:
        curr_metrics = [
            "Mean {} in WM".format(name),
            "Mean {} in GM".format(name),
            "Mean {} in CSF".format(name),
            "Max {} in WM".format(name),
        ]
        summary, stats = stats_mean_in_tissues(
            curr_metrics, images, wm, gm, csf
        )
        graph = graph_mean_in_tissues(
            "Mean {}".format(name), curr_metrics[:3], summary, args.online
        )
    else:
        curr_metrics = ["Mean {}".format(name), "Median {}".format(name)]
        summary, stats = stats_mean_median(curr_metrics, images)
        graph = graph_mean_median(
            "Mean {}".format(name), curr_metrics, summary, args.online
        )

    warning_dict = {}
    warning_dict[name] = analyse_qa(summary, stats, curr_metrics[:3])
    warning_list = np.concatenate([filenames for filenames in warning_dict[name].values()])
    warning_dict[name]["nb_warnings"] = len(np.unique(warning_list))

    graphs = [graph]

    stats_html = dataframe_to_html(stats)
    summary_dict = {}
    summary_dict[name] = stats_html
    pool = Pool(args.nb_threads)
    subjects_dict_pool = pool.starmap(
        _subj_parralel,
        zip(
            images,
            itertools.repeat(summary),
            itertools.repeat(name),
            itertools.repeat(args.skip),
            itertools.repeat(args.nb_columns),
            itertools.repeat(args.duration),
        ),
    )
    pool.close()
    pool.join()

    metrics_dict = {}
    subjects_dict = {}
    for dict_sub in subjects_dict_pool:
        for key in dict_sub:
            curr_key = os.path.basename(key).split('.')[0]
            subjects_dict[curr_key] = dict_sub[curr_key]
    metrics_dict[name] = subjects_dict

    nb_subjects = len(images)
    report = Report(args.output_report)
    report.generate(
        title="Quality Assurance " + args.image_type,
        nb_subjects=nb_subjects,
        summary_dict=summary_dict,
        graph_array=graphs,
        metrics_dict=metrics_dict,
        warning_dict=warning_dict,
        online=args.online,
    )


if __name__ == "__main__":
    main()
