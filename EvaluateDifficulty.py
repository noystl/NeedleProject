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

    def __init__(self, datapath, area_fname, area_topleft):

        self._path = datapath
        self._area_fname = area_fname
        self._area_topleft = area_topleft

    def get_shingles(self, points: pd.DataFrame, factor) -> set:
        """
        Converts the given track into a set of shingles.
        :param points: a pandas df containing the lat lon of the points consisting a gps track.
        :return: a set of the slope-shingles appearing in the track.
        """
        pts = points.to_numpy()
        elev = sm.compute_track_elevation(self._area_fname, self._area_topleft, pts)
        path_length = sm.compute_track_km(pts)[-1]
        tick = sm.get_tick(path_length)
        slopes = sm.compute_slope(pts, elev, factor * tick)
        return self._adjust_slopes(set(slopes))  # returns the rounded versions of slopes

    @staticmethod
    def _adjust_slopes(slopes):
        """
        takes a set of slopes and rounds the values to nearest 10 degrees
        :param slopes: python set of all slopes appearing in the track
        :return: a set of all slopes rounded to nearest 10
        """
        result = set()
        for slope in slopes:
            result.add((slope // 10) * 10)
        return result

    def _get_hp_slopes(self, length):
        """
        collects tracks from hp dataset which match the length of a given path
        """
        path = DifficultyEvaluator.slopes_dir_path + str(sm.get_length_tag(length))
        dictionary = {}
        if os.path.exists(path):
            with open(path, "r") as f:
                file = f.read()
            dictionary = json.loads(file)
        return dictionary

    def _get_hp_shingled_tracks(self, length):

        tracks = self._get_hp_slopes(length)
