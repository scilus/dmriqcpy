# -*- coding: utf-8 -*-
import os

import nibabel as nib
import numpy as np

from dmriqcpy.analysis.utils import get_stats_dataframes


def stats_mean_median(column_names, filenames):
    """
    Compute mean and median values in an image where voxels are higher than 0.

    Parameters
    ----------
    column_names : array of strings
        Name of the columns.
    filenames : array of strings
        Array of filenames in Nifti format.

    Returns
    -------
    stats_per_subjects : DataFrame
        DataFrame containing mean and medians for each subject.
    stats_across_subjects : DataFrame
        DataFrame containing mean, std, min and max of mean and medians
        across subjects.
    """
    values = []

    for filename in filenames:
        data = nib.load(filename).get_data()
        shape = data.shape

        if len(shape) > 3:
            sub = list(data[shape[0] // 2, shape[1] // 2, shape[2] // 2, :])
            idx = sub.index(max(sub))
            data = data[:, :, :, idx]
        mean = np.mean(data[data > 0])
        median = np.median(data[data > 0])

        values.append([mean, median])

    return get_stats_dataframes(filenames, values, column_names)


def stats_mean_in_tissues(
    column_names, images, wm_images, gm_images, csf_images
):
    """
    Compute mean value in WM, GM and CSF mask.

    Parameters
    ----------
    column_names : array of strings
        Name of the columns.
    images : array of strings
        Array of filenames in Nifti format.
    wm_images : array of strings
        WM filenames in Nifti format.
    gm_images : array of strings
        GM filenames in Nifti format.
    csf_images : array of strings
        CSF filenames in Nifti format.

    Returns
    -------
    stats_per_subjects : DataFrame
        DataFrame containing mean for each subject.
    stats_across_subjects : DataFrame
        DataFrame containing mean, std, min and max of mean across subjects.
    """
    values = []

    for i in range(len(images)):
        data = nib.load(images[i]).get_data()
        wm = nib.load(wm_images[i]).get_data()
        gm = nib.load(gm_images[i]).get_data()
        csf = nib.load(csf_images[i]).get_data()

        data_wm = np.mean(data[wm > 0])
        data_gm = np.mean(data[gm > 0])
        data_csf = np.mean(data[csf > 0])
        data_max = np.max(data[wm > 0])

        values.append([data_wm, data_gm, data_csf, data_max])

    return get_stats_dataframes(images, values, column_names)


def stats_frf(column_names, filenames):
    """
    Compute mean fiber response function.

    Parameters
    ----------
    column_names : array of strings
        Name of the columns.
    filenames : array of strings
        Array of filenames in txt format.

    Returns
    -------
    stats_per_subjects : DataFrame
        DataFrame containing mean for each subject.
    stats_across_subjects : DataFrame
        DataFrame containing mean, std, min and max of mean across subjects.
    """
    values = []

    for filename in filenames:
        frf = np.loadtxt(filename)
        values.append([frf[0], frf[1], frf[3]])

    return get_stats_dataframes(filenames, values, column_names)


def stats_tractogram(column_names, tractograms):
    """
    Compute mean number of streamlines.

    Parameters
    ----------
    column_names : array of strings
        Name of the columns.
    tractograms : array of strings
        Array of tractogram files.

    Returns
    -------
    stats_per_subjects : DataFrame
        DataFrame containing mean for each subject.
    stats_across_subjects : DataFrame
        DataFrame containing mean, std, min and max of mean across subjects.
    """
    values = []

    for tractogram_file in tractograms:
        tractogram = nib.streamlines.load(tractogram_file, lazy_load=True)
        values.append([tractogram.header["nb_streamlines"]])

    return get_stats_dataframes(tractograms, values, column_names)


def stats_mask_volume(column_names, images):
    """
    Compute mean volume in a mask.

    Parameters
    ----------
    column_names : array of strings
        Name of the columns.
    images : array of strings
        Array of filenames in Nifti format.

    Returns
    -------
    stats_per_subjects : DataFrame
        DataFrame containing mean for each subject.
    stats_across_subjects : DataFrame
        DataFrame containing mean, std, min and max of mean across subjects.
    """
    values = []

    for image in images:
        img = nib.load(image)
        voxel_volume = np.prod(img.header["pixdim"][1:4])
        values.append([np.count_nonzero(img.get_data()) * voxel_volume])

    return get_stats_dataframes(images, values, column_names)
