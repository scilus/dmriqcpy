#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import os
import shutil

import numpy as np
import pandas as pd
from scilpy.utils.bvec_bval_tools import identify_shells
from scilpy.viz.gradient_sampling import build_ms_from_shell_idx

from dmriqcpy.analysis.utils import dwi_protocol, read_protocol
from dmriqcpy.io.report import Report
from dmriqcpy.io.utils import (add_overwrite_arg, assert_inputs_exist,
                               assert_outputs_exist)
from dmriqcpy.viz.graph import (graph_directions_per_shells,
                                graph_dwi_protocol,
                                graph_subjects_per_shells)
from dmriqcpy.viz.screenshot import plot_proj_shell
from dmriqcpy.viz.utils import analyse_qa, dataframe_to_html

DESCRIPTION = """
Compute DWI protocol report.
"""


def _build_arg_parser():
    p = argparse.ArgumentParser(description=DESCRIPTION,
                                formatter_class=argparse.RawTextHelpFormatter)

    p.add_argument('output_report',
                   help='Filename of QC report (in html format).')

    p.add_argument('--bval', nargs='+', required=True,
                   help='List of bval files.')

    p.add_argument('--bvec', nargs='+', required=True,
                   help='List of bvec files.')

    p.add_argument('--metadata', nargs='+',
                   default='None',
                   help='Json files to get the metadata.')

    p.add_argument('--tags', nargs='+',
                   default=["EchoTime", "RepetitionTime", "SliceThickness",
                   "Manufacturer", "ManufacturersModelName"],
                   help='DICOM tags used to compare information. %(default)s')

    p.add_argument('--tolerance', '-t',
                   metavar='INT', type=int, default=20,
                   help='The tolerated gap between the b-values to '
                        'extract\nand the actual b-values. [%(default)s]')

    add_overwrite_arg(p)

    return p


def main():
    parser = _build_arg_parser()
    args = parser.parse_args()

    if not len(args.bval) == len(args.bvec):
        parser.error("Not the same number of images in input.")

    if args.metadata is not None:
        if not len(args.metadata) == len(args.bval):
            print('Number of metadata files: {}.\n'
                  'Number of bval files: {}.'.format(len(args.metadata),
                                                  len(args.bval)))
            parser.error("Not the same number of images in input.")
        else:
            stats_tags, stats_tags_for_graph, stats_tags_all = read_protocol(args.metadata, args.tags)

    all_data = np.concatenate([args.bval,
                               args.bvec])
    assert_inputs_exist(parser, all_data)
    assert_outputs_exist(parser, args, [args.output_report, "data", "libs"])

    if os.path.exists("data"):
        shutil.rmtree("data")
    os.makedirs("data")

    if os.path.exists("libs"):
        shutil.rmtree("libs")

    name = "DWI Protocol"
    summary, stats_for_graph, stats_all, shells = dwi_protocol(args.bval)

    if not isinstance(stats_tags_for_graph, list):
        stats_for_graph = pd.concat([stats_for_graph, stats_tags_for_graph],
                                    axis=1, join="inner")
        stats_all = pd.concat([stats_all, stats_tags_all],
                               axis=1, join="inner")

    warning_dict = {}
    warning_dict[name] = analyse_qa(stats_for_graph, stats_all,
                                    stats_all.columns)
    warning_images = [filenames for filenames in warning_dict[name].values()]
    warning_list = np.concatenate(warning_images)
    warning_dict[name]['nb_warnings'] = len(np.unique(warning_list))

    stats_html = dataframe_to_html(stats_all)
    summary_dict = {}
    summary_dict[name] = stats_html

    for curr_tag in stats_tags:
        if 'complete_' in curr_tag[0]:
            summary_dict[curr_tag[0]] = dataframe_to_html(curr_tag[1])
        else:
            summary_dict[curr_tag[0]] = dataframe_to_html(curr_tag[1], index=False)

    graphs = []
    graphs.append(graph_directions_per_shells("Nbr directions per shell",
                                              shells))
    graphs.append(graph_subjects_per_shells("Nbr subjects per shell", shells))

    for c in stats_for_graph.columns:#["Nbr shells", "Nbr directions"]:
        graph = graph_dwi_protocol(c, c, stats_for_graph)
        graphs.append(graph)

    subjects_dict = {}
    for bval, bvec in zip(args.bval, args.bvec):
        filename = os.path.basename(bval)
        subjects_dict[bval] = {}
        points = np.genfromtxt(bvec)
        if points.shape[0] == 3:
            points = points.T
        bvals = np.genfromtxt(bval)
        centroids, shell_idx = identify_shells(bvals)
        ms = build_ms_from_shell_idx(points, shell_idx)
        plot_proj_shell(ms, centroids, use_sym=True, use_sphere=True,
                        same_color=False, rad=0.025, opacity=0.2,
                        ofile=os.path.join("data", name + filename),
                        ores=(800, 800))
        subjects_dict[bval]['screenshot'] = os.path.join("data",
                                                         name + filename +
                                                         '.png')
    metrics_dict = {}
    for subj in args.bval:
        summary_html = dataframe_to_html(summary[subj])
        subjects_dict[subj]['stats'] = summary_html
    metrics_dict[name] = subjects_dict

    nb_subjects = len(args.bval)
    report = Report(args.output_report)
    report.generate(title="Quality Assurance DWI protocol",
                    nb_subjects=nb_subjects, metrics_dict=metrics_dict,
                    summary_dict=summary_dict, graph_array=graphs,
                    warning_dict=warning_dict)


if __name__ == '__main__':
    main()
