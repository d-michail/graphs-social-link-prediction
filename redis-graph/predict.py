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


def adamic_adar(rg, u, v, degrees, friends): 
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


def get_degree(rg, v):
    """Find the degree of a vertex"""
    query = f"MATCH (m1:Member {{name:{v}}})-[:Friend]->(m2:Member) WITH m1, count(m2) as degree RETURN m1, degree"
    result = rg.query(query).result_set
    if len(result) > 0:
        _, degree = result[0]
        return degree
    
    query = f"MATCH (m1:Member {{name:{v}}}) RETURN m1"
    result = rg.query(query).result_set
    if len(result) > 0:
        return 0

    raise ValueError('Failed to locate vertex: {}'.format(v))


def all_vertices(rg):
    query = "MATCH (m1:Member)-[:Friend]->(m2:Member) WITH m1, count(m2) as degree RETURN m1, degree"
    result = rg.query(query)
    for record in result.result_set:
        member, member_degree = record
        print(f"{member} - {member_degree}")


def query_vertices(rg, min_degree=100):
    """
    Find all vertices with a minimum degree
    """
    query = "MATCH (m1:Member)-[:Friend]->(m2:Member) WITH m1, count(m2) as degree, collect(m2) as friends  WHERE degree > {} RETURN m1, degree, friends".format(min_degree)
    result = rg.query(query)

    friends = {}
    degrees = {}
    for record in result.result_set:
        member, member_degree, member_friends = record
        name = member.properties['name']
        degrees[name] = member_degree
        friends[name] = list(map(lambda x: x.properties['name'], member_friends))
    
    return friends, degrees


def main():

    r = redis.Redis(host='localhost', port=6379)

    rg = Graph('LIVEJOURNAL', r)

    print (rg.labels())
    print (rg.relationshipTypes())
    print (rg.propertyKeys())

    friends, degrees = query_vertices(rg)
    results = []

    for v in friends.keys():
        adj = friends[v]
        for u in friends.keys():
            if u in adj: 
                continue
            score = adamic_adar(rg, v, u, degrees, friends)
            if score is not None: 
                results.append((v,u,score))

    results.sort(key=lambda x: x[2], reverse=True)
    topk = 10
    print (results[:topk])

    #rg.delete()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Predict")
    args = parser.parse_args()
    main()
