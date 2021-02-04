#!/usr/bin/env python

#
# Predict
#

import argparse
import multiprocessing
import numpy as np
import threading
import time

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
    local_results = []
    for v, u in queries:
        score = adamic_adar(driver, v, u)
        if score is not None:
            local_results.append((v, u, score))
    local_results.sort(key=lambda x: x[2], reverse=True)
    results[index] = local_results[:topk]
    print("Thread {} finished: {:f}".format(index, time.time()))

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


def main(args):

    driver = GraphDatabase.driver("bolt://localhost:7687", auth=(args.username, args.password), encrypted=False)

    print(get_node_labels(driver))
    print(get_relationship_types(driver))
    print(get_property_keys(driver))

    print('Looking for candidate vertices')
    print("Building candidate pairs start: {:f} sec".format(time.time()))
    friends = query_vertices(driver, min_degree=args.min_degree)

    print(friends.keys())

    print('Building candidate pairs')
    queries = []
    for v in friends.keys():
        adj = friends[v]
        for u in friends.keys():
            if u in adj:
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

    driver.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Predict")
    parser.add_argument('--mindegree', metavar='INT', type=int, default=100, dest='min_degree', help='Minimum degree')
    parser.add_argument('--username', type=str, default='neo4j', dest='username', help='Neo4j username')
    parser.add_argument('--password', type=str, default='demo', dest='password', help='Neo4j password')
    args = parser.parse_args()
    main(args)
