# -*- coding: utf-8 -*-

import numpy as np

from plotly.graph_objs import Box, Figure
import plotly.offline as off


def graph_mean_median(title, column_names, summary):
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

    Returns
    -------
    div : html div (string)
        Graph as a HTML div.
    """
    means = []
    medians = []
    np.random.seed(1)
    image = summary.index
    means = np.array(summary[column_names[0]])
    medians = np.array(summary[column_names[1]])

    mean = Box(
        name="Mean",
        y=means,
        boxpoints='all',
        jitter=0.3,
        text=image,
        pointpos=-1.8,
        hoverinfo="y+text"
    )

    median = Box(
        name="Median",
        y=medians,
        boxpoints='all',
        jitter=0.3,
        text=image,
        pointpos=-1.8,
        hoverinfo="y+text"
    )

    data = [mean, median]

    fig = Figure(data=data)
    max_value = max(np.max(means), np.max(medians))

    range_yaxis = [0, max_value + 2 * max_value]

    fig['layout']['yaxis'].update(range=range_yaxis)
    fig['layout'].update(title=title)
    fig['layout'].update(width=500, height=500)
    div = off.plot(fig, show_link=False, output_type='div')
    div = div.replace("<div>", "<div style=\"display:inline-block\">")
    return div
