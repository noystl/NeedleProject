import pandas as pd
import numpy as np
import math
from PointTag import PointTag
from TrackLength import TrackLength
from TrackDifficulty import TrackDifficulty
from TrackShape import TrackShape
from geopy.distance import geodesic


class OsmTrack:
    """
    Holds all the data of a public gps-track collected from osm.
    """

    def __init__(self, segment, track_id):
        self.MID_LENGTH_THRESH = 5  # Tracks who's length is between 20m to 40m are considered as medium-length track.
        self.LONG_THRESH = 20  # Tracks longer then 40m are considered long.
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
        times = self.gps_points['time']
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

    def in_boundaries(self, point: pd.DataFrame) -> bool:
        """
        Returns true if the given point is in the 'track boundaries', that is, inside the box bounding the
        track.
        :param point: a pandas df (lat, lon), containing the coordinates of an interest point.
        :return: True if the point is in the given track boundaries, False otherwise.
        """
        in_lat_boundaries = self.boundaries['south'] <= point.lat <= self.boundaries['north']
        in_lon_boundaries = self.boundaries['west'] <= point.lon <= self.boundaries['east']
        return in_lat_boundaries and in_lon_boundaries

    def is_close(self, point: pd.DataFrame, closeness_thresh=200, samp_ratio=1 / 10) -> bool:
        """
        Returns true iff the minimal distance of the interest point from the track is smaller than some threshold.
        :param point: a pandas df (lat, lon), containing the coordinates of an interest point.
        :param closeness_thresh: we say that an interest point belongs to this track if the minimal distance between
        the interest point to one of the track's points is smaller then closeness_thresh meters.
        :param samp_ratio: the relative part of the track's points we sample for the closeness check.
                the sampling is done deterministically.
        :return: True if the point is close to the track, otherwise False.
        """
        if not self.in_boundaries(point):
            return False
        min_dist = math.inf
        # We preform the check only on part of the points, to fasten the running time:
        num_of_samples = max(int(self.gps_points.shape[0] * samp_ratio), 1)  # sample at least one point
        step_size = int(len(self.gps_points) / num_of_samples)
        sample = self.gps_points[0:-1: step_size]
        for idx, track_point in sample.iterrows():
            min_dist = min(min_dist, geodesic([track_point.lat, track_point.lon], [point.lat, point.lon]).m)
        return min_dist < closeness_thresh

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

    def deduce_track_shape(self, thresh=30) -> TrackShape:
        """
        Infers the general shape of the track by looking at the distance between it's start and end points.
        :return: The shape of the track (LOOP if it's a closed curve, and CURVE otherwise)
        """
        end_point_idx = self.gps_points.shape[0] - 1
        dist = geodesic([self.gps_points.lat[0], self.gps_points.lon[0]],
                        [self.gps_points.lat[end_point_idx], self.gps_points.lon[end_point_idx]]).m
        return TrackShape.LOOP if dist < thresh else TrackShape.CURVE

    def get_track_boundaries(self) -> dict:
        """
        computes the track boundaries (northern boundary, southern boundary, etc...)
        :return: a dictionary of the form {'north': northern_boundary, 'south': southern_boundary,
        'east': eastern_boundary, 'west': northern_boundary}
        """
        boundaries = {'north': -math.inf, 'south': math.inf, 'east': -math.inf, 'west': math.inf}
        for i in range(len(self.gps_points)):
            boundaries['north'] = max(boundaries['north'], self.gps_points.lat[i])
            boundaries['south'] = min(boundaries['south'], self.gps_points.lat[i])
            boundaries['east'] = max(boundaries['east'], self.gps_points.lon[i])
            boundaries['west'] = min(boundaries['west'], self.gps_points.lon[i])
        return boundaries

    def get_attributes_shingles(self):
        shing = set()
        for interest_point in self.interest_points:
            shing.add(interest_point.value)
        shing.add(self.difficulty.value)
        shing.add(self.shape.value)
        if self.length < self.MID_LENGTH_THRESH:
            shing.add(TrackLength.SHORT.value)
        elif self.MID_LENGTH_THRESH <= self.length < self.LONG_THRESH:
            shing.add(TrackLength.MEDIUM.value)
        else:
            shing.add(TrackLength.LONG.value)
        return shing

    def get_dict_repr(self) -> dict:
        """
        Returns a representation of this track as a dictionary.
        :return: a dictionary of the the form:{
                                                'attributes': [...],
                                                'boundaries': {'north': n,
                                                                'south': s,
                                                                'west': w,
                                                                'east': e}
                                                }

        where attributes is a list of the enum values representing the properties the track has (only the properties
        that holds for the current track appear in the list).
        """
        dict_repr = {}
        attributes = self.get_attributes_shingles()

        dict_repr['attributes'] = list(attributes)
        dict_repr['boundaries'] = self.boundaries
        return dict_repr
