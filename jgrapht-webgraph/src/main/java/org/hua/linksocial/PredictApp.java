package org.hua.linksocial;

import java.io.IOException;
import java.util.HashSet;
import java.util.Set;

import org.jgrapht.Graphs;
import org.jgrapht.alg.linkprediction.AdamicAdarIndexLinkPrediction;
import org.jgrapht.alg.linkprediction.LinkPredictionIndexNotWellDefinedException;
import org.jgrapht.webgraph.ImmutableDirectedBigGraphAdapter;

import it.unimi.dsi.big.webgraph.BVGraph;
import it.unimi.dsi.fastutil.longs.LongLongPair;

public class PredictApp {

	public static void main(String args[]) throws IOException {

		if (args.length != 1) {
			System.out.println("Usage: app input.webgraph");
			System.exit(1);
		}

		String inputFile = args[0];
		BVGraph bvGraph = BVGraph.load(inputFile);

		final int minDegree = 100;

		ImmutableDirectedBigGraphAdapter graph = new ImmutableDirectedBigGraphAdapter(bvGraph);
		System.out.println("Graph has " + graph.iterables().vertexCount() + " number of vertices");
		System.out.println("Graph has " + graph.iterables().edgeCount() + " number of edges");

		AdamicAdarIndexLinkPrediction<Long, LongLongPair> alg = new AdamicAdarIndexLinkPrediction<>(graph);

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

				try {
					double score = alg.predict(s, t);
					if (score > 0) {
						System.out.println("Edge (" + s + ", " + t + ") score = " + score);
					}
				} catch (LinkPredictionIndexNotWellDefinedException e) {
					// ignore
				}
			}
		}
	}

}
