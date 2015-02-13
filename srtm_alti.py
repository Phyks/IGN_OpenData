#!/usr/bin/env python3
import struct
import sys

"""
This script filters the SRTM altimetry dataset from NASA to keep only the
relevant files for the specified area.

Input is an HGT file from the SRTM dataset.
Output is an ASCII XYZ gridded file, sorted by increasing X and decreasing Y.
"""


def lat_lng_to_row_col(lat, lng):
    return 1201 - round((lng % 1) * 3600 / 3), round((lat % 1) * 3600 / 3)


if len(sys.argv) < 6:
    print("Usage: "+sys.argv[0]+" LAT_MIN LNG_MIN LAT_MAX LNG_MAX HGT_FILE")
    sys.exit()

lat_min = float(sys.argv[1])
lng_min = float(sys.argv[2])
lat_max = float(sys.argv[3])
lng_max = float(sys.argv[4])
hgt_file = sys.argv[5]

if len(sys.argv) > 6:
    out_file = sys.argv[6]
else:
    out_file = "out.xyz"

print(("Looking for data between latitudes and longitudes " +
       "({0}, {1}) and ({2}, {3})").format(lat_min, lng_min, lat_max, lng_max))

# Extract relevant parts from the dataset and output it as xyz values
# X and Y are pixels coordinates in this case
out = "X\tY\tZ\n"
with open(hgt_file, "rb") as fh:
    # The first row in the file is very likely the northernmost one and there
    # are 1200 rows. 3 arc-seconds sampling
    row_min, col_min = lat_lng_to_row_col(lat_min, lng_min)
    row_max, col_max = lat_lng_to_row_col(lat_max, lng_max)
    print("Corresponding rectangle in the image is " +
          "({0}, {1}), ({2}, {3})".format(row_min, col_min, row_max, col_max))

    if col_min > col_max:
        col_min, col_max = col_max, col_min
    if row_min > row_max:
        row_min, row_max = row_max, row_min

    for i in range(row_max, row_min - 1, -1):
        for j in range(col_min, col_max + 1):
            fh.seek(((i - 1) * 1201 + (j - 1)) * 2)  # Find the right spot
            buf = fh.read(2)  # read two bytes and convert them
            val = struct.unpack('>h', buf)  # ">h" is a signed two byte integer
            out += "{0}\t{1}\t{2}\n".format(j,
                                            i,
                                            val[0])
out = out.strip()

# Write it to out.xyz file
with open(out_file, 'w') as fh:
    fh.write(out)

if len(sys.argv) < 7:
    print("Found data (also exported to "+out_file+"):")
    print(out)
else:
    print("Found data exported to "+out_file+".")
