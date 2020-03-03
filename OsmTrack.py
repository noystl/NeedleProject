import pandas as pd
import numpy as np
import math
from PointTag import PointTag
from TrackLength import TrackLength
from TrackDifficulty import TrackDifficulty
from TrackShape import TrackShape
from geopy.distance import geodesic

CLOSENESS_THRESH_METERS = 200
LOOP_THRESH_METERS = 100
SAMPLING_RATIO = 1 / 10
MID_LENGTH_THRESH = 5          # Tracks who's length is between 20m to 40m are considered as medium-length track.
LONG_THRESH = 20                # Tracks longer then 40m are considered long.


class OsmTrack:
    """
    Holds all the data of a public gps-track collected from osm.
    """

    def __init__(self, segment, track_id):
        self.id = track_id
        self.segment = segment
        self.interest_points = set()  # Waterways, historic places, etc...
        self.gps_points = self.extract_gps_points()  # Pandas df (lat, lon, time)
        self.length = self.calculate_length()  # The length of the track (in km)
        self.avg_velocity = self.calculate_avg_velocity()  # The average velocity of the track (in km\h)
        self.shape = self.deduce_track_shape()
        self.boundaries = self.get_track_boundaries()
        self.difficulty = TrackDifficulty.EASY  # Hardcoded for now.

    def add_interest_point(self, point_tag: PointTag):
        """
        Adds an interest point tag to self.interest_points.
        """
        self.interest_points.add(point_tag)

    def calculate_avg_velocity(self) -> float:
        """
        Calculated the average velocity of the track (in km per hour)
        :return: the velocity.
        """
        times = pd.Series([p.time for p in self.segment.points], name='time')
        dt = np.diff(times.values) / np.timedelta64(1, 'h')
        dv = []
        for i in range(len(self.gps_points.lat) - 1):
            geodesic_distance = geodesic([self.gps_points.lat[i], self.gps_points.lon[i]],
                                         [self.gps_points.lat[i + 1], self.gps_points.lon[i + 1]]).km
            dv.append(geodesic_distance / dt[i] if dt[i] > 0 else np.nan)
        return float(np.nanmean(dv))

    def calculate_length(self) -> float:
        """
        Calculates the track length (in km)
        :return: the length (km)
        """
        length = 0
        for i in range(len(self.gps_points.lat) - 1):
            length += geodesic([self.gps_points.lat[i], self.gps_points.lon[i]],
                               [self.gps_points.lat[i + 1], self.gps_points.lon[i + 1]]).km
        return length

    def is_close(self, point: pd.DataFrame) -> bool:
        """
        Returns true iff the minimal distance of the interest point from the track is smaller than some threshold.
        :param point: a pandas df (lat, lon), containing the coordinates of an interest point.
        :return: True if the point is close to the track, otherwise False.
        """
        min_dist = math.inf
        # We preform the check only on part of the points, to fasten the running time:
        sample = self.gps_points.sample(max(int(self.gps_points.shape[0] * SAMPLING_RATIO), 1))
        for idx, track_point in sample.iterrows():
            min_dist = min(min_dist, geodesic([track_point.lat, track_point.lon], [point.lat, point.lon]).m)
        return min_dist < CLOSENESS_THRESH_METERS

    def extract_gps_points(self) -> pd.DataFrame:
        """
        Extracts the gps points from a segment and saves them as a pandas df (lat, lon, time)
        :return: a data frame (lat, lon, time) containing the gps points of the track.
        """
        gps_points = pd.DataFrame([
            {'lat': p.latitude,
             'lon': p.longitude,
             'time': p.time,
             } for p in self.segment.points])
        return gps_points

    def deduce_track_shape(self) -> TrackShape:  # Todo: test more thoroughly
        """
        Infers the general shape of the track by looking at the distance between it's start and end points.
        :return: The shape of the track (LOOP if it's a closed curve, and CURVE otherwise)
        """
        end_point_idx = self.gps_points.shape[0] - 1
        dist = geodesic([self.gps_points.lat[0], self.gps_points.lon[0]],
                        [self.gps_points.lat[end_point_idx], self.gps_points.lon[end_point_idx]]).m
        return TrackShape.LOOP if dist < LOOP_THRESH_METERS else TrackShape.CURVE

    def get_track_boundaries(self) -> dict:  # todo: test
        """
        computes the track boundaries (northern boundary, southern boundary, etc...)
        :return: a dictionary of the form {'north': northern_boundary, 'south': southern_boundary,
        'east': eastern_boundary, 'west': northern_boundary}
        """
        boundaries = {'north': -math.inf, 'south': math.inf, 'east': -math.inf, 'west': math.inf}
        for i in range(len(self.gps_points)):
            boundaries['north'] = max(boundaries['north'], self.gps_points.lon[i])
            boundaries['south'] = min(boundaries['south'], self.gps_points.lon[i])
            boundaries['east'] = max(boundaries['east'], self.gps_points.lat[i])
            boundaries['west'] = min(boundaries['west'], self.gps_points.lat[i])
        return boundaries

    def create_attributes_vec(self) -> list:
        """
        Creates a list of binary values summing up the track properties:
        [WATERFALL, BIRDING, RIVER, CAVE, WATER, SPRING, GEOLOGIC, HISTORIC,
        SHORT, MEDIUM, LONG, EASY, INTERMEDIATE, DIFFICULT, LOOP]
        :return: a list as described above.
        """
        # todo: replace this tumor with something descent.
        # This dictionary maps each track property into an index in the attributes vector.
        prop_to_index = {PointTag.WATERFALL: 0, PointTag.BIRDING: 1, PointTag.RIVER: 2,
                         PointTag.CAVE: 3, PointTag.WATER: 4, PointTag.SPRING: 5, PointTag.GEOLOGIC: 6,
                         PointTag.HISTORIC: 7, TrackLength.SHORT: 8, TrackLength.MEDIUM: 9, TrackLength.LONG: 10,
                         TrackDifficulty.EASY: 11, TrackDifficulty.INTERMEDIATE: 12, TrackDifficulty.DIFFICULT: 13,
                         TrackShape.LOOP: 14, TrackShape.CURVE: 15}
        attributes = [0]*len(prop_to_index)

        # Record interest points:
        for interest_ptr in self.interest_points:
            attributes[prop_to_index[interest_ptr]] = 1

        # Record difficulty:
            attributes[prop_to_index[self.difficulty]] = 1

        # Record length:
        if self.length < MID_LENGTH_THRESH:
            attributes[prop_to_index[TrackLength.SHORT]] = 1
        elif MID_LENGTH_THRESH <= self.length < LONG_THRESH:
            attributes[prop_to_index[TrackLength.MEDIUM]] = 1
        else:
            attributes[prop_to_index[TrackLength.LONG]] = 1

        # Record shape:
        attributes[prop_to_index[self.shape]] = 1

        return attributes

    def get_dict_repr(self) -> dict:
        """
        Returns a representation of this track as a dictionary.
        :return: a dictionary of the the form:{
                                                'id': X,
                                                'attributes': [...],
                                                'boundaries': {'north': n,
                                                                'south': s,
                                                                'west': w,
                                                                'east': e}
                                                }

        where attributes is a list of binary values summing up the track properties:
        [WATERFALL, BIRDING, RIVER, CAVE, WATER, SPRING, GEOLOGIC, HISTORIC,
        SHORT, MEDIUM, LONG, EASY, INTERMEDIATE, DIFFICULT, LOOP, CURVE]
        """
        dict_repr = {}
        attributes = self.create_attributes_vec()

        dict_repr['id'] = self.id
        dict_repr['attributes'] = attributes
        dict_repr['boundaries'] = self.boundaries
        return dict_repr

