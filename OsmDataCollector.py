import os
from OsmTrack import OsmTrack
from PointTags import PointTags
import gpxpy
import wget
import shutil
import pandas as pd
import overpy
import matplotlib.pyplot as plt
import mplleaflet

DIR_PATH = 'files\\traces'
NUMBER_OF_WANTED_FILES = 30


class OsmDataCollector:
    """
    Collects data about a geographic area from OpenStreetMap
    """

    def __init__(self, bounding_box):
        self.box = bounding_box
        self.overpass_api = overpy.Overpass()
        self.water_points = []
        self.historic_points = []
        self.tracks = []
        self._collect_osm_data()

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

    def _collect_filtered_tracks(self):
        print("saving tracks...")
        for filename in os.listdir(DIR_PATH):
            gpx_file = open(os.path.join(DIR_PATH, filename), 'r', encoding="utf8")
            gpx = gpxpy.parse(gpx_file)
            for track in gpx.tracks:
                for seg in track.segments:
                    if seg.points[0].time is None:  # dismisses private segments
                        continue
                    curr_track = OsmTrack(seg)
                    if curr_track.avg_velocity > 12:
                        continue
                    self.tracks.append(curr_track)

    def _get_feature_nodes(self, node_tag):
        print("getting features")
        r = self.overpass_api.query("""
        node(""" + str(self.box[1]) + """,""" + str(self.box[0]) + """,""" + str(self.box[3]) + """,""" +
                                    str(self.box[2]) + """)[""" + node_tag + """]; out;""")
        return pd.DataFrame([{'lat': p.lat, 'lon': p.lon} for p in r.nodes])

    def _match_interest_points_to_tracks(self, interest_points, tag):
        for index, point in interest_points.iterrows():
            for track in self.tracks:
                if track.is_close(point):
                    track.add_interest_point(tag)

    def _collect_osm_data(self):
        self._get_gpx_files()
        self._collect_filtered_tracks()
        self.historic_points = self._get_feature_nodes(""" "historic" """)
        self.water_points = self._get_feature_nodes(""" "waterway" """)
        self._match_interest_points_to_tracks(self.historic_points, PointTags.HISTORIC)
        self._match_interest_points_to_tracks(self.water_points, PointTags.WATER)


def plot_tracks(tracks_to_plot, historic_points, water_points):
    print("plotting...")
    fig, ax = plt.subplots()
    ax.scatter(historic_points['lon'], historic_points['lat'], color='magenta', s=10, edgecolors='black')
    ax.scatter(water_points['lon'], water_points['lat'], color='blue', s=10, edgecolors='black')
    for track in tracks_to_plot:
        df = track.gps_points
        df = df.dropna()
        if (PointTags.HISTORIC and PointTags.WATER) in track.interest_points:
            ax.plot(df['lon'], df['lat'], color='red', linewidth=3, alpha=0.5)
        elif PointTags.HISTORIC in track.interest_points:
            ax.plot(df['lon'], df['lat'], color='magenta', linewidth=3, alpha=0.5)
        elif PointTags.WATER in track.interest_points:
            ax.plot(df['lon'], df['lat'], color='blue', linewidth=3, alpha=0.5)
        else:
            ax.plot(df['lon'], df['lat'], color='black', linewidth=3, alpha=0.5)

    mplleaflet.show()


if __name__ == "__main__":
    paris_streets = [2.3314, 48.8461, 2.3798, 48.8643]  # coordinates of the area: left, bottom, right, up
    louvre = [2.3295, 48.8586, 2.3422, 48.8636]  # coordinates of the area: left, bottom, right, up
    feldberg = [8.1026, 48.3933, 8.183, 48.4335]  # coordinates of the area: left, bottom, right, up
    baiersbronn = [8.1584, 48.4688, 8.4797, 48.6291]  # coordinates of the area: left, bottom, right, up

    data_collector = OsmDataCollector(baiersbronn)
    plot_tracks(data_collector.tracks, data_collector.historic_points, data_collector.water_points)

# (48.854,2.34,48.859,2.35);
