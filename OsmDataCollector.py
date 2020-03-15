import os
from OsmTrack import OsmTrack
from PointTag import PointTag
import slopeMap as sm
import gpxpy.gpx
import wget
import shutil
import pandas as pd
import overpy

DIR_PATH = 'files\\traces'


class OsmDataCollector:
    """
    Collects data over a certain geographic area given by a bounding box: [West, South, East, North]) which is a quartet
    of coordinates formatted according to osm api. The data is consisted of public gps trails, and map interest points
    (viewpoints, waterways, historic places etc.)
    """

    def __init__(self, bounding_box: list, speed_limit=12, shing_length=1, wanted_files=10):
        """
        :param bounding_box: A tuple of the form: (West, South, East, North). The bounding box of some area is available
        :param speed_limit: all tracks who's average speed is above speed_limit would not be collected.
        :param wanted_files: the number of wanted gpx data files to download from OpenStreetMap.
        in: https://www.openstreetmap.org/#map=12/48.5490/8.3191 (search the desired place, and press "export")
        For example:  [2.3295, 48.8586, 2.3422, 48.8636] is the bounding box representing the area of the Louvre museum.
        """
        self.id = 0
        self.box = bounding_box
        self.speed_limit = speed_limit
        self.shing_length = shing_length
        self.wanted_files_num = wanted_files
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
        Downloads GPX tracks files from OSM.
        """
        if os.path.isdir(DIR_PATH):
            shutil.rmtree(DIR_PATH)
        os.makedirs(DIR_PATH)
        print("saving gpx files...")

        for i in range(self.wanted_files_num):
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
            try:
                gpx = gpxpy.parse(gpx_file)
                for track in gpx.tracks:
                    for seg in track.segments:
                        if seg.points[0].time is None:  # dismisses private segments
                            continue
                        if len(seg.points) < 50:
                            continue
                        curr_track = OsmTrack(seg, self.id)
                        self.id += 1
                        if curr_track.avg_velocity > self.speed_limit or \
                                curr_track.length < (self.shing_length + 1) * sm.TICK:
                            continue
                        self.tracks.append(curr_track)
            except gpxpy.gpx.GPXXMLSyntaxException:
                print('gpx parsing error for' + filename)

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
        for track in self.tracks:
            for index, point in interest_points.iterrows():
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
