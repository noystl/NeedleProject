from datasketch import MinHash, MinHashLSH
from slopes_poc import data_generator as genDat
import slopeMap as sm
import numpy as np
import pandas as pd
import os
import json
from slopes_poc import poc, data_generator


class DifficultyEvaluator:
    gpx_dir_path = 'hp\\gpx'
    slopes_dir_path = 'hp\\tracks'
    seen_path = 'hp\\seen.json'

    def __init__(self, datapath, area_fname, area_topleft, shingle_length):
        """
        ctor
        :param datapath: ~~~
        :param area_fname: path to hgt file relevant to tested area
        :param area_topleft: list of length 2 with top left coordiantes of area file (at area_fname)
        """
        self._path = datapath
        self._area_fname = area_fname
        self._area_topleft = area_topleft
        self._shingle_length = shingle_length
        self._shingle_db = {}  # we're going to query shingles a lot in a run and we want to compute shingles once

    def get_shingles(self, points: pd.DataFrame, factor: float) -> set:
        """
        Converts the given track into a set of shingles.
        :param points: a pandas df containing the lat lon of the points consisting a gps track.
        :param factor: factor of segment size of shingle
        :param shingle_length: number of path segments per shingle
        :return: a set of the slope-shingles appearing in the track.
        """
        pts = points.to_numpy()
        elev = sm.compute_track_elevation(self._area_fname, self._area_topleft, pts)
        path_length = sm.compute_track_km(pts)[-1]
        tick = sm.get_tick(path_length)
        slopes = sm.compute_slope(pts, elev, factor * tick)
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
    def get_hp_slopes(length):
        """
        collects tracks from hp dataset which match the length of a given path
        """
        path = os.path.join(DifficultyEvaluator.slopes_dir_path, str(sm.get_length_tag(length)))
        dictionary = {}
        if os.path.exists(path):
            with open(path, "r") as f:
                file = f.read()
            dictionary = json.loads(file)
        return dictionary

    def get_hp_shingled_tracks(self, path_length):
        """
        returns shingles paths of similar length to path being checked
        :param path_length: length of test path (float)
        """
        # currently assume data saved is slopes of same tick as osms one
        # in the future create function that reads gps coords into correctly ticked data
        db_key = str(sm.get_length_tag(path_length)) + str(self._shingle_length)
        if db_key in self._shingle_db.keys():
            return self._shingle_db[db_key]
        slopes = self.get_hp_slopes(path_length)
        res = {}
        for key in slopes.keys():
            res[key] = [self.shingle_slopes(slopes[key][0], self._shingle_length), slopes[key][1]]
        self._shingle_db[db_key] = res
        return res
