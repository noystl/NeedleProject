import os
import wget
import shutil
import overpy

DIR_PATH = 'files/traces'
NUMBER_OF_WANTED_FILES = 10


class OsmDataCollector:
    """
    Collects data about a geographic area from OpenStreetMap
    """
    def __init__(self, bounding_box):
        self.box = bounding_box
        self.overpass_api = overpy.Overpass()

    def create_url(self, file_index):
        """
        Creates the http request used to get traces files from OSM.
        :param file_index:
        :return:
        """
        url = "https://api.openstreetmap.org/api/0.6/trackpoints?bbox=" \
              + str(self.box[0]) + "," + str(self.box[1]) + "," + str(self.box[2]) + \
              "," + str(self.box[3]) + "&page=" + str(file_index)
        return url

    def get_gpx_files(self):
        """
        Downloads GPX traces files from OSM.
        :return:
        """
        if os.path.isdir(DIR_PATH):
            shutil.rmtree(DIR_PATH)
        os.mkdir(DIR_PATH)
        print("saving gpx files...")

        for i in range(NUMBER_OF_WANTED_FILES):
            url = self.create_url(i)
            filename = wget.download(url, out=DIR_PATH)
            os.rename(filename, os.path.join(DIR_PATH, "tracks" + str(i) + ".gpx"))

    def get_feature(self):
        print("getting features")
        r = self.overpass_api.query("""
        node(""" + str(48.854) + """,""" + str(2.34) + """,""" + str(48.859) + """,""" + str(2.35) + """) 
        ["tourism" = "information"];
        out;
        """)
        print(r.nodes)

    def collect_osm_data(self, feature_list):
        # self.get_gpx_files()
        self.get_feature()


if __name__ == "__main__":
    BOX = [2.3314, 48.8461, 2.3798, 48.8643]  # coordinates of the area: left, bottom, right, up (Paris streets)

    data_collector = OsmDataCollector(BOX)
    data_collector.collect_osm_data([])
