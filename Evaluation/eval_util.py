"""
A utility module supplies functions that can be used for any classifier evaluation.
"""
import os
import gpxpy.gpx
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from OsmTrack import OsmTrack


def get_exp_dataframe(attr_name: str, data_type='validation') -> pd.DataFrame:
    """
    Creates a pandas df with 2 columns: (gpx, real) based on the data in data_path.
    For example, with attr_name == 'difficulty', those might be some typical lines in the df:
    gpx                       |   real
    ---------------------------------------
    'hp\\gpx\\France\\0.gpx'     'Easy'
    'hp\\gpx\\France\\30.gpx'    'Difficult'
    'hp\\gpx\\Germany\\7.gpx'    'Easy'
    ...
    Where the values in gpx are relative paths of gpx files, and real containing the true value of the given attribute
    for the tracks the gpx files represent.
    :param data_type: the path of the data for the experiment (could be either 'validation' or 'test')
    :param attr_name: we want to test the ability of our model to predict the attribute with this name.
    attr_name should be one of the next strings: 'shape', 'length', 'difficulty', 'features'.
    :return: pandas df (gpx, real, predicted)
    """
    # For now (until we'll implement functionality for gathering test data):
    if attr_name == 'shape':
        real_values = ['point to point', 'point to point', 'point to point', 'point to point', 'point to point',
                       'point to point', 'point to point', ]
    else:
        real_values = ['Difficult', 'Intermediate', 'Intermediate', 'Intermediate', 'Intermediate',
                       'Difficult', 'Difficult']

    for_tests = {'gpx': ['hp\\gpx\\Philippines\\0.gpx', 'hp\\gpx\\Philippines\\1.gpx', 'hp\\gpx\\Philippines\\2.gpx',
                         'hp\\gpx\\Philippines\\3.gpx', 'hp\\gpx\\Philippines\\4.gpx', 'hp\\gpx\\Philippines\\5.gpx',
                         'hp\\gpx\\Philippines\\6.gpx'],
                 'real': real_values
                 }
    return pd.DataFrame(for_tests, columns=['gpx', 'real'])


def convert_to_osm(gpx_path: str, idx: int) -> OsmTrack:
    """
    Converts the gpx in gpx_path into an OsmTrack object.
    :param gpx_path: the relative path of the gpx file, for example: 'hp\\gpx\\Philippines\\0.gpx'
    :param idx: the index of the track to be created.
    :return: the OsmTrack object created out of the gpx in the given path.
    """
    path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', gpx_path))
    file = open(path, 'r', encoding="utf8")
    gpx = gpxpy.parse(file)
    return OsmTrack(gpx.tracks[0].segments[0], idx)


def plot_results(eval_results: dict, title: str, xlabel: str):
    """
    Plots the evaluation results.
    :param eval_results: a dictionary of the form {'accuracy': [], 'precision': [], 'recall': []} containing the
    the values of accuracy, precision and recall calculated for the prediction model using different parameters.
    :param title: The title of the plot.
    :param xlabel: the label of axis x, the parameter against which the model was tested (for example, the
    loop-threshold when evaluating the ability of the model to recognize loops.)
    """
    plt.figure(title)
    plt.title(title)
    plt.xlabel(xlabel)
    loop_thresh = np.arange(1, len(eval_results['accuracy']) + 1)
    plt.plot(loop_thresh, eval_results['accuracy'], label='accuracy')
    plt.plot(loop_thresh, eval_results['precision'], label='precision')
    plt.plot(loop_thresh, eval_results['recall'], label='recall')
    plt.legend()
    plt.show()
