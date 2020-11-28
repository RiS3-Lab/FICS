from collections import defaultdict
from difflib import SequenceMatcher
from multiprocessing import Pool
from timeit import default_timer

import graphviz as gz
import networkx as nx
import numpy as np
from pymongo import MongoClient
from tqdm import tqdm

from act import Act
from learning.clustering import Clustering
from utils.inout import *


def process_cluster(clusters_samples, key, args, second_clustering_alg, project_dir, second_dataset_locations,
                    second_dataset_features, feature_type, node_features, node_features_locations):
    # Do not perform 2nd step clustering if the size of cluster is greater than 200 item
    # Based on the experiments, inconsistencies appear in clusters with smaller sizes
    cluster_items_locations = clusters_samples[key]
    node_differences = defaultdict(list)
    result = None
    if int(args.big_clusters_ignore) >= len(cluster_items_locations) > 1:
        # selected_locations = locations[locations_indices]
        # for item in selected_features:
        #     print item
        # print cluster_items_locations
        if args.second_clustering == 'online':
            second_clustering = Clustering(locations=cluster_items_locations,
                                           clustering_alg=second_clustering_alg,
                                           min_samples=1,
                                           from_chuck=args.clustering_feat[1],
                                           arguments=args,
                                           project_dir=project_dir,
                                           feature_type=feature_type,
                                           node_features=node_features,
                                           node_features_locations=node_features_locations)
        else:
            locations_indices = []
            for location in cluster_items_locations:
                locations_indices.append(second_dataset_locations.index(location))

            selected_features = second_dataset_features.ix[locations_indices]
            selected_features = selected_features.loc[:,
                                (selected_features != 0).any(axis=0)]
            second_clustering = Clustering(features_set=selected_features,
                                           locations=cluster_items_locations,
                                           clustering_alg=second_clustering_alg,
                                           min_samples=1,
                                           arguments=args,
                                           project_dir=project_dir,
                                           feature_type=feature_type,
                                           node_features=node_features,
                                           node_features_locations=node_features_locations)

        if second_clustering.cluster():
            second_clustering.get_clusters()
            result = dict(second_clustering.clusters_samples)
            node_differences = second_clustering.node_differences

        if len(node_differences) != len(result):
            print 'Node difference unsuccessful'
            exit(1)
        # print 'Cluster#', key, 'having', \
        #    len(cluster_items_locations), 'items, Done!'
    if result is None:
        return {'key': key, 'result': result, 'node_differences': None}
    else:
        return {'key': key, 'result': result, 'node_differences': node_differences}


def my_callback(result):
    # if not code:
    #     Cluster.erroneous_samples += 1
    if result['result'] is not None:
        Cluster.nested_clusters[result['key']] = result['result']
        Cluster.nested_clusters_node_differences[result['key']] = result['node_differences']
    Cluster.pbar.update()


