#TODO:
# (1) break file into modules-
#       1. class for a elev map that can be questioned.
#       2. file for the graph rep (?)
#       3. file for the slopes rep (?)
#       4. or a class that delivers the functionality of 3. , and omits 2. "on the way"(?)
# (2) generalize the SITE_COORDS, and SITE_ELEV_MAP for the project to use, by creating a file for them (?)


import os
import math
import mplleaflet
import numpy as np
import OsmDataCollector as odc
import matplotlib.pyplot as plt
from geopy.distance import distance
import scipy.ndimage
RAD_TO_DEG = 1 / 57.2957795


PARIS_COORS = [2.3314, 48.8461, 2.3798, 48.8643]
LOUVRE_COORS = [2.3295, 48.8586, 2.3422, 48.8636]
FELDBERG_COORS = [8.1026, 48.3933, 8.183, 48.4335]
BAIERSBRONN_COORS = [8.1584, 48.4688, 8.4797, 48.6291]

PARIS_ELEV_MAP = 'N48E002.hgt'
LOUVRE_ELEV_MAP = ''
FELDBERG_ELEV_MAP = ''
BAIERSBRONN_ELEV_MAP = ''


# Elevation Map #
def make_elev_map(area_file):
    """
    creates an elevation map of the area depicted in the supplied file.
    :param area_file: an hgt file holding the elevation values of the relevant tile.
    :return: 2-dim np array holding the elevation values of 30-meters "mini-tiles"
    in the supplied tile.
    """
    siz = os.path.getsize(area_file)
    dim = int(math.sqrt(siz / 2))
    # assert dim * dim * 2 == siz, 'Invalid file size'
    data = np.fromfile(area_file, np.dtype('>i2'), dim * dim).reshape((dim, dim))
    return data


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
def computeTrackElevation(points, dat):
    """
    computes the elevation values along the track, represented by it's points.
    :param points: 2-dim np array of the track's points: (lat, lon).
    :param dat: the area map as returned from make_elev_map.
    :return: the km values along the track.
    """
    elevations = []
    for x_coor, y_coor in points:
        x, y = get_elev_atpt(dat, 48, 2, x_coor, y_coor)
        ele = dat[int(x)][int(y)]
        elevations.append(ele)
    return np.asarray(elevations)


def computeTrackKm(points):  # TODO: compare with Noy's implementation of getting the track's length
    """
    computes the km values along the track, represented by it's points.
    distance over path in computed by: https://janakiev.com/blog/gps-points-distance-python/
    :param points: 2-dim np array of the track's points: (lat, lon).
    :return: the km values along the track.
    """
    d = 0
    kms = [0]
    for i in range(len(points) - 1):
        d += distance(points[i], points[i + 1]).m / 1000  # converted to kms
        kms.append(d)
    return np.asarray(kms)


def plotDistElevation(interestPoints, dat):
    """
    plots the change in elevation(in meters) over distance(in km).
    """
    kms = computeTrackKm(interestPoints)
    elevations = computeTrackElevation(interestPoints, dat)

    fig, ax = plt.subplots()
    ax.plot(kms, elevations)

    ax.scatter(interestPoints[:, 0], interestPoints[:, 1], color='r', s=10, edgecolors='black')

    # label axis:
    plt.xlabel('Distance (km)')
    plt.ylabel('Elevation (meters)')

    # change y axis range to capture representation of elevation:
    # plt.axis([0, np.amax(kms), 0, np.amax(elevations) + 10])
    # change y axis mark points to represent kms:
    # start, end = ax.get_xlim()
    # ax.xaxis.set_ticks(np.arange(start, end, 1))

    plt.show()


# slope Representation (for shingling: representing the tracks as vector of enums- percentage of slope) #
def computeSlope(trackPoints, tick):
    dat = make_elev_map(PARIS_ELEV_MAP)
    trackElevs = computeTrackElevation(trackPoints, dat)

    trackKms = computeTrackKm(trackPoints)
    kmMarks = np.arange(0, trackKms[-1], tick / 2)
    # handles the last segment of track- ignore it or take more than documented-
    # if we are past the midpoint of the segment:
    if trackKms[-1] > kmMarks[-1] + (tick / 4):
        np.append(kmMarks, kmMarks[-1] + tick / 2)

    # interpolate the elevation values at kmMarks:
    elevMarks = np.interp(kmMarks, trackKms, trackElevs)

    # TODO: FOR VISUALIZING-
    plotDistElevation(np.stack((kmMarks, elevMarks), axis=-1), dat)

    # get slopes of all sections:
    slopes = (elevMarks[2:] - elevMarks[:-2]) / tick  # slope of a straight lien
    slopes = np.array([math.degrees(rad) for rad in np.arctan(slopes)])  # the slope in degrees

    return slopes


def slopesSanityCheck():
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
    data_collector = odc.OsmDataCollector(PARIS_COORS)
    track = data_collector.tracks[0]
    points = track.extract_gps_points()
    points = points.to_numpy()[:, :2]

    # # create elevation map of the area:
    dat = make_elev_map(PARIS_ELEV_MAP)
    # fig, ax = plt.subplots()
    # im = ax.imshow(dat[::-1, :], cmap='gray')
    # plt.show()

    # # compute slopes, plot the change in elevation(in meters) over distance (in km). marking kmMark points
    # # according to the spacing:
    slopes = computeSlope(points, 0.5)
    print(slopes)

    # Slopes sanity check:
    slopesSanityCheck()

