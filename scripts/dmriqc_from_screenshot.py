#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import os
import shutil

from dmriqcpy.io.report import Report
from dmriqcpy.io.utils import (add_online_arg, add_overwrite_arg,
                               assert_inputs_exist, assert_outputs_exist)

DESCRIPTION = """
Compute the screenshot report in HTML format.
"""


def _build_arg_parser():
    p = argparse.ArgumentParser(description=DESCRIPTION,
                                formatter_class=argparse.RawTextHelpFormatter)

    p.add_argument('output_report',
                   help='HTML report')

    p.add_argument('data', nargs='+',
                   help='Screenshot folders')

    p.add_argument('--sym_link', action="store_true",
                   help='Use symlink instead of copy')

    add_online_arg(p)
    add_overwrite_arg(p)

    return p


def main():
    parser = _build_arg_parser()
    args = parser.parse_args()

    assert_inputs_exist(parser, args.data, are_directories=True)
    assert_outputs_exist(parser, args, [args.output_report, "data", "libs"])

    nb_subjects = len(os.listdir(args.data[0]))
    for folder in args.data[1:]:
        nb_subjects += len(os.listdir(folder))

    if os.path.exists("data"):
        shutil.rmtree("data")
    os.makedirs("data")

    if os.path.exists("libs"):
        shutil.rmtree("libs")

    metrics_dict = {}
    types = ""
    for folder in args.data:
        files = os.listdir(folder)
        name = os.path.basename(os.path.normpath(folder))
        subjects_dict = {}
        for subj_screenshot in files:
            if args.sym_link:
                os.symlink(os.path.abspath(folder) + "/" + subj_screenshot,
                           "data/" + subj_screenshot)
            else:
                shutil.copyfile(folder + "/" + subj_screenshot,
                                "data/" + subj_screenshot)
            subjects_dict[subj_screenshot] = {}
            subjects_dict[subj_screenshot]['screenshot'] =\
                "data/" + subj_screenshot
        metrics_dict[name] = subjects_dict
        types += " {0}".format(name)

    report = Report(args.output_report)
    report.generate(title="Quality Assurance" + types,
                    nb_subjects=nb_subjects, metrics_dict=metrics_dict)


if __name__ == '__main__':
    main()
