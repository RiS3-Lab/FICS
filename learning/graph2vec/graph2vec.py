import ast
import os
from copy import deepcopy
from time import time

import networkx as nx
import tensorflow as tf
import logging

from learning.graph2vec.train_utils import train_skipgram


def get_int_node_label(x):
    return int(x.split('+')[-1])


class Graph2Vec:

    def __init__(self, project_dir, files_paths, arguments):
        # os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
        # os.environ['TF_CPP_MIN_VLOG_LEVEL'] = '3'
        # tf.logging.set_verbosity(tf.logging.INFO)
        # logging.getLogger('tensorflow').disabled = True
        # logging.getLogger('tensorflow').propagate = False

        # tf.compat.v1.logging.set_verbosity(tf.compat.v1.logging.ERROR)

        self.fnames = files_paths
        self.project_dir = project_dir
        self.graphs = None
        self.node_label_attr_name = 'label'
        self.label_to_compressed_label_map = {}
        self.wlk_h = 2
        self.learning_rate = 0.1
        self.embedding_size = 512  # 512
        self.num_negative_samples = 6
        self.epochs = 500  # 1000
        self.batch_size = 128
        self.wl_extn = 'g2v' + str(self.wlk_h)
        self.final_embeddings = None
        self.corpus = None
        self.arguments = arguments

    def run(self):
        t0 = time()
        self.wlk_relabel_and_dump_memory_version(self.fnames, max_h=self.wlk_h)
        print 'dumped sg2vec sentences in {} sec.'.format(time() - t0)
        t0 = time()

        self.corpus, self.final_embeddings = train_skipgram(self.fnames, self.wl_extn, self.learning_rate,
                                                            self.embedding_size,
                                                            self.num_negative_samples, self.epochs, self.batch_size,
                                                            arguments=self.arguments)
        print 'Trained the skipgram model in {} sec.'.format(round(time() - t0, 2))

    def load_graphs(self):
        self.graphs = [nx.drawing.nx_agraph.read_dot(file_path) for file_path in self.fnames]

    def wlk_relabel_and_dump_memory_version(self, fnames, max_h):

        t0 = time()
        self.load_graphs()
        print 'loaded all graphs in {} sec'.format(round(time() - t0, 2))

        t0 = time()
        self.graphs = [self.initial_relabel(g) for g in self.graphs]
        print 'initial relabeling done in {} sec'.format(round(time() - t0, 2))

        for it in xrange(1, max_h + 1):
            t0 = time()
            self.label_to_compressed_label_map = {}
            self.graphs = [self.wl_relabel(g, it) for g in self.graphs]
            print 'WL iteration {} done in {} sec.'.format(it, round(time() - t0, 2))
            print 'num of WL rooted subgraphs in iter {} is {}'.format(it, len(self.label_to_compressed_label_map))

        t0 = time()
        for fname, g in zip(fnames, self.graphs):
            self.dump_sg2vec_str(fname, max_h, g)
        print 'dumped sg2vec sentences in {} sec.'.format(round(time() - t0, 2))

    def dump_sg2vec_str(self, fname, max_h, g=None):
        if not g:
            g = nx.read_gexf(fname + '.tmpg')
            new_g = deepcopy(g)
            for n in g.nodes():
                del new_g.nodes[n]['relabel']
                new_g.nodes[n]['relabel'] = ast.literal_eval(g.nodes[n]['relabel'])
            g = new_g

        opfname = fname + '.' + self.wl_extn

        # if os.path.isfile(opfname):
        #     return

        with open(opfname, 'w') as fh:
            for n, d in g.nodes(data=True):
                for i in xrange(0, max_h + 1):
                    try:
                        center = d['relabel'][i]
                    except:
                        continue
                    neis_labels_prev_deg = []
                    neis_labels_next_deg = []

                    if i != 0:
                        neis_labels_prev_deg = list(
                            set([g.node[nei]['relabel'][i - 1] for nei in nx.all_neighbors(g, n)]))
                        neis_labels_prev_deg.sort()
                    NeisLabelsSameDeg = list(set([g.node[nei]['relabel'][i] for nei in nx.all_neighbors(g, n)]))
                    if i != max_h:
                        neis_labels_next_deg = list(
                            set([g.node[nei]['relabel'][i + 1] for nei in nx.all_neighbors(g, n)]))
                        neis_labels_next_deg.sort()

                    nei_list = NeisLabelsSameDeg + neis_labels_prev_deg + neis_labels_next_deg
                    nei_list = ' '.join(nei_list)

                    sentence = center + ' ' + nei_list
                    print>> fh, sentence

        if os.path.isfile(fname + '.tmpg'):
            os.system('rm ' + fname + '.tmpg')

    def wl_relabel(self, g, it):

        try:
            opfname = g + '.tmpg'
            g = nx.drawing.nx_agraph.read_dot(g + '.tmpg')
            new_g = deepcopy(g)
            for n in g.nodes():
                new_g.nodes[n]['relabel'] = ast.literal_eval(g.nodes[n]['relabel'])
            g = new_g
        except:
            opfname = None
            pass

        prev_iter = it - 1
        for node in g.nodes():
            prev_iter_node_label = get_int_node_label(g.nodes[node]['relabel'][prev_iter])
            node_label = [prev_iter_node_label]
            neighbors = list(nx.all_neighbors(g, node))
            neighborhood_label = sorted([get_int_node_label(g.nodes[nei]['relabel'][prev_iter]) for nei in neighbors])
            node_neighborhood_label = tuple(node_label + neighborhood_label)
            if not self.label_to_compressed_label_map.has_key(node_neighborhood_label):
                compressed_label = len(self.label_to_compressed_label_map) + 1
                self.label_to_compressed_label_map[node_neighborhood_label] = compressed_label
                g.node[node]['relabel'][it] = str(it) + '+' + str(compressed_label)
            else:
                g.node[node]['relabel'][it] = str(it) + '+' + str(
                    self.label_to_compressed_label_map[node_neighborhood_label])

        if opfname:
            nx.drawing.nx_agraph.write_dot(g, opfname)
        else:
            return g

    def initial_relabel(self, g):

        try:
            opfname = g + '.tmpg'
            g = nx.drawing.nx_agraph.read_dot(g)
        except:
            opfname = None
            pass

        nx.convert_node_labels_to_integers(g,
                                           first_label=0)  # this needs to be done for the initial interation only
        for node in g.nodes(): g.node[node]['relabel'] = {}

        for node in g.nodes():
            try:
                label = g.node[node][self.node_label_attr_name]
            except:
                # no node label referred in 'node_label_attr_name' is present, hence assigning an invalid compressd label
                g.node[node]['relabel'][0] = '0+0'
                continue

            if not self.label_to_compressed_label_map.has_key(label):
                compressed_label = len(
                    self.label_to_compressed_label_map) + 1  # starts with 1 and incremented every time a new node label is seen
                self.label_to_compressed_label_map[label] = compressed_label  # inster the new label to the label map
                g.node[node]['relabel'][0] = '0+' + str(compressed_label)
            else:
                g.node[node]['relabel'][0] = '0+' + str(self.label_to_compressed_label_map[label])

        if opfname:
            nx.drawing.nx_agraph.write_dot(g, opfname)
        else:
            return g
