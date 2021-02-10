package org.hua.linksocial;

import java.io.BufferedReader;
import java.io.FileInputStream;
import java.io.FileNotFoundException;
import java.io.IOException;
import java.io.InputStreamReader;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.stream.Collectors;

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

public class PredictWebGraphApp {

	private static long singleRun(int run, ImmutableDirectedBigGraphAdapter graph, Map<Long, Long> renumber, int minDegree)
			throws InterruptedException {

		System.out.println("Run " + run);
		System.out.println("Starting queries computation: " + System.currentTimeMillis() + " ms");
		long start = System.currentTimeMillis();

		long vertexCount = graph.iterables().vertexCount();
		List<Long> minDegreeVertices = new ArrayList<>();
		for (long s = 0; s < vertexCount; s++) {
			if (graph.iterables().outDegreeOf(s) < minDegree) {
				continue;
			}
			minDegreeVertices.add(s);
		}
		
		List<Pair<Long, Long>> queries = new ArrayList<>();
		for (Long s: minDegreeVertices) {
			// index neighbors
			Set<Long> other = new HashSet<>();
			for (LongLongPair e : graph.outgoingEdgesOf(s)) {
				other.add(Graphs.getOppositeVertex(graph, e, s));
			}

			// test all possible neighbors
			for (Long t: minDegreeVertices) {
				if (s == t || other.contains(t)) {
					continue;
				}
				queries.add(Pair.of(s, t));
			}
		}
		System.out.println("Computed " + queries.size() + " queries");
		System.out.println("Finished queries computation: " + System.currentTimeMillis() + " ms");

		int cores = Runtime.getRuntime().availableProcessors();
		System.out.println("Spliting into " + cores + " cores");
		List<List<Pair<Long, Long>>> queriesPartitions = Lists.partition(queries, queries.size() / cores);

		final int topK = 10;
		Map<Integer, List<Triple<Long, Long, Double>>> responses = new HashMap<>();
		Thread[] threads = new Thread[cores];
		for (int i = 0; i < cores; i++) {
			System.out.println("Starting thread " + i);
			threads[i] = new Thread(new SingleTask(graph.copy(), renumber, i, topK, queriesPartitions.get(i), responses));
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

		System.out.println("Joined all results: " + System.currentTimeMillis() + " ms");
		System.out.println(finalResults);

		long end = System.currentTimeMillis();
		return end - start;
	}

	public static void main(String args[]) throws IOException, InterruptedException {

		Args argsModel = new Args();
		JCommander.newBuilder().addObject(argsModel).build().parse(args);

		if (argsModel.getParameters().size() < 1) {
			System.out.println("Required input file missing");
			System.exit(-1);
		}
	
		String inputFile = argsModel.getParameters().get(0);
		final int minDegree = argsModel.getMinDegree();
		
		Map<Long, Long> renumber = readRenumberFile(argsModel.getRenumberFile());

		System.out.println("Will read from webgraph file: " + inputFile);
		System.out.println("Will query vertices of minimum degree: " + minDegree);

		System.out.println("Starting graph load: " + System.currentTimeMillis() + " ms");
		BVGraph bvGraph = BVGraph.load(inputFile);
		System.out.println("Graph load done: " + System.currentTimeMillis() + " ms");
		ImmutableDirectedBigGraphAdapter graph = new ImmutableDirectedBigGraphAdapter(bvGraph);
		System.out.println("Graph has " + graph.iterables().vertexCount() + " number of vertices");
		System.out.println("Graph has " + graph.iterables().edgeCount() + " number of edges");

		double avg = 0;
		for (int i = 0; i < argsModel.getRepeat(); i++) {
			avg += singleRun(i, graph, renumber, minDegree);
		}
		avg /= argsModel.getRepeat();
		System.out.println("Average time taken: " + avg + " (ms)");
	}

	private static class SingleTask implements Runnable {

		private ImmutableDirectedBigGraphAdapter graph;
		private Map<Long, Long> renumber;
		private int index;
		private int topK;
		private List<Pair<Long, Long>> queries;
		private Map<Integer, List<Triple<Long, Long, Double>>> responses;

		public SingleTask(ImmutableDirectedBigGraphAdapter graph, Map<Long, Long> renumber, int index, int topK, List<Pair<Long, Long>> queries,
				Map<Integer, List<Triple<Long, Long, Double>>> responses) {
			this.graph = graph;
			this.renumber = renumber;
			this.index = index;
			this.topK = topK;
			this.queries = queries;
			this.responses = responses;
		}

		@Override
		public void run() {
			System.out.println("Thread " + index + " start: " + System.currentTimeMillis() + " ms");
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
			
			if (renumber.size() > 0) {
				result = result.stream()
						.map(t -> Triple.of(renumber.get(t.getFirst()), renumber.get(t.getSecond()), t.getThird()))
						.collect(Collectors.toList());
			}

			// System.out.println("Thread " + index + " found: " + result);

			responses.put(index, result);
			System.out.println("Thread " + index + " end: " + System.currentTimeMillis() + " ms");
		}

	}
	
	private static Map<Long, Long> readRenumberFile(String renumberFile)
			throws FileNotFoundException, IOException {
		if (renumberFile == null) {
			return Map.of();
		}

		Map<Long, Long> renumber = new HashMap<>();

		try (BufferedReader reader = new BufferedReader(new InputStreamReader(new FileInputStream(renumberFile)))) {
			String line = reader.readLine();
			while (line != null) {
				if (line.startsWith("#")) {
					continue;
				}
				String[] fields = line.split("\\s+");
				long source = Long.valueOf(fields[0]);
				long target = Long.valueOf(fields[1]);
				renumber.put(target, source);
				line = reader.readLine();
			}
		}
		return renumber;
	}

}
