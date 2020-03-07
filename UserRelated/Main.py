"""
This module get a list of preferences from the user as command-line arguments and finds similar osm-tracks according to
the request.

Command-Line Arguments Example:
baiersbronn 48.6 48.5 8.4 8.3 0 0 0 0 0 1 0 1 1 1 2

Note:
Pay attention that we don't have a real osm-DB yet, so in order to run this module, please generate a fake DB first
with createExampData.
"""


import argparse
import json
from UserRelated import ResultsTests as tests
from datasketch import MinHash, MinHashLSH
from PointTag import PointTag
from TrackLength import TrackLength
from TrackDifficulty import TrackDifficulty
from TrackShape import TrackShape

areas_paths = {'baiersbronn': 'ExampleData\\ExampleDB.json'}  # Other areas in the future :)
USER_ID = 'user'
SIMILARITY_THRESH = 0.6


def add_limits_args(parser: argparse.ArgumentParser):
    """
    Adds to the parser the limit arguments defining the area the user is interested in.
    :param parser: command-line arguments parser.
    """
    parser.add_argument("north_lim", help="northern limit of the search inside the area.", type=float)
    parser.add_argument("south_lim", help="southern limit of the search inside the area.", type=float)
    parser.add_argument("east_lim", help="eastern limit of the search inside the area.", type=float)
    parser.add_argument("west_lim", help="western limit of the search inside the area.", type=float)


def add_interest_points_args(parser: argparse.ArgumentParser):
    """
    Adds to the parser interest-points arguments, defining what interest points the user wants to have in
    the resulted track.
    :param parser: command-line arguments parser.
    """
    # The following arguments characterise the track the user wants to get:
    parser.add_argument("waterfall", help="1 if the wanted track should contain a waterfall, 0 otherwise.", type=int)
    parser.add_argument("birding", help="1 if the wanted track is good for bird-lovers, 0 otherwise.", type=int)
    parser.add_argument("river", help="1 if the wanted track should contain a river, 0 otherwise.", type=int)
    parser.add_argument("cave", help="1 if the wanted track should contain a cave, 0 otherwise.", type=int)
    parser.add_argument("lake", help="1 if the wanted track should contain a lake, 0 otherwise.", type=int)
    parser.add_argument("spring", help="1 if the wanted track should contain a spring, 0 otherwise.", type=int)
    parser.add_argument("geo", help="1 if the track should contain a geological interest point, 0 otherwise.",
                        type=int)
    parser.add_argument("historic", help="1 if the track should contain a historic interest point, 0 otherwise.",
                        type=int)


def init_arg_parser():
    """
    Creates a command-line arguments parser object (see: https://docs.python.org/3/library/argparse.html)
    and initializes it with all of the relevant arguments.
    :return: a command-line arguments parser.
    """
    parser = argparse.ArgumentParser(description='Gets arguments from the user.')
    parser.add_argument("search_area", help="The general geographic area to search tracks in.",
                        choices=['baiersbronn'])  # Other areas options in the future :)

    add_limits_args(parser)
    add_interest_points_args(parser)

    parser.add_argument("length", help="1 for a short track, 2 for medium-length and 3 for long", type=int)
    parser.add_argument("difficulty", help="1 for an easy track, 2 for intermediate and 3 for difficult", type=int)
    parser.add_argument("shape", help="1 for a loop and 2 for out and back", type=int)

    return parser


def add_interest_points_shingles(shing_set: set, args: argparse.Namespace):
    """
    Adds interest points shingles shingles to shing_set.
    :param shing_set: the user preferences shingle set.
    :param args: the given command-line arguments.
    """
    if args.waterfall: shing_set.add(PointTag.WATERFALL.value)
    if args.birding: shing_set.add(PointTag.BIRDING.value)
    if args.river: shing_set.add(PointTag.RIVER.value)
    if args.cave: shing_set.add(PointTag.CAVE.value)
    if args.lake: shing_set.add(PointTag.WATER.value)
    if args.spring: shing_set.add(PointTag.SPRING.value)
    if args.geo: shing_set.add(PointTag.GEOLOGIC.value)
    if args.historic: shing_set.add(PointTag.HISTORIC.value)


