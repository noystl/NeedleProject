import os
import math
import numpy

if __name__ == "__main__":
    fn = 'C:/Users/Matan Pinkas/Desktop/N48E002.hgt'

    siz = os.path.getsize(fn)
    dim = int(math.sqrt(siz / 2))

    assert dim * dim * 2 == siz, 'Invalid file size'

    data = numpy.fromfile(fn, numpy.dtype('>i2'), dim * dim).reshape((dim, dim))
    x = 1
