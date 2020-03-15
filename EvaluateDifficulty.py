import slopeMap as sm
import pandas as pd
import OsmTrack
import os
import json
import TrackDifficulty as td


class DifficultyEvaluator:
    gpx_dir_path = 'hp\\gpx'
    pts_dir_path = 'hp\\tracks'
    shingles_dir_path = 'hp\\shingles'
    seen_path = 'hp\\seen.json'

    def __init__(self, area_fname, area_topleft, shingle_length):
        """
        ctor
        :param area_fname: path to hgt file relevant to tested area
        :param area_topleft: list of length 2 with top left coordiantes of area file (at area_fname)
        """
        self._area_fname = area_fname
        self._area_topleft = area_topleft
        self._shingle_length = shingle_length
        self._shingle_db = {}  # we're going to query shingles a lot in a run and we want to compute shingles once

    def get_shingles(self, points: pd.DataFrame) -> set:
        """
        Converts the given track into a set of shingles.
        :param points: a pandas df containing the lat lon of the points consisting a gps track.
        :return: a set of the slope-shingles appearing in the track.
        """
        pts = points.to_numpy()
        elev = sm.compute_track_elevation(self._area_fname, self._area_topleft, pts)
        path_length = sm.compute_track_km(pts)[-1]
        slopes = sm.compute_slope(pts, elev, path_length)
        return self.shingle_slopes(slopes, self._shingle_length)

    @staticmethod
    def shingle_slopes(slopes: list, shingle_length=1):
        """
        generate shingles
        :param slopes: python list of slopes in path (length n)
        :param shingle_length: integer, number of slopes to use per shingle
        :returns: set of unique shingles in <slopes>
        (values of shingles are integers with up to 2 * <shingle_length> digits)
        """
        singles = DifficultyEvaluator.adjust_slopes(slopes)
        if shingle_length == 1:
            return set(singles)
        res = []
        for i in range(len(slopes) - shingle_length + 1):
            shingle = 0
            for j in range(shingle_length):
                shingle *= 100
                shingle += singles[i + j]
            res.append(shingle)
        return set(res)

    @staticmethod
    def adjust_slopes(slopes):
        """
        takes a set of slopes and rounds the values to nearest 10 degrees
        :param slopes: python set of all slopes appearing in the track
        :return: a set of all slopes are adjusted to values between 0 and 19 (inclusive)
        where 0 is -90 defree, 1 is -80 ... 19 is 90 degrees
        """
        # the scaling values as whole integers 0 to 19 is to allow for creating shingles of multiple slopes
        result = []
        for slope in slopes:
            result.append(int((slope // 10) + 9))
        return result

    @staticmethod
    def _calc_hp_slopes(dictionary: dict):
        """
        reformats dictionary into the form {key: [slopes, difficulty]}
        where slopes is a list of floats and difficulty is a string
        """
        res = {}
        for key in dictionary.keys():
            slope = sm.compute_slope(dictionary[key][0], dictionary[key][1], dictionary[key][2])
            res[key] = [slope, dictionary[key][-1]]
        return res

    @staticmethod
    def get_hp_slopes(length):
        """
        collects tracks from hp dataset which match the length of a given path
        """
        path = os.path.join(DifficultyEvaluator.pts_dir_path, str(sm.get_length_tag(length)) + '.json')
        dictionary = {}

        if os.path.exists(path):
            with open(path, "r") as f:
                file = f.read()
            dictionary = json.loads(file)
        return DifficultyEvaluator._calc_hp_slopes(dictionary)

    def get_hp_shingled_tracks(self, path_length):
        """
        returns shingles paths of similar length to path being checked
        :param path_length: length of test path (float)
        """
        # currently assume data saved is slopes of same tick as osms one
        # in the future create function that reads gps coords into correctly ticked data
        db_key = str(sm.get_length_tag(path_length)) + "shingle_len" + str(self._shingle_length)

        # checks if data was already gathered during this run
        if db_key in self._shingle_db.keys():
            return self._shingle_db[db_key]

        # checks if data was already gathered during some other run
        path = os.path.join(DifficultyEvaluator.shingles_dir_path, db_key + '.json')
        if os.path.exists(path):
            with open(path, "r") as f:
                file = f.read()
            data_jason = json.loads(file)
            tmp = {}
            for key in data_jason.keys():
                tmp[key] = [set(data_jason[key][0]), data_jason[key][1]]
            self._shingle_db[db_key] = tmp
            return self._shingle_db[db_key]

        # calculates the shingles according to parameters
        slopes = self.get_hp_slopes(path_length)
        res = {}
        res_json = {}
        for key in slopes.keys():
            shingled = self.shingle_slopes(slopes[key][0], self._shingle_length)
            res[key] = [shingled, slopes[key][1]]
            res_json[key] = [list(shingled), slopes[key][1]]

        # saves the data both for run and locally for future runs
        self._shingle_db[db_key] = res
        if not os.path.exists(DifficultyEvaluator.shingles_dir_path):
            os.makedirs(DifficultyEvaluator.shingles_dir_path)
        with open(path, 'w') as f:
            json.dump(res_json, f, indent=4)
        return res

    def pred_difficulty_known_heights(self, track: pd.DataFrame, k: int):
        points = track[['lat', 'lon']]
        pts = points.to_numpy()
        elev = track['elev']
        path_length = sm.compute_track_km(pts)[-1]
        slopes = sm.compute_slope(pts, elev, path_length)
        osm_shingles = self.shingle_slopes(slopes, self._shingle_length)

        shingle_dict = self.get_hp_shingled_tracks(path_length)
        id = shingle_dict.keys()

        shingle_lst = []
        diff_lst = []
        # not sure if getting keys and values are returned ordered so im inserting them manually
        for key in id:
            shingle_lst.append(shingle_dict[key][0])
            diff_lst.append(shingle_dict[key][-1])

        best_indexes, best_values = DifficultyEvaluator.get_k_best(osm_shingles, shingle_lst, k)

        res_dict = {td.TrackDifficulty.EASY.value: 0, td.TrackDifficulty.INTERMEDIATE.value: 0,
                    td.TrackDifficulty.DIFFICULT.value: 0, td.TrackDifficulty.V_DIFFICULT.value: 0}

        for i in range(len(best_indexes)):
            res_dict[diff_lst[best_indexes[i]]] += best_values[i]

        best_key = ""
        best_score = -1
        for key in res_dict.keys():
            if res_dict[key] > best_score:
                best_score = res_dict[key]
                best_key = key
        if best_key == td.TrackDifficulty.EASY.value:
            result = td.TrackDifficulty.EASY
        elif best_key == td.TrackDifficulty.INTERMEDIATE.value:
            result = td.TrackDifficulty.INTERMEDIATE
        elif best_key == td.TrackDifficulty.DIFFICULT.value:
            result = td.TrackDifficulty.DIFFICULT
        elif best_key == td.TrackDifficulty.V_DIFFICULT.value:
            result = td.TrackDifficulty.V_DIFFICULT
        return result

    def pred_difficulty(self, osm_track: OsmTrack, k):
        """

        """
        osm_shingles = self.get_shingles(osm_track.gps_points.iloc[:, :-1])
        shingle_dict = self.get_hp_shingled_tracks(osm_track.length)
        id = shingle_dict.keys()

        shingle_lst = []
        diff_lst = []
        # not sure if getting keys and values are returned ordered so im inseting them manually
        for key in id:
            shingle_lst.append(shingle_dict[key][0])
            diff_lst.append(shingle_dict[key][-1])

        best_indexes, best_values = DifficultyEvaluator.get_k_best(osm_shingles, shingle_lst, k)
        res_dict = {td.TrackDifficulty.EASY.value: 0, td.TrackDifficulty.INTERMEDIATE.value: 0,
                    td.TrackDifficulty.DIFFICULT.value: 0, td.TrackDifficulty.V_DIFFICULT.value: 0}
        for i in range(len(best_indexes)):
            res_dict[diff_lst[best_indexes[i]]] += best_values[i]

        best_key = ""
        best_score = -1
        for key in res_dict.keys():
            if res_dict[key] > best_score:
                best_score = res_dict[key]
                best_key = key
        if best_key == td.TrackDifficulty.EASY.value:
            result = td.TrackDifficulty.EASY
        elif best_key == td.TrackDifficulty.INTERMEDIATE.value:
            result = td.TrackDifficulty.INTERMEDIATE
        elif best_key == td.TrackDifficulty.DIFFICULT.value:
            result = td.TrackDifficulty.DIFFICULT
        elif best_key == td.TrackDifficulty.V_DIFFICULT.value:
            result = td.TrackDifficulty.V_DIFFICULT
        return result

    @staticmethod
    def get_jacc(set1: set, set2: set) -> float:
        """
        given 2 python sets returns their jaccard similarity
        :return: float representing similarity (in [0,1])
        """
        union_set = set.union(set1, set2)
        intersection_set = set.intersection(set1, set2)
        return len(intersection_set) / len(union_set)

    @staticmethod
    def get_k_best(item: set, cmp_lst: list, k: int):
        """
        :param item: set to be scores against
        :param cmp_lst: list of sets
        :param k: interger, number of most similar sets
        :return: list of length <=k of indexes of to set from cmp_lst and a list of same size of their similarity
        """
        i = 0
        lowest_val = 1  # lowest value in the list
        lowest_index = -1  # index of lowest value (in res not in cmp_lst)
        res = []
        res_val = []
        # push the first k tracks into the list
        while i < len(cmp_lst):
            similarity = DifficultyEvaluator.get_jacc(item, cmp_lst[i])
            res.append(i)
            res_val.append(similarity)
            if similarity < lowest_val:
                lowest_index = i
                lowest_val = similarity
            i += 1
            if i == k:
                break
        else:  # else happens if cmp_lst length is less than k
            return res, res_val

        while i < len(cmp_lst):
            similarity = DifficultyEvaluator.get_jacc(item, cmp_lst[i])
            if similarity > lowest_val:
                res[lowest_index] = i
                res_val[lowest_index] = similarity
                tmp = DifficultyEvaluator.get_min_index(res_val)
                lowest_val = res_val[tmp]
                lowest_index = tmp
            i += 1
        return res, res_val

    @staticmethod
    def get_min_index(lst):
        """
        returns the index of the minimal element
        """
        min = lst[0]
        min_index = 0
        i = 1
        while i < len(lst):
            if min > lst[i]:
                min = lst[i]
                min_index = i
            i += 1
        return min_index