def add_length_shingle(shing_set: set, args: argparse.Namespace):
    """
    Adds the appropriate length shingle to the shingles set.
    :param shing_set: the user preferences shingle set
    :param args: the given command-line arguments.
    """
    if args.length == 1:
        shing_set.add(TrackLength.SHORT.value)
    elif args.length == 2:
        shing_set.add(TrackLength.MEDIUM.value)
    else:
        shing_set.add(TrackLength.LONG.value)


def add_difficulty_shingle(shing_set: set, args: argparse.Namespace):
    """
    Adds the appropriate difficulty shingle to the shingles set.
    :param shing_set: the user preferences shingle set
    :param args: the given command-line arguments.
    """
    if args.difficulty == 1:
        shing_set.add(TrackDifficulty.EASY.value)
    elif args.difficulty == 2:
        shing_set.add(TrackDifficulty.INTERMEDIATE.value)
    else:
        shing_set.add(TrackDifficulty.DIFFICULT.value)


def add_shape_shing(shing_set: set, args: argparse.Namespace):
    """
    Adds the appropriate shape shingle to the shingles set.
    :param shing_set: the user preferences shingle set
    :param args: the given command-line arguments.
    """
    shing_set.add(TrackShape.LOOP.value) if args.shape == 1 else shing_set.add(TrackShape.CURVE.value)


# Todo: this is a code duplication of the slopes_poc branch, we should have a separate class for LSH-ing we can reuse.
def get_min_hash(shingles: set) -> MinHash:
    """
    given a set of shingles, creates a MinHash object updated with those shingles.
    :param shingles: a set of track shingles.
    :return: a MinHash object updated with the given shingles.
    """
    track_min_hash = MinHash(num_perm=128)
    for shin in shingles:
        track_min_hash.update(str(shin).encode('utf-8'))
    return track_min_hash


def create_user_shingles(args: argparse.Namespace) -> set:
    """
    Creates a set of shingles defining the user's path preferences.
    :param args: the given command-line arguments.
    :return: a set of shingles as described.
    """
    shing = set()
    add_interest_points_shingles(shing, args)
    add_length_shingle(shing, args)
    add_difficulty_shingle(shing, args)
    add_shape_shing(shing, args)
    return shing


def get_osm_tracks(area_path: str) -> dict:
    """
    Reads a dictionary with the data collected on paths in the given search area.
    :param area_path: path to the file containing the data relevant to the given search are.
    :return: a dictionary with data on tracks in the given area.
    """
    with open(area_path, 'r') as f:
        osm_tracks_dict = json.load(f)
    return osm_tracks_dict['tracks']


def in_geo_limits(args: argparse.Namespace, track_data: dict) -> bool:
    """
    Checks if the given track is in the geographic limits the user had given.
    :param args: command lines arguments.
    :param track_data: a dictionary containing a track's data.
    :return: true if the track lies in the geographic boundaries the user had set, false otherwise.
    """
    return (track_data['boundaries']['north'] <= args.north_lim and
            track_data['boundaries']['south'] >= args.south_lim and
            track_data['boundaries']['east'] <= args.east_lim and
            track_data['boundaries']['west'] >= args.west_lim)


if __name__ == '__main__':
    """
    Gets the user track preferences as command-line arguments, finds the most similar tracks to the request, and 
    (in the future) presents the results to the user. The presentation of the results now is temporal and mainly 
    used for testing.
    Usage Example: baiersbronn 48.6 48.5 8.4 8.3 0 0 0 0 0 1 0 1 1 1 2
    """
    arg_parser = init_arg_parser()
    command_line_args = arg_parser.parse_args()

    user_shing = create_user_shingles(command_line_args)
    lsh = MinHashLSH(threshold=SIMILARITY_THRESH, num_perm=128)
    user_min_hash = get_min_hash(user_shing)
    lsh.insert(USER_ID, user_min_hash)

    tracks_dict = get_osm_tracks(areas_paths[command_line_args.search_area])
    for track in tracks_dict:
        if in_geo_limits(command_line_args, track):
            min_hash = get_min_hash(set(track['attributes']))
            lsh.insert(track['id'], min_hash)

    similar_tracks = lsh.query(user_min_hash)

    # For testing:
    similar_tracks.remove(USER_ID)  # The user's shingle-set is similar to itself (so it always appears in the results).
    tests.pretty_print_results(user_shing, tracks_dict, command_line_args, similar_tracks)
    tests.plot_results(command_line_args, similar_tracks)