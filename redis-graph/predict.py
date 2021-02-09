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
import multiprocessing
import numpy as np
import threading
import time

import redis
from redisgraph import Node, Edge, Graph, Path


def adamic_adar(rg, u, v, degrees, friends):
    """Compute adamic adar for two vertices"""
    intersection = set(friends[u]).intersection(set(friends[v]))
    result = 0
    for z in intersection:
        if z in degrees:
            dz = degrees[z]
        else:
            # query DB and cache result
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

    raise ValueError("Failed to locate vertex: {}".format(v))


def query_vertices(rg, min_degree):
    """
    Find all vertices with a minimum degree
    """
    query = "MATCH (m1:Member)-[:Friend]->(m2:Member) WITH m1, count(m2) as degree, collect(m2) as friends  WHERE degree >= {} RETURN m1, degree, friends".format(
        min_degree
    )
    result = rg.query(query)

    friends = {}
    degrees = {}
    for record in result.result_set:
        member, member_degree, member_friends = record
        name = member.properties["name"]
        degrees[name] = member_degree
        friends[name] = list(map(lambda x: x.properties["name"], member_friends))

    return friends, degrees


def run_queries(index, results, rg, queries, degrees, friends, topk):
    print('Thread {} starting {} queries'.format(index, len(queries)))
    print("Thread {} start: {:f} sec".format(index, time.time()))
    local_results = []
    for v, u in queries:
        score = adamic_adar(rg, v, u, degrees, friends)
        if score is not None:
            local_results.append((v, u, score))
    local_results.sort(key=lambda x: x[2], reverse=True)
    results[index] = local_results[:topk]
    print("Thread {} finished: {:f}".format(index, time.time()))


def single_run(rg): 
    start = time.time()
    print(rg.labels())
    print(rg.relationshipTypes())
    print(rg.propertyKeys())

    print('Looking for candidate vertices')
    print('Using minimum degree: {}'.format(args.min_degree))
    print("Building candidate pairs start: {:f} sec".format(time.time()))
    friends, degrees = query_vertices(rg, min_degree=args.min_degree)

    print('Building candidate pairs')
    queries = []
    for v in friends.keys():
        adj = friends[v]
        for u in friends.keys():
            if v == u or u in adj:
                continue
            queries.append((v, u))

    print("Building candidate pairs finished: {:f} sec".format(time.time()))
    print("Candidate pairs: {}".format(len(queries)))

    cores = multiprocessing.cpu_count()
    results = [[] for _ in range(cores)]
    print('Spliting to {} parts'.format(cores))
    queries_per_thread = np.array_split(np.array(queries), cores)
    threads = []
    topk = 10

    for i in range(cores):
        th = threading.Thread(
            target=run_queries, args=[i, results, rg, queries_per_thread[i], degrees, friends, topk]
        )
        threads.append(th)
        th.start()

    for th in threads:
        th.join()

    print('Merging results')
    all_results = [item for sublist in results for item in sublist]
    all_results.sort(key=lambda x: x[2], reverse=True)
    print("Merged all results done: {:f} sec".format(time.time()))
    print (all_results[:topk])

    end=time.time()
    return end-start, all_results[:topk]
    #rg.delete()



def main(args):

    r = redis.Redis(host="localhost", port=6379)
    rg = Graph("GRAPH", r)

    avg = 0
    for i in range(args.repeat):
        print("Starting run {}".format(i))
        time, results = single_run(rg)
        print("Run {}, time {} sec, results {}".format(i, time, results))
        avg += time
    avg /= args.repeat

    print("Average time {} sec".format(avg))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Predict")
    parser.add_argument('--mindegree', metavar='INT', type=int, default=100, dest='min_degree', help='Minimum degree')
    parser.add_argument('--repeat', metavar='INT', type=int, default=10, dest='repeat', help='How many times to repeat the experiment')

    args = parser.parse_args()
    main(args)
