import heapq
import operator
from collections import defaultdict
from multiprocessing import Pool

import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from tqdm import tqdm

from utils.inout import *

nodes_sizes = []
times = []

def process_sample(afs_file):
    afs_graph = nx.drawing.nx_agraph.read_dot(afs_file)
    return len(afs_graph.nodes)


def my_callback(nodes_len):
    global nodes_sizes
    nodes_sizes.append(nodes_len)
    Statistics.pbar.update()


def process_time(time_file_path):
    time_file = open(time_file_path, 'r')
    return float(time_file.read())


def time_callback(time):
    global times
    times.append(time)
    Statistics.pbar.update()


class Statistics:

    def __init__(self, arguments, project_clusters_info_file='', stat_type='', project_dir=''):
        self.arguments = arguments
        self.stat_type = stat_type
        self.project_dir = project_dir
        self.project_cluster_info_file = project_clusters_info_file
        self.features_type = get_basename(self.project_cluster_info_file).split('.')[0]
        self.alg = get_basename(get_parent_dir(self.project_cluster_info_file))
        self.project_name = get_basename(get_basename(self.project_dir))
        self.vul_info = None
        self.vul_gt_functions = []
        Statistics.pbar = None

    def print_slices_info(self):

        # bcs_dir = self.get_bc_dir_of_project()
        # afs_files = self.get_construct_files(bcs_dir, ext='.afs.dot')
        dataset_dir = self.get_dataset_dir_of_project()
        afs_files = []  # self.get_constructs_from_dataset(dataset_dir, 'afs_NN.csv')
        for afs_file in get_files_in_dir(dataset_dir, ext='afs_NN.csv'):
            afs_files += self.get_constructs_from_dataset(afs_file)

        Statistics.pbar = tqdm(total=len(afs_files))
        p = Pool(processes=self.arguments.count_cpu)
        chunks_nodes_sizes = []
        global nodes_sizes
        for afs_file in afs_files:
            p.apply_async(process_sample, (afs_file,), callback=my_callback)
        p.close()
        p.join()
        Statistics.pbar.close()
        chunks_nodes_sizes.append(nodes_sizes)

        # chunk_files = self.get_construct_files(bcs_dir, ext='.afs.bb1.dot')
        chunk_files = []  # self.get_constructs_from_dataset(dataset_dir, 'afs.bb1_NN.csv')
        for chunk_file in get_files_in_dir(dataset_dir, ext='afs.bb1_NN.csv'):
            chunk_files += self.get_constructs_from_dataset(chunk_file)

        Statistics.pbar = tqdm(total=len(chunk_files))
        p = Pool(processes=self.arguments.count_cpu)
        nodes_sizes = []
        for chunk_file in chunk_files:
            p.apply_async(process_sample, (chunk_file,), callback=my_callback)
        p.close()
        p.join()
        Statistics.pbar.close()
        chunks_nodes_sizes.append(nodes_sizes)

        fig = plt.figure()
        xlabels = ['{}\nfull-Con'.format(len(afs_files)), '{}\n1-Con'.format(len(chunk_files))]
        ax = fig.add_subplot(111)
        ax.boxplot(chunks_nodes_sizes, showfliers=False)
        ax.set_xticks(np.arange(len(xlabels)) + 1)
        ax.set_xticklabels(xlabels, ha='center')
        fig.subplots_adjust(bottom=0.1)

        ax.set_aspect(0.03)
        ax.set_ylim(bottom=-5, top=150)

        ax.tick_params(axis='x', pad=5)
        ax.tick_params(axis='y', pad=5)
        plt.grid()

        plots_dir = join_path(self.arguments.data_dir, self.arguments.plots_dir)
        make_dir_if_not_exist(plots_dir)
        plots_dir = join_path(plots_dir, get_basename(self.project_dir))
        make_dir_if_not_exist(plots_dir)
        plt.savefig(join_path(plots_dir, '{}_slices_sizes_bp.pdf'.format(get_basename(self.project_dir))),
                    bbox_inches='tight', pad_inches=0)

    def print_performance_time(self):

        bcs_dir = self.get_bc_dir_of_project()
        time_files = get_files_in_dir(bcs_dir, ext='.time.txt')

        extracted_times = list()
        bc_time = np.sum(self.get_time_from_files('bc.time.txt', time_files))
        pdg_time = np.sum(self.get_time_from_files('.pdg.time.txt', time_files))
        cons_time = np.sum(self.get_time_from_files('.afs.time.txt', time_files))
        bb_cons_time = np.sum(self.get_time_from_files('.afs.bb.time.txt', time_files))

        dataset_dir = self.get_dataset_dir_of_project()
        fe_time, bb_fe_time = self.get_time_from_file(dataset_dir, '.feature_extraction.time.txt')
        first_clus_time, bb_first_clus_time = self.get_time_from_file(dataset_dir, '.1st-clustering.time.txt')
        second_clus_time, bb_second_clus_time = self.get_time_from_file(dataset_dir, '.2nd-clustering.time.txt')
        pc_time, bb_pc_time = self.get_time_from_file(dataset_dir, '.post-clustering.time.txt')

        extracted_times += [bc_time, pdg_time, cons_time, bb_cons_time, fe_time + first_clus_time,
                            bb_fe_time + bb_first_clus_time, second_clus_time,
                            bb_second_clus_time, pc_time, bb_pc_time,
                            bc_time + pdg_time + cons_time + bb_cons_time + fe_time + bb_fe_time + first_clus_time +
                            bb_first_clus_time + second_clus_time + bb_second_clus_time + pc_time + bb_pc_time]

        extracted_times_min = []
        extracted_times_hour = []
        for time in extracted_times:
            extracted_times_min.append(time / 60.0)
            extracted_times_hour.append(time / 3600.0)

        return extracted_times_min, extracted_times_hour

    @staticmethod
    def draw_bar_chart(arguments, time_data_min, time_data_hour):
        projects_times = time_data_hour
        plots_dir = join_path(arguments.data_dir, arguments.plots_dir)
        indices = ['Bitcode Generation', 'DDG Extraction', 'Construct Extraction (full-con)',
                   'Construct Extraction (1-con)',
                   '1st-step Clustering (full-con)',
                   '1st-step Clustering (1-con)', '2nd-step Clustering (full-con)',
                   '2nd-step Clustering (1-con)', 'Saving Inconsistencies (full-con)',
                   'Saving Inconsistencies (1-con)', 'Total']
        data = pd.DataFrame(projects_times)
        data.index = indices
        print 'Time (Hours)'
        print data
        data_min = pd.DataFrame(time_data_min)
        data_min.index = indices
        print 'Time (Minutes)'
        print data_min
        data.plot(kind='bar')
        plt.grid(color='lightgray', linestyle='-.', linewidth=0.2)
        plt.xticks(rotation=45, horizontalalignment='right')
        # plt.xlabel('Step', fontsize=14)
        plt.ylabel('Execution Time (h)', fontsize=14)
        plt.savefig(join_path(plots_dir, 'time_bar_plot.pdf'),
                    bbox_inches='tight', pad_inches=0)
        plt.savefig(join_path(plots_dir, 'time_bar_plot.eps'),
                    bbox_inches='tight', pad_inches=0)

    def get_time_from_file(self, dataset_dir, file_name):
        tmp_files = get_files_in_dir(dataset_dir, ext=file_name)
        afs_file = ''
        afs_bb_file = ''
        for tmp_file in tmp_files:
            if get_basename(tmp_file).startswith('afs.bb'):
                afs_bb_file = tmp_file
            else:
                afs_file = tmp_file

        afs_time = 0
        if exist_file(afs_file):
            afs = open(afs_file, 'r')
            afs_time = float(afs.read())
        else:
            print 'File does not exist:', afs_file

        afs_bb_time = 0
        if exist_file(afs_bb_file):
            afs_bb = open(afs_bb_file, 'r')
            afs_bb_time = float(afs_bb.read())
        else:
            print 'File does not exist:', afs_file

        return afs_time, afs_bb_time

    def get_time_from_files(self, time_file_type, time_files):
        global times
        times = []
        tmp_time_files = [time_file for time_file in time_files if time_file.endswith(time_file_type)]
        Statistics.pbar = tqdm(total=len(tmp_time_files))
        p = Pool(processes=self.arguments.count_cpu)
        for time_file_path in tmp_time_files:
            p.apply_async(process_time, (time_file_path,), callback=time_callback)
        p.close()
        p.join()
        return times

    def get_constructs_from_dataset(self, csv_file):
        # dataset_file = get_files_in_dir(dataset_dir, ext=file_name)
        dataset = pd.read_csv(csv_file)

        return dataset['location'].tolist()

    def print_slices_similarities(self):
        dataset_dir = self.get_dataset_dir_of_project()
        json_helper_file = join_path(self.project_dir, self.project_name + '.json')
        json_file = open(json_helper_file)
        json_data = json.load(json_file)
        type_selected_features = {}
        for stat_sim_type in self.arguments.stat_sim_types:
            dataset_file = get_files_in_dir(dataset_dir, ext=stat_sim_type + '.afs.csv')[0]
            dataset_data = pd.read_csv(dataset_file)
            type_selected_features[stat_sim_type] = self.get_features_from_targeted_locations(json_data, dataset_data)

        bcs_dir = self.get_bc_dir_of_project()
        for inconsistency in json_data[self.project_name]['inconsistencies']:
            location_slicetype = {}
            for slice in inconsistency['slices']:
                afs_location, slice_type = self.get_afs_location(bcs_dir, slice)
                location_slicetype[afs_location] = slice_type
            for sim_type, selected_features in type_selected_features.iteritems():
                inconsistency_rows = selected_features.loc[selected_features['location'].
                    isin(list(location_slicetype.keys()))]
                counter = 0
                if len(inconsistency_rows) == 0:
                    print 'Couldn\'t find slices'
                    print location_slicetype.keys()
                    print '=' * 100
                    continue
                for index, row in inconsistency_rows.iterrows():
                    counter += 1
                    print str(counter), index, row['location']
                inconsistency_rows = inconsistency_rows.drop('location', 1)
                inconsistency_rows = inconsistency_rows.dropna(axis=1, how='all')
                inconsistency_rows = inconsistency_rows.fillna(0)
                print inconsistency_rows
                # print '-' * 50
                # print "Node features + metadata"
                # self.print_similarities(cosine_similarity(inconsistency_rows))
                # inconsistency_rows = inconsistency_rows.drop('metadata_num_edges', 1)
                # inconsistency_rows = inconsistency_rows.drop('metadata_num_nodes', 1)
                # inconsistency_rows = inconsistency_rows.drop('metadata_entropy_centrality_distribution', 1)
                print sim_type, "features"
                self.print_similarities(cosine_similarity(inconsistency_rows))
                print '-' * 50
            print '=' * 100

        # plots_dir = join_path(self.arguments.data_dir, self.arguments.plots_dir)
        # make_dir_if_not_exist(plots_dir)
        # plots_dir = join_path(plots_dir, get_basename(self.project_dir))
        # make_dir_if_not_exist(plots_dir)
        # plt.savefig(join_path(plots_dir, '{}_slices_sizes_bp.png'.format(get_basename(self.project_dir))))

    def print_similarities(self, similarity_matrix):
        for i in range(similarity_matrix.shape[0]):
            row = ''
            for j in range(similarity_matrix.shape[0]):
                if i >= j:
                    continue
                sim = "%.5f" % round(similarity_matrix[i][j], 5)
                row = '{} {}'.format(row, sim)
            print row

    def get_features_from_targeted_locations(self, json_data, dataset_data):
        targeted_locations = set()
        bcs_dir = self.get_bc_dir_of_project()
        for inconsistency in json_data[self.project_name]['inconsistencies']:
            for slice in inconsistency['slices']:
                afs_location, slice_type = self.get_afs_location(bcs_dir, slice)
                targeted_locations.add(afs_location)
        return dataset_data.loc[dataset_data['location'].isin(targeted_locations)]

    def get_afs_location(self, bcs_dir, slice):
        slice_type = 'unknown'
        if 'buggy' in slice:
            slice_type = 'buggy'
        elif 'patched' in slice:
            slice_type = 'patched'
        slice_info = slice[slice_type]
        afs_location = join_path(bcs_dir, slice_info['directory'], slice_info['file'], 'pdg',
                                 '{}.pdg_{}_{}.afs.dot'.format(slice_info['function'],
                                                               slice_info['variable']['type'],
                                                               slice_info['variable']['name']))
        return afs_location, slice_type

    def get_bc_dir_of_project(self):
        project_dir = self.project_dir
        project_dir = project_dir.replace(self.arguments.projects_dir, self.arguments.bcs_dir)
        return project_dir

    def get_dataset_dir_of_project(self):
        project_dir = self.project_dir
        project_dir = project_dir.replace(self.arguments.bcs_dir, self.arguments.datasets_dir)
        return project_dir

    def print_vul_info(self):
        self.load_vul_info()
        clusters_info = {}
        clusters_functions = defaultdict(list)
        target_cluster = -2
        features = read_csv_header(join_path(get_parent_dir(get_parent_dir(self.project_cluster_info_file)),
                                             '{}.csv'.format(self.features_type)))
        number_of_features = len(features)

        for line in read_lines(self.project_cluster_info_file):
            if line.startswith('Cluster'):
                line_items = line.split()
                target_cluster = line_items[1].replace('#', '')
            elif line.startswith('# Items'):
                line_items = line.split()
                cluster_items = line_items[2].replace('#', '')
                clusters_info[target_cluster] = int(cluster_items)
            elif line.startswith('='):
                pass
            else:
                clusters_functions[target_cluster].append(line)

        vul_functions_clusters = defaultdict(list)
        for cluster, functions in clusters_functions.iteritems():
            for vul_function in self.vul_gt_functions:
                for function_name in functions:
                    if function_name.endswith(vul_function):
                        vul_functions_clusters[vul_function].append((cluster, clusters_info[cluster]))

        sorted_clusters = dict(sorted(clusters_info.iteritems(), key=operator.itemgetter(1), reverse=True))
        top_biggest = 5
        if len(sorted_clusters) < top_biggest:
            biggest_clusters_dict = sorted_clusters
        else:
            biggest_clusters = heapq.nlargest(top_biggest, sorted_clusters, key=sorted_clusters.get)
            biggest_clusters_dict = {}
            for clus in biggest_clusters:
                biggest_clusters_dict[clus] = clusters_info[clus]

        print self.project_name, self.features_type, self.alg
        print 'Cluster of Vul Function: {}'.format(vul_functions_clusters)
        for key, value in vul_functions_clusters.iteritems():
            if value[0][1] <= 100:
                for item in clusters_functions[value[0][0]]:
                    if not item.endswith(key):
                        print 'similar function: %s' % item
        print '# Clusters: {}'.format(len(clusters_info) - 1)
        if '-1' in clusters_info.keys():
            print '# Single Clusters: {}'.format(clusters_info['-1'])
        print '# Biggest Clusters: {}'.format(biggest_clusters_dict)
        print '# Features: {}'.format(number_of_features)
        print '{}'.format('=' * 100)

    def load_vul_info(self):
        self.vul_info = load_json_file(join_path(self.arguments.data_dir, 'vul_info.txt'))
        if self.project_name in self.vul_info:
            self.vul_gt_functions = self.vul_info[self.project_name]

    def get_construct_files(self, bcs_dir, ext):
        if self.arguments.has_control_flow:
            afs_files = get_files_in_dir(bcs_dir, ext=ext, start='_CDD_')
        else:
            afs_files = get_files_in_dir(bcs_dir, ext=ext, start='_ODD_')
        return afs_files
