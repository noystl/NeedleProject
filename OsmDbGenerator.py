"""
This class generates a "data base" (a folder) containing all of the data we collected over osm-tracks in the
supported geographic search areas.
"""

from OsmDataCollector import OsmDataCollector
from TrackDifficulty import TrackDifficulty
import json
from EvaluateDifficulty import DifficultyEvaluator
import os
import shutil
import hpcrawler

COORS_DIR_PATH = '\\tracks_gps_points\\'
AREAS_DIR_PATH = 'areas_databases\\'
TILES_PATH = 'supported_areas_tiles\\'
SHING_ELEM_NUM = 2
K_NEIGHBORS = 3


class OsmDbGenerator:
    """
    Generates a JSON file with osm-tracks data for each one of the supported search areas.
    """
    def __init__(self):
        # The Coordinated of the bounding boxes of the supported search areas:
        self.supported_areas = {
                                'baiersbronn': {'box': [8.1584, 48.4688, 8.4797, 48.6291],
                                                'corner': [48, 8],
                                                'tile': 'N48E008'}  # More areas in the future.
                                }

        # We crawl tracks in the following countries out of https://www.hikingproject.com/ :
        self.countries_to_crawl = ['Philippines']
        self._create_hp_db()

    @staticmethod
    def _create_dir(dir_name: str):
        """
        Creates a directory with the given name.
        """
        if os.path.isdir(dir_name):
            shutil.rmtree(dir_name)
        os.makedirs(dir_name)

    def _create_hp_db(self):
        seen_countries = []
        while not set(self.countries_to_crawl).issubset(set(seen_countries)):
            hpc = hpcrawler.HpCrawler(self.countries_to_crawl)
            try:
                hpc.crawl()
                seen_countries = hpcrawler.HpCrawler.load_seen().keys()
            except Exception as e:
                seen = hpcrawler.HpCrawler.load_seen()
                del hpc
                print("\n", str(e), "\ninner state: ", seen, "\nstarting again..\n")
                continue

    def create_osm_db(self):
        """
        Creates a json with osm tracks data.
        """
        self._create_dir(AREAS_DIR_PATH)

        for area_name in self.supported_areas:

            diff_evaluator = DifficultyEvaluator(TILES_PATH + self.supported_areas[area_name]['tile'] + '.hgt',
                                                 self.supported_areas[area_name]['corner'],
                                                 SHING_ELEM_NUM)

            area_dir_name = AREAS_DIR_PATH + area_name
            area_coor_dir_name = area_dir_name + COORS_DIR_PATH

            self._create_dir(area_dir_name)
            self._create_dir(area_coor_dir_name)

            area_osm_data = OsmDataCollector(self.supported_areas[area_name]['box'])
            tracks_dict = {'tracks': {}}
            for track in area_osm_data.tracks:
                difficulty = diff_evaluator.pred_difficulty(track, K_NEIGHBORS)
                if difficulty == 'Easy':
                    track.difficulty = TrackDifficulty.EASY
                elif difficulty == 'Intermediate':
                    track.difficulty = TrackDifficulty.INTERMEDIATE
                else:
                    track.difficulty = TrackDifficulty.DIFFICULT
                tracks_dict['tracks'][track.id] = track.get_dict_repr()
                track.gps_points.to_csv(area_coor_dir_name + str(track.id))
            with open(area_dir_name + '\\' + area_name + "_db.json", "w") as write_file:
                json.dump(tracks_dict, write_file, indent=4)


if __name__ == '__main__':
    OsmDbGenerator = OsmDbGenerator()
    OsmDbGenerator.create_osm_db()
