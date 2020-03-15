from sklearn import metrics
from Evaluation import eval_util
from EvaluateDifficulty import DifficultyEvaluator
from TrackDifficulty import TrackDifficulty
import slopeMap as sm

TEST_TILES_PATH = 'test_tiles\\'


def get_model_predictions(tracks: list, shingle_length=1, neighbors=5) -> list:
    """
    Gets the predictions of the models for the given tracks with the given number of neighbors.
    :param shingle_length: The number of elements in a shingle.
    :param tracks: a list of pandas df of the form (lat, lon, time, elev) representing an hp tracks with known
    heights.
    :param neighbors: the number of neighbors the model is using (in KNN) to evaluate the difficulty of the
    given tracks.
    :return: a list of the predicted difficulty levels of the given tracks.
    """
    predictions = []
    diff_evaluator = DifficultyEvaluator(TEST_TILES_PATH + 'N14E120' + '.hgt',
                                         [14, 120],
                                         shingle_length)
    for track in tracks:
        difficulty = diff_evaluator.pred_difficulty_known_heights(track, neighbors)
        predictions.append(difficulty.value)
    return predictions


def eval_difficulty(shingle_length=2):
    """
    Evaluates the ability of the model to classify the tracks by difficulty.
    """
    exp_data = eval_util.get_exp_dataframe('difficulty')

    tracks = []
    real = []
    for idx, row in exp_data.iterrows():
        track = eval_util.read_track_to_df(row.gpx)
        points = track[['lat', 'lon']]
        pts = points.to_numpy()
        path_length = sm.compute_track_km(pts)[-1]
        if path_length < (shingle_length + 1) * sm.TICK:
            continue
        tracks.append(track)
        real.append(row['real'])

    labels = [TrackDifficulty.EASY.value, TrackDifficulty.INTERMEDIATE.value, TrackDifficulty.DIFFICULT.value]
    results = {'accuracy': [], 'precision': [], 'recall': []}

    for k in range(1, 55):
        print('Evaluating for k = ' + str(k))
        predictions = get_model_predictions(tracks, shingle_length, k)
        results['accuracy'].append(metrics.accuracy_score(real, predictions))
        results['precision'].append(metrics.precision_score(real, predictions, labels=labels, average='weighted'))
        results['recall'].append(metrics.recall_score(real, predictions, labels=labels, average='weighted'))
    return results


if __name__ == '__main__':
    eval_util.plot_results(eval_difficulty(), "Quality of Difficulty Prediction", 'Neighbors')
