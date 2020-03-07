from OsmDataCollector import OsmDataCollector
import json
import os
import shutil

baiersbronn = [8.1584, 48.4688, 8.4797, 48.6291]
COORS_PATH = 'tracks_gps_points\\'


def create_osm_db(area, n=10):
    """
    Creates a json with osm tracks data, for testing purpose.
    :param area: the bounding box of the tracks to be generated.
    :param n: The number of fake osm recodes to be generated.
    """
    if os.path.isdir(COORS_PATH):
        shutil.rmtree(COORS_PATH)
    os.makedirs(COORS_PATH)

    osm_data = OsmDataCollector(area)
    data = {'tracks': []}
    for i in range(n):
        if len(osm_data.tracks) > i:
            data['tracks'].append(osm_data.tracks[i].get_dict_repr())
            osm_data.tracks[i].gps_points.to_csv(COORS_PATH + str(osm_data.tracks[i].id))
    with open("ExampleDB.json", "w") as write_file:
        json.dump(data, write_file, indent=4)


if __name__ == '__main__':
    create_osm_db(baiersbronn, 30)
