import multiprocessing as mp

class Arguments:
    def __init__(self, actions, languages, data_dir, projects_dir, asts_dir, bcs_dir,
                 datasets_dir, plots_dir, search_spaces, clang_lib_dir, clustering_algs, clustering_feat,
                 second_clustering, cose_similarity_chunk_size, big_clusters_ignore, chunk_window_size,
                 split, projects, save_format,
                 ignore_compile_commands,
                 feature_types, llvm_config, includes, pdg_dumper, clang, stat_type, stat_sim_types, has_control_flow,
                 inconsistency_type, similarity_threshold, granularity, dependency, call_inconsistency,
                 type_inconsistency, store_inconsistency, inconsistency_query_options, ssh, filtering, count_cpu, ids,
                 starting_report_item, prepare):
        self.actions = actions
        self.languages = languages
        self.data_dir = data_dir
        self.projects_dir = projects_dir
        self.asts_dir = asts_dir
        self.bcs_dir = bcs_dir
        self.datasets_dir = datasets_dir
        self.plots_dir = plots_dir
        self.search_spaces = search_spaces
        self.clang_lib_dir = clang_lib_dir
        self.clustering_algs = clustering_algs
        self.clustering_feat = clustering_feat
        self.second_clustering = second_clustering
        self.cose_similarity_chunk_size = cose_similarity_chunk_size
        self.big_clusters_ignore = big_clusters_ignore
        self.chunk_window_size = chunk_window_size
        self.split = split
        self.projects = projects
        self.save_format = save_format
        self.ignore_compile_commands = ignore_compile_commands
        self.feature_types = feature_types
        self.llvm_config = llvm_config
        self.includes = includes
        self.pdg_dumper = pdg_dumper
        self.clang = clang
        self.stat_type = stat_type
        self.stat_sim_types = stat_sim_types
        self.has_control_flow = has_control_flow
        self.inconsistency_type = inconsistency_type
        self.similarity_threshold = similarity_threshold
        self.granularity = granularity
        self.dependency = dependency
        self.call_inconsistency = call_inconsistency
        self.type_inconsistency = type_inconsistency
        self.store_inconsistency = store_inconsistency
        self.inconsistency_query_options = inconsistency_query_options
        self.ssh = ssh
        self.filtering = filtering
        self.count_cpu = count_cpu
        self.ids = ids
        self.starting_report_item = starting_report_item
        self.prepare = prepare

        try:
            mp.cpu_count()
        except:
            self.count_cpu = 1
        print 'Running the code by {} CPUs'.format(self.count_cpu)
