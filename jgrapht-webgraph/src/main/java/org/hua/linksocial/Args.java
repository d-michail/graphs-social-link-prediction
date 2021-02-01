package org.hua.linksocial;

import java.util.ArrayList;
import java.util.List;

import com.beust.jcommander.Parameter;

public class Args {

	@Parameter
	private List<String> parameters = new ArrayList<>();

	@Parameter(names = "-mindegree", description = "Minimum degree")
	private Integer minDegree = 100;

	public List<String> getParameters() {
		return parameters;
	}

	public void setParameters(List<String> parameters) {
		this.parameters = parameters;
	}

	public Integer getMinDegree() {
		return minDegree;
	}

	public void setMinDegree(Integer minDegree) {
		this.minDegree = minDegree;
	}

}