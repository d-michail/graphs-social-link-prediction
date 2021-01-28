#!/usr/bin/env python

#
# Predict
#

import argparse
import sys
import os
import subprocess
import csv
import gzip

import redis
from redisgraph import Node, Edge, Graph, Path


def main():

    r = redis.Redis(host='localhost', port=6379)

    rg = Graph('LIVEJOURNAL', r)

    print (rg.labels())
    print (rg.relationshipTypes())
    print (rg.propertyKeys())

    query = """MATCH p = (s)-[]->(t) RETURN p"""
    result = rg.query(query)

    # Iterate through resultset
    for record in result.result_set:
        path = record[0]
        print(path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Predict")
    args = parser.parse_args()
    main()
