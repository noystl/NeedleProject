from datasketch import MinHash, MinHashLSH
import pandas as pd

"""
This is our cool cool slopes comparision demo! In this POC we'll take a single OSM track, represent it's slopes as a 
shingles vector, and use MinHash LSH to compare it efficiently with other tracks.
"""

NUMBER_OF_SHINGLES = 100
SHINGLE_LENGTH = 50  # just a random number, should be modified later.


def calc_slope(x1: float, x2: float, y1: float, y2: float) -> float:
    """
    calculates the slope between two points (x1,y1), (x2,y2)
    """
    pass


def get_shingles(points: pd.DataFrame) -> set:
    """
    Converts the given track into a set of shingles.
    :param points: a pandas df containing the lat lon of the points consisting a gps track.
    :return: a set of the slope-shingles appearing in the track.
    """
    pass


def get_minhash(shingles: set) -> MinHash:
    """
    given a set of shingles, creates a MinHash object updated with those shingles.
    :param shingles: a set of shingles
    :return: a MinHash object updated with the given shingles.
    """
    minhash = MinHash(num_perm=128)
    for shin in shingles:
        minhash.update(shin.encode('utf-8'))  # not sure what should go into update here.
    return minhash


if __name__ == '__main__':
    osm_track = None  # We want to find a similar track to this one.
    test_tracks = None  # We will choose the most similar track from this set
    lsh = MinHashLSH(threshold=0.7, num_perm=128)

    # For each track, get it's shingles, convert them into a a minhash object, and insert it into the lsh obj.
    # Then, we can return the closest track using lsh.query (example: http://ekzhu.com/datasketch/lsh.html)
