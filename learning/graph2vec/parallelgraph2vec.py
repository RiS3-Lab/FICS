import json
import glob
import hashlib
import logging
from collections import namedtuple

import pandas as pd
import networkx as nx
# from nltk.cluster import cosine_distance
# from sklearn.metrics.pairwise import cosine_similarity, euclidean_distances, cosine_distances
from tqdm import tqdm
from joblib import Parallel, delayed
# from parser import parameter_parser
# import numpy.distutils.system_info as sysinfo
from gensim.models.doc2vec import Doc2Vec, TaggedDocument


class WeisfeilerLehmanMachine:
    """
    Weisfeiler Lehman feature extractor class.
    """

    def __init__(self, graph, features, iterations):
        """
        Initialization method which also executes feature extraction.
        :param graph: The Nx graph object.
        :param features: Feature hash table.
        :param iterations: Number of WL iterations.
        """
        self.iterations = iterations
        self.graph = graph
        self.features = features
        self.nodes = self.graph.nodes()
        self.extracted_features = [str(v) for k, v in features.items()]
        self.do_recursions()

    def do_a_recursion(self):
        """
        The method does a single WL recursion.
        :return new_features: The hash table with extracted WL features.
        """
        new_features = {}
        for node in self.nodes:
            nebs = self.graph.neighbors(node)
            degs = [self.features[neb] for neb in nebs]
            features = "_".join([str(self.features[node])] + sorted([str(deg) for deg in degs]))
            hash_object = hashlib.md5(features.encode())
            hashing = hash_object.hexdigest()
            new_features[node] = hashing
        self.extracted_features = self.extracted_features + list(new_features.values())
        return new_features

    def do_recursions(self):
        """
        The method does a series of WL recursions.
        """
        for iteration in range(self.iterations):
            self.features = self.do_a_recursion()


def feature_extractor(path, rounds):
    """
    Function to extract WL features from a graph.
    :param path: The path to the graph json.
    :param rounds: Number of WL iterations.
    :return doc: Document collection object.
    """
    graph, features, name, graph_len, graph_hash = dataset_reader(path)
    machine = WeisfeilerLehmanMachine(graph, features, rounds)
    doc = TaggedDocument(words=machine.extracted_features, tags=[name, str(graph_len), graph_hash])
    return doc


def dataset_reader(path):
    """
    Function to read the graph and features from a json file.
    :param path: The path to the graph json.
    :return graph: The graph object.
    :return features: Features hash table.
    :return name: Name of the graph.
    """
    # name = path.strip(".json").split("/")[-1]
    # data = json.load(open(path))
    # graph = nx.from_edgelist(data["edges"])
    name = path
    graph = nx.drawing.nx_agraph.read_dot(path)
    graph_len = 0
    graph_hash = extract_node_names_features(graph, name)
    features = {}
    for node in graph.nodes:
        features[node] = graph.nodes[node]['label']
        graph_len += 1

    # if "features" in data.keys():
    #     features = data["features"]
    # else:
    #     features = nx.degree(graph)
    #
    # features = {int(k): v for k, v, in features.items()}
    return graph, features, name, graph_len, graph_hash


def extract_node_names_features(graph, name):
    lines_numbers = set()
    basic_block_ids = set()
    llvm_instructions = set()
    for node in graph.nodes:
        label = graph.nodes[node]['label']
        if 'line' in graph.nodes[node]:
            line = graph.nodes[node]['line']
            lines_numbers.add(line)
        if 'basic_block_id' in graph.nodes[node]:
            bb_id = graph.nodes[node]['basic_block_id']
            basic_block_ids.add(bb_id)
        llvm_instructions.add(label)

    return compute_construct_hash(name, lines_numbers, basic_block_ids, llvm_instructions)


def compute_construct_hash(name, lines_numbers, basic_block_ids, llvm_instructions):
    construct_string = ''
    # print self.file_info
    construct_string += name[:name.find('.c/pdg') + 2]
    # print construct_string
    for id in basic_block_ids:
        construct_string += str(id)
    for line in lines_numbers:
        construct_string += str(line)
    for llvm_instruction in llvm_instructions:
        construct_string += str(llvm_instruction)
    # print construct_string
    # self.construct_hash = int(hashlib.sha1(construct_string).hexdigest(), 16) % (10 ** 8)
    return hashlib.sha1(construct_string).hexdigest()


def save_embedding(output_path, model, files, dimensions):
    """
    Function to save the embedding.
    :param output_path: Path to the embedding csv.
    :param model: The embedding model object.
    :param files: The list of files.
    :param dimensions: The embedding dimension parameter.
    """
    out = []
    for f in files:
        identifier = f.split("/")[-1].strip(".json")
        out.append([int(identifier)] + list(model.docvecs["g_" + identifier]))

    out = pd.DataFrame(out, columns=["type"] + ["x_" + str(dimension) for dimension in range(dimensions)])
    out = out.sort_values(["type"])
    out.to_csv(output_path, index=None)


class Graph2Vec:

    def __init__(self, project_dir, files_paths, arguments=None):
        self.graph_files = files_paths
        self.project_dir = project_dir
        self.arguments = arguments
        self.graphs = None
        self.node_label_attr_name = 'label'

        self.wlk_h = 2
        self.wl_iterations = 5
        if self.arguments:
            self.workers = self.arguments.count_cpu
        else:
            self.workers = 4
        self.learning_rate = 0.1
        self.embedding_size = 1024  # 512
        self.num_negative_samples = 6
        self.epochs = 100  # 1000
        self.batch_size = 10
        self.final_embeddings = None
        self.corpus = None
        self.min_count = 0
        self.down_sampling = 0.0001

    def run(self):
        # print("\nFeature extraction started ...\n")
        document_collections = \
            Parallel(n_jobs=self.workers)(
                delayed(feature_extractor)(g, self.wl_iterations) for g in self.graph_files)
        # print("\nOptimization started.\n")
        unique_hashes = set()
        docs = []
        # analyzedDocument = namedtuple('AnalyzedDocument', 'words tags')
        for index, text in enumerate(document_collections):
            tags = text[1]
            graph_file = tags[0]
            graph_len = int(tags[1])
            graph_hash = tags[2]
            if graph_len > 2 and graph_hash not in unique_hashes:
                docs.append(text)
                unique_hashes.add(graph_hash)
            else:
                self.graph_files.remove(graph_file)

        document_collections = docs
        model = Doc2Vec(document_collections,
                        vector_size=self.embedding_size,
                        window=0,
                        min_count=self.min_count,
                        dm=0,
                        sample=self.down_sampling,
                        workers=self.workers,
                        epochs=self.epochs,
                        alpha=self.learning_rate)
        out = []
        for f in self.graph_files:
            out.append(list(model.docvecs[f]))
        self.final_embeddings = out
