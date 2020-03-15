import os
import math
import numpy as np
import matplotlib.pyplot as plt
from geopy.distance import distance

LEN_SPACING = 5  # size of the "buckets" of the length_tag
TICK = 0.125  # in kms


def get_tick(track_len):
    """
    returns the tick according to the track's length supplied.
    :param track_len: a track's length (km)
    :return: double (km)
    """
    len_tag = get_length_tag(track_len)
    return TICK * (len_tag + 1)


def get_length_tag(track_len):
    """
    :param track_len: int representing track's length in km
    :return: int >=0 representing the length tag of the given  track's length
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


def compute_track_km(points):
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
    plt.axis([0, np.amax(kms), min(0, np.amin(elevations) - 10), np.amax(elevations) + 10])
    # # change y axis mark points to represent kms:
    start, end = ax.get_xlim()
    ax.xaxis.set_ticks(np.arange(start, end, 1))

    plt.show()


# slope Representation #
def compute_slope(track_points, track_elevs, track_length):
    """
    :param track_points: 2-dim np array of the track's points: (lat, lon).
    :param track_elevs: float
    :param track_length: np array of length n, holding the elevations at points.
    :return: python list of floats representing the track's angles (values are in [-90, 90])
    """
    track_kms = compute_track_km(track_points)
    tick = get_tick(track_length)

    # gets the last multiple of tick  that was seen in track, and discards the leftover track:
    km_marks = np.arange(0, track_kms[-1], tick)
    if track_kms[-1] % tick == 0:
        np.append(km_marks, track_kms[-1])

    # interpolate the elevation values at kmMarks:
    elev_marks = np.interp(km_marks, track_kms, track_elevs)

    # get slopes of all sections:
    slopes = (elev_marks[1:] - elev_marks[:-1]) / tick  # slope between all 2 following tick points
    slopes = [math.degrees(rad) for rad in np.arctan(slopes)]  # the slope in degrees

    return slopes
