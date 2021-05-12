# -*- coding: utf-8 -*-

import numpy as np
import pandas as pd

from scilpy.utils.bvec_bval_tools import identify_shells


def get_nearest_bval(bvals, curr_bval, tol=20):
    """
    Get nearest bval in a list of bvals
    If not in the list, return the current bval
    Parameters
    ----------
    bvals: array
        list of bvals
    curr_bval: float
        current bval
    tol: int
        tolerance threshold to check
        if the current bval is in the list

    Returns
    -------
    bval: float
        Return the nearest bval or the current one.


    """
    indices = np.where(np.logical_and(bvals <= curr_bval + tol,
                                      bvals >= curr_bval - tol))[0]
    if len(indices) > 0:
        bval = bvals[indices[0]]
    else:
        bval = curr_bval
    return bval


def read_protocol(in_jsons, tags):
    """
    Return dwi protocol for each subject

    Parameters
    ----------
    in_json : List
        List of jsons files
    tags: List
        List of tags to check

    Returns
    -------

    """
    dfs = []
    for in_json in in_jsons:
        data = pd.read_json(in_json, orient='index')
        dfs.append(data.T)

    temp = pd.concat(dfs, ignore_index=True)

    dfs = []
    for tag in tags:
        if tag in temp.columns:
            ts = temp.groupby(tag)[tag].count()
            tdf = pd.DataFrame(ts)
            tdf = tdf.rename(columns={tag: "Number of subjects"})
            tdf.reset_index(inplace=True)
            tdf = tdf.rename(columns={tag: "Value(s)"})
            tdf = tdf.sort_values(by=['Number of subjects'],
                                  ascending=False)
            dfs.append((tag, tdf))

    return dfs


def dwi_protocol(bvals, tol=20):
    """
    Return dwi protocol for each subject

    Parameters
    ----------
    bvals : List
        List of bvals
    tol: int
        tolerance threshold to check
        if the current bval is in the list

    Returns
    -------

    """
    stats_per_subjects = {}
    values_stats = []
    column_names = ["Nbr shells", "Nbr directions"]
    shells = {}
    for i, filename in enumerate(bvals):
        values = []

        bval = np.loadtxt(bvals[i])

        centroids, shells_indices = identify_shells(bval, threshold=tol)
        s_centroids = sorted(centroids)
        values.append(', '.join(str(x) for x in s_centroids))
        values.append(len(shells_indices))
        columns = ["bvals"]
        columns.append("Nbr directions")
        for centroid in s_centroids:
            nearest_centroid = get_nearest_bval(list(shells.keys()), centroid)
            if np.int(nearest_centroid) not in shells:
                shells[np.int(nearest_centroid)] = {}
            nb_directions = len(shells_indices[shells_indices ==
                                               np.where(centroids == centroid)[
                                                   0]])
            if filename not in shells[np.int(nearest_centroid)]:
                shells[np.int(nearest_centroid)][filename] = 0
            shells[np.int(nearest_centroid)][filename] += nb_directions
            values.append(nb_directions)
            columns.append("Nbr bval {}".format(centroid))

        values_stats.append([len(centroids) - 1, len(shells_indices)])

        stats_per_subjects[filename] = pd.DataFrame([values], index=[bvals[i]],
                                                    columns=columns)

    stats = pd.DataFrame(values_stats, index=[bvals],
                         columns=column_names)

    stats_across_subjects = pd.DataFrame([stats.mean(),
                                          stats.std(),
                                          stats.min(),
                                          stats.max()],
                                         index=['mean', 'std', 'min', 'max'],
                                         columns=column_names)

    return stats_per_subjects, stats, stats_across_subjects, shells
