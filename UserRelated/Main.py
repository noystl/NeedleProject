"""
This module get a list of preferences from the user as command-line arguments and finds similar osm-tracks according to
the request.

Command-Line Arguments Example:
baiersbronn 48.6 48.52 8.4 8.3 0 0 0 0 0 1 0 1 1 2 2
"""

import argparse
import json
import os
import folium
import pandas as pd
from datasketch import MinHash, MinHashLSH
from PointTag import PointTag
from TrackLength import TrackLength
from TrackDifficulty import TrackDifficulty
from TrackShape import TrackShape

areas_paths = {'baiersbronn':  # Other areas in the future :)
                   os.path.abspath(os.path.join(os.path.dirname(__file__), '..',
                                                'areas_databases\\baiersbronn\\baiersbronn_db.json'))}
SIMILARITY_THRESH = 0.7


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
    parser.add_argument("difficulty", help="1 for an easy track, 2 for intermediate, 3 for difficult and 4 for very "
                                           "difficult", type=int)
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
    elif args.difficulty == 3:
        shing_set.add(TrackDifficulty.DIFFICULT.value)
    else:
        shing_set.add(TrackDifficulty.V_DIFFICULT.value)


def add_shape_shing(shing_set: set, args: argparse.Namespace):
    """
    Adds the appropriate shape shingle to the shingles set.
    :param shing_set: the user preferences shingle set
    :param args: the given command-line arguments.
    """
    shing_set.add(TrackShape.LOOP.value) if args.shape == 1 else shing_set.add(TrackShape.CURVE.value)


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


def pretty_print_results(user_shingles: set, tracks_dict: dict, given_args, result: list):
    """
    Prints the preferences of the user and the data on the similar-osm tracks the program had found.
    :param user_shingles: the shingle set of the user's preferences.
    :param tracks_dict: a dictionary containing the data we collected over the osm-tracks in the requested area.
    :param given_args: the given command-line arguments.
    :param result: a list containing the ids of the osm-tracks the program decided were similar enough to the
    user's request.
    """
    print('USER REQUEST: ')
    print('Track attributes: ' + str(user_shingles))
    print('Location: ')
    print('\t North: ' + str(given_args.north_lim))
    print('\t South: ' + str(given_args.south_lim))
    print('\t East: ' + str(given_args.east_lim))
    print('\t West: ' + str(given_args.west_lim))
    print('\n')

    print('TRACKS FOUND: ')
    for t_id in result:
        print('Track id: ' + str(t_id))
        print('Track attributes: ' + str(set(tracks_dict[t_id]['attributes'])))
        print('Location: ')
        print('\t North: ' + str(tracks_dict[t_id]['boundaries']['north']))
        print('\t South: ' + str(tracks_dict[t_id]['boundaries']['south']))
        print('\t East: ' + str(tracks_dict[t_id]['boundaries']['east']))
        print('\t West: ' + str(tracks_dict[t_id]['boundaries']['west']))
        print('\n')


def plot_output(args, results: list, tracks_data: dict):
    """
    Plots the similar tracks found and their attributes on an interactive map (kept in the file fol.html)
    :param args: the command-line arguments we got from the user.
    :param results: a list containing the ids of the osm-tracks the program decided were similar enough to the
    user's request.
    :param tracks_data: a dictionary containing the data we collected over the osm-tracks in the requested area.
    """
    colors_list = [
        'red', 'green', 'orange', 'lightred', 'pink', 'black', 'blue', 'darkpurple',
        'darkred', 'cadetblue', 'darkblue', 'darkgreen', 'purple', 'gray'
    ]

    # Calculate the center coordinate of the search area and create a map object in this area:
    location_x = (args.north_lim + args.south_lim) / 2
    location_y = (args.west_lim + args.east_lim) / 2
    output_map = folium.Map(location=[location_x, location_y], zoom_start=13)

    # Present the similar tracks on the map:
    for result_id in results:
        coors_rel_path = 'areas_databases\\' + args.search_area + '\\tracks_gps_points\\' + result_id
        df = pd.read_csv(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', coors_rel_path)))
        points = [(row[0], row[1]) for row in df[['lat', 'lon']].values]

        folium.PolyLine(points, color=colors_list[int(result_id) % len(colors_list)], opacity=1).add_to(output_map)

        folium.Marker(
            location=[points[0][0], points[0][1]],
            popup='track ' + result_id + '\n' + str(tracks_data[result_id]['attributes']),
            icon=folium.Icon(color=colors_list[int(result_id) % len(colors_list)], icon='info-sign')
        ).add_to(output_map)

    output_map.save('recommended_tracks.html')


if __name__ == '__main__':
    """
    Gets the user track preferences as command-line arguments, finds the most similar tracks to the request, and 
    (in the future) presents the results to the user.
    Usage Example: baiersbronn 48.6 48.52 8.4 8.3 0 0 0 0 0 1 0 1 1 2 2
    """
    arg_parser = init_arg_parser()
    command_line_args = arg_parser.parse_args()

    user_shing = create_user_shingles(command_line_args)
    lsh = MinHashLSH(threshold=SIMILARITY_THRESH, num_perm=128)
    user_min_hash = get_min_hash(user_shing)

    tracks_dict = get_osm_tracks(areas_paths[command_line_args.search_area])
    for track_id in tracks_dict:
        if in_geo_limits(command_line_args, tracks_dict[track_id]):
            min_hash = get_min_hash(set(tracks_dict[track_id]['attributes']))
            lsh.insert(track_id, min_hash)

    similar_tracks = lsh.query(user_min_hash)
    plot_output(command_line_args, similar_tracks, tracks_dict)
    pretty_print_results(user_shing, tracks_dict, command_line_args, similar_tracks)
