# -*- coding: utf-8 -*-

import numpy as np
from plotly.graph_objs import Bar, Box, Figure
import plotly.offline as off


def graph_mean_median(title, column_names, summary, online=False):
    """
    Compute plotly graph with mean and median stats

    Parameters
    ----------
    title : string
        Title of the graph.
    column_names : array of strings
        Name of the columns in the summary DataFrame.
    summary : DataFrame
        DataFrame containing the mean and median stats.
    online: Boolean
        If false it will include plotlyjs

    Returns
    -------
    div : html div (string)
        Graph as a HTML div.
    """
    include_plotlyjs = not online

    np.random.seed(1)
    image = summary.index
    means = np.array(summary[column_names[0]])
    medians = np.array(summary[column_names[1]])

    mean = Box(
        name="Mean",
        y=means,
        boxpoints="all",
        jitter=0.3,
        text=image,
        pointpos=-1.8,
        hoverinfo="y+text",
    )

    median = Box(
        name="Median",
        y=medians,
        boxpoints="all",
        jitter=0.3,
        text=image,
        pointpos=-1.8,
        hoverinfo="y+text",
    )

    data = [mean, median]

    fig = Figure(data=data)
    max_value = max(np.max(means), np.max(medians))

    range_yaxis = [0, max_value + 2 * max_value]

    fig["layout"]["yaxis"].update(range=range_yaxis)
    fig["layout"].update(title=title)
    fig["layout"].update(width=500, height=500)
    div = off.plot(
        fig,
        show_link=False,
        include_plotlyjs=include_plotlyjs,
        output_type="div",
    )
    div = div.replace("<div>", '<div style="display:inline-block">')
    return div


def graph_mean_in_tissues(title, column_names, summary, online=False):
    """
    Compute plotly graph with mean value in tissue masks

    Parameters
    ----------
    title : string
        Title of the graph.
    column_names : array of strings
        Name of the columns in the summary DataFrame.
    summary : DataFrame
        DataFrame containing the mean stats.
    online: Boolean
        If false it will include plotlyjs

    Returns
    -------
    div : html div (string)
        Graph as a HTML div.
    """
    include_plotlyjs = not online

    np.random.seed(1)
    metric = summary.index
    means_wm = np.array(summary[column_names[0]])
    means_gm = np.array(summary[column_names[1]])
    means_csf = np.array(summary[column_names[2]])
    wm = Box(
        name="WM",
        y=means_wm,
        boxpoints="all",
        jitter=0.3,
        text=metric,
        pointpos=-1.8,
        hoverinfo="y+text",
    )

    gm = Box(
        name="GM",
        y=means_gm,
        boxpoints="all",
        jitter=0.3,
        text=metric,
        pointpos=-1.8,
        hoverinfo="y+text",
    )

    csf = Box(
        name="CSF",
        y=means_csf,
        boxpoints="all",
        jitter=0.3,
        text=metric,
        pointpos=-1.8,
        hoverinfo="y+text",
    )
    data = [wm, gm, csf]

    fig = Figure(data=data)

    range_yaxis = [0, np.max(means_wm) + 2 * np.max(means_wm)]

    fig["layout"]["yaxis"].update(range=range_yaxis)
    fig["layout"].update(title=title)
    fig["layout"].update(width=500, height=500)

    div = off.plot(
        fig,
        show_link=False,
        include_plotlyjs=include_plotlyjs,
        output_type="div",
    )
    div = div.replace("<div>", '<div style="display:inline-block">')
    return div


def graph_frf_eigen(title, column_names, summary, online=False):
    """
    Compute plotly graph with mean frf values

    Parameters
    ----------
    title : string
        Title of the graph.
    column_names : array of strings
        Name of the columns in the summary DataFrame.
    summary : DataFrame
        DataFrame containing the mean stats.
    online: Boolean
        If false it will include plotlyjs

    Returns
    -------
    div : html div (string)
        Graph as a HTML div.
    """
    include_plotlyjs = not online

    np.random.seed(1)
    metric = summary.index
    e1 = np.array(summary[column_names[0]])
    e2 = np.array(summary[column_names[1]])

    e1_graph = Box(
        name="Eigen value 1",
        y=e1,
        boxpoints="all",
        jitter=0.3,
        text=metric,
        pointpos=-1.8,
        hoverinfo="y+text",
    )

    e2_graph = Box(
        name="Eigen value 2",
        y=e2,
        boxpoints="all",
        jitter=0.3,
        text=metric,
        pointpos=-1.8,
        hoverinfo="y+text",
    )

    data = [e1_graph, e2_graph]

    fig = Figure(data=data)

    fig["layout"].update(title=title)
    fig["layout"].update(width=500, height=500)
    div = off.plot(
        fig,
        show_link=False,
        include_plotlyjs=include_plotlyjs,
        output_type="div",
    )
    div = div.replace("<div>", '<div style="display:inline-block">')
    return div

def graph_frf_b0(title, column_names, summary, online=False):
    """
    Compute plotly graph with mean b0 values

    Parameters
    ----------
    title : string
        Title of the graph.
    column_names : array of strings
        Name of the columns in the summary DataFrame.
    summary : DataFrame
        DataFrame containing the mean stats.
    online: Boolean
        If false it will include plotlyjs

    Returns
    -------
    div : html div (string)
        Graph as a HTML div.
    """
    include_plotlyjs = not online

    np.random.seed(1)
    metric = summary.index
    e1_graph = Box(
        name="Mean B0",
        y=np.array(summary[column_names[2]]),
        boxpoints='all',
        jitter=0.3,
        text=metric,
        pointpos=-1.8,
        hoverinfo="y+text"
    )

    data = [e1_graph]

    fig = Figure(data=data)

    fig['layout'].update(title=title)
    fig['layout'].update(width=500, height=500)
    div = off.plot(fig, show_link=False, include_plotlyjs=include_plotlyjs,
                   output_type='div')
    div = div.replace("<div>", "<div style=\"display:inline-block\">")
    return div


