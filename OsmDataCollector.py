import os
from OsmTrack import OsmTrack
from PointTag import PointTag
from TrackShape import TrackShape
import gpxpy
import wget
import shutil
import pandas as pd
import overpy
import matplotlib.pyplot as plt
import mplleaflet

DIR_PATH = 'files\\traces'
NUMBER_OF_WANTED_FILES = 2  # This is the number of gpx files we download from osm.
SPEED_LIMIT_KMH = 12  # This is what we consider as the maximal speed for a pedestrian.


class OsmDataCollector:
    """
    Collects data over a certain geographic area given by a bounding box: [West, South, East, North]) which is a quartet
    of coordinates formatted according to osm api. The data is consisted of public gps trails, and map interest points
    (viewpoints, waterways, historic places etc.)
    """

    def __init__(self, bounding_box: list):
        """
        :param bounding_box: A tuple of the form: (West, South, East, North). The bounding box of some area is available
        in: https://www.openstreetmap.org/#map=12/48.5490/8.3191 (search the desired place, and press "export")
        For example:  [2.3295, 48.8586, 2.3422, 48.8636] is the bounding box representing the area of the Louvre museum.
        """
        self.id = 0
        self.box = bounding_box
        self.overpass_api = overpy.Overpass()
        self.interest_points_dict = {}  # Contains the interest points coordinates by tag.
        self.tracks = []  # A list of OsmTrack objects.
        self._collect_osm_data()

    def _create_url(self, file_index: int) -> str:
        """
        Creates an http request used to get one gps-traces file from OSM.
        For more information, see: https://wiki.openstreetmap.org/wiki/API_v0.6#GPS_traces
        :param file_index: The index of file to be retrieved.
        :return: The mentioned http request.
        """
        url = "https://api.openstreetmap.org/api/0.6/trackpoints?bbox=" \
              + str(self.box[0]) + "," + str(self.box[1]) + "," + str(self.box[2]) + \
              "," + str(self.box[3]) + "&page=" + str(file_index)
        return url

    def _get_gpx_files(self):
        """
        Downloads GPX traces files from OSM.
        """
        if os.path.isdir(DIR_PATH):
            shutil.rmtree(DIR_PATH)
        os.makedirs(DIR_PATH)
        print("saving gpx files...")

        for i in range(NUMBER_OF_WANTED_FILES):
            url = self._create_url(i)
            filename = wget.download(url, out=DIR_PATH)
            os.rename(filename, os.path.join(DIR_PATH, "tracks" + str(i) + ".gpx"))

    def _collect_filtered_tracks(self):
        """
        Parses the collected gpx files, and extracts tracks. For each track, the method tests if it's average velocity
        is lower then 12 km per hour (if so, the track probably describes walking or running), and if its public.
        Tracks that hold both attributes are saved in self.tracks.
        """
        print("saving tracks...")
        for filename in os.listdir(DIR_PATH):
            gpx_file = open(os.path.join(DIR_PATH, filename), 'r', encoding="utf8")
            gpx = gpxpy.parse(gpx_file)
            for track in gpx.tracks:
                for seg in track.segments:
                    if seg.points[0].time is None:  # dismisses private segments
                        continue
                    curr_track = OsmTrack(seg, self.id)
                    self.id += 1
                    if curr_track.avg_velocity > SPEED_LIMIT_KMH or len(curr_track.gps_points) < 50:
                        continue
                    self.tracks.append(curr_track)

    def _get_interest_points(self, node_tag: str) -> pd.DataFrame:
        """
        Uses Overpass-API to extract the coordinates of interest points inside self.box.
        :param node_tag: What kind of interest point should be extracted. For example: "historic".

        For more information:
        https://wiki.openstreetmap.org/wiki/Map_Features
        https://towardsdatascience.com/loading-data-from-openstreetmap-with-python-and-the-overpass-api-513882a27fd0

        :return: a pandas df (lat, lon) containing the
        """
        print("getting features: " + node_tag)
        r = self.overpass_api.query("""
        node(""" + str(self.box[1]) + """,""" + str(self.box[0]) + """,""" + str(self.box[3]) + """,""" +
                                    str(self.box[2]) + """)[""" + node_tag + """]; out;""")
        return pd.DataFrame([{'lat': p.lat, 'lon': p.lon} for p in r.nodes])

    def _match_interest_points_to_tracks(self, interest_points: pd.DataFrame, tag: PointTag):
        """
        Attaches to each track the interest points that are geographically close to it.
        :param interest_points: A pandas data frame (lat, lon) containing the coordinates of the interest points.
        :param tag: an Enum representing the type of the interest point.
        """
        for index, point in interest_points.iterrows():
            for track in self.tracks:
                if track.is_close(point):
                    track.add_interest_point(tag)

    def _handle_interest_points(self):
        """
        Gets interest points of all categories, and attaches them to the correct tracks.
        """
        query_list = [""" "historic" """, """ "waterway" = "waterfall" """, """ "natural" = "water" """,
                      """ "leisure" = "bird_hide" """, """ "natural" = "cave_entrance" """, """ "geological" """,
                      """ "waterway" = "river" """, """ "natural" = "spring" """]
        tags = [PointTag.HISTORIC, PointTag.WATERFALL, PointTag.WATER, PointTag.BIRDING, PointTag.CAVE,
                PointTag.GEOLOGIC, PointTag.RIVER, PointTag.SPRING]
        for query, tag in zip(query_list, tags):
            interest_points = self._get_interest_points(query)
            self.interest_points_dict[tag] = interest_points
            self._match_interest_points_to_tracks(interest_points, tag)

    def _collect_osm_data(self):
        """
        Collects the public gps-tracks in self.box and creates corresponding OsmTracks objects, using additional
        geographic data collected from the map (interest points).
        """
        self._get_gpx_files()
        self._collect_filtered_tracks()
        self._handle_interest_points()


