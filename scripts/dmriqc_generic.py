#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
from functools import partial

import numpy as np

from dmriqcpy.io.report import Report
from dmriqcpy.io.utils import (
    add_online_arg,
    add_overwrite_arg,
    add_nb_columns_arg,
    add_nb_threads_arg,
    add_skip_arg,
    assert_inputs_exist,
    assert_list_arguments_equal_size,
    assert_outputs_exist,
    clean_output_directories,
    list_files_from_paths,
)
from dmriqcpy.reporting.report import (
    generate_metric_reports_parallel,
    generate_report_package,
    get_generic_qa_stats_and_graph,
    get_qa_stats_and_graph_in_tissues,
)
from dmriqcpy.viz.utils import dataframe_to_html

DESCRIPTION = """
Compute report in HTML format from images.
"""


def _build_arg_parser():
    p = argparse.ArgumentParser(
        description=DESCRIPTION, formatter_class=argparse.RawTextHelpFormatter
    )

    p.add_argument("image_type", help="Type of image (e.g. B0 resample).")
    p.add_argument("output_report", help="Filename of QC report (in html format).")

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
        help="Duration of each image in GIF in milliseconds. [%(default)s]",
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

    images = list_files_from_paths(args.images)
    all_images = images

    with_tissues = False
    if args.wm is not None and args.gm is not None and args.csf is not None:
        wm = list_files_from_paths(args.wm)
        gm = list_files_from_paths(args.gm)
        csf = list_files_from_paths(args.csf)
        assert_list_arguments_equal_size(parser, images, wm, gm, csf)

        with_tissues = True
        all_images = np.concatenate([images, wm, gm, csf])

    assert_inputs_exist(parser, all_images)
    assert_outputs_exist(parser, args, [args.output_report, "data", "libs"])
    clean_output_directories()

    name = args.image_type
    nb_subjects = len(images)

    if with_tissues:
        summary, stats, qa_report, qa_graphs = get_qa_stats_and_graph_in_tissues(
            images, name, wm, gm, csf, args.online
        )
    else:
        summary, stats, qa_report, qa_graphs = get_generic_qa_stats_and_graph(
            images, name, args.online
        )

    warning_dict = {name: qa_report}
    summary_dict = {name: dataframe_to_html(stats)}

    metrics_dict = {
        name: generate_metric_reports_parallel(
            zip(images),
            args.nb_threads,
            nb_subjects // args.nb_threads,
            report_package_generation_fn=partial(
                generate_report_package,
                stats_summary=summary,
                skip=args.skip,
                nb_columns=args.nb_columns,
                duration=args.duration,
            ),
        )
    }

    report = Report(args.output_report)
    report.generate(
        title="Quality Assurance " + args.image_type,
        nb_subjects=nb_subjects,
        summary_dict=summary_dict,
        graph_array=qa_graphs,
        metrics_dict=metrics_dict,
        warning_dict=warning_dict,
        online=args.online,
    )


if __name__ == "__main__":
    main()
