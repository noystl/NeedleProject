import math
import os
import time

import folium
import overpy
import pandas as pd
import json
from sklearn.metrics import precision_score, recall_score, accuracy_score
from Evaluation import eval_util
from PointTag import PointTag
import glob
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits import mplot3d
import OsmDataCollector

RATIO_MAX = 10  # the experiment's max ratio value
THRESH_MAX = 20  # the experiment's max thresh value
THRESH_STEP = 5  # the experiment's thresh step


def get_interest_points(box: list, node_tag: str) -> pd.DataFrame:
    """
    Uses Overpass-API to extract the coordinates of interest points inside self.box.
    :param box: a list containing the track bounding box (boundaries) coordinates: [western limit, southern limit,
    eastern limit, northern limit]
    :param node_tag: What kind of interest point should be extracted. For example: "historic".
    For more information:
    https://wiki.openstreetmap.org/wiki/Map_Features
    https://towardsdatascience.com/loading-data-from-openstreetmap-with-python-and-the-overpass-api-513882a27fd0
    :return: a pandas df (lat, lon) containing the
    """
    overpass_api = overpy.Overpass()
    while True:
        try:
            r = overpass_api.query("""node(""" + str(box[1]) + """,""" + str(box[0]) +
                                   """,""" + str(box[3]) + """,""" + str(box[2]) + """)
                                   [""" + node_tag + """]; out;""")
            break
        except overpy.exception.OverpassTooManyRequests as e:
            print(str(e))

    return pd.DataFrame([{'lat': p.lat, 'lon': p.lon} for p in r.nodes])


def get_model_predictions(tracks: list, tracks_candidates: list, closeness_thresh=200, sample_ratio=1 / 10) -> list:
    """
    Gets the predictions of the models for the given tracks with the given number of neighbors.
    :param tracks: a list of OsmTrack objects
    given tracks.
    :param tracks_candidates: a panda's df list holding the candidates corresponding to the tracks in <tracks>
    :param sample_ratio: we sample 1/sample_ratio of the track points to determine if a candidate
    interest point belongs to it.
    :param closeness_thresh: we consider a candidate interest point as a part of the track if it's closer then
    closeness_thresh to any of the track's points.
    :return: a list of the predicted results for the existence of an interest point near the given tracks.
    """
    predictions = [0]*len(tracks)
    for track_idx, track in enumerate(tracks):
        candidate_points = tracks_candidates[track_idx]
        for idx, point in candidate_points.iterrows():
            if track.is_close(point, closeness_thresh, sample_ratio):
                predictions[track_idx] = 1
                break
    return predictions


def adjust_data(exp_data: pd.DataFrame, feature: PointTag):
    """
    Adjusts the actual tags of the data to be 1 if the tested feature appears in the actual tag, 0
    if not and None if the data doe's not contain tags (and therefore may not be trusted).
    :param exp_data: a df (gpx, real) where 'gpx' containing paths of track gpx files, and 'real'
    containing a list of the interest  points the corresponding tracks contain.
    :param feature: the feature tested in this experiment.
    """
    feature_tags = []
    for feature_list in exp_data['real']:
        if not feature_list:
            feature_tags.append(None)
        if feature.value in feature_list:
            feature_tags.append(1)
        else:
            feature_tags.append(0)
    feature_tags_df = pd.DataFrame({'real': feature_tags})
    exp_data.update(feature_tags_df)


def get_exp_results(exp_data: pd.DataFrame, tracks: list, tracks_candidates: list) -> dict:
    """
    Gets the accuracy, precision and recall of the algorithm for different values of 'sampling ratio' (=
    we sample 1/sample_ratio of the track points to determine if a candidate
    interest point belongs to it.)
    :param exp_data: a df (gpx, real) where 'gpx' containing paths of track gpx files, and 'real'
    containing a list of the interest  points the corresponding tracks contain.
    :param tracks: a list of OsmTrack objects
    :param tracks_candidates: a panda's df list holding the candidates corresponding to the tracks in <tracks>
    :return: a dictionary of the form {'accuracy': [], 'precision': [], 'recall': []} containing the values
    of accuracy, precision and recall for different sampling ratios and accuracy threshold values.
    """
    results = {'accuracy': [], 'precision': [], 'recall': []}
    real = exp_data['real'].values.tolist()

    for ratio in range(1, RATIO_MAX + 1):
        print("\tratio: ", 1/ratio)
        for thresh in range(0, THRESH_MAX + 1, THRESH_STEP):
            print("\t\tthresh: ", thresh)

            predictions = get_model_predictions(tracks, tracks_candidates, thresh, sample_ratio=(1/ratio))
            results['accuracy'].append(accuracy_score(real, predictions))
            results['precision'].append(precision_score(real, predictions))
            results['recall'].append(recall_score(real, predictions))
    return results


