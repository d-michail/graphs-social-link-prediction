package org.hua.linksocial;

import java.io.BufferedReader;
import java.io.FileInputStream;
import java.io.FileNotFoundException;
import java.io.IOException;
import java.io.InputStream;
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
import org.jgrapht.opt.graph.sparse.SparseIntDirectedGraph;

import com.beust.jcommander.JCommander;
import com.google.common.collect.Lists;

public class LoadAndPredictSparseGraphApp {

	public static void main(String[] args) throws FileNotFoundException, IOException {
		Args argsModel = new Args();
		JCommander.newBuilder().addObject(argsModel).build().parse(args);

		if (argsModel.getParameters().size() < 1) {
			System.out.println("Required input file missing");
			System.exit(-1);
		}

		String inputFile = argsModel.getParameters().get(0);
		final int minDegree = argsModel.getMinDegree();
		System.out.println("Using minimum degree: " + minDegree);

		Map<Integer, Integer> renumber = readRenumberFile(argsModel.getRenumberFile());

		try {
			List<Pair<Integer, Integer>> edges = new ArrayList<>();
			int maxVertex = -1;
			System.out.println("Starting graph loading: " + System.currentTimeMillis() + " ms");
			InputStream fileStream = new FileInputStream(inputFile);

			BufferedReader reader = new BufferedReader(new InputStreamReader(fileStream));
			String line = reader.readLine();
			while (line != null) {
				if (line.startsWith("#")) {
					continue;
				}
				String[] fields = line.split("\\s+");
				int source = Integer.valueOf(fields[0]);
				int target = Integer.valueOf(fields[1]);
				maxVertex = Math.max(maxVertex, source);
				maxVertex = Math.max(maxVertex, target);
				edges.add(Pair.of(source, target));

				line = reader.readLine();
			}
			reader.close();

			SparseIntDirectedGraph graph = new SparseIntDirectedGraph(maxVertex + 1, edges);
			System.out.println("Finished graph loading: " + System.currentTimeMillis() + " ms");

			System.out.println("Graph contains " + graph.vertexSet().size() + " vertices");
			System.out.println("Graph contains " + graph.edgeSet().size() + " edges");

			double avg = 0;
			for (int i = 0; i < argsModel.getRepeat(); i++) {
				avg += singleRun(i, graph, minDegree, renumber);
			}
			avg /= argsModel.getRepeat();
			System.out.println("Average time taken: " + avg + " (ms)");
		} catch (Exception e) {
			System.out.println("Error: " + e);
			e.printStackTrace();
		}

	}

	private static Map<Integer, Integer> readRenumberFile(String renumberFile)
			throws FileNotFoundException, IOException {
		if (renumberFile == null) {
			return Map.of();
		}

		Map<Integer, Integer> renumber = new HashMap<>();

		try (BufferedReader reader = new BufferedReader(new InputStreamReader(new FileInputStream(renumberFile)))) {
			String line = reader.readLine();
			while (line != null) {
				if (line.startsWith("#")) {
					continue;
				}
				String[] fields = line.split("\\s+");
				int source = Integer.valueOf(fields[0]);
				int target = Integer.valueOf(fields[1]);
				renumber.put(target, source);
				line = reader.readLine();
			}
		}
		return renumber;
	}

