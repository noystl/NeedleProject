"""
A utility module supplies functions that can be used for any classifier evaluation.
"""
import gpxpy.gpx
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from OsmTrack import OsmTrack

EVAL_DATA_PATH = 'EvalData\\hp\\gpx\\Philippines\\progress.json'  # Just until the real test data will be ready.
GPX_REL_PATH = 'EvalData\\hp\\gpx\\Philippines\\'


def get_exp_dataframe(attr_name: str) -> pd.DataFrame:
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
    :param attr_name: we want to test the ability of our model to predict the attribute with this name.
    attr_name should be one of the next strings: 'shape', 'length', 'difficulty', 'features'.
    :return: pandas df (gpx, real, predicted)
    """
    assert attr_name in {'difficulty', 'length', 'shape', 'features'}
    eval_data = pd.read_json(EVAL_DATA_PATH)
    eval_data = eval_data.transpose()
    eval_data.columns = ['gpx', 'difficulty', 'length', 'shape', 'features']
    eval_data = eval_data[['gpx', attr_name]]
    eval_data.columns = ['gpx', 'real']

    gpx_paths = []
    for i in range(len(eval_data)):
        gpx_paths.append(GPX_REL_PATH + str(i) + '.gpx')
    gpx_indices_df = pd.DataFrame({'gpx': gpx_paths})
    eval_data.update(gpx_indices_df)
    return eval_data


def convert_to_osm(gpx_path: str, idx: int) -> OsmTrack:
    """
    Converts the gpx in gpx_path into an OsmTrack object.
    :param gpx_path: the relative path of the gpx file, for example: 'hp\\gpx\\Philippines\\0.gpx'
    :param idx: the index of the track to be created.
    :return: the OsmTrack object created out of the gpx in the given path.
    """
    file = open(gpx_path, 'r', encoding="utf8")
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

