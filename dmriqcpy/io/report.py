# -*- coding: utf-8 -*-

from os.path import dirname, join, realpath
from shutil import copytree

from jinja2 import Environment, FileSystemLoader


class Report():
    """
    Class to create html report for dmriqc.
    """
    def __init__(self, report_name):
        """
        Initialise the Report Class.

        Parameters
        ----------
        report_name : string
            Report name in html format.
        """
        self.path = dirname(realpath(__file__))
        self.env = Environment(loader=FileSystemLoader(
            join(self.path, "../template")))

        self.report_name = report_name
        if ".html" not in self.report_name:
            self.report_name += ".html"

    def generate(self, title=None, nb_subjects=None,
                 summary_dict=None, graph_array=None, metrics_dict=None,
                 warning_dict=None):
        """
        Generate and save the report.

        Parameters
        ----------
        title : string
            Title of the report, name displayed in the browser tab.
        nb_subjects : int
            Number of subjects.
        summary_dict : dict
            Dictionnary of the statistic summaries for each metric.
            summary_dict[METRIC_NAME] = HTML_CODE
        graph_array : array
            Array of graph div from plotly to display in the summary
            tab.
        metrics_dict : dict
            Dictionnary of the subjects informations for each metric.
            metrics_dict[METRIC_NAME] = {SUBJECT:
                                            { 'stats': HTML_CODE,
                                              'screenshot': IMAGE_PATH}
                                        }
        warning_dict : dict
            Dictionnary of warning subjects for each metric.
            warning_dict[METRIC_NAME] = { 'WANING_TYPE': ARRAY_OF_SUBJECTS,
                                          'nb_warnings': NUMBER_OF_SUBJECTS}
        """

        copytree(join(self.path, "../template/libs"), "libs",
                 copy_function=copy)

        with open(self.report_name, 'w') as out_file:
            template = self.env.get_template('template.html')
            rendered = template.render(title=title,
                                       nb_subjects=nb_subjects,
                                       summary_dict=summary_dict,
                                       graph_summ=graph_array,
                                       metrics_dict=metrics_dict,
                                       warning_list=warning_dict)
            out_file.write(rendered)
            out_file.close()