def get_candidates(area_path, tested_feature, tracks) -> list:
    """
    saves the experiment's data (csv candidates files)under area_path, and returns the tracks candidates list.
    :param area_path: the directory under which we want to save our experiment's data
    :param tested_feature: the feature tested in this experiment.
    :param tracks: a list of OsmTrack objects
    :return: a panda's df list holding the corresponding candidates of the tracks in <tracks>
    """
    query_list = {PointTag.HISTORIC: """ "historic" """, PointTag.WATERFALL: """ "waterway" = "waterfall" """,
                  PointTag.WATER: """ "natural" = "water" """, PointTag.BIRDING: """ "leisure" = "bird_hide" """,
                  PointTag.CAVE: """ "natural" = "cave_entrance" """, PointTag.GEOLOGIC: """ "geological" """,
                  PointTag.RIVER: """ "waterway" = "river" """, PointTag.SPRING: """ "natural" = "spring" """}

    print("mining...")
    if not os.path.exists(area_path):
        os.makedirs(area_path)

    saved_tracks = glob.glob(area_path + '\\*.csv')
    last_track = len(saved_tracks)

    for i in np.arange(last_track, len(tracks)):
        print("\t", i+1, "/", len(tracks))
        path = os.path.join(area_path, str(i) + ".csv")
        track = tracks[i]
        track_bb = [track.boundaries['west'], track.boundaries['south'], track.boundaries['east'],
                    track.boundaries['north']]
        track_ips = get_interest_points(track_bb, query_list[tested_feature])
        track_ips.to_csv(path)

    candidates = []
    for i in range(len(glob.glob(area_path + '\\*.csv'))):
        candidates.append(pd.read_csv(os.path.join(area_path, str(i) + ".csv")))
    return candidates


def eval_interest_points(tested_feature: PointTag) -> dict:
    """
    Evaluates the ability of the model to associate interest points to a track, over the New Zealand Data.
    :param tested_feature: we will evaluate the ability of the model to check if an interest point of this types
    belongs to a track.
    :returns: a dictionary of the form {'accuracy': [], 'precision': [], 'recall': []} containing the values
    of accuracy, precision and recall for different sampling ratios and accuracy threshold values.
    """
    print("setup...")

    area_path = 'interest_points_eval\\nz'
    exp_data = eval_util.get_exp_dataframe('features')
    adjust_data(exp_data, tested_feature)
    exp_data = exp_data[(exp_data['real'] == 1) | (exp_data['real'] == 0)]
    exp_data = exp_data.reset_index(drop=True)

    tracks = [eval_util.convert_to_osm(exp_data.gpx[i], i) for i in range(len(exp_data))]

    candidates = get_candidates(area_path, tested_feature, tracks)

    print("experimenting...")
    res_file_path = os.path.join(area_path, tested_feature.value + ".json")
    if not os.path.exists(res_file_path):
        exp_results = get_exp_results(exp_data, tracks, candidates)
        with open(res_file_path, 'w') as f:
            json.dump(exp_results, f, indent=4)

    else:
        with open(res_file_path, "r") as f:
            file = f.read()
        exp_results = json.loads(file)

    return exp_results


def visualize_experiment_results(experiment_res: dict, quality: str):
    """
    :param experiment_res: the interest points experiment results
    :param quality: the quality we want to plot (from {'recall', 'precision', 'accuracy'})
    """
    qualities = {'recall', 'precision', 'accuracy'}
    assert(quality in qualities)

    ratio = np.array([1 / i for i in range(1, RATIO_MAX + 1)])  # sampling ratio
    thresh = np.arange(0, THRESH_MAX + 1, THRESH_STEP)  # closeness thresh

    X, Y = np.meshgrid(thresh, ratio)
    Z = np.array(experiment_res[quality]).reshape(RATIO_MAX, THRESH_MAX // THRESH_STEP + 1)

    ax = plt.axes(projection="3d")
    ax.plot_wireframe(Y, X, Z, color='green')
    ax.set_xlabel('sampling ratio')
    ax.set_ylabel('closeness thresh (meters)')
    ax.set_zlabel(quality)

    # change axis range to even the graph's representations:
    ax.set_xlim3d(0, 1)
    ax.set_ylim3d(0, 200)
    ax.set_zlim3d(0, 1)

    ax.plot_surface(Y, X, Z, rstride=1, cstride=1,
                    cmap='PuBuGn', edgecolor='none')
    ax.set_title('Quality of Connecting Interest Point: ' + val + ' to Tracks: ' + quality)
    plt.show()


if __name__ == '__main__':
    tag = PointTag.WATERFALL
    val = str(tag.value)

    # RUN THE EXPERIMENT:
    res = eval_interest_points(tag)

    # EXPERIMENT VISUALIZATION:
    for quality in {'recall', 'precision', 'accuracy'}:
        visualize_experiment_results(res, quality)
