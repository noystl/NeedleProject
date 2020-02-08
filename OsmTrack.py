import PointTag
import pandas as pd
import numpy as np
import math
from geopy.distance import geodesic

CLOSENESS_THRESH_METERS = 200
SAMPLING_RATIO = 1/50


class OsmTrack:
    """
    Holds all the data of a public gps-track collected from osm.
    """

    def __init__(self, segment):
        self.segment = segment
        self.interest_points = set()  # Waterways, historic places, etc...
        self.gps_points = self.extract_gps_points()  # Pandas df (lat, lon, time)
        self.length = self.calculate_length()  # The length of the track (in km)
        self.avg_velocity = self.calculate_avg_velocity()  # The average velocity of the track (in km\h)

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

    def calculate_length(self) -> float:  # Todo: test.
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
