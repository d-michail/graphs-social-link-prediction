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
import math

import redis
from redisgraph import Node, Edge, Graph, Path

MIN_DEGREE=100

def adamic_adar(u, v, degrees, friends, rg): 
    intersection = set(friends[u]).intersection(set(friends[v]))
    result = 0
    for z in intersection: 
        if z in degrees: 
            dz = degrees[z]
        else:
            dz = get_degree(rg, z)
            degrees[z] = dz
        if dz < 2: 
            return None

        result += 1.0 / math.log(dz)
    return result


def get_degree(redis_graph, v):
    query = "MATCH (m1:Member)-[:Friend]->(m2:Member) WITH m1, count(m2) as degree WHERE ID(m1) = {} RETURN m1, degree".format(v)
    print(query)
    result = redis_graph.query(query).result_set
    print(result)
    if len(result) == 0: 
        print('Failed to locate vertex: {}'.format(v))
    _, degree = result[0]
    return degree


def main():

    r = redis.Redis(host='localhost', port=6379)

    rg = Graph('LIVEJOURNAL', r)

    print (rg.labels())
    print (rg.relationshipTypes())
    print (rg.propertyKeys())

    # Find all vertices which have degree > 100
    query = "MATCH (m1:Member)-[:Friend]->(m2:Member) WITH m1, count(m2) as degree, collect(m2) as friends  WHERE degree > {} RETURN m1, degree, friends".format(MIN_DEGREE)
    result = rg.query(query)

    friends = {}
    degrees = {}
    for record in result.result_set:
        member, member_degree, member_friends = record
        degrees[member.id] = member_degree
        friends[member.id] = list(map(lambda x: x.id, member_friends))

    for v in friends.keys():
        adj = friends[v]
        for u in friends.keys():
            if u in adj: 
                continue
            adamic_adar(v, u, degrees, friends, rg)
            #print('Will query {}-{}'.format(u,v))

    #rg.delete()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Predict")
    args = parser.parse_args()
    main()
