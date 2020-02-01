import os

import gpxpy
import wget
import numpy as np
import pandas as pd
import shutil
import overpy
import matplotlib.pyplot as plt
import mplleaflet
from geopy.distance import geodesic

DIR_PATH = 'files\\traces'
NUMBER_OF_WANTED_FILES = 9


class OsmDataCollector:
    """
    Collects data about a geographic area from OpenStreetMap
    """

    def __init__(self, bounding_box):
        self.box = bounding_box
        self.overpass_api = overpy.Overpass()
        self.tracks = []
        self._collect_osm_data()

    @staticmethod
    def _compute_track_velocity(coords, segment):
        """
        Computes the average velocity of a track.
        :param coords:
        :param segment:
        :return:
        """
        times = pd.Series([p.time for p in segment.points], name='time')
        dt = np.diff(times.values) / np.timedelta64(1, 'h')
        dv = []
        for i in range(len(coords.lat) - 1):
            geodesic_distance = geodesic([coords.lat[i], coords.lon[i]],
                                         [coords.lat[i + 1], coords.lon[i + 1]]).km
            dv.append(geodesic_distance / dt[i] if dt[i] > 0 else np.nan)
        return np.nanmean(dv)

    def _create_url(self, file_index):
        """
        Creates the http request used to get traces files from OSM.
        :param file_index:
        :return:
        """
        url = "https://api.openstreetmap.org/api/0.6/trackpoints?bbox=" \
              + str(self.box[0]) + "," + str(self.box[1]) + "," + str(self.box[2]) + \
              "," + str(self.box[3]) + "&page=" + str(file_index)
        return url

    def _get_gpx_files(self):
        """
        Downloads GPX traces files from OSM.
        :return:
        """
        if os.path.isdir(DIR_PATH):
            shutil.rmtree(DIR_PATH)
        os.mkdir(DIR_PATH)
        print("saving gpx files...")

        for i in range(NUMBER_OF_WANTED_FILES):
            url = self._create_url(i)
            filename = wget.download(url, out=DIR_PATH)
            os.rename(filename, os.path.join(DIR_PATH, "tracks" + str(i) + ".gpx"))

    def _collect_tracks(self):
        print("saving tracks...")
        for filename in os.listdir(DIR_PATH):
            gpx_file = open(os.path.join(DIR_PATH, filename), 'r', encoding="utf8")
            gpx = gpxpy.parse(gpx_file)
            for track in gpx.tracks:
                for seg in track.segments:
                    if seg.points[0].time is None:  # dismisses private segments
                        continue
                    coords = pd.DataFrame([
                        {'lat': p.latitude,
                         'lon': p.longitude,
                         'time': p.time,
                         } for p in seg.points])
                    if self._compute_track_velocity(coords, seg) > 7:
                        continue
                    self.tracks.append(coords)

    def _get_feature_nodes(self, node_tag):
        print("getting features")
        r = self.overpass_api.query("""
        node(""" + str(self.box[1]) + """,""" + str(self.box[0]) + """,""" + str(self.box[3]) + """,""" +
                                    str(self.box[2]) + """)[""" + node_tag + """]; out;""")
        print(r.nodes)

    def _collect_osm_data(self):
        self._get_gpx_files()
        self._collect_tracks()
        # self._get_feature_nodes(""" "tourism" = "viewpoint" """)


def present_tracks(tracks_to_plot):
    print("plotting...")
    fig, ax = plt.subplots()
    for df in tracks_to_plot:
        df = df.dropna()
        ax.plot(df['lon'], df['lat'], color='magenta', linewidth=2, alpha=0.5)
    mplleaflet.show()


if __name__ == "__main__":
    paris_streets = [2.3314, 48.8461, 2.3798, 48.8643]  # coordinates of the area: left, bottom, right, up
    louvre = [2.3295, 48.8586, 2.3422, 48.8636]  # coordinates of the area: left, bottom, right, up

    data_collector = OsmDataCollector(louvre)
    present_tracks(data_collector.tracks)

# (48.854,2.34,48.859,2.35);
