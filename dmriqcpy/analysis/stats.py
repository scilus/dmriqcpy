
# -*- coding: utf-8 -*-

import nibabel as nib
import numpy as np
import pandas as pd


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
        DataFrame containing mean, std, min and max of mean and medians.
        across subjects
    """
    values = []
    for filename in filenames:
        data = nib.load(filename).get_data()

        mean = np.mean(data[data > 0])
        median = np.median(data[data > 0])

        values.append(
            [mean, median])

    stats_per_subjects = pd.DataFrame(values, index=[filenames],
                                      columns=column_names)

    stats_across_subjects = pd.DataFrame([stats_per_subjects.mean(),
                                          stats_per_subjects.std(),
                                          stats_per_subjects.min(),
                                          stats_per_subjects.max()],
                                         index=['mean', 'std', 'min', 'max'],
                                         columns=column_names)

    return stats_per_subjects, stats_across_subjects


def stats_mean_in_tissues(column_names, images, wm_images, gm_images,
                          csf_images):
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
        DataFrame containing mean, std, min and max of mean.
        across subjects
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

        values.append(
            [data_wm, data_gm, data_csf, data_max])

    stats_per_subjects = pd.DataFrame(values, index=[images],
                                      columns=column_names)

    stats_across_subjects = pd.DataFrame([stats_per_subjects.mean(),
                                          stats_per_subjects.std(),
                                          stats_per_subjects.min(),
                                          stats_per_subjects.max()],
                                         index=['mean', 'std', 'min', 'max'],
                                         columns=column_names)

    return stats_per_subjects, stats_across_subjects