	private static long singleRun(int run, SparseIntDirectedGraph graph, int minDegree, Map<Integer, Integer> renumber)
			throws InterruptedException {

		System.out.println("Run " + run);
		System.out.println("Starting queries computation: " + System.currentTimeMillis() + " ms");
		long start = System.currentTimeMillis();

		int vertexCount = graph.vertexSet().size();
		List<Integer> minDegreeVertices = new ArrayList<>();
		for (int s = 0; s < vertexCount; s++) {
			if (graph.outDegreeOf(s) < minDegree) {
				continue;
			}
			minDegreeVertices.add(s);
		}
		System.out.println("Found " + minDegreeVertices.size() + " vertices with degree >= " + minDegree);
		
		System.out.println(minDegreeVertices);

		List<Pair<Integer, Integer>> queries = new ArrayList<>();
		for (Integer s : minDegreeVertices) {
			// index neighbors
			Set<Integer> other = new HashSet<>();
			for (Integer e : graph.outgoingEdgesOf(s)) {
				other.add(Graphs.getOppositeVertex(graph, e, s));
			}

			// test all possible neighbors
			for (Integer t : minDegreeVertices) {
				if (s.equals(t) || other.contains(t)) {
					continue;
				}
				queries.add(Pair.of(s, t));
			}
		}
		System.out.println("Computed " + queries.size() + " queries");
		System.out.println("Finished queries computation: " + System.currentTimeMillis() + " ms");

		int cores = Runtime.getRuntime().availableProcessors();
		System.out.println("Spliting into " + cores + " cores");
		List<List<Pair<Integer, Integer>>> queriesPartitions = Lists.partition(queries, queries.size() / cores);

		final int topK = 10;
		Map<Integer, List<Triple<Integer, Integer, Double>>> responses = new HashMap<>();
		Thread[] threads = new Thread[cores];
		for (int i = 0; i < cores; i++) {
			System.out.println("Starting thread " + i);
			threads[i] = new Thread(new SingleTask(graph, i, topK, queriesPartitions.get(i), responses));
			threads[i].start();
		}

		for (int i = 0; i < cores; i++) {
			threads[i].join();
		}

		List<Triple<Integer, Integer, Double>> finalResults = new ArrayList<>();
		for (int i = 0; i < cores; i++) {
			finalResults.addAll(responses.get(i));
		}
		finalResults.sort(Comparator.comparing((Triple<Integer, Integer, Double> t) -> t.getThird()).reversed());
		finalResults = finalResults.subList(0, topK);

		if (renumber.size() > 0) {
			finalResults = finalResults.stream()
					.map(t -> Triple.of(renumber.get(t.getFirst()), renumber.get(t.getSecond()), t.getThird()))
					.collect(Collectors.toList());
		}

		System.out.println("Joined all results: " + System.currentTimeMillis() + " ms");
		System.out.println(finalResults);

		long end = System.currentTimeMillis();
		return end - start;
	}

	private static class SingleTask implements Runnable {

		private SparseIntDirectedGraph graph;
		private int index;
		private int topK;
		private List<Pair<Integer, Integer>> queries;
		private Map<Integer, List<Triple<Integer, Integer, Double>>> responses;

		public SingleTask(SparseIntDirectedGraph graph, int index, int topK, List<Pair<Integer, Integer>> queries,
				Map<Integer, List<Triple<Integer, Integer, Double>>> responses) {
			this.graph = graph;
			this.index = index;
			this.topK = topK;
			this.queries = queries;
			this.responses = responses;
		}

		@Override
		public void run() {
			System.out.println("Thread " + index + " start: " + System.currentTimeMillis() + " ms");
			AdamicAdarIndexLinkPrediction<Integer, Integer> alg = new AdamicAdarIndexLinkPrediction<>(graph);
			List<Triple<Integer, Integer, Double>> result = new ArrayList<>();
			for (Pair<Integer, Integer> q : queries) {
				try {
					double score = alg.predict(q.getFirst(), q.getSecond());
					if (score > 0) {
						result.add(Triple.of(q.getFirst(), q.getSecond(), score));
					}
				} catch (LinkPredictionIndexNotWellDefinedException e) {
					// ignore
				}
			}

			result.sort(Comparator.comparing((Triple<Integer, Integer, Double> t) -> t.getThird()).reversed());
			result = result.subList(0, topK);

			// System.out.println("Thread " + index + " found: " + result);

			responses.put(index, result);
			System.out.println("Thread " + index + " end: " + System.currentTimeMillis() + " ms");
		}

	}
}
