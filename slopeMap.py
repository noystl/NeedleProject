import os
import math
import numpy as np
import matplotlib.pyplot as plt
from geopy.distance import distance
import OsmDataCollector as odc
import locale

areas_paths = {'baiersbronn': ['N48E008', [48, 8]]}  # Other areas in the future :)

MAX_TRACK_LEN = 10001  # maximum supported track length - this parameter is obsolete
LEN_SPACING = 5  # size of the "buckets" of the length_tag
TICK = 0.25  # in kms
DEG_GENERALIZE = 15  # size of "buckets for slopes, in degrees


def get_num_of_len_tags():  # this function is obsolete
    """
    :return: the number of different categories of length.
    """
    return MAX_TRACK_LEN // LEN_SPACING


def get_tick(track_len):
    """
    returns the tick according to the track's length supplied.
    the tag is computed from the formula:
    for int i in [0,
    return [LEN_SPACING * i, LEN_SPACING * (i + 1)] =  TICK * (i + 1) / 100
    :param track_len: a track's length (km)
    :return: double (km)
    """
    #ranges = np.arange(0, MAX_TRACK_LEN, LEN_SPACING)
    i = track_len // LEN_SPACING + 1
    if track_len % LEN_SPACING == 0:
        i -= 1
    return TICK * i
    # the below implementation is wasteful (and makes the ticks slightly larger than necessary)
    # for i in range(len(ranges) - 1):
    #    if ranges[i] >= track_len:
    #        return (TICK * 100) * (i + 1) / 100

