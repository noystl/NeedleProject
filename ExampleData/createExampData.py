from OsmDataCollector import OsmDataCollector
import json

baiersbronn = [8.1584, 48.4688, 8.4797, 48.6291]


def create_osm_db(area, n=10):                                      # Todo: clean files at the end, to put the files in a folder
    """
    Creates a jason with fake osm tracks data, for testing purpose.
    :param area: the bounding box of the tracks to be generated.
    :param n: The number of fake osm recodes to be generated.
    """
    osm_data = OsmDataCollector(area)
    data = {'tracks': []}
    for i in range(n):
        if len(osm_data.tracks) > i:
            data['tracks'].append(osm_data.tracks[i].get_dict_repr())
            osm_data.tracks[i].gps_points.to_csv(str(osm_data.tracks[i].id))
    with open("ExampleDB.json", "w") as write_file:
        json.dump(data, write_file, indent=4)


if __name__ == '__main__':
    create_osm_db(baiersbronn, 1)
