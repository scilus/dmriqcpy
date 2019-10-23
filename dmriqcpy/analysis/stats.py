
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
    column_names : array of strings
        Name of the columns in the summary DataFrame.
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
