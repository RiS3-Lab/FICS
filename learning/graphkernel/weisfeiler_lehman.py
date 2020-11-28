"""Weisfeiler_Lehman graph kernel.
Python implementation based on: "Weisfeiler-Lehman Graph Kernels", by:
Nino Shervashidze, Pascal Schweitzer, Erik J. van Leeuwen, Kurt
Mehlhorn, Karsten M. Borgwardt, JMLR, 2012.
http://jmlr.csail.mit.edu/papers/v12/shervashidze11a.html
Author : Sandro Vega-Pons, Emanuele Olivetti
"""

import numpy as np
import networkx as nx
import copy

import pandas as pd


class GK_WL():
    """
    Weisfeiler_Lehman graph kernel.
    """

    def compare_list(self, graph_list, h=1, node_label=True):
        """Compute the all-pairs kernel values for a list of graphs.
        This function can be used to directly compute the kernel
        matrix for a list of graphs. The direct computation of the
        kernel matrix is faster than the computation of all individual
        pairwise kernel values.
        Parameters
        ----------
        graph_list: list
            A list of graphs (list of networkx graphs)
        h : interger
            Number of iterations.
        node_label : boolean
            Whether to use original node labels. True for using node labels
            saved in the attribute 'node_label'. False for using the node
            degree of each node as node attribute.
        Return
        ------
        K: numpy.array, shape = (len(graph_list), len(graph_list))
        The similarity matrix of all graphs in graph_list.
        """
        graph_list = self.convert_node_names_to_int(graph_list)
        self.graphs = graph_list
        n = len(graph_list)
        lists = [0] * n
        k = [0] * (h + 1)
        n_nodes = 0
        n_max = 0

        # Compute adjacency lists and n_nodes, the total number of
        # nodes in the dataset.
        for i in range(n):
            self.get_adj_list(graph_list, i, lists)
            n_nodes = n_nodes + graph_list[i].number_of_nodes()

            # Computing the maximum number of nodes in the graphs. It
            # will be used in the computation of vectorial
            # representation.
            if (n_max < graph_list[i].number_of_nodes()):
                n_max = graph_list[i].number_of_nodes()

        phi = np.zeros((n_max, n), dtype=np.uint64)

        # INITIALIZATION: initialize the nodes labels for each graph
        # with their labels or with degrees (for unlabeled graphs)

        labels = [0] * n
        label_lookup = {}
        label_counter = 0

        # label_lookup is an associative array, which will contain the
        # mapping from multiset labels (strings) to short labels
        # (integers)

        if node_label is True:
            for i in range(n):
                l_aux = nx.get_node_attributes(graph_list[i],
                                               'label').values()
                # It is assumed that the graph has an attribute
                # 'label'
                labels[i] = np.zeros(len(l_aux), dtype=np.int32)

                for j in range(len(l_aux)):
                    if not (l_aux[j] in label_lookup):
                        label_lookup[l_aux[j]] = label_counter
                        labels[i][j] = label_counter
                        label_counter += 1
                    else:
                        labels[i][j] = label_lookup[l_aux[j]]
                    # labels are associated to a natural number
                    # starting with 0.
                    phi[labels[i][j], i] += 1
        else:
            for i in range(n):
                labels[i] = np.array(graph_list[i].degree().values())
                for j in range(len(labels[i])):
                    phi[labels[i][j], i] += 1

        # Simplified vectorial representation of graphs (just taking
        # the vectors before the kernel iterations), i.e., it is just
        # the original nodes degree.
        self.vectors = np.copy(phi.transpose())

        k = np.dot(phi.transpose(), phi)

        # MAIN LOOP
        it = 0
        new_labels = copy.deepcopy(labels)

        while it < h:
            # create an empty lookup table
            label_lookup = {}
            label_counter = 0

            phi = np.zeros((n_nodes, n), dtype=np.uint64)
            for i in range(n):
                for v in range(len(lists[i])):
                    # form a multiset label of the node v of the i'th graph
                    # and convert it to a string
                    long_label = np.concatenate((np.array([labels[i][v]]),
                                                 np.sort(labels[i]
                                                         [lists[i][v]])))
                    long_label_string = str(long_label)
                    # if the multiset label has not yet occurred, add it to the
                    # lookup table and assign a number to it
                    if not (long_label_string in label_lookup):
                        label_lookup[long_label_string] = label_counter
                        new_labels[i][v] = label_counter
                        label_counter += 1
                    else:
                        new_labels[i][v] = label_lookup[long_label_string]
                # fill the column for i'th graph in phi
                aux = np.bincount(new_labels[i])
                # phi[new_labels[i], i] += aux[new_labels[i]]
                np.add(phi[new_labels[i], i], aux[new_labels[i]], out=phi[new_labels[i], i], casting="unsafe")

            k += np.dot(phi.transpose(), phi)
            labels = copy.deepcopy(new_labels)
            it = it + 1

        # Compute the normalized version of the kernel
        k_norm = np.zeros(k.shape)
        for i in range(k.shape[0]):
            for j in range(k.shape[1]):
                k_norm[i, j] = k[i, j] / np.sqrt(k[i, i] * k[j, j])

        return k_norm

    def convert_node_names_to_int(self, graph_list):
        graphs = []
        for i in range(len(graph_list)):
            # nodes = list(graph.nodes)
            # mapping = zip(nodes, pd.Series(nodes).astype('category').cat.codes.values)
            graphs.append(nx.convert_node_labels_to_integers(graph_list[i]))
            # print graph_list[i].nodes
        return graphs

    def get_adj_list(self, graph_list, i, lists):
        adj_list = []
        for n, nbrdict in graph_list[i].adjacency():
            adj_list.append(nbrdict.keys())
        print adj_list
        lists[i] = adj_list

    def compare(self, g_1, g_2, h=1, node_label=True):
        """Compute the kernel value (similarity) between two graphs.
        The kernel is normalized to [0,1] by the equation:
        k_norm(g1, g2) = k(g1, g2) / sqrt(k(g1,g1) * k(g2,g2))
        Parameters
        ----------
        g_1 : networkx.Graph
            First graph.
        g_2 : networkx.Graph
            Second graph.
        h : interger
            Number of iterations.
        node_label : boolean
            Whether to use the values under the graph attribute 'node_label'
            as node labels. If False, the degree of the nodes are used as
            labels.
        Returns
        -------
        k : The similarity value between g1 and g2.
        """
        gl = [g_1, g_2]
        return self.compare_list(gl, h, node_label)[0, 1]
