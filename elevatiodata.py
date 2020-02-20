import os
import math
import numpy as np
import matplotlib.pyplot as plt


def make_elev_map():
    # needs to adjust for generic location of high file
    fn = 'C:/Users/Matan Pinkas/Desktop/N48E002.hgt'
    siz = os.path.getsize(fn)
    dim = int(math.sqrt(siz / 2))
    assert dim * dim * 2 == siz, 'Invalid file size'
    data = np.fromfile(fn, np.dtype('>i2'), dim * dim).reshape((dim, dim))
    return data


def get_elev_atpt(elev_map, lon, lat, x, y):
    """
    :param data: 2d array of elevation in a grid (2d np array of ints)
    :param lon: longitude of top left corner
    :param lat: latitude of top left corder
    :param x: longitude of point to be checked
    :param y: latitude of point to be checked
    """
    frac_x = x - lon
    frac_y = y - lat
    cell_x = 1 / elev_map.shape[1]
    cell_y = 1 / elev_map.shape[0]
    elev_x = frac_x // cell_x
    elev_y = frac_y // cell_y
    return elev_x, elev_y


if __name__ == "__main__":
    dat = make_elev_map()
    x, y = get_elev_atpt(dat, 48, 2, 48.8606, 2.3376)
    ele = dat[int(x)][int(y)]
    print(np.amax(dat))
    # fig, ax = plt.subplots()
    # im = ax.imshow(dat[::-1, :])
    # plt.show()
    x = 1