# def plot_by_interest(track: OsmTrack, ax):
#     df = track.gps_points
#     df = df.dropna()
#     if (PointTag.HISTORIC and PointTag.WATER) in track.interest_points:
#         ax.plot(df['lon'], df['lat'], color='red', linewidth=3, alpha=0.5)
#     elif PointTag.HISTORIC in track.interest_points:
#         ax.plot(df['lon'], df['lat'], color='magenta', linewidth=3, alpha=0.5)
#     elif PointTag.WATER in track.interest_points:
#         ax.plot(df['lon'], df['lat'], color='blue', linewidth=3, alpha=0.5)
#     else:
#         ax.plot(df['lon'], df['lat'], color='black', linewidth=3, alpha=0.5)


def plot_by_shape(track: OsmTrack, ax):
    df = track.gps_points
    df = df.dropna()
    if track.shape is TrackShape.LOOP:
        ax.plot(df['lon'], df['lat'], color='red', linewidth=3, alpha=0.5)
    else:
        ax.plot(df['lon'], df['lat'], color='blue', linewidth=3, alpha=0.5)


def plot_tracks(tracks_to_plot, interest_points_dict):  # For debugging
    print("plotting...")
    fig, ax = plt.subplots()
    color_palette = {PointTag.RIVER: "r", PointTag.HISTORIC: "m", PointTag.GEOLOGIC: "k", PointTag.WATER: "g",
                     PointTag.SPRING: "b", PointTag.CAVE: "y", PointTag.BIRDING: "w", PointTag.WATERFALL: "c"}
    for category in interest_points_dict:
        points = interest_points_dict[category]
        if not points.empty:
            ax.scatter(points['lon'], points['lat'], color=color_palette[category], s=10, edgecolors='black')
    for track in tracks_to_plot:
        plot_by_shape(track, ax)
    mplleaflet.show()


if __name__ == "__main__":
    paris_streets = [2.3314, 48.8461, 2.3798, 48.8643]  # coordinates of the area: left, bottom, right, up
    louvre = [2.3295, 48.8586, 2.3422, 48.8636]  # coordinates of the area: left, bottom, right, up
    feldberg = [8.1026, 48.3933, 8.183, 48.4335]  # coordinates of the area: left, bottom, right, up
    baiersbronn = [8.1584, 48.4688, 8.4797, 48.6291]  # coordinates of the area: left, bottom, right, up

    data_collector = OsmDataCollector(baiersbronn)
    plot_tracks(data_collector.tracks, data_collector.interest_points_dict)

# (48.854,2.34,48.859,2.35);
