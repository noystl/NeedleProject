import math
from sklearn import metrics
from Evaluation import eval_util
from EvaluateDifficulty import DifficultyEvaluator
from TrackDifficulty import TrackDifficulty

TEST_TILES_PATH = 'test_tiles\\'


def get_model_predictions(tracks: list, neighbors=5) -> list:
    """
    Gets the predictions of the models for the given tracks with the given number of neighbors.
    :param tracks: a list of OsmTrack objects
    :param neighbors: the number of neighbors the model is using (in KNN) to evaluate the difficulty of the
    given tracks.
    :return: a list of the predicted difficulty levels of the givien tracks.
    """
    predictions = []
    for track in tracks:
        track_corner = [math.floor(track.boundaries['south']), math.floor(track.boundaries['west'])]
        tile_name = 'N' + str(track_corner[0]) + 'E' + str(track_corner[1])
        diff_evaluator = DifficultyEvaluator(TEST_TILES_PATH + tile_name + '.hgt',
                                             track_corner,
                                             1)
        diff_evaluator.add_difficulty(track)
        predictions.append(track.difficulty.value)
    return predictions


def eval_difficulty():
    """
    Evaluates the ability of the model to classify the tracks by difficulty.
    """
    exp_data = eval_util.get_exp_dataframe('difficulty')
    exp_data.update(exp_data['real'].str.lower())
    exp_data = exp_data.replace('very difficult', TrackDifficulty.DIFFICULT.value)

    tracks = [eval_util.convert_to_osm(exp_data.gpx[i], i) for i in range(len(exp_data))]
    labels = [TrackDifficulty.EASY.value, TrackDifficulty.INTERMEDIATE.value, TrackDifficulty.DIFFICULT.value]
    results = {'accuracy': [], 'precision': [], 'recall': []}

    for thresh in range(1, 3):
        predictions = get_model_predictions(tracks, thresh)
        real = exp_data['real'].values.tolist()
        results['accuracy'].append(metrics.accuracy_score(real, predictions))
        results['precision'].append(metrics.precision_score(real, predictions, labels=labels, average='micro'))
        results['recall'].append(metrics.recall_score(real, predictions, labels=labels, average='micro'))
    return results


if __name__ == '__main__':
    eval_util.plot_results(eval_difficulty(), "Quality of Difficulty Prediction", 'Neighbors')
