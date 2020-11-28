import subprocess
from multiprocessing import Pool
from subprocess import call

import networkx as nx
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from tqdm import tqdm

from astfile import ASTFile
from bitcodefile import BitCodeFile
# from learning.graph2vec.graph2vec import Graph2Vec
from learning.graph2vec.parallelgraph2vec import Graph2Vec
from learning.graphkernel.weisfeiler_lehman import GK_WL
from learning.similarity import counter_cosine_similarity, get_graph_similarity
from sourcefile import SourceFile
from utils.inout import *


def process_sample(source_file, args, project_dir, compile_arguments, type=''):
    if type == 'ast' or type == 'bc':
        source_file_obj = SourceFile(source_file=source_file, arguments=args,
                                     project_dir=project_dir, compile_arguments=compile_arguments,
                                     analysis_type=type)
        try:
            source_file_obj.analyze()
        except:
            pass
            # print 'CRASH', type, source_file
    if type == 'pdg' or type == 'as':
        file_handler = BitCodeFile(file_info=source_file, arguments=args, analysis_type=type)
        success = file_handler.analyze()
        return int(success)
    return 1


def my_callback(code):
    if not code:
        ProjectCode.erroneous_samples += 1
    ProjectCode.pbar.update()


class ProjectCode:

    def __init__(self, project_dir, arguments, project_includes=None, feature_type='', file_locations=None,
                 module_name='whole'):
        self.project_dir = project_dir
        self.module_name = module_name
        self.arguments = arguments
        self.project_includes = project_includes
        self.asts = []
        self.afs_features_counters = []
        self.afs_file_infos = []
        self.feature_type = feature_type.split('_')
        self.file_locations = file_locations
        self.has_similarity_matrix = False
        self.num_features = 0
        self.num_abstract_slices = 0
        ProjectCode.pbar = None
        ProjectCode.erroneous_samples = 0

    def retrieve_ast(self):
        source_files = get_files_in_dir(self.project_dir, ext='.c', search_spaces=self.arguments.search_spaces)
        # project_includes = self.get_includes()
        # print project_includes
        compile_commands_path = join_path(self.project_dir, 'compile_commands.json')
        compile_commands = []
        if not is_file(compile_commands_path):
            print 'There is no compile commands file'
        else:
            compile_commands = load_json(compile_commands_path)
            if len(compile_commands) == 0:
                print 'Compile commands file is empty'

        ProjectCode.pbar = tqdm(total=len(source_files))
        p = Pool(processes=self.arguments.count_cpu)
        for source_file in source_files:
            compile_arguments = get_arguments(str(source_file).replace(self.project_dir, ''), compile_commands)
            p.apply_async(process_sample, (source_file, self.arguments, self.project_dir,
                                           compile_arguments, 'ast'),
                          callback=my_callback)

        p.close()
        p.join()
        ProjectCode.pbar.close()

    def retrieve_bc(self):

        compile_commands_path = join_path(self.project_dir, 'compile_commands.json')

        # compile_commands = []
        source_files_compile_args = {}
        if not is_file(compile_commands_path):
            print 'There is no compile commands file'
            source_files = get_files_in_dir(self.project_dir, ext='.c', search_spaces=self.arguments.search_spaces)
        else:
            compile_commands = load_json(compile_commands_path)
            if len(compile_commands) == 0:
                print 'Compile commands file is empty'
                source_files = get_files_in_dir(self.project_dir, ext='.c', search_spaces=self.arguments.search_spaces)
            else:
                source_files_compile_args = get_cfiles_compile_db(compile_commands)
                source_files = source_files_compile_args.keys()

        print 'Total number of c files : {}'.format(len(source_files))
        # print 'Total number of compiled files : {}'.format(len(compile_commands))
        # print 'ignoring {} assembly files:'.format(len(get_files_in_dir(self.project_dir, ext='.s',
        #                                                                search_spaces=self.arguments.search_spaces)))
        # check_missing_files(source_files, compile_commands)
        # project_includes = self.get_includes()
        # print project_includes

        ProjectCode.pbar = tqdm(total=len(source_files))
        p = Pool(processes=1)

        for source_file in source_files:
            # compile_arguments = get_arguments(source_file, compile_commands)
            compile_arguments = source_files_compile_args[source_file]
            p.apply_async(process_sample, (source_file, self.arguments, self.project_dir, compile_arguments, 'bc'),
                          callback=my_callback)

        p.close()
        p.join()
        ProjectCode.pbar.close()

    def prepare_bc(self):
        bc_dir = self.get_bc_dir_of_project()
        bitcode_files = get_files_in_dir(bc_dir, ext='.bc',
                                         search_spaces=self.arguments.search_spaces)

        if len(bitcode_files) == 0:
            print 'There is no bitcode in:', bc_dir
            exit(0)
        print 'Total number of c files : {}'.format(len(bitcode_files))

        for bitcode_file in bitcode_files:
            sf = SourceFile('', arguments=self.arguments)
            sf.emit_llvm_ll_and_functions(bitcode_file)

    def retrieve_pdg(self):
        bcs_dir = self.get_bc_dir_of_project()
        bcs_files = get_files_in_dir(bcs_dir, ext='.bc')
        if len(bcs_files) == 0:
            print 'No bitcode found'
            return
        ProjectCode.pbar = tqdm(total=len(bcs_files))
        p = Pool(processes=self.arguments.count_cpu)
        for bc_file in bcs_files:
            p.apply_async(process_sample, (bc_file, self.arguments, bcs_dir, {}, 'pdg'),
                          callback=my_callback)

        p.close()
        p.join()
        ProjectCode.pbar.close()

    def retrieve_as(self):
        ProjectCode.erroneous_samples = 0
        bcs_dir = self.get_bc_dir_of_project()
        pdg_files = get_files_in_dir(bcs_dir, ext='.pdg.dot')
        # pdg_files = get_files_in_dir(bcs_dir, ext='.pdg.dot')
        if len(pdg_files) == 0:
            print 'No pdg found'
            return
        ProjectCode.pbar = tqdm(total=len(pdg_files))
        p = Pool(processes=self.arguments.count_cpu)
        for pdg_file in pdg_files:
            p.apply_async(process_sample, (pdg_file, self.arguments, bcs_dir, {}, 'as'),
                          callback=my_callback)

        p.close()
        p.join()
        ProjectCode.pbar.close()
        print 'Number of erroneous PDGs:', ProjectCode.erroneous_samples

    def get_includes(self):
        include_files = get_files_in_dir(self.project_dir, ext='.d')
        includes = set()
        for include_file_name in include_files:
            header_files = [file_name for file_name in read_file(include_file_name).split() if file_name.endswith('.h')]
            for header_file in header_files:
                project_name = get_basename(self.project_dir)
                if project_name in header_file:
                    tmp_header = header_file[header_file.rfind(project_name) + len(project_name) + 1:]
                elif header_file.startswith('/usr'):
                    includes.add(get_parent_dir(header_file))
                    continue
                else:
                    tmp_header = header_file
                while tmp_header != '':
                    header_parent = get_parent_dir(tmp_header)
                    includes.add(join_path(self.project_dir, header_parent))
                    tmp_header = header_parent

        return list(includes)

    def get_ast_dir_of_project(self):
        project_dir = self.project_dir
        project_dir = project_dir.replace(self.arguments.projects_dir, self.arguments.asts_dir)
        return project_dir

    def get_bc_dir_of_project(self):
        project_dir = self.project_dir
        project_dir = project_dir.replace(self.arguments.projects_dir, self.arguments.bcs_dir)
        return project_dir

    def get_dataset_dir_of_project(self):
        project_dir = self.project_dir
        dataset_dir = project_dir.replace(self.arguments.bcs_dir, self.arguments.datasets_dir)
        return dataset_dir

    def extract_features(self, save=False):
        if self.feature_type[0] == 'ast':
            self.extract_features_ast()
        elif self.feature_type[0].startswith('afs'):
            if self.feature_type[1] == 'GKWL':
                self.extract_graph_similarity()
            elif self.feature_type[1] == 'G2v':
                self.extract_graph2vec_features(save=save)
                # self.save_features()
            else:
                self.extract_features_afs(save=save)

    def extract_graph2vec_features_old(self):
        bcs_dir = self.get_bc_dir_of_project()
        if self.module_name != 'whole':
            bcs_dir = join_path(bcs_dir, self.module_name)
        if self.file_locations is not None:
            afs_files = self.file_locations
        else:
            afs_files = self.get_construct_files(bcs_dir)
        g2v = Graph2Vec(project_dir=bcs_dir, files_paths=afs_files, arguments=self.arguments)
        g2v.run()
        dict_to_save = {}
        for i in range(len(g2v.final_embeddings)):
            graph_fname = get_filename_without_ext(g2v.corpus._id_to_graph_name_map[i])
            graph_embedding = g2v.final_embeddings[i, :].tolist()
            dict_to_save[graph_fname] = graph_embedding

        for key, values in dict_to_save.iteritems():
            features = {}
            counter = 0
            for value in values:
                counter += 1
                feature_name = 'representation_{}'.format(counter)
                features[feature_name] = value
            self.afs_features_counters.append(features)
            self.afs_file_infos.append(key)

    def extract_graph_similarity(self):
        bcs_dir = self.get_bc_dir_of_project()
        if self.module_name != 'whole':
            bcs_dir = join_path(bcs_dir, self.module_name)
        if self.file_locations is not None:
            afs_files = self.file_locations
        else:
            afs_files = self.get_construct_files(bcs_dir)

        graph_list = [nx.drawing.nx_agraph.read_dot(graph_file) for graph_file in afs_files]
        gkwl = GK_WL()
        sim_matrix = gkwl.compare_list(graph_list=graph_list)
        print sim_matrix

    def extract_graph_similarity_old(self):
        bcs_dir = self.get_bc_dir_of_project()
        afs_files = self.get_construct_files(bcs_dir)
        n = len(afs_files)
        similarity_matrix = np.zeros(shape=(n, n))
        pbar = tqdm(total=((n * (n + 1)) / 2) - n)
        for i, afs_file in enumerate(afs_files):
            afs_graph_i = nx.drawing.nx_agraph.read_dot(afs_file).to_undirected()
            for j in range(i + 1, len(afs_files)):
                afs_graph_j = nx.drawing.nx_agraph.read_dot(afs_files[j]).to_undirected()
                similarity = get_graph_similarity(afs_graph_i, afs_graph_j)
                similarity_matrix[i][j] = similarity_matrix[j][i] = similarity
                pbar.update()
                del afs_graph_j
            del afs_graph_i
            # pbar.update()
        pbar.close()
        print similarity_matrix
        similarity_matrix = MinMaxScaler().fit_transform(similarity_matrix)
        print similarity_matrix
        return similarity_matrix

    def extract_graph2vec_features(self, save=False):
        bcs_dir = self.get_bc_dir_of_project()
        dataset_dir = self.get_dataset_dir_of_project()
        if self.module_name != 'whole':
            bcs_dir = join_path(bcs_dir, self.module_name)
        if self.file_locations is not None:
            afs_files = self.file_locations
        else:
            afs_files = self.get_construct_files_from_dataset(dataset_dir)
        g2v = Graph2Vec(project_dir=bcs_dir, files_paths=afs_files, arguments=self.arguments)
        g2v.run()
        dict_to_save = {}
        for i in range(len(g2v.final_embeddings)):
            graph_embedding = g2v.final_embeddings[i]
            dict_to_save[g2v.graph_files[i]] = graph_embedding

        for key, values in dict_to_save.iteritems():
            features = {}
            counter = 0
            for value in values:
                counter += 1
                feature_name = 'representation_{}'.format(counter)
                features[feature_name] = value
            self.afs_features_counters.append(features)
            self.afs_file_infos.append(key)

        module_subsection_counter = 1
        if len(self.afs_file_infos) > 0 and save:
            self.module_name = '{}{}'.format(self.module_name, module_subsection_counter)
            self.save_features()

    def extract_features_afs(self, save=False):
        bcs_dir = self.get_bc_dir_of_project()
        if self.module_name != 'whole':
            bcs_dir = join_path(bcs_dir, self.module_name)

        afs_files = self.get_construct_files(bcs_dir)

        module_name = self.module_name
        pbar = tqdm(total=len(afs_files))
        counter = 0
        module_subsection_counter = 1
        unique_constructs = set()
        for afs_file in afs_files:
            bc_handler = BitCodeFile(afs_file, self.arguments, feature_type=self.feature_type[1])
            # if ast_handler.ast is None:
            #     continue
            bc_handler.extract_features()
            # if bc_handler.construct_hash in unique_constructs:
            #     continue
            # unique_constructs.add(bc_handler.construct_hash)
            # is size of chunk is larger than 2 nodes
            if bc_handler.graph_len > 2 and bc_handler.construct_hash not in unique_constructs:
                self.afs_features_counters.append(bc_handler.afs_features_counters)
                self.afs_file_infos.append(bc_handler.file_info)
                counter += 1
            unique_constructs.add(bc_handler.construct_hash)
            del bc_handler
            pbar.update()
            if counter % self.arguments.cose_similarity_chunk_size == 0 and save:
                self.module_name = '{}{}'.format(module_name, module_subsection_counter)
                self.save_features()
                self.afs_features_counters = []
                self.afs_file_infos = []
                module_subsection_counter += 1
            # pprint(ast_handler.compute_functions_similarities())
        if len(self.afs_file_infos) > 0 and save:
            self.module_name = '{}{}'.format(module_name, module_subsection_counter)
            self.save_features()
        pbar.close()
        print 'Number of features: ', self.num_features
        print 'Number of Abstract Slices: ', self.num_abstract_slices

    def get_construct_files_from_dataset(self, dataset_dir):
        if self.arguments.has_control_flow:
            dataset = get_files_in_dir(dataset_dir, ext='_{}_NN.csv'.format(self.feature_type[0]), start='_CDD_')
        else:
            dataset = get_files_in_dir(dataset_dir, ext='_{}_NN.csv'.format(self.feature_type[0]), start='_ODD_')
        dataframe = pd.read_csv(dataset[0])
        return list(dataframe['location'])

    def get_construct_files(self, bcs_dir):
        if self.arguments.has_control_flow:
            afs_files = get_files_in_dir(bcs_dir, ext='.{}.dot'.format(self.feature_type[0]), start='_CDD_')
        else:
            afs_files = get_files_in_dir(bcs_dir, ext='.{}.dot'.format(self.feature_type[0]), start='_ODD_')
        return afs_files

    def extract_features_ast(self):
        asts_dir = self.get_ast_dir_of_project()
        ast_files = get_files_in_dir(asts_dir, ext='.graphml')
        pbar = tqdm(total=len(ast_files))
        for ast_file in ast_files:
            ast_handler = ASTFile(ast_file, self.arguments, feature_type=self.feature_type[1])
            if ast_handler.ast is None:
                continue
            ast_handler.extract_features()
            self.asts.append(ast_handler)
            pbar.update()
            # pprint(ast_handler.compute_functions_similarities())
        pbar.close()

    def save_features(self):
        if self.feature_type[0] == 'ast':
            self.save_ast_features()
        elif self.feature_type[0].startswith('afs'):
            self.save_afs_features()

    def save_afs_features(self):
        dataset = []
        for i in range(len(self.afs_features_counters)):
            features = self.afs_features_counters[i]
            if len(features) == 0:
                print self.afs_file_infos[i]
            else:
                features['location'] = '{}'.format(self.afs_file_infos[i])
                dataset.append(features)

        dataframe = pd.DataFrame(dataset)
        num_rows = len(dataframe.index)
        if num_rows == 0:
            print 'No chunk is available'
            return
        self.num_features = len(dataframe.columns)
        self.num_abstract_slices = len(dataframe.index)
        datasets_dir = self.project_dir.replace(self.arguments.bcs_dir,
                                                self.arguments.datasets_dir
                                                )

        make_dir_if_not_exist(datasets_dir)
        if self.arguments.has_control_flow:
            prefix = '_CDD_'
        else:
            prefix = '_ODD_'
        csv_file = '{}{}_{}_{}.csv'.format(prefix, self.module_name, self.feature_type[0], self.feature_type[1])
        csv_file = join_path(datasets_dir, csv_file)
        dataframe.to_csv(csv_file, index=False)

    def save_ast_features(self):
        dataset = []
        for astfile in self.asts:
            for counter in range(len(astfile.functions_features_counters)):
                features = astfile.functions_features_counters[counter]
                # features['location'] = '{}:{}'.format(astfile.ast_file, astfile.function_names[counter])
                features['location'] = '{}'.format(astfile.ast_file)
                dataset.append(features)
                # print features

        # print len(dataset)
        dataframe = pd.DataFrame(dataset)
        datasets_dir = self.project_dir.replace(self.arguments.projects_dir,
                                                self.arguments.datasets_dir
                                                )

        make_dir_if_not_exist(datasets_dir)
        datasets_dir = join_path(datasets_dir, self.feature_type)
        dataframe.to_csv('{}.csv'.format(datasets_dir), index=False)

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

    def link_bc_files(self):
        bcs_dir = self.get_bc_dir_of_project()
        bcs_files = get_files_in_dir(bcs_dir, ext='.bc')
        if len(bcs_files) == 0:
            print 'No bitcode found'
            return

        llvm_link_output = bcs_dir + 'llvm-link-res.bc'
        LOG = open(llvm_link_output, 'w')
        # parse_start_time = default_timer()
        print bcs_files
        try:
            call(['llvm-link-3.8'] + bcs_files,
                 stdout=LOG, stderr=subprocess.STDOUT, close_fds=True)
        except:
            print 'crash in clang', self.source_file
            return True
