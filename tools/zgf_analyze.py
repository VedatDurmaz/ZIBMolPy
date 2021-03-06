#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
What it does
============
	B{This is the eighth step of ZIBgridfree.}

	This tool will

		1. Calculate the initial $S$ matrix (the $\phi$ overlap matrix)

		\[ S_{ij} = \left[ \sum_{n=1}^{N_i} \phi_j(q_n^{(i)}) \cdot \\frac{ \phi_i(q_n^{(i)}) }{ \exp{ (-\\beta} \cdot U_{res}(q_n^{(i)})) } \\right] \cdot \\frac{1}{N_i} 
		= \left[ \sum_{n=1}^{N_i} \phi_j(q_n^{(i)}) \cdot \mathtt{frame\_weight}_i(q_n^{(i)}) \\right] \cdot \\frac{1}{N_i} \]

		2. Symmetrize $S$ using the direct node weights obtained by L{zgf_reweight}
		3. Calculate the corrected node weights
		4. Calculate eigenvalues and eigenvectors of the symmetrized $S$ matrix
		5. Sort the eigenvectors in descending order according to the value of the corresponding eigenvalue
		6. Orthogonalize the eigenvectors and deal with degeneracies
		7. Perform PCCA+ on the orthogonalized eigenvectors in order to obtain $\chi$ matrix and cluster weights
		8. Calculate the eigenvectors $\\xi$ of the $Q_c$ matrix
		9. Calculate $Q_c$ (i.e. the Markov state model) from $\\xi$ and PCCA+ output

	You may continue your analysis by visualizing the clustering with L{zgf_browser}. If you like the clustering, you can extract the frames belonging to the metastable conformations by using L{zgf_extract_conformations} for visualization of cluster representatives. If you don't like the clustering, you can rerun L{zgf_analyze} and try a different number of clusters.

	B{The next step is L{zgf_create_tnodes},} if you wish to calculate transition probabilities in form of the $P_c(\\tau)$ or $P(\\tau)$ matrix.

How it works
============
	At the command line, type::
		$ zgf_analyze [options]

PCCA+
=====
	You will have to specify a number of clusters for PCCA+. An initial guess for this number will be made based on the largest gap between the calculated eigenvalues. Ideally there is only real eigenvalue one, followed by a number of eigenvalues very close to one (together forming the Perron cluster, which gives the number of metastable conformations), followed by a significant gap to mark the end of the Perron cluster. Eigenvectors belonging to eigenvalues that are not in the Perron cluster are irrelevant for PCCA+. The quality of the clustering result can be evaluated by taking a look at the (stochastic) $\chi$ matrix, which for each node gives the membership to the metastable conformations identified during PCCA+. All matrices can also be exported for use in Matlab. The matrices are stored in the analysis/ directory.

Symmetrization error threshold
==============================
	This parameter helps to adjust the weighting of overlap regions between $\phi$ functions.

