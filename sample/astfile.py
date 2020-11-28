from collections import Counter
import networkx as nx

from learning.similarity import counter_cosine_similarity


class ASTFile:

    def __init__(self, ast_file, arguments, ast=None, feature_type=''):
        self.ast_file = ast_file
        self.arguments = arguments
        self.ast = ast
        if self.ast is None:
            try:
                self.ast = nx.read_graphml(self.ast_file)
                # self.ast = self.index.read(self.ast_file)
            except Exception, e:
                print e
                print self.ast_file

        self.functions_root_nodes = []
        self.features = []
        self.functions_features_counters = []
        self.function_names = []
        self.feature_type = feature_type

    def extract_features(self):
        self.functions_root_nodes = [x for x, y in self.ast.nodes(data=True)
                                     if 'type' in y and y['type'] == '"FUNCTION_DECL"']

        for root_node in self.functions_root_nodes:
            # print root_node
            self.extract_potential_features(root_node)
            self.functions_features_counters.append(Counter(self.features))
            self.function_names.append(self.ast.node[root_node]['spelling'].replace('"', ''))

    def extract_potential_features(self, root_node):
        # self.print_graph(root_node)
        s = list(nx.dfs_preorder_nodes(self.ast, root_node))
        self.features = []

        feature_types = self.feature_type.split('+')
        for feature_type in feature_types:
            if feature_type == 'MR':
                self.extract_members(s)
            elif feature_type == 'C':
                self.extract_calls(s)
            elif feature_type == 'NT':
                self.extract_node_types(s)

    def extract_members(self, s):

        for item in s:
            node_type = self.ast.node[item]['type'].replace('"', '')
            if node_type == 'MEMBER_REF_EXPR' or node_type == 'MEMBER_REF':
                node_spelling = self.ast.node[item]['spelling'].replace('"', '')
                if node_spelling != '':
                    self.features.append('{}_{}'.format(node_type, node_spelling))

    def extract_calls(self, s):

        for item in s:
            node_type = self.ast.node[item]['type'].replace('"', '')
            if node_type == 'CALL_EXPR':
                node_spelling = self.ast.node[item]['spelling'].replace('"', '')
                if node_spelling != '':
                    self.features.append('{}_{}'.format(node_type, node_spelling))

    def extract_node_types(self, s):

        for item in s:
            node_type = self.ast.node[item]['type'].replace('"', '')
            self.features.append('NODE_TYPE_{}'.format(node_type))

    def print_graph(self, root_node):
        if self.ast.node[root_node]['spelling'].replace('"', '') in \
                ['X509v3_addr_get_afi', 'ssl3_get_record', 'aes_gcm_ctrl']:
            print root_node, self.ast.node[root_node]['spelling']
            s = list(nx.dfs_preorder_nodes(self.ast, root_node))
            for item in s:
                print self.ast.node[item]

    def compute_functions_similarities(self):
        functions_similarities = []

        for i in range(len(self.functions_features_counters) - 1):
            for j in range(len(self.functions_features_counters)):
                if i == i + j:
                    continue
                if i + j >= len(self.functions_features_counters):
                    continue
                functions_similarities.append({'func1': self.ast.node[self.functions_root_nodes[i]]['spelling'],
                                               'func2': self.ast.node[self.functions_root_nodes[i + j]]['spelling'],
                                               'score': counter_cosine_similarity(self.functions_features_counters[i],
                                                                                  self.functions_features_counters[i +
                                                                                                                   j])})

        return sorted(functions_similarities, key=lambda k: k['score'], reverse=True)

    def extract_backup_features(self, root_node):
            # self.print_graph(root_node)
            s = list(nx.dfs_preorder_nodes(self.ast, root_node))
            features = []
            for item in s:
                node_type = self.ast.node[item]['type'].replace('"', '')
                features.append(node_type)
                if node_type == 'MEMBER_REF_EXPR' or node_type == 'MEMBER_REF' or node_type =='TYPEDEF_DECL':
                    node_spelling = self.ast.node[item]['spelling'].replace('"', '')
                    if node_spelling != '':
                        features.append(node_spelling)
            # print features
            return features
