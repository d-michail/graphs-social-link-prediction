#!/usr/bin/env python

#
# Predict
#

import argparse
import multiprocessing
import numpy as np
import threading
import time
import sys

from neo4j import GraphDatabase


def adamic_adar(driver, u, v):
    """Compute adamic adar for two vertices"""
    query = """MATCH (m1:Member {name: '%s'})
        MATCH (m2:Member {name: '%s'})
        RETURN gds.alpha.linkprediction.adamicAdar(m1, m2, {relationshipQuery:'Friend', orientation:'NATURAL'})
    """%(u, v)
    with driver.session() as session:
        result = session.read_transaction(lambda tx: tx.run(query)).single()[0]
    return result


def query_vertices(driver, min_degree):
    """
    Find all vertices with a minimum degree
    """
    query = f"MATCH (m1:Member)-[:Friend]->(m2:Member) WITH m1, count(m2) as degree, collect(m2) as friends WHERE degree >= {min_degree} RETURN m1, friends"
    with driver.session() as session:
        result = list(session.read_transaction(lambda tx: tx.run(query)))

    friends = {}
    for record in result:
        member, member_friends = record
        name = member["name"]
        friends[name] = list(map(lambda x: x["name"], member_friends))

    return friends


def run_queries(index, results, driver, queries, topk):
    print('Thread {} starting {} queries'.format(index, len(queries)))
    print("Thread {} start: {:f} sec".format(index, time.time()))
    sys.stdout.flush()
    local_results = []
    i = 0
    for v, u in queries:
        if i % 1000 == 0:
            print('Thread {} at query {}'.format(index, i))
            sys.stdout.flush()
        score = adamic_adar(driver, v, u)
        if score is not None:
            local_results.append((v, u, score))
        i += 1
    local_results.sort(key=lambda x: x[2], reverse=True)
    results[index] = local_results[:topk]
    print("Thread {} finished: {:f}".format(index, time.time()))
    sys.stdout.flush()

def get_node_labels(driver):
    with driver.session() as session:
        res = session.read_transaction(lambda tx: tx.run('CALL db.labels()'))
    return list(res)

def get_relationship_types(driver):
    with driver.session() as session:
        res = session.read_transaction(lambda tx: tx.run('CALL db.relationshipTypes()'))
    return list(res)

def get_property_keys(driver):
    with driver.session() as session:
        res = session.read_transaction(lambda tx: tx.run('CALL db.propertyKeys()'))
    return list(res)

def single_run():
    driver = GraphDatabase.driver("bolt://localhost:7687", auth=(args.username, args.password), encrypted=False)

    start = time.time()
    print(get_node_labels(driver))
    print(get_relationship_types(driver))
    print(get_property_keys(driver))

    print('Looking for candidate vertices')
    print("Building candidate pairs start: {:f} sec".format(time.time()))
    sys.stdout.flush()
    friends = query_vertices(driver, min_degree=args.min_degree)

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
    sys.stdout.flush()

    cores = multiprocessing.cpu_count()
    results = [[] for _ in range(cores)]
    print('Spliting to {} parts'.format(cores))
    queries_per_thread = np.array_split(np.array(queries), cores)
    threads = []
    topk = 10

    for i in range(cores):
        th = threading.Thread(
            target=run_queries, args=[i, results, driver, queries_per_thread[i], topk]
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
    sys.stdout.flush()

    end=time.time()

    driver.close()

    return end-start, all_results[:topk]


def main(args):
    avg = 0
    for i in range(args.repeat):
        print("Starting run {}".format(i))
        time, results = single_run()
        print("Run {}, time {} sec, results {}".format(i, time, results))
        avg += time
    avg /= args.repeat

    print("Average time {} sec".format(avg))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Predict")
    parser.add_argument('--mindegree', metavar='INT', type=int, default=100, dest='min_degree', help='Minimum degree')
    parser.add_argument('--username', type=str, default='neo4j', dest='username', help='Neo4j username')
    parser.add_argument('--password', type=str, default='demo', dest='password', help='Neo4j password')
    parser.add_argument('--repeat', metavar='INT', type=int, default=10, dest='repeat', help='How many times to repeat the experiment')
    args = parser.parse_args()
    main(args)
