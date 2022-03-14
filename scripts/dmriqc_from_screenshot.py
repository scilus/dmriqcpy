#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import glob
import os
import pandas as pd
import shutil

from dmriqcpy.io.report import Report
from dmriqcpy.io.utils import (add_online_arg, add_overwrite_arg,
                               assert_inputs_exist, assert_outputs_exist)
from dmriqcpy.viz.utils import dataframe_to_html

DESCRIPTION = """
Compute the screenshot report in HTML format.
"""


def _build_arg_parser():
    p = argparse.ArgumentParser(description=DESCRIPTION,
                                formatter_class=argparse.RawTextHelpFormatter)

    p.add_argument('output_report',
                   help='HTML report')

    p.add_argument('--data', nargs='+',
                   help='Screenshot and stats (optional) folders.')

    p.add_argument('--stats', action="store_true",
                   help='Use included csv files.')

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
        screenshot_files = []
        stats_files = []

        for ext in ["png","jpeg","jpg"]:
            screenshot_files = screenshot_files + sorted(glob.glob(folder + '/*' + ext))
        if args.stats:
            stats_files = sorted(glob.glob(folder + '/*.csv'))
            if len(screenshot_files) != len(stats_files):
                parser.error("Not same number of stats and screenshots")


        name = os.path.basename(os.path.normpath(folder))
        subjects_dict = {}
        for index, curr_screenshot in enumerate(screenshot_files):
            screenshot_basename = os.path.basename(curr_screenshot)
            if args.sym_link:
                os.symlink(os.path.abspath(folder) + "/" + screenshot_basename,
                           "data/" + screenshot_basename)
            else:
                shutil.copyfile(curr_screenshot,
                                "data/" + screenshot_basename)
            subjects_dict[screenshot_basename] = {}
            subjects_dict[screenshot_basename]['screenshot'] =\
                "data/" + screenshot_basename
            if args.stats:
                subjects_dict[screenshot_basename]['stats'] = dataframe_to_html(pd.read_csv(stats_files[index], index_col=False))

        metrics_dict[name] = subjects_dict
        types += " {0}".format(name)

    report = Report(args.output_report)
    report.generate(title="Quality Assurance" + types,
                    nb_subjects=nb_subjects, metrics_dict=metrics_dict,
                    online=args.online)


if __name__ == '__main__':
    main()
