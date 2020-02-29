import math
from datasketch import MinHash, MinHashLSH
from slopes_poc import TestDataGenerator as genDat
from geopy.distance import geodesic
import pandas as pd

"""
This is our cool cool slopes comparision demo! In this POC we'll take a single OSM track, represent it's slopes as a 
shingles vector, and use MinHash LSH to compare it efficiently with other tracks.
"""

NUMBER_OF_SHINGLES = 100
SHINGLE_LENGTH = 50  # just a random number, should be modified later.


def get_shingles(points: pd.DataFrame) -> set:    # Todo: test this!
    """
    Converts the given track into a set of shingles.
    :param points: a pandas df containing the lat lon of the points consisting a gps track.
    :return: a set of the slope-shingles appearing in the track.
    """
    shing_set = set()

    def win_len(s, e):
        return geodesic([points.lat[s], points.lon[s]], [points.lat[e], points.lon[e]]).m

    def calc_slope(x1, x2, y1, y2):
        return (x1 - x2) / (y1 - y2) if y1 != y2 else 0   # Todo: what are we suppose todo when the slope is undefined?

    for i in range(len(points)):
        win_start = i
        win_end = win_start

        while win_end < len(points) and win_len(win_start, win_end) < SHINGLE_LENGTH:
            win_end += 1

        if win_end >= len(points):
            break

        slope = calc_slope(points.lat[win_start], points.lat[win_end], points.lon[win_start], points.lon[win_end])
        shingle = math.floor(slope * 100)
        shing_set.add(shingle)

    return shing_set


def get_minhash(shingles: set) -> MinHash:
    """
    given a set of shingles, creates a MinHash object updated with those shingles.
    :param shingles: a set of shingles
    :return: a MinHash object updated with the given shingles.
    """
    minhash = MinHash(num_perm=128)
    for shin in shingles:
        minhash.update(str(shin).encode('utf-8'))  # not sure what should go into update here.
    return minhash


if __name__ == '__main__':

    osm_track = genDat.generate_osm_track()  # We want to find a similar track to this one.
    test_tracks = genDat.generate_test_tracks()  # We will choose the most similar track from this set
    lsh = MinHashLSH(threshold=0.7, num_perm=128)

    for idx, track_pts in enumerate(test_tracks):
        shingles = get_shingles(track_pts)
        min_hash = get_minhash(shingles)
        lsh.insert(str(idx), min_hash)

    shingles = get_shingles(osm_track)
    osm_min_hash = get_minhash(shingles)
    lsh.insert("osm_track", get_minhash(shingles))

    result = lsh.query(osm_min_hash)
    print("Approximate neighbours with Jaccard similarity > 0.7", result)
