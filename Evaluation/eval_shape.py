from Evaluation import eval_util
from TrackShape import TrackShape
from sklearn import metrics


def get_model_predictions(tracks: list, thresh=100) -> list:
    """
    Gets the model's predictions for the shapes of the given tracks.
    :param tracks: a list of OsmTracks objects.
    :param thresh: The loop-threshold model will use to make predictions
    :return: the shape-predictions of the model for the given tracks.
    """
    predictions = []
    for track in tracks:
        predictions.append(track.deduce_track_shape(thresh).value)
    return predictions


def eval_shape():
    """
    Evaluates the ability of the model to predict the track shape.
    """
    exp_data = eval_util.get_exp_dataframe('shape')
    exp_data = exp_data.replace('point to point', TrackShape.CURVE.value)
    exp_data = exp_data.replace('point to point Very', TrackShape.CURVE.value)
    exp_data = exp_data.replace('out and back', TrackShape.CURVE.value)
    tracks = [eval_util.convert_to_osm(exp_data.gpx[i], i) for i in range(len(exp_data))]
    results = {'accuracy': [], 'precision': [], 'recall': []}

    for thresh in range(1, 125):
        predictions = get_model_predictions(tracks, thresh)
        real = exp_data['real'].values.tolist()
        results['accuracy'].append(metrics.accuracy_score(real, predictions))
        results['precision'].append(
            metrics.precision_score(real, predictions, zero_division=1, pos_label=TrackShape.LOOP.value))
        results['recall'].append(
            metrics.recall_score(real, predictions, zero_division=1, pos_label=TrackShape.LOOP.value))
    return results


if __name__ == '__main__':
    eval_util.plot_results(eval_shape(), 'Shape Classification Quality', 'Loop Threshold(m)')
