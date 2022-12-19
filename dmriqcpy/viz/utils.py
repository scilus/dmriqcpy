# -*- coding: utf-8 -*-
import fury
import numpy as np
import vtk
from plotly.graph_objs import Figure
import plotly.offline as off
from vtk.util import numpy_support

"""
Some functions comes from
https://github.com/scilus/scilpy/blob/master/scilpy/viz/gradient_sampling.py
"""


def analyse_qa(stats_per_subjects, stats_across_subjects, column_names):
    """
    Analyse the subjects and flag warning

    Parameters
    ----------
    stats_per_subjects : DataFrame
        DataFrame containing the stats per subjects.
    stats_across_subjects : DataFrame
        DataFrame containing the stats across subjects.
    column_names : array of strings
        Name of the columns in the summary DataFrame.

    Returns
    -------
    warning : dict
        Dictionnary of warning subjects for each metric.
    """
    warning = {}
    for metric in column_names:
        warning[metric] = []
        std = stats_across_subjects.at["std", metric]
        mean = stats_across_subjects.at["mean", metric]
        for name in stats_per_subjects.index:
            if (
                stats_per_subjects.at[name, metric] > mean + 2 * std
                or stats_per_subjects.at[name, metric] < mean - 2 * std
            ):
                warning[metric].append(name)
    return warning


def dataframe_to_html(data_frame, index=True):
    """
    Convert DataFrame to HTML table.

    Parameters
    ----------
    data_frame : DataFrame
        DataFrame.
    index : bool
        Print rows index labels
    Returns
    -------
    data_frame_html : string
        HTML table.
    """
    data_frame_html = data_frame.to_html(index=index).replace(
        '<table border="1" ' 'class="dataframe">',
        '<table align="center" class="table table-striped">',
    )
    return data_frame_html


def graph_to_html(
    data, title, range_yaxis=None, width=500, height=500, include_plotlyjs=False
):
    fig = Figure(data=data)
    fig["layout"].update(title=title)
    fig["layout"].update(width=width, height=height)

    if range_yaxis is not None:
        fig["layout"]["yaxis"].update(range=range_yaxis)

    div = off.plot(
        fig,
        show_link=False,
        include_plotlyjs=include_plotlyjs,
        output_type="div",
    )
    return div.replace("<div>", '<div style="display:inline-block">')


def renderer_to_arr(ren, size):
    """
    Convert DataFrame to HTML table.

    Parameters
    ----------
    ren : Renderer
        vtk Renderer.

    size : tuple of int
        Size of the output image

    Returns
    -------
    arr : array
        Image as numpy array.

    Notes
    -----
    Inspired from https://github.com/fury-gl/fury/blob/master/fury/window.py
    """
    width, height = size

    graphics_factory = vtk.vtkGraphicsFactory()
    graphics_factory.SetOffScreenOnlyMode(1)

    render_window = vtk.vtkRenderWindow()
    render_window.SetOffScreenRendering(1)
    render_window.AddRenderer(ren)
    render_window.SetSize(width, height)

    render_window.SetAlphaBitPlanes(True)

    render_window.SetMultiSamples(0)

    ren.UseDepthPeelingOn()

    ren.SetMaximumNumberOfPeels(4)

    ren.SetOcclusionRatio(0.0)

    render_window.Render()

    window_to_image_filter = vtk.vtkWindowToImageFilter()
    window_to_image_filter.SetInput(render_window)
    window_to_image_filter.Update()

    vtk_image = window_to_image_filter.GetOutput()
    h, w, _ = vtk_image.GetDimensions()
    vtk_array = vtk_image.GetPointData().GetScalars()
    components = vtk_array.GetNumberOfComponents()
    arr = numpy_support.vtk_to_numpy(vtk_array).reshape(w, h, components)
    return arr


def compute_labels_map(lut_fname, unique_vals, compute_lut):
    labels = {}
    if compute_lut:
        labels[0] = np.array((0, 0, 0), dtype=np.int8)
        vtkcolors = fury.colormap.distinguishable_colormap(
            nb_colors=len(unique_vals)
        )
        for index, curr_label in enumerate(unique_vals[1:]):
            labels[curr_label] = np.array(
                (
                    vtkcolors[index][0] * 255,
                    vtkcolors[index][1] * 255,
                    vtkcolors[index][2] * 255,
                ),
                dtype=np.int8,
            )
    else:
        with open(lut_fname) as f:
            for line in f:
                tokens = " ".join(line.split()).split()
                if tokens and not tokens[0].startswith("#"):
                    labels[np.int(tokens[0])] = np.array(
                        (tokens[2], tokens[3], tokens[4]), dtype=np.int8
                    )

    return labels
