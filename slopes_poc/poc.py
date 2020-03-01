from datasketch import MinHash, MinHashLSH
from slopes_poc import data_generator as genDat
import pandas as pd

"""
This is our cool cool slopes comparision demo! In this POC we'll take a single OSM track, represent it's slopes as a 
shingles vector, and use MinHash LSH to compare it efficiently with other tracks.
"""

SHINGLE_LENGTH = 50  # just a random number, should be modified later.


def get_shingles(points: pd.DataFrame) -> set:  # Waiting for Bar's Implementation
    """
    Converts the given track into a set of shingles.
    :param points: a pandas df containing the lat lon of the points consisting a gps track.
    :return: a set of the slope-shingles appearing in the track.
    """
    shing_set = set()

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


def handle_track(key: str, points: pd.DataFrame, lsh_idx: MinHashLSH) -> MinHash:
    """
    Gets the track shingles, minhashes them and inserts the result into an LSH index
    :param key: the key of this track in the LSH index.
    :param points: a pandas df containing the track points (lat, lon).
    :param lsh_idx: the minHashLSH index.
    :return the minhash of the tracks's shingles
    """
    shingles = get_shingles(points)
    min_hash = get_minhash(shingles)
    lsh_idx.insert(key, min_hash)

    return min_hash


if __name__ == '__main__':

    osm_track = genDat.generate_osm_track()  # We want to find a similar track to this one.
    test_tracks = genDat.generate_test_tracks(osm_track)  # We will choose the most similar track from this set
    lsh = MinHashLSH(threshold=0.7, num_perm=128)

    for idx, track_pts in enumerate(test_tracks):
        handle_track(str(idx), track_pts, lsh)

    osm_min_hash = handle_track('osm_track', osm_track, lsh)
    result = lsh.query(osm_min_hash)

    print("Approximate neighbours with Jaccard similarity > 0.7", result)