"""

import os
from os import path
import sys
from ZIBMolPy.utils import register_file_dependency
from ZIBMolPy.phi import get_phi_num, get_phi_denom, get_phi
from ZIBMolPy.pool import Pool
from ZIBMolPy.algorithms import cluster_by_isa, orthogonalize, symmetrize, opt_soft
from ZIBMolPy.ui import userinput, Option, OptionsList
from scipy.io import savemat
import numpy as np
import time

import zgf_cleanup

options_desc = OptionsList([
	Option("e", "error", "choice", "error threshold for symmetrize", choices=("1E-02", "1E-03", "1E-04", "1E-05", "1E-06", "1E-07", "1E-08", "1E-09", "1E-10")),
	Option("m", "export-matlab", "bool", "export matrices as mat-files", default=False),
	Option("c", "auto-cluster", "bool", "choose number of clusters automatically", default=False),
	Option("o", "overwrite-mat", "bool", "overwrite existing matrices", default=False),
	Option("f", "fast-mat", "bool", "fast but less stable matrix calculation", default=False),
	Option("i", "ignore-failed", "bool", "reweight and ignore mdrun-failed nodes", default=False),
	Option("n", "optimize-chi", "bool", "optimize chi matrix", default=False),
	Option("s", "summary", "bool", "print cluster summary", default=False),
	])

sys.modules[__name__].__doc__ += options_desc.epytext() # for epydoc

def is_applicable():
	pool = Pool()
	return( len(pool.where("isa_partition")) > 0 and len(pool.where("isa_partition and 'weight_direct' not in obs")) == 0 )

#===============================================================================
def main():
	options = options_desc.parse_args(sys.argv)[0]

	zgf_cleanup.main()
	
	pool = Pool()
	active_nodes = pool.where("isa_partition")
	if(options.ignore_failed):
			active_nodes = pool.where("isa_partition and not state=='mdrun-failed'")

	assert(len(active_nodes) == len(active_nodes.multilock())) # make sure we lock ALL nodes

	if active_nodes.where("'weight_direct' not in obs"):
		active_nodes.unlock()
		sys.exit("Matrix calculation not possible: Not all of the nodes have been reweighted.")
	
	print "\n### Getting S matrix ..."
	s_matrix = cache_matrix(pool.s_mat_fn, active_nodes, overwrite=options.overwrite_mat, fast=options.fast_mat)
	register_file_dependency(pool.s_mat_fn, pool.filename)

	node_weights = np.array([node.obs.weight_direct for node in active_nodes])
	
	print "\n### Symmetrizing S matrix ..."
	(corr_s_matrix, corr_node_weights) = symmetrize(s_matrix, node_weights, correct_weights=True, error=float(options.error))

	# store intermediate results
	register_file_dependency(pool.s_corr_mat_fn, pool.s_mat_fn)

	np.savez(pool.s_corr_mat_fn, matrix=corr_s_matrix, node_names=[n.name for n in active_nodes])
	
	if options.export_matlab:
		savemat(pool.analysis_dir+"node_weights.mat", {"node_weights":node_weights, "node_weights_corrected":corr_node_weights})
		savemat(pool.analysis_dir+"s_mats.mat", {"s_matrix":s_matrix, "s_matrix_corrected":corr_s_matrix})

	for (n, cw) in zip(active_nodes, corr_node_weights):
		n.obs.weight_corrected = cw
		
	print "\n### Node weights after symmetrization of S matrix:"
	for n in active_nodes:
		print "%s: initial weight: %f, corrected weight: %f, weight change: %f" % (n.name, n.obs.weight_direct, n.obs.weight_corrected, abs(n.obs.weight_direct - n.obs.weight_corrected))
		n.save()

	active_nodes.unlock()

	# calculate and sort eigenvalues in descending order
	(eigvalues, eigvectors) = np.linalg.eig(corr_s_matrix)
	argsorted_eigvalues = np.argsort(-eigvalues)
	eigvalues = eigvalues[argsorted_eigvalues]
	eigvectors = eigvectors[:, argsorted_eigvalues]
	
	gaps = np.abs(eigvalues[1:]-eigvalues[:-1])
	gaps = np.append(gaps, 0.0)
	wgaps = gaps*eigvalues

	print "\n### Sorted eigenvalues of symmetrized S matrix:"
	for (idx, ev, gap, wgap) in zip(range(1, len(eigvalues)+1), eigvalues, gaps, wgaps):
		print "EV%04d: %f, gap to next: %f, EV-weighted gap to next: %f" % (idx, ev, gap, wgap)
	n_clusters = np.argmax(wgaps)+1
	print "\n### Maximum gap %f after top %d eigenvalues." % (np.max(gaps), n_clusters)
	print "### Maximum EV-weighted gap %f after top %d eigenvalues." % (np.max(wgaps), np.argmax(wgaps)+1)
	sys.stdout.flush()
	if not options.auto_cluster:
		n_clusters = userinput("Please enter the number of clusters for PCCA+", "int", "x>0")
	print "### Using %d clusters for PCCA+ ..."%n_clusters

	if options.export_matlab:
		savemat(pool.analysis_dir+"evs.mat", {"evs":eigvectors})
	
	# orthogonalize and normalize eigenvectors 
	eigvectors = orthogonalize(eigvalues, eigvectors, corr_node_weights)

	# perform PCCA+
	# First two return-values "c_f" and "indicator" are not needed
	(chi_matrix, rot_matrix) = cluster_by_isa(eigvectors, n_clusters)[2:]

	if(options.optimize_chi):
		print "\n### Optimizing chi matrix ..."
		
		outliers = 5
		mean_weight = np.mean(corr_node_weights)
		threshold = mean_weight/100*outliers
		print "Light-weight node threshold (%d%% of mean corrected node weight): %.4f."%(outliers, threshold)

		# accumulate nodes for optimization
		edges = np.where(np.max(chi_matrix, axis=1) > 0.9999)[0] # edges of simplex
		heavies = np.where( corr_node_weights > threshold)[0] # heavy-weight nodes
		filtered_eigvectors = eigvectors[ np.union1d(edges, heavies) ]

		# perform the actual optimization
		rot_matrix = opt_soft(filtered_eigvectors, rot_matrix, n_clusters)

		chi_matrix = np.dot(eigvectors[:,:n_clusters], rot_matrix)
		
		# deal with light-weight nodes: shift and scale
		for i in np.where(corr_node_weights <= threshold)[0]:
			if(i in edges):
				print "Column %d belongs to (potentially dangerous) light-weight node, but its node is a simplex edge."%(i+1)
				continue
			print "Column %d is shifted and scaled."%(i+1)
			col_min = np.min( chi_matrix[i,:] )
			chi_matrix[i,:] -= col_min
			chi_matrix[i,:] /= 1-(n_clusters*col_min)
			
	qc_matrix = np.dot( np.dot( np.linalg.inv(rot_matrix), np.diag(eigvalues[range(n_clusters)]) ), rot_matrix ) - np.eye(n_clusters)
	cluster_weights = rot_matrix[0]
	
	print "\n### Matrix numerics check"
	print "-- Q_c matrix row sums --"
	print np.sum(qc_matrix, axis=1)
	print "-- cluster weights: first column of rot_matrix --"
	print cluster_weights
	print "-- cluster weights: numpy.dot(node_weights, chi_matrix) --"
	print np.dot(corr_node_weights, chi_matrix)
	print "-- chi matrix column max values --"
	print np.max(chi_matrix, axis=0)
	print "-- chi matrix row sums --"
	print np.sum(chi_matrix, axis=1)

	# store final results
	np.savez(pool.chi_mat_fn, matrix=chi_matrix, n_clusters=n_clusters, node_names=[n.name for n in active_nodes])
	np.savez(pool.qc_mat_fn,  matrix=qc_matrix,  n_clusters=n_clusters, node_names=[n.name for n in active_nodes], weights=cluster_weights)

	if options.export_matlab:		
		savemat(pool.analysis_dir+"chi_mat.mat", {"chi_matrix":chi_matrix})
		savemat(pool.analysis_dir+"qc_mat.mat", {"qc_matrix":qc_matrix, "weights":cluster_weights})

	register_file_dependency(pool.chi_mat_fn, pool.s_corr_mat_fn)
	register_file_dependency(pool.qc_mat_fn, pool.s_corr_mat_fn)

	for fn in (pool.s_mat_fn, pool.s_corr_mat_fn):
		register_file_dependency(pool.chi_mat_fn, fn)
		register_file_dependency(pool.qc_mat_fn, fn)

	# touch analysis directory (triggering update in zgf_browser)
	atime = mtime = time.time()
	os.utime(pool.analysis_dir, (atime, mtime))

	# show summary
	if(options.summary):
		print "\n### Preparing cluster summary ..."
		chi_threshold = 1E-3
		from pprint import pformat
	
		for i in range(n_clusters):
			involved_nodes = [active_nodes[ni] for ni in np.argwhere(chi_matrix[:,i] > chi_threshold)]
			max_chi_node = active_nodes[ np.argmax(chi_matrix[:,i]) ]
			c_max = []

			for c in  pool.converter:
				coord_range = pool.coord_range(c)
				scale = c.plot_scale
				edges = scale(np.linspace(np.min(coord_range), np.max(coord_range), num=50))
				hist_cluster = np.zeros(edges.size-1)

				for (n, chi) in zip([n for n in active_nodes], chi_matrix[:,i]):
					samples = scale( n.trajectory.getcoord(c) )
					hist_node = np.histogram(samples, bins=edges, weights=n.frameweights, normed=True)[0]
					hist_cluster += n.obs.weight_corrected * hist_node * chi

				c_max.append( scale(np.linspace(np.min(coord_range), np.max(coord_range), num=50))[np.argmax(hist_cluster)] )

			msg = "### Cluster %d (weight=%.4f, #involved nodes=%d, representative='%s'):"%(i+1, cluster_weights[i], len(involved_nodes), max_chi_node.name)
			print "\n"+msg
			print "-- internal coordinates --"
			print "%s"%pformat(["%.2f"%cm for cm in c_max])
			print "-- involved nodes --"
			print "%s"%pformat([n.name for n in involved_nodes])			
			print "-"*len(msg)


#===============================================================================
# "cache" specialized for "calc_matrix" in order to save a proper npz
def cache_matrix(filename, nodes, shift=0, overwrite=False, fast=False):
	if(path.exists(filename) and not overwrite):
		return(np.load(filename)["matrix"])
	t1 = time.time()
	mat = calc_matrix(nodes, shift, fast)
	t2 = time.time()
	print("Matrix calculation took %f seconds.")%(t2-t1)
	for n in nodes:
		register_file_dependency(filename, n.trr_fn)
	np.savez(filename, matrix=mat, node_names=[n.name for n in nodes])
	return(mat)


#===============================================================================
def calc_matrix(nodes, shift=0, cache_denom=False):
	mat = np.zeros( (len(nodes), len(nodes)) )
	for (i, ni) in enumerate(nodes):
		print("Working on: %s"%ni)
		if(cache_denom):
			phi_denom = get_phi_denom(ni.trajectory, nodes)
		frame_weights = ni.frameweights
		if shift > 0:
			frame_weights = frame_weights[:-shift]
		for (j, nj) in enumerate(nodes):
			if(cache_denom):
				mat[i, j] = np.average(get_phi_num(ni.trajectory, nj)[shift:] / phi_denom[shift:], weights=frame_weights)
			else:
				mat[i, j] = np.average(get_phi(ni.trajectory, nj)[shift:], weights=frame_weights)
	return(mat)


#===============================================================================
if(__name__ == "__main__"):
	main()

#EOF

