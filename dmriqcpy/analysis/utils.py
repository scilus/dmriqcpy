# -*- coding: utf-8 -*-
import logging
import numpy as np
import os
import pandas as pd

"""
Some functions comes from
https://github.com/scilus/scilpy/blob/master/scilpy/utils/bvec_bval_tools.py
"""


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
    dfs : Tuple
        Tuple of DataFrame for each tag (tag_name, DataFrame).
    dfs_for_graph: DataFrame
        DataFrame containing all valid tag info (mean, std, min, max).
    dfs_for_graph: DataFrame
        DataFrame containing all valid for all subjects.
    """
    dfs = []
    for in_json in in_jsons:
        data = pd.read_json(in_json, orient='index')
        dfs.append(data.T)

    temp = pd.concat(dfs, ignore_index=True)
    index = [os.path.basename(item).split('.')[0] for item in in_jsons]
    dfs = []
    tmp_dfs_for_graph = []
    dfs_for_graph_all = []
    dfs_for_graph = []
    for tag in tags:
        if tag in temp.columns:
            if not isinstance(temp[tag][0], list):
                ts = temp.groupby(tag)[tag].count()
                tdf = pd.DataFrame(ts)
                tdf = tdf.rename(columns={tag: "Number of subjects"})
                tdf.reset_index(inplace=True)
                tdf = tdf.rename(columns={tag: "Value(s)"})
                tdf = tdf.sort_values(by=['Value(s)'],
                                      ascending=False)
                dfs.append((tag, tdf))

                t = temp[tag]
                t.index = index
                tdf = pd.DataFrame(t)

                if isinstance(temp[tag][0], int) or\
                   isinstance(temp[tag][0], float):
                    tmp_dfs_for_graph.append(tdf)

                dfs.append(('complete_' + tag, tdf))
        else:
            logging.warning("{} does not exist in the metadata.".format(tag))

    if tmp_dfs_for_graph:
        dfs_for_graph = pd.concat(tmp_dfs_for_graph, axis=1, join="inner")
        dfs_for_graph_all = pd.DataFrame([dfs_for_graph.mean(),
                                         dfs_for_graph.std(),
                                         dfs_for_graph.min(),
                                         dfs_for_graph.max()],
                                         index=['mean', 'std', 'min', 'max'],
                                         columns=dfs_for_graph.columns)

    return dfs, dfs_for_graph, dfs_for_graph_all


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
    index = [item.split('.')[0] for item in bvals]
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

        stats_per_subjects[filename] = pd.DataFrame([values], index=[index[i]],
                                                    columns=columns)

    stats = pd.DataFrame(values_stats, index=index,
                         columns=column_names)

    stats_across_subjects = pd.DataFrame([stats.mean(),
                                         stats.std(),
                                         stats.min(),
                                         stats.max()],
                                         index=['mean', 'std', 'min', 'max'],
                                         columns=column_names)

    return stats_per_subjects, stats, stats_across_subjects, shells


def identify_shells(bvals, threshold=40.0, roundCentroids=False, sort=False):
    """
    Guessing the shells from the b-values. Returns the list of shells and, for
    each b-value, the associated shell.

    Starting from the first shell as holding the first b-value in bvals,
    the next b-value is considered on the same shell if it is closer than
    threshold, or else we consider that it is on another shell. This is an
    alternative to K-means considering we don't already know the number of
    shells K.

    Note. This function should be added in Dipy soon.

    Parameters
    ----------
    bvals: array (N,)
        Array of bvals
    threshold: float
        Limit value to consider that a b-value is on an existing shell. Above
        this limit, the b-value is placed on a new shell.
    roundCentroids: bool
        If true will round shell values to the nearest 10.
    sort: bool
        Sort centroids and shell_indices associated.

    Returns
    -------
    centroids: array (K)
        Array of centroids. Each centroid is a b-value representing the shell.
        K is the number of identified shells.
    shell_indices: array (N,)
        For each bval, the associated centroid K.
    """
    if len(bvals) == 0:
        raise ValueError('Empty b-values.')

    # Finding centroids
    bval_centroids = [bvals[0]]
    for bval in bvals[1:]:
        diffs = np.abs(np.asarray(bval_centroids, dtype=float) - bval)
        if not len(np.where(diffs < threshold)[0]):
            # Found no bval in bval centroids close enough to the current one.
            # Create new centroid (i.e. new shell)
            bval_centroids.append(bval)
    centroids = np.array(bval_centroids)

    # Identifying shells
    bvals_for_diffs = np.tile(bvals.reshape(bvals.shape[0], 1),
                              (1, centroids.shape[0]))

    shell_indices = np.argmin(np.abs(bvals_for_diffs - centroids), axis=1)

    if roundCentroids:
        centroids = np.round(centroids, decimals=-1)

    if sort:
        sort_index = np.argsort(centroids)
        sorted_centroids = np.zeros(centroids.shape)
        sorted_indices = np.zeros(shell_indices.shape)
        for i in range(len(centroids)):
            sorted_centroids[i] = centroids[sort_index[i]]
            sorted_indices[shell_indices == i] = sort_index[i]
        return sorted_centroids, sorted_indices

    return centroids, shell_indices
