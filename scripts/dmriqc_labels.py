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
    assert_outputs_exist,
    clean_output_directories,
    list_files_from_paths,
)
from dmriqcpy.reporting.report import (
    generate_metric_reports_parallel,
    generate_report_package,
)


DESCRIPTION = """
Compute the labels report in HTML format.

Using LUT like:
#No. Label Name:                            R   G   B
"""


def _build_arg_parser():
    p = argparse.ArgumentParser(
        description=DESCRIPTION, formatter_class=argparse.RawTextHelpFormatter
    )

    p.add_argument("output_report", help="Filename of QC report (in html format).")

    p.add_argument(
        "--t1",
        nargs="+",
        required=True,
        help="Folder or list of T1 images in Nifti format."
    )

    p.add_argument(
        "--label",
        nargs="+",
        required=True,
        help="Folder or list of label images in Nifti format."
    )

    p.add_argument(
        "--lut", nargs=1, default="", help="Look Up Table for RGB."
    )

    p.add_argument(
        "--compute_lut",
        action="store_true",
        help="Compute Look Up Table for RGB."
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

    t1 = list_files_from_paths(args.t1)
    label = list_files_from_paths(args.label)

    if not len(t1) == len(label) and len(label) != 1:
        parser.error("Not the same number of images in input.")

    if len(label) == 1:
        label = label * len(t1)

    all_images = np.concatenate([t1, label])
    if args.lut:
        all_images = np.concatenate(all_images, args.lut)

    assert_inputs_exist(parser, all_images)
    assert_outputs_exist(parser, args, [args.output_report, "data", "libs"])
    clean_output_directories()

    name = "Labels"
    nb_subjects = len(t1)

    metrics_dict = {
        name: generate_metric_reports_parallel(
            zip(t1, label),
            args.nb_threads,
            nb_subjects // args.nb_threads,
            report_package_generation_fn=partial(
                generate_report_package,
                skip=args.skip,
                nb_columns=args.nb_columns,
                lut=args.lut,
                compute_lut=args.compute_lut
            ),
        )
    }

    report = Report(args.output_report)
    report.generate(
        title="Quality Assurance labels",
        nb_subjects=nb_subjects,
        metrics_dict=metrics_dict,
        online=args.online,
    )


if __name__ == "__main__":
    main()
