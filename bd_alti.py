#!/usr/bin/env python3
import math
import os
import pyproj
import sys

"""
This script filters the BD ALTI from IGN (ESRI grid) to keep only the relevant
files for the specified area.

Input is an Arc/Info E00 (ASCII) file from the IGN BD ALTI database.
Output is an ASCII XYZ gridded file, sorted by increasing X and decreasing Y.
"""


def has_overlap(a, b):
    """
    Returns
    * False if no overlap between the intervals represented by a and b,
    * True otherwise
    """
    return (max(0, min(a[1], b[1]) - max(a[0], b[0])) > 0)


def parse_header(fh):
    """
    Parses the header of an Arc/Info E00 (ASCII) altitude file.
    """
    ncols = int(fh.readline().strip().split(" ")[-1])
    nrows = int(fh.readline().strip().split(" ")[-1])
    xllcorner = float(fh.readline().strip().split(" ")[-1])
    yllcorner = float(fh.readline().strip().split(" ")[-1])
    cellsize = float(fh.readline().strip().split(" ")[-1])

    return ncols, nrows, xllcorner, yllcorner, cellsize


if len(sys.argv) < 6:
    print("Usage: "+sys.argv[0]+" LAT_MIN LNG_MIN LAT_MAX LNG_MAX DATA_FOLDER")
    sys.exit()

lat_min = float(sys.argv[1])
lng_min = float(sys.argv[2])
lat_max = float(sys.argv[3])
lng_max = float(sys.argv[4])
data_folder = os.path.expanduser(sys.argv[5])

if len(sys.argv) > 6:
    out_file = sys.argv[6]
else:
    out_file = "out.xyz"

print(("Looking for data between latitudes and longitudes " +
       "({0}, {1}) and ({2}, {3})").format(lat_min, lng_min, lat_max, lng_max))

wgs84 = pyproj.Proj("+init=EPSG:4326")
lambert = pyproj.Proj("+init=EPSG:2154")
x_min, y_min = pyproj.transform(wgs84, lambert, lng_min, lat_min)
x_max, y_max = pyproj.transform(wgs84, lambert, lng_max, lat_max)

if x_min > x_max:
    x_min, x_max = x_max, x_min
if y_min > y_max:
    y_min, y_max = y_max, y_min

print(("Looking for data between map coordinates " +
       "({0}, {1}) and ({2}, {3})").format(x_min, y_min, x_max, y_max))

founds = []
for f in os.listdir(data_folder):
    if not(f.endswith(".asc")):
        continue
    file = os.path.join(data_folder, f)
    with open(file, 'r') as fh:
        ncols, nrows, xllcorner, yllcorner, cellsize = parse_header(fh)

        if has_overlap([x_min, x_max],
                       [xllcorner, xllcorner + cellsize * ncols]):
            if has_overlap([y_min, y_max],
                           [yllcorner, yllcorner + cellsize * nrows]):
                founds.append(file)

if len(founds) == 0:
    print("No matching dataset found =(.")
else:
    print("Matching datasets:")
    print("\n".join(founds))


# Extract relevant parts from the datasets and output it as xyz values
out = "X\tY\tZ\n"
for f in founds:
    with open(f, 'r') as fh:
        ncols, nrows, xllcorner, yllcorner, cellsize = parse_header(fh)

        col_min = math.floor((x_min - xllcorner) / cellsize)
        col_max = math.ceil((x_max - xllcorner) / cellsize)
        # The (0, 0) point is the lower left one, that is on the last line.
        row_max = nrows - math.floor((y_min - yllcorner) / cellsize)
        row_min = nrows - math.ceil((y_max - yllcorner) / cellsize)

        i = 0
        for line in fh.readlines():
            if i >= row_min and i <= row_max:
                row = [float(j) for j in line.strip().split(" ")]
                for j in range(col_min, col_max):
                    out += "{0}\t{1}\t{2}\n".format(xllcorner + j * cellsize,
                                                    (yllcorner +
                                                     (nrows - i) * cellsize),
                                                    row[j])
            i += 1

out = out.strip()

# Write it to out.xyz file
with open(out_file, 'w') as fh:
    fh.write(out)

if len(sys.argv) < 7:
    print("Found data (also exported to "+out_file+"):")
    print(out)
else:
    print("Found data exported to "+out_file+".")
