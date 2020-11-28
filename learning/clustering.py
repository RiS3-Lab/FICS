from collections import defaultdict

# from hdbscan import HDBSCAN
from scipy.sparse.csgraph import connected_components
from sklearn.cluster import AffinityPropagation, MeanShift, DBSCAN
from sklearn.decomposition import LatentDirichletAllocation
from sklearn.metrics.pairwise import *
import dask.dataframe as dd

from sample.projectcode import ProjectCode
from utils import inout
from utils.inout import *
from scipy import sparse
from sklearn.metrics import pairwise_distances
from scipy.spatial.distance import cosine


class Clustering:

    def __init__(self, dataset='', clustering_alg='dbscancos_0.9', features_set=None, locations=None, min_samples=2,
                 from_chuck=None, module_name='root', arguments=None, project_dir='', feature_type='',
                 node_features=None, node_features_locations=None):
        self.arguments = arguments
        self.project_dir = project_dir
        self.dataset = dataset
        self.module_name = module_name
        self.locations = locations
        if from_chuck is not None:
            project_code = ProjectCode(project_dir=self.project_dir, arguments=self.arguments,
                                       feature_type=from_chuck, file_locations=self.locations)
            project_code.extract_features()
            self.features_set = pd.DataFrame(project_code.afs_features_counters)
            self.locations = project_code.afs_file_infos
        else:
            if self.locations is None:
                self.features_set, self.locations = Clustering.split_dataset(self.dataset,
                                                                             feature_type)
            else:
                self.features_set = features_set
                self.locations = locations
        # if 'location' in features_set.columns.values:
        #     features_set.drop('location', axis=1, inplace=True)
        params = clustering_alg.split('_')
        self.clustering_alg = params[0]
        self.param = float(params[1])
        self.model = None
        # LDA Parameters
        self.n_features = 1000
        self.n_samples = len(self.features_set)
        self.n_topics = 1000
        self.max_iter = 50
        self.learning_offset = 2
        # DBScan Parameters
        self.eps = self.param  # 0.9
        self.min_samples = min_samples
        # Affinity Parameters
        self.preference = self.param  # 100
        # Mean Shift
        self.bandwidth = self.param  # 1.2
        # hdbscan
        self.min_cluster_size = int(self.param)
        #########
        self.set_default_settings()
        self.clusters_samples = defaultdict(list)
        self.node_features = node_features
        self.node_features_locations = node_features_locations
        self.node_differences = defaultdict(list)
        self.clusters_samples_len_sorted_keys = list()
        self.cluster_labels = None

    def set_default_settings(self):
        if self.clustering_alg == 'dbscan' or self.clustering_alg == 'dbscancos':
            # self.features_set = StandardScaler().fit_transform(self.features_set)
            self.model = DBSCAN(eps=self.eps, min_samples=self.min_samples, n_jobs=5)
        elif self.clustering_alg == 'lda':
            self.model = LatentDirichletAllocation(n_components=self.n_topics, max_iter=self.max_iter,
                                                   learning_method='online', learning_offset=self.learning_offset,
                                                   random_state=0, n_jobs=10)
        elif self.clustering_alg == 'aff' or self.clustering_alg == 'affcos':
            self.model = AffinityPropagation()
        elif self.clustering_alg == 'means':
            self.model = MeanShift(n_jobs=5, bandwidth=self.bandwidth)
            self.param = self.bandwidth
        # elif self.clustering_alg == 'hdbscan':
        #     self.model = HDBSCAN(min_cluster_size=self.min_cluster_size, min_samples=self.min_samples
        #                          , metric='manhattan')
        #     # , algorithm='generic', metric='cosine')
        elif self.clustering_alg == 'cc':
            self.model = 'cc'

    def cluster(self):

        if self.model is None or len(self.features_set) == 0:
            return False
        if self.clustering_alg == 'affcos':
            self.model.affinity = 'euclidean'
            self.model.preference = self.preference
            # print cosine_distances(self.features_set)
            self.model.fit(cosine_similarity(self.features_set))
            # self.param = self.preference
        elif self.clustering_alg == 'dbscancos':
            # self.model.metric = 'euclidean'
            self.model.metric = 'precomputed'
            distances = cosine_distances(self.features_set)
            # distances[distances < (1 - self.param)] = 0
            self.model.fit(distances)
            # self.param = self.eps
        elif self.clustering_alg == 'hdbscan':
            self.model.fit(self.features_set)
            self.cluster_labels = self.model.labels_
        elif self.clustering_alg == 'cc':
            # similarity = cosine_similarity(self.features_set)
            # similarity = self.get_cosine_similarity()
            similarity = self.get_similarity_sparse_input()
            adjacency_mask = similarity >= self.param
            del similarity
            del self.features_set
            nb_clusters, self.cluster_labels = connected_components(adjacency_mask, connection='strong')
            # print nb_clusters
            # print self.cluster_labels
        else:
            self.model.fit(self.features_set)
        return True

    def get_similarity_scipy(self):
        return 1 - pairwise_distances(self.features_set, metric="cosine")

    def get_similarity_sparse_input(self):
        # sparse_features = sparse.csr_matrix(self.features_set)
        # return cosine_similarity(sparse_features)
        return cosine_similarity(self.features_set)

    def similarity_cosine_by_chunk(self, len, start, end):
        if end > len:
            end = len
        return cosine_similarity(X=self.features_set[start:end], Y=self.features_set, dense_output=False)

    def get_cosine_similarity(self):
        chunk_size = int(self.arguments.cose_similarity_chunk_size)
        len = self.features_set.shape[0]
        # cosine_similarities = None
        # if len <= chunk_size:
        #     cosine_similarities = cosine_similarity(self.features_set)
        # else:
        filesnames = []
        similarity_files_dir = join(self.arguments.data_dir, self.arguments.datasets_dir,
                                    get_basename(self.project_dir))
        for filename in get_files_in_dir(similarity_files_dir, start='tmp-sim-'):
            if os.path.exists(filename):
                inout.remove_file(filename)
        for chunk_start in xrange(0, len, chunk_size):
            print 'chunk start index', chunk_start
            filename = join(self.arguments.data_dir, self.arguments.datasets_dir,
                            get_basename(self.project_dir), 'tmp-sim-{}.txt'.format(chunk_start))
            sim_file = open(filename, "wb")
            cosine_similarity_chunk = self.similarity_cosine_by_chunk(len, chunk_start, chunk_start + chunk_size)
            np.savetxt(sim_file, cosine_similarity_chunk, fmt="%.2g", delimiter=',', newline='\n')
            del cosine_similarity_chunk
            sim_file.close()
            filesnames.append(filename)

        cosine_similarities = None
        for filename in filesnames:
            if cosine_similarities is None:
                cosine_similarities = np.genfromtxt(filename, delimiter=',')
            else:
                cosine_similarities = np.concatenate((cosine_similarities, np.genfromtxt(filename, delimiter=',')),
                                                     axis=0)
        return cosine_similarities

    def get_clusters(self):

        if self.clustering_alg == 'dbscan' or self.clustering_alg == 'dbscancos':
            # print self.model.labels_
            for i in range(len(self.model.labels_)):
                self.clusters_samples[self.model.labels_[i]].append(self.locations[i])
        elif self.clustering_alg == 'lda':
            sample_cluster_distrib = self.model.transform(self.features_set)
            counter = 0
            for i in range(len(self.locations)):
                counter += 1
                sample_cluster = np.argmax(sample_cluster_distrib[i])
                self.clusters_samples[sample_cluster].append(self.locations[i])
        elif self.clustering_alg == 'aff' or self.clustering_alg == 'affcos':
            for i in range(len(self.model.labels_)):
                self.clusters_samples[self.model.labels_[i]].append(self.locations[i])
        elif self.clustering_alg == 'means':
            for i in range(len(self.model.labels_)):
                self.clusters_samples[self.model.labels_[i]].append(self.locations[i])
        elif self.clustering_alg == 'hdbscan':
            for i in range(len(self.cluster_labels)):
                self.clusters_samples[self.cluster_labels[i]].append(self.locations[i])
        elif self.clustering_alg == 'cc':

            for i in range(len(self.cluster_labels)):
                self.clusters_samples[self.cluster_labels[i]].append(self.locations[i])

                if self.node_features is not None:
                    self.set_node_difference(i)
        self.sort_clusters()

    def set_node_difference(self, i):
        location_index = self.node_features_locations[self.locations[i]]
        node_features = self.node_features.iloc[location_index]
        node_features = node_features.iloc[node_features.to_numpy().nonzero()[0]].to_dict()
        self.node_differences[self.cluster_labels[i]].append(node_features)

    def sort_clusters(self):
        self.clusters_samples_len_sorted_keys = sorted(self.clusters_samples,
                                                       key=lambda k: len(self.clusters_samples[k]),
                                                       reverse=True)

    @staticmethod
    def split_dataset(dataset, feature_type):
        df = pd.read_csv(dataset, nrows=1)
        features = list(df.columns.values)
        features.remove('location')
        features_type = {'location': 'str'}
        if feature_type == 'NN':
            for feature in features:
                features_type[feature] = 'Int64'
        elif feature_type == 'G2v':
            for feature in features:
                features_type[feature] = 'float64'
        elif feature_type == '':
            print 'Feature Type is empty ...'
        # print 'Reading dataset ...'
        dataframe = pd.read_csv(dataset, dtype=features_type)
        # dataframe = dd.read_csv(dataset, dtype=features_type, header=0, blocksize=int(5e5), sample=1e9)
        # print 'Converting dataframe to pandas ...'
        # dataframe.compute()
        # print 'Filling Null values with 0 ...'
        dataframe = dataframe.fillna(0)
        return dataframe.drop('location', axis=1), dataframe['location'].tolist()

    @staticmethod
    def make_dataset_binary(dataframe):
        columns = dataframe.columns.values.tolist()
        columns.remove('location')
        for column in columns:
            dataframe.ix[dataframe[column] > 0, column] = 1
        return dataframe

    def save_clusters(self, step=''):

        content = '\n'
        for key in self.clusters_samples_len_sorted_keys:
            dic_value = self.clusters_samples[key]
            content = '{} Cluster #{} :\n'.format(content, key)
            content = '{} # Items: {}  \n'.format(content, len(dic_value))
            for item in dic_value:
                content = '{}  {}\n'.format(content, item)
            content = '{} {}\n'.format(content, '=' * 100)

        clusters_file_directory = get_parent_dir(get_filename_without_ext(self.dataset))
        clustering_feature_name = str(get_basename(get_filename_without_ext(self.dataset)))
        clusters_file = '{}_{}.{}_{}.{}.clusters.txt'.format(step,
                                                             clustering_feature_name.split('_')[1],
                                                             clustering_feature_name.split('_')[0],
                                                             str(self.param), self.module_name)
        clusters_file = join_path(clusters_file_directory, clusters_file)
        cluster_file_path = join_path(get_parent_dir(clusters_file), self.clustering_alg)
        make_dir_if_not_exist(cluster_file_path)
        clusters_file = join_path(cluster_file_path, get_basename(clusters_file))
        write_file(clusters_file, content)
