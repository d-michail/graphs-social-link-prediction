#!/usr/bin/env python

#
# Preprocess a SNAP downloaded dataset for loading using redis-graph.
# We use the tool from https://github.com/redisgraph/redisgraph-bulk-loader
# for loading thus the output should correspond to that format.
#

import argparse
import sys
import os
import subprocess
import csv
import gzip
import time


def main(ifilename):

    print("Reading from gzip input file: {}".format(ifilename))

    nodes_csv = "Member.csv"
    edges_csv = "Friend.csv"

    print("Writing nodes to output file: {}".format(nodes_csv))
    print("Writing edges to output file: {}".format(edges_csv))

    start=time.time()
    print("Preprocess start: {:f} sec".format(start))
    nodes = set()
    edges = set()

    with gzip.open(ifilename, "rt") as gzin, open(nodes_csv, "wt") as nodesout, open(
        edges_csv, "wt"
    ) as edgesout:
        nodesout.write("_id, name\n")
        edgesout.write("source, target\n")
        for line in gzin:
            if not line.startswith("#"):
                fields = line.split()
                try:
                    source = fields[0]
                    target = fields[1]
                    if source == target: 
                        continue

                    if source not in nodes:
                        nodesout.write("{}, \"{}\"\n".format(int(source), source))
                        nodes.add(source)
                    if target not in nodes:
                        nodesout.write("{}, \"{}\"\n".format(int(target), target))
                        nodes.add(target)

                    e = (source, target)
                    if e not in edges: 
                        edges.add(e)
                        edgesout.write("{}, {}\n".format(int(source), int(target)))
                except:
                    print("Failed to parse line: {}".format(line))

    end = time.time()
    print("Preprocess finished: {:f} sec".format(end))
    print("Took: {:f} sec".format(end-start))

def is_valid_input_file(parser, arg):
    if not os.path.exists(arg):
        parser.error("The file %s does not exist!" % arg)
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
    args = parser.parse_args()
    main(args.ifilename)
