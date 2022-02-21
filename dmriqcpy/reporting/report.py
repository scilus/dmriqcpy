import os
from functools import partial
from multiprocessing import Pool

import numpy as np

from dmriqcpy.analysis.stats import (
    stats_mean_in_tissues,
    stats_mask_volume,
    stats_mean_median,
    stats_frf,
    stats_tractogram,
)
from dmriqcpy.viz.graph import (
    graph_mean_in_tissues,
    graph_mask_volume,
    graph_mean_median,
    graph_frf,
    graph_tractogram,
)
from dmriqcpy.viz.screenshot import (
    screenshot_mosaic_wrapper,
    screenshot_mosaic_blend,
    screenshot_tracking,
)
from dmriqcpy.viz.utils import dataframe_to_html, analyse_qa


def get_qa_report(summary, stats, qa_labels):
    qa_report = analyse_qa(summary, stats, qa_labels)
    files_flagged_warning = np.concatenate([filenames for filenames in qa_report.values()])
    qa_report["nb_warnings"] = len(np.unique(files_flagged_warning))
    return qa_report


def _get_stats_and_graphs(
    metrics, stats_fn, stats_labels, graph_fn, graph_title, qa_labels=None, include_plotlyjs=False
):
    qa_labels = qa_labels or stats_labels
    summary, stats = stats_fn(stats_labels, metrics)
    qa_report = get_qa_report(summary, stats, qa_labels)
    return summary, stats, qa_report, graph_fn(graph_title, qa_labels, summary, include_plotlyjs)


def get_tractogram_qa_stats_and_graph(tractograms, report_is_online):
    return _get_stats_and_graphs(
        tractograms,
        stats_tractogram,
        ["Nb streamlines"],
        graph_tractogram,
        "Tracking",
        include_plotlyjs=not report_is_online,
    )


def get_frf_qa_stats_and_graph(frfs, report_is_online):
    return _get_stats_and_graphs(
        frfs,
        stats_frf,
        ["Mean Eigen value 1", "Mean Eigen value 2", "Mean B0"],
        graph_frf,
        "FRF",
        include_plotlyjs=not report_is_online,
    )


def get_mask_qa_stats_and_graph(masks, name, report_is_online):
    return _get_stats_and_graphs(
        masks,
        stats_mask_volume,
        ["{} volume".format(name)],
        graph_mask_volume,
        "{} mean volume".format(name),
        include_plotlyjs=not report_is_online,
    )


def get_qa_stats_and_graph_in_tissues(metric, name, wm_masks, gm_masks, csf_masks, report_is_online):
    stats_labels = [
        "Mean {} in WM".format(name),
        "Mean {} in GM".format(name),
        "Mean {} in CSF".format(name),
        "Max {} in WM".format(name),
    ]
    return _get_stats_and_graphs(
        metric,
        partial(
            stats_mean_in_tissues, wm_images=wm_masks, gm_images=gm_masks, csf_images=csf_masks
        ),
        stats_labels,
        graph_mean_in_tissues,
        "Mean {}".format(name),
        stats_labels[:3],
        not report_is_online,
    )


def get_generic_qa_stats_and_graph(metrics, name, report_is_online):
    return _get_stats_and_graphs(
        metrics,
        stats_mean_median,
        ["Mean {}".format(name), "Median {}".format(name)],
        graph_mean_median,
        "Mean {}".format(name),
        include_plotlyjs=not report_is_online,
    )


def generate_report_package(
    metric_image_path,
    blend_image_path=None,
    stats_summary=None,
    skip=1,
    nb_columns=15,
    duration=100,
    cmap=None,
    blend_val=0.5,
    lut=None,
    pad=20,
    blend_is_mask=False,
    metric_is_tracking=False,
):
    if metric_is_tracking:
        screenshot_path = screenshot_tracking(metric_image_path, blend_image_path, "data")
    elif blend_image_path:
        screenshot_path = screenshot_mosaic_blend(
            metric_image_path,
            blend_image_path,
            directory="data",
            skip=skip,
            pad=pad,
            nb_columns=nb_columns,
            blend_val=blend_val,
            cmap=cmap,
            lut=lut,
            is_mask=blend_is_mask,
        )
    else:
        screenshot_path = screenshot_mosaic_wrapper(
            metric_image_path,
            directory="data",
            skip=skip,
            pad=pad,
            nb_columns=nb_columns,
            duration=duration,
            cmap=cmap,
            lut=lut,
        )

    subject_data = {"screenshot": screenshot_path}
    subj_metric_name = os.path.basename(metric_image_path)
    if stats_summary is not None:
        subject_data["stats"] = dataframe_to_html(stats_summary.loc[subj_metric_name])

    return subj_metric_name, subject_data


def generate_metric_reports_parallel(
    metrics_iterable,
    nb_threads,
    chunksize=1,
    report_package_generation_fn=generate_report_package,
):
    with Pool(nb_threads) as pool:
        qc_tabs_data_pool = pool.starmap_async(
            report_package_generation_fn,
            metrics_iterable,
            chunksize=chunksize,
        )
        return {tag: data for tag, data in qc_tabs_data_pool.get()}
