package org.hua.linksocial;

import java.io.IOException;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;

import org.jgrapht.Graphs;
import org.jgrapht.alg.linkprediction.AdamicAdarIndexLinkPrediction;
import org.jgrapht.alg.linkprediction.LinkPredictionIndexNotWellDefinedException;
import org.jgrapht.alg.util.Pair;
import org.jgrapht.alg.util.Triple;
import org.jgrapht.webgraph.ImmutableDirectedBigGraphAdapter;

import com.beust.jcommander.JCommander;
import com.google.common.collect.Lists;

import it.unimi.dsi.big.webgraph.BVGraph;
import it.unimi.dsi.fastutil.longs.LongLongPair;

public class PredictApp {

	public static void main(String args[]) throws IOException, InterruptedException {

		Args argsModel = new Args();
		JCommander.newBuilder().addObject(argsModel).build().parse(args);

		if (argsModel.getParameters().size() < 1) {
			System.out.println("Required input file missing");
			System.exit(-1);
		}

		String inputFile = argsModel.getParameters().get(0);
		final int minDegree = argsModel.getMinDegree();

		System.out.println("Will read from webgraph file: " + inputFile);
		System.out.println("Will query vertices of minimum degree: " + minDegree);

		BVGraph bvGraph = BVGraph.load(inputFile);
		ImmutableDirectedBigGraphAdapter graph = new ImmutableDirectedBigGraphAdapter(bvGraph);
		System.out.println("Graph has " + graph.iterables().vertexCount() + " number of vertices");
		System.out.println("Graph has " + graph.iterables().edgeCount() + " number of edges");

		ImmutableDirectedBigGraphAdapter copy = graph.copy();

		AdamicAdarIndexLinkPrediction<Long, LongLongPair> alg = new AdamicAdarIndexLinkPrediction<>(graph);

		List<Pair<Long, Long>> queries = new ArrayList<>();
		long vertexCount = graph.iterables().vertexCount();
		for (long s = 0; s < vertexCount; s++) {
			if (graph.iterables().outDegreeOf(s) < minDegree) {
				continue;
			}

			// index neighbors
			Set<Long> other = new HashSet<>();
			for (LongLongPair e : graph.outgoingEdgesOf(s)) {
				other.add(Graphs.getOppositeVertex(graph, e, s));
			}

			// test all possible neighbors
			for (long t = 0; t < vertexCount; t++) {
				if (other.contains(t)) {
					continue;
				}

				if (graph.iterables().outDegreeOf(t) < minDegree) {
					continue;
				}

				queries.add(Pair.of(s, t));
			}
		}
		System.out.println("Computed " + queries.size() + " queries");

		int cores = Runtime.getRuntime().availableProcessors();
		System.out.println("Spliting into " + cores + " cores");
		List<List<Pair<Long, Long>>> queriesPartitions = Lists.partition(queries, queries.size() / cores);

		final int topK = 10;
		Map<Integer, List<Triple<Long, Long, Double>>> responses = new HashMap<>();
		Thread[] threads = new Thread[cores];
		for (int i = 0; i < cores; i++) {
			System.out.println("Starting thread " + i);
			threads[i] = new Thread(new SingleTask(graph.copy(), i, topK, queriesPartitions.get(i), responses));
			threads[i].start();
		}

		for (int i = 0; i < cores; i++) {
			threads[i].join();
		}
		
		List<Triple<Long, Long, Double>> finalResults = new ArrayList<>();
		for (int i = 0; i < cores; i++) {
			finalResults.addAll(responses.get(i));
		}
		finalResults.sort(Comparator.comparing((Triple<Long, Long, Double> t) -> t.getThird()).reversed());
		finalResults = finalResults.subList(0, topK);
		
		System.out.println(finalResults);
	}

	private static class SingleTask implements Runnable {

		private ImmutableDirectedBigGraphAdapter graph;
		private int index;
		private int topK;
		private List<Pair<Long, Long>> queries;
		private Map<Integer, List<Triple<Long, Long, Double>>> responses;

		public SingleTask(ImmutableDirectedBigGraphAdapter graph, int index, int topK, List<Pair<Long, Long>> queries,
				Map<Integer, List<Triple<Long, Long, Double>>> responses) {
			this.graph = graph;
			this.index = index;
			this.topK = topK;
			this.queries = queries;
			this.responses = responses;
		}

		@Override
		public void run() {
			AdamicAdarIndexLinkPrediction<Long, LongLongPair> alg = new AdamicAdarIndexLinkPrediction<>(graph);
			List<Triple<Long, Long, Double>> result = new ArrayList<>();
			for (Pair<Long, Long> q : queries) {
				try {
					double score = alg.predict(q.getFirst(), q.getSecond());
					if (score > 0) {
						result.add(Triple.of(q.getFirst(), q.getSecond(), score));
					}
				} catch (LinkPredictionIndexNotWellDefinedException e) {
					// ignore
				}
			}

			result.sort(Comparator.comparing((Triple<Long, Long, Double> t) -> t.getThird()).reversed());
			result = result.subList(0, topK);

			//System.out.println("Thread " + index + " found: " + result);

			responses.put(index, result);
		}

	}

}