def graph_tractogram(title, column_names, summary, online=False):
    """
    Compute plotly graph with mean number of streamlines

    Parameters
    ----------
    title : string
        Title of the graph.
    column_names : array of strings
        Name of the columns in the summary DataFrame.
    summary : DataFrame
        DataFrame containing the mean stats.
    online: Boolean
        If false it will include plotlyjs

    Returns
    -------
    div : html div (string)
        Graph as a HTML div.
    """
    include_plotlyjs = not online

    np.random.seed(1)
    metric = summary.index
    nb_streamlines = np.array(summary[column_names[0]])

    nb_streamlines_graph = Box(
        name="Nb streamlines",
        y=nb_streamlines,
        boxpoints="all",
        jitter=0.3,
        text=metric,
        pointpos=-1.8,
        hoverinfo="y+text",
    )

    data = [nb_streamlines_graph]

    fig = Figure(data=data)

    fig["layout"].update(title=title)
    fig["layout"].update(width=500, height=500)
    div = off.plot(
        fig,
        show_link=False,
        include_plotlyjs=include_plotlyjs,
        output_type="div",
    )
    div = div.replace("<div>", '<div style="display:inline-block">')
    return div


def graph_mask_volume(title, column_names, summary, online=False):
    """
    Compute plotly graph with mean mask volume

    Parameters
    ----------
    title : string
        Title of the graph.
    column_names : array of strings
        Name of the columns in the summary DataFrame.
    summary : DataFrame
        DataFrame containing the mean stats.
    online: Boolean
        If false it will include plotlyjs

    Returns
    -------
    div : html div (string)
        Graph as a HTML div.
    """
    include_plotlyjs = not online

    np.random.seed(1)
    metric = summary.index
    volume = np.array(summary[column_names[0]])

    volume_graph = Box(
        name="Volume",
        y=volume,
        boxpoints="all",
        jitter=0.3,
        text=metric,
        pointpos=-1.8,
        hoverinfo="y+text",
    )

    data = [volume_graph]

    fig = Figure(data=data)

    fig["layout"].update(title=title)
    fig["layout"].update(width=500, height=500)
    div = off.plot(
        fig,
        show_link=False,
        include_plotlyjs=include_plotlyjs,
        output_type="div",
    )
    div = div.replace("<div>", '<div style="display:inline-block">')
    return div


def graph_dwi_protocol(title, column_name, summary, online=False):
    """
    Compute plotly graph with mean mask volume

    Parameters
    ----------
    title : string
        Title of the graph.
    column_name : array of strings
        Name of the columns in the summary DataFrame.
    summary : DataFrame
        DataFrame containing the mean stats.
    online: Boolean
        If false it will include plotlyjs

    Returns
    -------
    div : html div (string)
        Graph as a HTML div.
    """
    include_plotlyjs = not online

    np.random.seed(1)
    metric = summary.index
    data = np.array(summary[column_name])

    graph = Box(
        name=column_name,
        y=data,
        boxpoints="all",
        jitter=0.3,
        text=metric,
        pointpos=-1.8,
        hoverinfo="y+text",
    )

    data = [graph]

    fig = Figure(data=data)

    fig["layout"].update(title=title)
    fig["layout"].update(width=500, height=500)
    div = off.plot(
        fig,
        show_link=False,
        include_plotlyjs=include_plotlyjs,
        output_type="div",
    )
    div = div.replace("<div>", '<div style="display:inline-block">')
    return div


def graph_directions_per_shells(title, summary, online=False):
    """
    Compute plotly graph with mean mask volume

    Parameters
    ----------
    title : string
        Title of the graph.
    summary : dict
        DataFrame containing the mean stats.
    online: Boolean
        If false it will include plotlyjs

    Returns
    -------
    div : html div (string)
        Graph as a HTML div.
    """
    include_plotlyjs = not online

    np.random.seed(1)
    data_graph = []
    for i in sorted(summary):
        metric = list(summary[i].keys())
        data = list(summary[i].values())

        graph = Box(
            name="b=" + str(i),
            y=data,
            boxpoints="all",
            jitter=0.3,
            text=metric,
            pointpos=-1.8,
            hoverinfo="y+text",
        )

        data_graph.append(graph)

    fig = Figure(data=data_graph)

    fig["layout"].update(title=title)
    fig["layout"].update(width=700, height=500)
    div = off.plot(
        fig,
        show_link=False,
        include_plotlyjs=include_plotlyjs,
        output_type="div",
    )
    div = div.replace("<div>", '<div style="display:inline-block">')
    return div


def graph_subjects_per_shells(title, summary, online=False):
    """
    Compute plotly graph with mean mask volume

    Parameters
    ----------
    title : string
        Title of the graph.
    summary : dict
        DataFrame containing the mean stats.
    online: Boolean
        If false it will include plotlyjs

    Returns
    -------
    div : html div (string)
        Graph as a HTML div.
    """
    include_plotlyjs = not online

    np.random.seed(1)
    data_graph = []
    for i in sorted(summary):
        metric = list(summary[i].keys())
        data = [len(metric)]

        graph = Bar(name="b=" + str(i), y=data, x=["b=" + str(i)], hoverinfo="y")

        data_graph.append(graph)

    fig = Figure(data=data_graph)

    fig["layout"].update(title=title)
    fig["layout"].update(width=700, height=500)
    div = off.plot(
        fig,
        show_link=False,
        include_plotlyjs=include_plotlyjs,
        output_type="div",
    )
    div = div.replace("<div>", '<div style="display:inline-block">')
    return div
