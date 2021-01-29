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

MIN_DEGREE=100

def main():

    r = redis.Redis(host='localhost', port=6379)

    rg = Graph('LIVEJOURNAL', r)

    print (rg.labels())
    print (rg.relationshipTypes())
    print (rg.propertyKeys())

    # Find all vertices which have degree > 100
    # TODO: add also the neighbors in the result
    query = "MATCH (m1:Member)-[:Friend]->(m2:Member) WITH m1, count(m2) as friends WHERE friends > {} RETURN m1, friends".format(MIN_DEGREE)
    result = rg.query(query)

    degrees = {}
    for record in result.result_set:
        member, count = record
        degrees[member.id] = count

    for v in degrees.keys():
        for u in degrees.keys():
            # TODO
            pass

    print(degrees)        


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Predict")
    args = parser.parse_args()
    main()
