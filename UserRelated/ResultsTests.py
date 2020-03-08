"""
Supplies visual and textual representation of the results for our use :)
"""

import matplotlib.pyplot as plt
import mplleaflet
import os
import pandas as pd


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
    for track_id in result:
        print('Track id: ' + str(track_id))
        print('Track attributes: ' + str(set(tracks_dict[track_id]['attributes'])))
        print('Location: ')
        print('\t North: ' + str(tracks_dict[track_id]['boundaries']['north']))
        print('\t South: ' + str(tracks_dict[track_id]['boundaries']['south']))
        print('\t East: ' + str(tracks_dict[track_id]['boundaries']['east']))
        print('\t West: ' + str(tracks_dict[track_id]['boundaries']['west']))
        print('\n')


def draw_line(x1, x2, y1, y2, ax):
    """
    Draws a line on ax from (x1,y1) to (x2,y2)
    """
    xs = [x1, x2]
    ys = [y1, y2]
    ax.plot(xs, ys, color='red', linewidth=5, alpha=0.5)


def draw_user_limits(args, ax):
    """
    Draws the geographic limits the user had defined.
    :param args: the given command-line arguments.
    :param ax: the pyplot object we are going to draw on.
    """
    draw_line(args.west_lim, args.east_lim, args.north_lim, args.north_lim, ax)
    draw_line(args.west_lim, args.east_lim, args.south_lim, args.south_lim, ax)
    draw_line(args.west_lim, args.west_lim, args.north_lim, args.south_lim, ax)
    draw_line(args.east_lim, args.east_lim, args.north_lim, args.south_lim, ax)


def plot_results(args, result: list):
    """
    Plots the osm tracks we consider as similar to what the user had wanted, in addition to the geographic limits
    she/he supplied.
    :param args: the given command-line arguments.
    :param result: a list containing the ids of the osm-tracks the program decided were similar enough to the
    user's request.
    """
    fig, ax = plt.subplots()
    draw_user_limits(args, ax)
    for track_id in result:
        df = pd.read_csv(os.path.abspath(os.path.join(os.path.dirname(__file__), '..',
                                                      'areas_databases\\baiersbronn\\tracks_gps_points\\') + str(
            track_id)))
        df = df.dropna()
        ax.plot(df['lon'], df['lat'], color='blue', linewidth=3, alpha=0.5)
    mplleaflet.show()
