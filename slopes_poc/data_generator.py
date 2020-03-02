import pandas as pd
import numpy as np
import math
import OsmDataCollector as odc

PARIS_COORS = [2.3314, 48.8461, 2.3798, 48.8643]


def generate_osm_track() -> pd.DataFrame:
    """
    Generates a pandas data frame (lat, lon) of an osm track. In the experiment, we'll try to
    find the closest track to this one.
    :return: pandas df as described above.
    """
    data_collector = odc.OsmDataCollector(PARIS_COORS)
    track = data_collector.tracks[0]
    return track.extract_gps_points().iloc[:, :-1]


def generate_test_tracks(osm_track: pd.DataFrame) -> list:
    """
    Generates a list of tracks that are different variations of osm_track.
    For example: a cyclic shit of the original track, random permutation over it's points...
    :param osm_track: the osm track chosen for the POC.
    :return: a list of the generated tracks and the osm_track chosen for the test.
    """
    tracks = [osm_track]

    t1 = osm_track.reindex(np.roll(osm_track.index, 30))  # Cyclic shift of 30 places upward.
    tracks.append(t1)

    t2 = osm_track.sample(frac=1).reset_index(drop=True)  # Random shuffle
    tracks.append(t2)

    t3 = osm_track.reindex(index=osm_track.index[::-1])  # Reverse
    tracks.append(t3)

    t4 = osm_track.apply(lambda x: x + 0.01 if x.name == 'lat' else x)  # Adding 0.01 to the latitude.
    tracks.append(t4)

    t5 = osm_track.apply(lambda x: x - 0.3 if x.name == 'lat' else x + 0.01)  # Sub 0.3 from lat, add 0.01 to lon.
    tracks.append(t5)

    return tracks