class Cluster(Act):
    clusters_dot_dir = ''
    pbar = None
    nested_clusters = defaultdict(dict)
    nested_clusters_node_differences = defaultdict(dict)
    prefix = ''

    def start(self):
        firststep_features = self.arguments.clustering_feat[0].split('_')
        secondstep_features = self.arguments.clustering_feat[1].split('_')

        if firststep_features[0] != secondstep_features[0]:
            show_error('First step and second step chunks are different')

        if self.arguments.has_control_flow:
            self.prefix = '_CDD_'
        else:
            self.prefix = '_ODD_'

        first_clustering_features = '{}_{}.csv'.format(firststep_features[0], firststep_features[1])
        second_clustering_features = '{}_{}.csv'.format(secondstep_features[0], secondstep_features[1])

        second_dataset_locations = None
        second_dataset_features = None

        for project_name in self.arguments.projects:
            project_dir = join_path(self.arguments.data_dir, self.arguments.bcs_dir, project_name)
            datasets_dir = join_path(self.arguments.data_dir, self.arguments.datasets_dir, project_name)
            datasets = get_files_in_dir(datasets_dir, ext=first_clustering_features, start=self.prefix)
            for dataset in datasets:
                if get_basename(get_parent_dir(dataset)) == project_name or len(self.arguments.projects) == 0:
                    print dataset
                    parent_module_name = get_basename(dataset).split('_')[2]
                    first_clustering_alg = self.arguments.clustering_algs[0]
                    second_clustering_alg = self.arguments.clustering_algs[1]

                    first_clustering_params = first_clustering_alg.split('_')
                    second_clustering_params = second_clustering_alg.split('_')
                    node_difference_dataset = dataset[:dataset.rindex('_') + 1] + 'NN.csv'

                    # print 'Start first step clustering ...'
                    print 'Loading first dataset features ...'
                    start_time = default_timer()
                    partitioned_features, partitioned_locations = self.get_partitioned_dataset(dataset, project_name,
                                                                                               parent_module_name,
                                                                                               firststep_features[1])
                    elapsed_time = default_timer() - start_time
                    print 'Spent Time: {}'.format(elapsed_time)

                    if self.arguments.second_clustering == 'offline':
                        print 'Loading second dataset features ...'
                        start_time = default_timer()
                        second_dataset = join_path(get_parent_dir(dataset), '{}{}_{}'.format(self.prefix,
                                                                                             parent_module_name,
                                                                                             second_clustering_features))
                        second_dataset_features, second_dataset_locations = Clustering.split_dataset(second_dataset,
                                                                                                     secondstep_features[
                                                                                                         1])
                        elapsed_time = default_timer() - start_time
                        print 'Spent Time: {}'.format(elapsed_time)
                    for module_name, value in partitioned_locations.iteritems():
                        Cluster.nested_clusters = defaultdict(dict)
                        print '-' * 100
                        print 'Module:', module_name
                        print '-' * 100
                        print 'Loading Node features ...'
                        if firststep_features[1] == 'NN':
                            node_features = partitioned_features[module_name]
                            node_features_locations = partitioned_locations[module_name]
                            node_features_locations = self.convert_list_to_dict(node_features_locations)
                        else:
                            node_diff_partitioned_features, node_diff_partitioned_locations = \
                                self.get_partitioned_dataset(node_difference_dataset, project_name,
                                                             parent_module_name,
                                                             'NN')
                            node_features = node_diff_partitioned_features
                            node_features_locations = node_diff_partitioned_locations
                            node_features_locations = self.convert_list_to_dict(node_features_locations)
                        print 'Start first step clustering ...'
                        first_clustering = Clustering(dataset=dataset, features_set=partitioned_features[module_name],
                                                      locations=value, clustering_alg=first_clustering_alg,
                                                      module_name=module_name, arguments=self.arguments,
                                                      project_dir=project_dir, feature_type=firststep_features[1])

                        start_time = default_timer()
                        if first_clustering.cluster():
                            print 'Getting Clusters ...'
                            first_clustering.get_clusters()
                            print 'Saving Clusters ...'
                            first_clustering.save_clusters('1st_step')
                            elapsed_time = default_timer() - start_time
                            print 'Spent Time: {}'.format(elapsed_time)
                            time_file = join_path(datasets_dir, first_clustering_params[0],
                                                  '{}.{}.{}.1st-clustering.time.txt'.format(
                                                      firststep_features[0], first_clustering_params[1],
                                                      module_name))
                            write_file(time_file, '{}'.format(elapsed_time))
                            clusters_samples_len_sorted_keys = first_clustering.clusters_samples_len_sorted_keys
                            clusters_samples = first_clustering.clusters_samples
                            del first_clustering
                            print 'Start second step clustering ...'
                            start_time = default_timer()
                            Cluster.pbar = tqdm(total=len(clusters_samples_len_sorted_keys))
                            # processes = self.arguments.count_cpu
                            # p = Pool(processes=1)

                            for key in clusters_samples_len_sorted_keys:
                                result = process_cluster(clusters_samples, key, self.arguments,
                                                         second_clustering_alg, project_dir,
                                                         second_dataset_locations, second_dataset_features,
                                                         secondstep_features[1], node_features, node_features_locations)
                                my_callback(result)
                            # for key in clusters_samples_len_sorted_keys:
                            #     p.apply_async(process_cluster, (clusters_samples, key, self.arguments,
                            #                                     second_clustering_alg, project_dir,
                            #                                     second_dataset_locations, second_dataset_features,
                            #                                     Cluster.nested_clusters),
                            #                   callback=my_callback)
                            #
                            # p.close()
                            # p.join()
                            Cluster.pbar.close()

                            elapsed_time = default_timer() - start_time
                            print 'Spent Time: {}'.format(elapsed_time)
                            time_file = join_path(datasets_dir, first_clustering_params[0],
                                                  '{}.{}.{}.2nd-clustering.time.txt'.format(
                                                      firststep_features[0], first_clustering_params[1],
                                                      module_name))
                            write_file(time_file, '{}'.format(elapsed_time))

                        print 'Saving Clusters ...'
                        start_time = default_timer()
                        sorted_keys_no_child_clusters = defaultdict(list)
                        for parent_cluster_key, child_clusters in Cluster.nested_clusters.iteritems():
                            for key, value in child_clusters.iteritems():
                                sorted_keys_no_child_clusters[parent_cluster_key].append(len(value))
                        # print sorted_keys_no_child_clusters
                        print 'Ranking Clusters ...'
                        keys_scores = self.find_ranking_scores_majority(Cluster.nested_clusters, firststep_features[0])
                        sorted_keys = sorted(keys_scores,
                                             key=lambda k: (
                                                 keys_scores[k]
                                             ), reverse=True)
                        print 'Finding Node differences ...'
                        differences = self.find_differences()
                        # differences = self.find_differences(node_features, node_features_locations)
                        # if firststep_features[1] == 'NN':
                        #     differences = self.find_differences(Cluster.nested_clusters,
                        #                                         partitioned_features[module_name],
                        #                                         partitioned_locations[module_name])
                        # else:
                        #     differences = self.find_differences(Cluster.nested_clusters,
                        #                                         node_diff_partitioned_features[module_name],
                        #                                         node_diff_partitioned_locations[module_name])

                        # dataset = join_path(get_parent_dir(dataset), 'SM.afs.csv')
                        dataset = join_path(get_parent_dir(dataset), second_clustering_features)
                        # self.save_clusters(dataset, Cluster.nested_clusters, sorted_keys,
                        #                    first_clustering_alg=first_clustering_alg,
                        #                    second_clustering_alg=second_clustering_alg,
                        #                    clustering_feat=self.arguments.clustering_feat,
                        #                    module_name=module_name,
                        #                    differences=differences)
                        print 'Saving inconsistencies ...'
                        self.save_clusters_db(dataset, Cluster.nested_clusters, sorted_keys,
                                              first_clustering_alg=first_clustering_alg,
                                              second_clustering_alg=second_clustering_alg,
                                              clustering_feat=self.arguments.clustering_feat,
                                              module_name=module_name,
                                              differences=differences)

                        elapsed_time = default_timer() - start_time
                        print 'Post-Clustering Spent Time: {}'.format(elapsed_time)
                        time_file = join_path(datasets_dir, first_clustering_params[0],
                                              '{}.{}.{}.post-clustering.time.txt'.format(
                                                  firststep_features[0], first_clustering_params[1],
                                                  module_name))
                        write_file(time_file, '{}'.format(elapsed_time))

    def convert_list_to_dict(self, node_features_locations):
        node_features_locations_dict = {}
        for index, item in enumerate(node_features_locations):
            node_features_locations_dict[item] = index
        node_features_locations = node_features_locations_dict
        return node_features_locations

    def get_partitioned_dataset(self, first_dataset, project_name, parent_module_name, firststep_feature):
        features, locations = Clustering.split_dataset(first_dataset, firststep_feature)
        return {parent_module_name: features}, {parent_module_name: locations}
        # if self.arguments.split != 'True':
        #    return {'whole': features}, {'whole': locations}
        # partitioned_features = {}
        # partitioned_locations = defaultdict(list)
        # partitioned_locations_indices = defaultdict(list)
        # project_bcs_dir = join_path(self.arguments.data_dir, self.arguments.bcs_dir, project_name)
        # for i in range(len(locations)):
        #     location = locations[i]
        #     module = location[len(project_bcs_dir) + 1:].split('/')[0]
        #     if module.endswith('.c'):
        #         module = 'root'
        #     partitioned_locations[module].append(location)
        #     partitioned_locations_indices[module].append(i)
        #
        # for key, indices in partitioned_locations_indices.iteritems():
        #     selected_features = features.ix[indices]
        #     selected_features = selected_features.loc[:, (selected_features != 0).any(axis=0)]
        #     partitioned_features[key] = selected_features
        # return partitioned_features, partitioned_locations

    def find_differences(self):
        features_differences = {}

        for parent_cluster_key, item in Cluster.nested_clusters_node_differences.iteritems():
            node_differences = []
            for inconsistency_id, cluster_constructs in item.iteritems():
                for construct in cluster_constructs:
                    node_differences.append(construct)

            inconsistency_node_differences = pd.DataFrame(node_differences)
            inconsistency_node_differences.fillna(0, inplace=True)
            nunique = inconsistency_node_differences.apply(pd.Series.nunique)
            cols_to_drop = nunique[nunique == 1].index
            features_difference = inconsistency_node_differences.drop(cols_to_drop, axis=1)
            features_differences[parent_cluster_key] = features_difference

        print 'Found features differences'
        return features_differences

    def find_differences_old(self, features, locations):
        features_differences = {}

        selected_indices = []
        for parent_cluster_key, child_clusters in Cluster.nested_clusters.iteritems():
            for key, value in child_clusters.iteritems():
                for location in value:
                    location_index = locations[location]
                    if location_index >= 0:
                        selected_indices.append(location_index)

        features = features.loc[selected_indices]
        for parent_cluster_key, child_clusters in Cluster.nested_clusters.iteritems():
            indices = []
            for key, value in child_clusters.iteritems():
                for location in value:
                    location_index = locations[location]
                    if location_index >= 0:
                        indices.append(location_index)

            features_difference = features.loc[indices]
            nunique = features_difference.apply(pd.Series.nunique)
            cols_to_drop = nunique[nunique == 1].index
            features_difference = features_difference.drop(cols_to_drop, axis=1)
            features_differences[parent_cluster_key] = features_difference

        print 'Found features differences'
        return features_differences

    def find_ranking_scores_majority(self, nested_clusters, chunk_type):
        scores = {}
        sorted_keys_no_child_clusters = defaultdict(list)
        for parent_cluster_key, child_clusters in nested_clusters.iteritems():
            for key, value in child_clusters.iteritems():
                sorted_keys_no_child_clusters[parent_cluster_key].append(len(value))

        for key, value in sorted_keys_no_child_clusters.iteritems():
            metric = (np.max(value) - np.min(value))
            scores[key] = metric

        return scores

    def find_ranking_scores(self, nested_clusters, chunk_type):
        scores = defaultdict(list)
        sorted_keys_no_child_clusters = defaultdict(list)
        for parent_cluster_key, child_clusters in nested_clusters.iteritems():
            variables = []
            basic_blocks = []
            file_names = []
            function_names = []
            for key, value in child_clusters.iteritems():
                sorted_keys_no_child_clusters[parent_cluster_key].append(len(value))
                for item in value:
                    base_name_splits = get_basename(item).split('.pdg_')
                    function_names.append(base_name_splits[0])
                    file_names.append(get_parent_dir(get_parent_dir(item)))
                    variable_parts = base_name_splits[-1].split('.{}.dot'.format(chunk_type))[0][4:].split('_0x')
                    variables.append(variable_parts[0])
                    # print variable_parts
                    if len(variable_parts) > 1:
                        basic_blocks.append(variable_parts[1:])
                    # print basic_blocks

            if len(basic_blocks) > 0:
                metric0 = []
                for i in range(len(basic_blocks)):
                    for j in range(i + 1, len(basic_blocks)):
                        if basic_blocks[i] == basic_blocks[j]:
                            metric0.append(0)
                        else:
                            metric0.append(1)
                scores[parent_cluster_key].append(np.average(metric0))

            metric1 = []
            for i in range(len(variables)):
                for j in range(i + 1, len(variables)):
                    metric1.append(SequenceMatcher(None, variables[i], variables[j]).ratio())
            scores[parent_cluster_key].append(np.average(metric1))

            metric2 = []
            for i in range(len(function_names)):
                for j in range(i + 1, len(function_names)):
                    if function_names[i] == function_names[j]:
                        metric2.append(0)
                    else:
                        metric2.append(1)
            scores[parent_cluster_key].append(np.average(metric2))

            metric3 = []
            for i in range(len(file_names)):
                for j in range(i + 1, len(file_names)):
                    if file_names[i] == file_names[j]:
                        metric3.append(0)
                    else:
                        metric3.append(1)
            scores[parent_cluster_key].append(np.average(metric3))

        max_len_subclusters = 0
        for key, value in sorted_keys_no_child_clusters.iteritems():
            if len(value) > max_len_subclusters:
                max_len_subclusters = len(value)
        for key, value in sorted_keys_no_child_clusters.iteritems():
            metric4 = (np.max(value) - np.min(value)) * 1.0 / np.sum(value)
            metric5 = 1 - (len(value)) * 1.0 / max_len_subclusters
            scores[key].append(metric4)
            scores[key].append(metric5)

        keys_scores = {}
        for key, value in scores.iteritems():
            keys_scores[key] = 1 - np.average(value)

        return keys_scores

    def save_clusters(self, dataset, nested_clusters, sorted_keys, first_clustering_alg='', second_clustering_alg='',
                      step='2nd_step',
                      clustering_feat='', module_name='whole', differences=None):

        first_clustering_params = first_clustering_alg.split('_')
        second_clustering_params = second_clustering_alg.split('_')
        clusters_file_no_ext = '{}_{}.{}_{}.{}.{}.clusters'.format(step, clustering_feat[0], first_clustering_params[1],
                                                                   clustering_feat[1], second_clustering_params[1],
                                                                   module_name)
        clusters_file_no_ext = join_path(get_parent_dir(dataset), clusters_file_no_ext)
        clusters_file = '{}.txt'.format(clusters_file_no_ext)
        cluster_file_path = join_path(get_parent_dir(clusters_file), second_clustering_params[0])
        make_dir_if_not_exist(cluster_file_path)
        # comment: Ignore making directory for dot files of clusters' slices. We don't need them currently
        # self.clusters_dot_dir = join_path(cluster_file_path, get_basename(clusters_file_no_ext))
        # remove_directory(self.clusters_dot_dir)
        # make_dir_if_not_exist(self.clusters_dot_dir)
        clusters_file = join_path(cluster_file_path, get_basename(clusters_file))

        content = '\n'
        counter = 0
        for key in sorted_keys:
            dic_value = nested_clusters[key]
            if len(dic_value) == 1:
                continue
            if key == -1:
                continue
            counter += 1
            content = '{} Cluster #{} :\n'.format(content, key)
            content = '{} {}\n'.format(content, '-' * 50)
            for sub_cluster_key, sub_cluster_value in dic_value.iteritems():
                content = '{} Sub Cluster #{} :\n'.format(content, sub_cluster_key)
                content = '{} {}\n'.format(content, '-' * 50)
                content = '{} # Items: {}  \n'.format(content, len(sub_cluster_value))
                for item in sub_cluster_value:
                    # comment: Ignore saving c and dot files of clusters' slices. We don't need them currently
                    # self.manage_dot_file('Cluster {}'.format(key), 'Sub Cluster {}'.format(sub_cluster_key), item)
                    # self.manage_source_file('Cluster {}'.format(key), 'Sub Cluster {}'.format(sub_cluster_key), item)
                    line_numbers = self.get_line_numbers(item)
                    content = '{}  {} {}\n'.format(content, item, line_numbers)
                content = '{} {}\n'.format(content, '-' * 50)

            if differences is not None:
                content = '{} {}\n'.format(content, '+' * 30)
                content = '{} {}\n'.format(content, differences[key])

            content = '{} {}\n'.format(content, '=' * 100)

        print 'Number of Clusters: {}'.format(counter)
        write_file(clusters_file, content)

    def save_clusters_db(self, dataset, nested_clusters, sorted_keys, first_clustering_alg='', second_clustering_alg='',
                         step='2nd_step',
                         clustering_feat='', module_name='whole', differences=None):

        client = MongoClient('mongodb://localhost:27017')
        fics_db = client["fics"]

        first_clustering_params = first_clustering_alg.split('_')
        second_clustering_params = second_clustering_alg.split('_')
        clusters_file_no_ext = '{}_{}.{}_{}.{}.{}.clusters'.format(step, clustering_feat[0], first_clustering_params[1],
                                                                   clustering_feat[1], second_clustering_params[1],
                                                                   module_name)
        clusters_file_no_ext = join_path(get_parent_dir(dataset), clusters_file_no_ext)
        clusters_file = '{}.txt'.format(clusters_file_no_ext)
        # cluster_file_path = join_path(get_parent_dir(clusters_file), second_clustering_params[0])

        project_name = get_basename(get_parent_dir(dataset))
        dataset_path = get_parent_dir(get_parent_dir(get_parent_dir(dataset)))
        project_source_path = join_path(dataset_path,
                                        self.arguments.projects_dir)
        project_bcs_path = join_path(dataset_path,
                                     self.arguments.bcs_dir)

        collection = fics_db[project_name]
        counter = 0
        inconsistencies = []
        for key in sorted_keys:
            dic_value = nested_clusters[key]
            if len(dic_value) == 1:
                continue
            if key == -1:
                continue
            counter += 1

            inconsistency = dict(folder_name=project_name, cluster_number=int(key),
                                 construct_type=clustering_feat[0].split('_')[0],
                                 firststep_algorithm=first_clustering_params[0],
                                 secondstep_algorithm=second_clustering_params[0],
                                 firststep_features=clustering_feat[0].split('_')[1],
                                 firststep_threshold=float(first_clustering_params[1]),
                                 secondstep_features=clustering_feat[1].split('_')[1],
                                 secondstep_threshold=float(second_clustering_params[1]),
                                 module_name=module_name,
                                 dependency=self.prefix)
            subclusters = []
            construct_counter = 0
            for sub_cluster_key, sub_cluster_value in dic_value.iteritems():
                subcluster = dict(sub_cluster_number=int(sub_cluster_key), constructs_total=len(sub_cluster_value))
                constructs = []
                for item in sub_cluster_value:
                    line_numbers = self.get_line_numbers(item, as_list=True)
                    source_path = join_path(project_source_path,
                                            item[len(project_bcs_path) + 1:item.find('.c/pdg') + 2])

                    names = get_basename(item).split('.pdg_')
                    function_name = names[0]
                    function_name = function_name[5:]
                    variable_name = names[1].split('.afs')[0]
                    variable_name_bb = variable_name.split('_0x')
                    variable_name = variable_name_bb[0]
                    bbs = []
                    if len(variable_name_bb) > 1:
                        bbs = '0x' + variable_name_bb[1]
                        bbs = bbs.split('_')

                    construct = dict(
                        graph_path=item, source_file_path=source_path,
                        lines=line_numbers, function_name=function_name, bbs=bbs, variable_name=variable_name)

                    node_diff_lines = self.find_lines(item)

                    node_diffs = []
                    if differences is not None:
                        columns = differences[key].columns
                        differences[key].reset_index(inplace=True, drop=True)
                        for index, row in differences[key].iterrows():
                            # print key, index, row
                            if index == construct_counter:
                                for column_index, column in enumerate(columns):
                                    node_diff = {}
                                    column_value = int(row[column])
                                    column_name = column.replace('.', ';')
                                    node_diff['node_name'] = column_name
                                    node_diff['node_value'] = column_value
                                    node_diff['lines'] = node_diff_lines[column]
                                    # node_diff['node_{}'.format(column_index)] = [column, column_value]
                                    node_diffs.append(node_diff)

                    construct['node_diffs'] = node_diffs
                    construct_counter += 1
                    constructs.append(construct)

                subcluster['constructs'] = constructs
                subclusters.append(subcluster)

            inconsistency['subclusters'] = subclusters
            # print inconsistency
            collection.insert_one(inconsistency)
            # inconsistencies.append(inconsistency)
        # collection.insert_many(inconsistencies)
        print 'Number of Clusters: {}'.format(counter)

    def get_line_numbers(self, dot_file, as_list=False):
        line_numbers = []
        graph = nx.drawing.nx_agraph.read_dot(dot_file)
        for node in graph.nodes:
            if 'line' in graph.nodes[node]:
                line_number = int(graph.nodes[node]['line'])
                if line_number not in line_numbers:
                    line_numbers.append(line_number)
        line_numbers.sort()
        if as_list:
            return line_numbers
        lines = ''
        for line in line_numbers:
            lines += '{}, '.format(line)
        return lines[:-2]

    def get_subcluster_path(self, cluster_name, subcluster_name):
        cluster_path = join_path(self.clusters_dot_dir, cluster_name)
        subcluster_path = join_path(cluster_path, subcluster_name)
        make_dir_if_not_exist(cluster_path)
        make_dir_if_not_exist(subcluster_path)
        return subcluster_path

    def manage_dot_file(self, cluster_name, subcluster_name, dot_file):
        subcluster_path = self.get_subcluster_path(cluster_name, subcluster_name)
        dst_dot_file = join_path(subcluster_path, get_basename(dot_file))
        copy_file(dot_file, dst_dot_file)
        # self.render_pdf_graph(dst_dot_file)

    def manage_source_file(self, cluster_name, subcluster_name, dot_file):
        parent_dir_len = len(self.arguments.data_dir) + len(self.arguments.bcs_dir) + 1
        src_file = join_path(self.arguments.data_dir, self.arguments.projects_dir,
                             get_parent_dir(get_parent_dir(dot_file[parent_dir_len:])))

        subcluster_path = self.get_subcluster_path(cluster_name, subcluster_name)
        dst_file = join_path(subcluster_path, get_basename(dot_file) + '.c')
        copy_file(src_file, dst_file)

    def render_pdf_graph(self, graph_file):
        # pass
        # Visualize dot graph
        dot = gz.Source.from_file(graph_file)
        dot.render(view=False)

    def find_lines(self, item):
        # print item
        label_lines = defaultdict(list)
        graph = nx.drawing.nx_agraph.read_dot(item)
        for node in graph.nodes:
            label = graph.nodes[node]['label']
            if 'line' in graph.nodes[node]:
                label_lines[label].append(graph.nodes[node]['line'])
        # print label_lines
        return label_lines
