import PointTags
import pandas as pd
import numpy as np
import math
from geopy.distance import geodesic


class OsmTrack:
    def __init__(self, segment):
        self.segment = segment
        self.interest_points = set()  # Rivers, historic interest points, etc...
        self.gps_points = self.extract_gps_points()
        self.length = self.calculate_length()
        self.avg_velocity = self.calculate_avg_velocity()

    def add_interest_point(self, point_tag: PointTags):
        self.interest_points.add(point_tag)

    def calculate_avg_velocity(self):
        times = pd.Series([p.time for p in self.segment.points], name='time')
        dt = np.diff(times.values) / np.timedelta64(1, 'h')
        dv = []
        for i in range(len(self.gps_points.lat) - 1):
            geodesic_distance = geodesic([self.gps_points.lat[i], self.gps_points.lon[i]],
                                         [self.gps_points.lat[i + 1], self.gps_points.lon[i + 1]]).km
            dv.append(geodesic_distance / dt[i] if dt[i] > 0 else np.nan)
        return np.nanmean(dv)

    def calculate_length(self):
        return 0

    def is_close(self, point):
        min_dist = math.inf
        sample = self.gps_points.sample(max(int(self.gps_points.shape[0] / 50), 1))
        for idx, track_point in sample.iterrows():
            min_dist = min(min_dist, geodesic([track_point.lat, track_point.lon], [point.lat, point.lon]).m)
        return min_dist < 200

    def extract_gps_points(self):
        gps_points = pd.DataFrame([
            {'lat': p.latitude,
             'lon': p.longitude,
             'time': p.time,
             } for p in self.segment.points])
        return gps_points
