#!/usr/bin/env python

#
# Preprocess a SNAP downloaded dataset for loading using jgrapht-webgraph.
# We simply delete the comments.
#

import argparse
import sys
import os
import subprocess
import csv
import gzip

def main(ifilename, ofilename):

    print("Reading from gzip input file: {}".format(ifilename))
    print("Writing to gzip output file: {}".format(ofilename))

    with gzip.open(ifilename, "rt") as gzin, gzip.open(ofilename, "wt") as gzout:
        for line in gzin:
            if not line.startswith("#"):
                gzout.write(line)


def is_valid_input_file(parser, arg):
    if not os.path.exists(arg):
        parser.error("The file %s does not exist!" % arg)
    return os.path.abspath(os.path.normpath(arg))


def is_valid_output_file(parser, arg):
    if os.path.exists(arg):
        parser.error("The file %s already exists!" % arg)
    return os.path.abspath(os.path.normpath(arg))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Preprocess")
    parser.add_argument(
        "-i",
        dest="ifilename",
        required=True,
        help="input file",
        metavar="FILE",
        type=lambda x: is_valid_input_file(parser, x),
    )
    parser.add_argument(
        "-o",
        dest="ofilename",
        required=True,
        help="output file",
        metavar="FILE",
        type=lambda x: is_valid_output_file(parser, x),
    )
    args = parser.parse_args()
    main(args.ifilename, args.ofilename)
