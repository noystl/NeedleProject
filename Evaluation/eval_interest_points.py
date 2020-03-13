import overpy
import pandas as pd
from sklearn import metrics
from Evaluation import eval_util
from PointTag import PointTag


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
    r = overpass_api.query("""
    node(""" + str(box[1]) + """,""" + str(box[0]) + """,""" + str(box[3]) + """,""" +
                           str(box[2]) + """)[""" + node_tag + """]; out;""")
    return pd.DataFrame([{'lat': p.lat, 'lon': p.lon} for p in r.nodes])


def get_model_predictions(tracks: list, feature: PointTag, closeness_thresh=200, sample_ratio=1 / 10) -> list:
    """
    Gets the predictions of the models for the given tracks with the given number of neighbors.
    :param feature: the tested feature (interest-point type)
    :param sample_ratio: we sample 1/sample_ratio of the track points to determine if a candidate
    interest point belongs to it.
    :param closeness_thresh: we consider a candidate interest point as a part of the track if it's closer then
    closeness_thresh to any of the track's points.
    :param tracks: a list of OsmTrack objects
    given tracks.
    :return: a list of the predicted difficulty levels of the givien tracks.
    """

    query_list = {PointTag.HISTORIC: """ "historic" """, PointTag.WATERFALL: """ "waterway" = "waterfall" """,
                  PointTag.WATER: """ "natural" = "water" """, PointTag.BIRDING: """ "leisure" = "bird_hide" """,
                  PointTag.CAVE: """ "natural" = "cave_entrance" """, PointTag.GEOLOGIC: """ "geological" """,
                  PointTag.RIVER: """ "waterway" = "river" """, PointTag.SPRING: """ "natural" = "spring" """}

    predictions = [0]*len(tracks)

    for track_idx, track in enumerate(tracks):
        track_bb = [track.boundaries['west'], track.boundaries['south'], track.boundaries['east'],
                    track.boundaries['north']]
        candidate_points = get_interest_points(track_bb, query_list[feature])
        for idx, point in candidate_points.iterrows():
            if track.is_close(point, closeness_thresh, sample_ratio):
                predictions[track_idx] = 1
                break
    return predictions


def adjust_data(exp_data: pd.DataFrame, feature: PointTag):
    """
    Adjusts the actual tags of the data to be 1 if the tested feature appears in the actual tag and 0
    otherwise.
    :param exp_data: a df (gpx, real) where 'gpx' containing paths of track gpx files, and 'real'
    containing a list of the interest  points the corresponding tracks contain.
    :param feature: the feature tested in this experiment.
    """
    feature_tags = []
    for feature_list in exp_data['real']:
        if not feature_list:
            feature_tags.append(2)              # todo: fix this bad code, I should insert there None ore something.
        if feature.value in feature_list:
            feature_tags.append(1)
        else:
            feature_tags.append(0)
    feature_tags_df = pd.DataFrame({'real': feature_tags})
    exp_data.update(feature_tags_df)


def get_results_closeness_exp(exp_data: pd.DataFrame, tracks: list) -> dict:
    """
    Gets the accuracy, precision and recall of the algorithm for different values of 'closeness threshold' (=
    we say that an interest point belongs to some track if the minimal distance from it to the track is smaller
    than this threshold)
    :param exp_data: a df (gpx, real) where 'gpx' containing paths of track gpx files, and 'real'
    containing a list of the interest  points the corresponding tracks contain.
    :param tracks: a list of OsmTrack objects
    :return: a dictionary of the form {'accuracy': [], 'precision': [], 'recall': []} containing the values
    of accuracy, precision and recall for different thresholds.
    """
    results = {'accuracy': [], 'precision': [], 'recall': []}

    for thresh in range(1, 100):
        predictions = get_model_predictions(tracks, PointTag.WATERFALL, thresh)
        real = exp_data['real'].values.tolist()
        results['accuracy'].append(metrics.accuracy_score(real, predictions))
        results['precision'].append(metrics.precision_score(real, predictions, zero_division=1))
        results['recall'].append(metrics.recall_score(real, predictions, zero_division=1))
    return results


def get_results_sampling_exp(exp_data: pd.DataFrame, tracks: list) -> dict:
    """
    Gets the accuracy, precision and recall of the algorithm for different values of 'sampling ratio' (=
    we sample 1/sample_ratio of the track points to determine if a candidate
    interest point belongs to it.)
    :param exp_data: a df (gpx, real) where 'gpx' containing paths of track gpx files, and 'real'
    containing a list of the interest  points the corresponding tracks contain.
    :param tracks: a list of OsmTrack objects
    :return: a dictionary of the form {'accuracy': [], 'precision': [], 'recall': []} containing the values
    of accuracy, precision and recall for different sampling ratios.
    """
    results = {'accuracy': [], 'precision': [], 'recall': []}

    for i in range(1, 50):
        predictions = get_model_predictions(tracks, PointTag.WATERFALL, sample_ratio=(1/i))
        real = exp_data['real'].values.tolist()
        results['accuracy'].append(metrics.accuracy_score(real, predictions))
        results['precision'].append(metrics.precision_score(real, predictions, zero_division=1))
        results['recall'].append(metrics.recall_score(real, predictions, zero_division=1))
    return results


def eval_interest_points(tested_feature: PointTag) -> tuple:
    """
    Evaluates the ability of the model to classify the tracks by difficulty.
    :param tested_feature: we will evaluate the ability of the model to check if an interest point of this types
    belongs to a track.
    :return a tuple containing the results of two experiments. In the first position, there are the
    sampling ratio experiment results, and in the second, the closeness thresh experiments results.
    """
    exp_data = eval_util.get_exp_dataframe('features')
    adjust_data(exp_data, tested_feature)
    exp_data = exp_data[exp_data['real'] != 2]
    exp_data = exp_data.reset_index(drop=True)

    tracks = [eval_util.convert_to_osm(exp_data.gpx[i], i) for i in range(len(exp_data))]
    samp_experiment_results = get_results_sampling_exp(exp_data, tracks)
    closeness_experiment_results = get_results_closeness_exp(exp_data, tracks)
    return samp_experiment_results, closeness_experiment_results


if __name__ == '__main__':
    eval_util.plot_results(eval_interest_points(PointTag.WATERFALL)[0], 'Quality of Connecting Interest Point: ' +
                           PointTag.WATERFALL.value + ' to Tracks', 'Sampling Ratio')
    eval_util.plot_results(eval_interest_points(PointTag.WATERFALL)[1], 'Quality of Connecting Interest Point: ' +
                           PointTag.WATERFALL.value + ' to Tracks', 'Closeness Threshold (meters)')
