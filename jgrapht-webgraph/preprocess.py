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
import time


def main(ifilename, ofilename, renumber=False):

    print("Reading from gzip input file: {}".format(ifilename))
    print("Writing to gzip output file: {}".format(ofilename))
    print("Preprocess start: {:f} sec".format(time.time()))

    next_node = 0
    nodes = {}
    edges= set()

    with gzip.open(ifilename, "rt") as gzin, open(ofilename, "wt") as gzout:
        for line in gzin:
            if line.startswith("#"):
                continue
            fields = line.split()
            if len(fields) != 2: 
                print("Failed to parse line: {}".format(line))
                continue

            source = fields[0]
            if renumber: 
                if source in nodes: 
                    source = nodes[source]
                else: 
                    nodes[source] = next_node
                    source = next_node
                    next_node += 1

            target = fields[1]
            if renumber: 
                if target in nodes: 
                    target = nodes[target]
                else: 
                    nodes[target] = next_node
                    target = next_node
                    next_node += 1

            e = (source, target)
            if e not in edges: 
                edges.add(e)
                gzout.write("{} {}\n".format(source, target))

    if renumber:
        renumber_filename = "renumber.txt"
        print("Writing renumbering map to output file: {}".format(renumber_filename))
        with open(renumber_filename, 'wt') as out: 
            for k, v in nodes.items():
                out.write("{} {}\n".format(k, v))

    print("Preprocess finished: {:f} sec".format(time.time()))            

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
    parser.add_argument(
        "-r",
        dest="renumber",
        help="Whether to renumber the vertices",
        type=bool,
        metavar="BOOLEAN",
        default=False,
    )
    args = parser.parse_args()
    main(args.ifilename, args.ofilename, renumber=args.renumber)
