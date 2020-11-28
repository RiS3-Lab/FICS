import hashlib
import subprocess
from collections import Counter, defaultdict
# from node2vec import Node2Vec
from operator import itemgetter
from subprocess import call
from timeit import default_timer

import networkx as nx
import numpy as np
from gensim.models import Word2Vec

from learning.node2vec import node2vec
from slicer import Slicer
from utils.inout import *


class BitCodeFile:

    def __init__(self, file_info, arguments, analysis_type='', feature_type=''):
        self.file_info = file_info
        self.arguments = arguments
        self.analysis_type = analysis_type
        self.feature_type = feature_type

        self.features = []
        self.afs_features_counters_list = defaultdict(list)
        self.afs_features_counters = {}
        self.afs_graph = None
        self.graph_len = 0
        self.basic_block_ids = set()
        self.lines_numbers = set()
        self.llvm_instructions = set()
        self.construct_hash = None

    def analyze(self):
        if self.analysis_type == 'pdg':
            return self.extract_pdg()
        elif self.analysis_type == 'as':
            return self.extract_as()
        else:
            return False

    def extract_pdg(self):
        pdg_dir = join_path(get_parent_dir(self.file_info), 'pdg')
        make_dir_if_not_exist(pdg_dir)
        for function_name in self.get_functions():
            function_pdg_file = join_path(pdg_dir, '{}.pdg.dot'.format(function_name))
            # llvm_pdg_log_file = join_path(pdg_dir, '{}.log.txt'.format(function))
            time_file = join_path(pdg_dir, '{}.pdg.time.txt'.format(function_name))
            # args = ['-entrypoint', function, '-nocfg', '>', function_pdg_file]
            parse_start_time = default_timer()
            try:
                OUTPUT = open(function_pdg_file, 'w')

                # set 60 seconds timeout for pdg extraction
                call(['timeout', '60', self.arguments.pdg_dumper, self.file_info,
                      '-entrypoint', function_name, '-nocfg'],
                     stdout=OUTPUT, stderr=subprocess.STDOUT, close_fds=True)
                OUTPUT.close()

                if not exist_file(function_pdg_file):
                    print 'error in:', function_name, self.file_info
                # output = open(function_pdg_file, 'r')
                # output_lines = output.readlines()
                # for i in range(len(output_lines)):
                #     if 'WARNING' in output_lines[i]:
                #         # digraph "DependenceGraph"
                #         print function_pdg_file

                parse_elapsed = default_timer() - parse_start_time
                write_file(time_file, '{}'.format(parse_elapsed))
            except:
                print 'crash in pdg dumper', self.file_info, function_name
                return False

        return True

    def get_functions(self):
        functions = []
        functions_file = join_path(get_parent_dir(self.file_info), 'functions.txt')
        try:
            for line in read_lines(functions_file):
                # Do not consider inlinehint functions
                if ' inlinehint ' not in line.split(':')[1]:
                    functions.append(line.split('@')[1].split('(')[0])
        except Exception, e:
            print functions_file, e
        return functions

    def extract_as(self):
        slicer = Slicer(pdg_graph_file=self.file_info, arguments=self.arguments)
        if not slicer.error:
            slicer.run()
            del slicer
            return True
        else:
            return False

    def extract_features(self):
        self.extract_potential_features()

    def extract_potential_features(self):
        self.afs_graph = nx.drawing.nx_agraph.read_dot(self.file_info)
        self.graph_len = len(self.afs_graph)
        if self.feature_type == 'NN':
            self.extract_node_names_features()
            self.afs_features_counters = Counter(self.features)
        elif self.feature_type == 'NNMD':
            self.extract_node_names_features()
            self.afs_features_counters = Counter(self.features)
            self.extract_metadata_features()
        elif self.feature_type == 'SM':
            self.extract_semantic_features()

    def extract_node_names_features(self):
        for node in self.afs_graph.nodes:
            label = self.afs_graph.nodes[node]['label']
            if 'line' in self.afs_graph.nodes[node]:
                line = self.afs_graph.nodes[node]['line']
                self.lines_numbers.add(line)
            if 'basic_block_id' in self.afs_graph.nodes[node]:
                bb_id = self.afs_graph.nodes[node]['basic_block_id']
                self.basic_block_ids.add(bb_id)
            self.features.append(label)
            self.llvm_instructions.add(label)

        self.compute_construct_hash()

    def extract_metadata_features(self):
        self.afs_features_counters['metadata_num_edges'] = len(self.afs_graph.edges)
        self.afs_features_counters['metadata_num_nodes'] = len(self.afs_graph.nodes)
        # d = self.centrality_distribution(self.afs_graph)
        # self.afs_features_counters['metadata_entropy_centrality_distribution'] = self.entropy(d)

    def entropy(self, dist):
        """
        Returns the entropy of `dist` in bits (base-2).

        """
        dist = np.asarray(dist)
        ent = np.nansum(dist * np.log2(1 / dist))
        return ent

    def centrality_distribution(self, G):
        """
        Returns a centrality distribution.

        Each normalized centrality is divided by the sum of the normalized
        centralities. Note, this assumes the graph is simple.

        """
        if len(G) == 1:
            print self.file_info
        centrality = nx.degree_centrality(G).values()
        centrality = np.asarray(centrality)
        centrality /= centrality.sum()
        return centrality

    def extract_semantic_features(self):
        # self.build_laplacian_features()
        self.build_node2vec_features_node_representation()
        # self.build_graph2vec_features_node_representation()

    def build_node2vec_features_node_representation(self):
        afs_graph = nx.DiGraph()
        for e in self.afs_graph.edges():
            afs_graph.add_weighted_edges_from([(e[0], e[1], 1)])
        walks = self.get_node2vec_walks(afs_graph)
        if len(walks):
            node2vec_ref = self.learn_embeddings(walks)
        else:
            node2vec_ref = {}

        data = []
        for node in afs_graph.nodes:
            data.append(node2vec_ref.get_vector(node))

        data = np.array(data)
        data = np.average(data, axis=0)

        for index, value in enumerate(data):
            feature_name = 'representation_{}'.format(index)
            self.afs_features_counters[feature_name] = value

    def build_node2vec_features_similar_nodes(self):
        afs_graph = nx.DiGraph()
        for e in self.afs_graph.edges():
            afs_graph.add_weighted_edges_from([(e[0], e[1], 1)])
        walks = self.get_node2vec_walks(afs_graph)
        if len(walks):
            node2vec_ref = self.learn_embeddings(walks)
        else:
            node2vec_ref = {}

        # for index, value in enumerate(node2vec_ref.get_vector(node)):
        for node in afs_graph.nodes:
            similar_nodes = sorted(node2vec_ref.wv.most_similar(node), key=itemgetter(1), reverse=True)
            sn_len = len(similar_nodes)
            for item in similar_nodes[0:min(sn_len, 5)]:

                similar_label = self.afs_graph.node[item[0]]['label']
                node_label = self.afs_graph.node[node]['label']
                # feature_name = '{}_{}'.format(similar_label, node_label)
                feature_name = '{}'.format(similar_label)
                if feature_name not in self.afs_features_counters_list.keys():
                    self.afs_features_counters[feature_name] = 1
                else:
                    self.afs_features_counters[feature_name] += 1

    def build_node2vec_features_single_node(self):
        afs_graph = nx.DiGraph()
        for e in self.afs_graph.edges():
            afs_graph.add_weighted_edges_from([(e[0], e[1], 1)])
        walks = self.get_node2vec_walks(afs_graph)
        if len(walks):
            node2vec_ref = self.learn_embeddings(walks)
        else:
            node2vec_ref = {}

        for node in afs_graph.nodes:
            # print node, self.afs_graph.node[node]['label']
            # print node2vec_ref.get_vector(node)

            for index, value in enumerate(node2vec_ref.get_vector(node)):
                feature_name = '{} ({})'.format(self.afs_graph.node[node]['label'], index)
                if feature_name not in self.afs_features_counters_list.keys():
                    self.afs_features_counters_list[feature_name].append(round(value, 2))
                else:
                    self.afs_features_counters_list[feature_name].append(round(value, 2))
        for key, value in self.afs_features_counters_list.iteritems():
            self.afs_features_counters[key] = round(np.average(value), 2)

    def get_node2vec_walks(self, afs_graph):
        num_walks = 10
        walk_length = 10
        p = 0.25
        q = 0.25
        node2vec_graph = node2vec.Graph(afs_graph, True, p, q)
        node2vec_graph.preprocess_transition_probs()
        walks = node2vec_graph.simulate_walks(num_walks, walk_length)
        return walks

    def learn_embeddings(self, walks):
        '''
        Learn embeddings by optimizing the Skipgram objective using SGD.
        '''
        dimensions = 128
        window_size = 10
        workers = 5
        iteration = 1
        output = '/Users/mansourahmadi/Desktop/aaa.out'
        walks = [map(str, walk) for walk in walks]
        model = Word2Vec(walks, size=dimensions, window=window_size, min_count=0, sg=1, workers=workers, iter=iteration)
        # print model
        return model.wv

    def compute_construct_hash(self):
        construct_string = ''
        # print self.file_info
        construct_string += self.file_info[:self.file_info.find('.c/pdg') + 2]
        # print construct_string
        for id in self.basic_block_ids:
            construct_string += str(id)
        for line in self.lines_numbers:
            construct_string += str(line)
        for llvm_instruction in self.llvm_instructions:
            construct_string += str(llvm_instruction)
        # print construct_string
        # self.construct_hash = int(hashlib.sha1(construct_string).hexdigest(), 16) % (10 ** 8)
        self.construct_hash = hashlib.sha1(construct_string).hexdigest()
