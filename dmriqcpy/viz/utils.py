# -*- coding: utf-8 -*-


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
        std = stats_across_subjects.at['std', metric]
        mean = stats_across_subjects.at['mean', metric]
        for name in stats_per_subjects.index:
            if stats_per_subjects.at[name, metric] > mean + 2 * std or\
               stats_per_subjects.at[name, metric] < mean - 2 * std:
                warning[metric].append(name[0])
    return warning


def dataframe_to_html(data_frame):
    """
    Convert DataFrame to HTML table.

    Parameters
    ----------
    data_frame : DataFrame
        DataFrame.

    Returns
    -------
    data_frame_html : string
        HTML table.
    """
    data_frame_html = data_frame.to_html().replace(
        '<table border="1" '
        'class="dataframe">',
        '<table align="center" class="table table-striped">')
    return data_frame_html