def get_length_tag(track_len):
    """
    :param track_len: int representing track's length in km
    :return: an int representing the length tag of the given  track's length
    """
    if track_len % LEN_SPACING == 0:
        return int(track_len // LEN_SPACING - 1)
    return int(track_len // LEN_SPACING)


# Elevation Map #
def make_elev_map(area_filename):
    """
    creates an elevation map of the area depicted in the supplied file,
    downloaded from: https://dwtkns.com/srtm30m/
    :param area_filename: an hgt file holding the elevation values of the relevant tile.
    :return: 2-dim np array holding the elevation values of 30-meters "mini-tiles"
    in the supplied tile.
    """
    siz = os.path.getsize(area_filename)
    dim = int(math.sqrt(siz / 2))
    elev_map = np.fromfile(area_filename, np.dtype('>i2'), dim * dim).reshape((dim, dim))
    return elev_map


def get_elev_atpt(elev_map, lon, lat, x, y):
    """
    :param elev_map: 2d array of elevation in a grid (2d np array of ints)
    :param lon: longitude of top left corner
    :param lat: latitude of top left corner
    :param x: longitude of point to be checked
    :param y: latitude of point to be checked
    :return the elevation value of the (<x>, <y>) coordinate in the <elev_map>, whose
    top left corner (lat, lon) values are <lat>, <lon>.
    """
    frac_x = x - lon
    frac_y = y - lat
    cell_x = 1 / elev_map.shape[1]
    cell_y = 1 / elev_map.shape[0]
    elev_x = frac_x // cell_x
    elev_y = frac_y // cell_y
    return elev_x, elev_y


# Elevation representation (for graph display- testing intuition) #
def compute_track_elevation(elev_map, tile_rep, points):
    """
    computes the elevation values along the track, represented by it's points.
    :param elev_map: 2d array of elevation in a grid (2d np array of ints)
    :param tile_rep: list of shape (2,) of top left coordiantes of elev map
    :param points: 2-dim np array of the track's points: (lat, lon).
    :return: the elevation values along the track.
   """
    dat = make_elev_map(elev_map)
    elevations = []
    for x_coor, y_coor in points:
        x, y = get_elev_atpt(dat, tile_rep[0], tile_rep[1], x_coor, y_coor)
        ele = dat[int(x)][int(y)]
        elevations.append(ele)
    return np.asarray(elevations)


def compute_track_km(points):  # TODO: compare with Noy's implementation of getting the track's length
    """
    computes the km values along the track, represented by it's points.
    distance over path in computed by: https://janakiev.com/blog/gps-points-distance-python/
    :param points: 2-dim np array of the track's points: (lat, lon).
    :return: the km values along the track.
    """
    d = 0
    kms = [0]
    for i in range(len(points) - 1):
        d += distance(points[i], points[i + 1]).km
        kms.append(d)
    return np.asarray(kms)


def plot_dist_elevation(kms, elevations):
    """
    plots the change in elevation(in meters) over distance(in km).
    :param kms: np array of length n, holding the track points, in every round km.
    :param elevations: np array of length n, holding the elevations at kms.
    """
    fig, ax = plt.subplots()
    ax.plot(kms, elevations)

    ax.scatter(kms, elevations, color='r', s=10, edgecolors='black')

    # label axis:
    plt.xlabel('Distance (km)')
    plt.ylabel('Elevation (meters)')

    # # change y axis range to capture representation of elevation:
    plt.axis([0, np.amax(kms), 0, np.amax(elevations) + 10])
    # # change y axis mark points to represent kms:
    start, end = ax.get_xlim()
    ax.xaxis.set_ticks(np.arange(start, end, 1))

    plt.show()


# slope Representation #
def compute_slope(track_points, track_elevs, track_length):  # TODO: notify about the signature change
    """
    returns a python list of
    :param track_points: 2-dim np array of the track's points: (lat, lon).
    :param track_elevs: np array of length n, holding the elevations at points.
    :param track_length: float
    :return: python list of floats representing the angles (values are in [-90, 90],
            all <DEG_GENERALIZE> degrees subsections are mapped to one value representing
            the slope of that subsection)
    """
    tick = get_tick(track_length)
    trackKms = compute_track_km(track_points)
    kmMarks = np.arange(0, trackKms[-1] + 1, tick / 2)

    # handles the last segment of track (to add it to kmMarks or not):
    # there are two options: # TODO - Matan choose from the options the one you meant

    # (1) gets the last multiple of tick / 2 that was seen in track, and discards the leftover track.
    # DO NOTHING

    # (2) add the last km value of the original track
    # (NOTE: the last kmMark will probably not be a multiple of tick / 2)
    #  ADD THIS CODE:
    if trackKms[-1] > kmMarks[-1]:
      np.append(kmMarks, trackKms[-1])

    # interpolate the elevation values at kmMarks:
    elevMarks = np.interp(kmMarks, trackKms, track_elevs)

    # TODO: FOR VISUALIZING-
    plot_dist_elevation(kmMarks, elevMarks)

    # get slopes of all sections:
    slopes = (elevMarks[1:] - elevMarks[:-1]) / tick  # slope of a straight line
    slopes = [math.degrees(rad) for rad in np.arctan(slopes)]  # the slope in degrees

    return slopes


def slopes_sanity_check():
    kms = np.array([0, 1, 2, 3, 4, 5])
    elevs = np.array([0, 1, 2, 0, 0, 0])
    slopes = (elevs[2:] - elevs[:-2]) / 2
    slopes = [math.degrees(rad) for rad in np.arctan(slopes)]
    print(slopes)

    fig, ax = plt.subplots()
    ax.plot(kms, elevs)
    ax.scatter(kms, elevs, color='r', s=10, edgecolors='red')
    # label axis:
    plt.xlabel('Distance (km)')
    plt.ylabel('Elevation (meters)')
    plt.show()


if __name__ == "__main__":
    # # get track gps points (lat, lon):
    elev_map_path, tile_rep = areas_paths['baiersbronn']
    BAIERSBRONN_COORS = [8.1584, 48.4688, 8.4797, 48.6291]

    data_collector = odc.OsmDataCollector(BAIERSBRONN_COORS)
    track = data_collector.tracks[0]
    points = track.extract_gps_points()
    points = points.to_numpy()[:, :2]
    elevs = compute_track_elevation(elev_map_path, tile_rep, points)

    # # compute slopes, plot the change in elevation(in meters) over distance (in km). marking kmMark points
    # # according to the spacing:
    slopes = compute_slope(points, elevs, track.length())  # TODO add getter in OSM
    print(slopes)

    # Slopes sanity check:
    slopes_sanity_check()


