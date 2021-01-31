package org.hua.linksocial;

import java.io.FileInputStream;
import java.io.InputStream;
import java.util.zip.GZIPInputStream;

import it.unimi.dsi.big.webgraph.BVGraph;
import it.unimi.dsi.big.webgraph.ScatteredArcsASCIIGraph;

/**
 * Load a graph from a gzip file to a webgraph file.
 * 
 * The input file must be in gzip, it should not contain any comments and each
 * line must be a single edge. Node counts must start with zero and be
 * consecutive integers. Source vertices must appear in increasing order and
 * their numbers. Targets may appear in any order.
 */
public class LoadGraphApp {

	public static void main(String args[]) {

		if (args.length != 2) {
			System.out.println("Usage: app input.gz output.webgraph");
			System.exit(1);
		}

		String inputFile = args[0];
		String outputFile = args[1];

		try {
			InputStream fileStream = new FileInputStream(inputFile);
			InputStream gzipStream = new GZIPInputStream(fileStream);
			//final int shift = 0;
			//ArcListASCIIGraph onceLoadWrapperGraph = ArcListASCIIGraph.loadOnce(gzipStream, shift);
			ScatteredArcsASCIIGraph tmpGraph = new ScatteredArcsASCIIGraph(gzipStream);
			BVGraph.store(tmpGraph, outputFile);
		} catch (Exception e) {
			System.out.println("Error: " + e);
			e.printStackTrace();
		}

	}

}
