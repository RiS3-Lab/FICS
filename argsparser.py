import argparse

from act.actiontype import ActionType
from arguments import Arguments
from sample.languagetype import LanguageType
from settings import *
from utils import inout


class ArgsParser:
    def __init__(self):
        self.parser = argparse.ArgumentParser()
        self.init_arguments()
        self.arguments = None

    def parse(self):
        args, unparsed = self.parser.parse_known_args()
        self.arguments = Arguments(
            actions=args.actions.split(','),
            languages=args.languages.split(','),
            data_dir=args.data_dir,
            projects_dir=args.projects_dir,
            asts_dir=args.asts_dir,
            bcs_dir=BCS_DIR,
            datasets_dir=DATASETS_DIR,
            plots_dir=PLOTS_DIR,
            search_spaces=SEARCH_SPACES,
            clang_lib_dir=args.clang_lib_dir,
            clustering_algs=args.clustering_algs.split(','),
            clustering_feat=args.clustering_feat.split(','),
            second_clustering=args.second_clustering,
            cose_similarity_chunk_size=args.cose_similarity_chunk_size,
            big_clusters_ignore=args.big_clusters_ignore,
            chunk_window_size=args.chunk_window_size,
            split=args.split,
            projects=args.projects.split(','),
            save_format=SAVE_FORMAT,
            ignore_compile_commands=IGNORE_COMPILE_COMMANDS,
            feature_types=args.feature_types.split(','),
            llvm_config=LLVM_CONFIG,
            includes=args.includes.split(','),
            pdg_dumper=PDG_DUMPER,
            clang=CLANG,
            stat_type=STAT_TYPE,
            stat_sim_types=STAT_SIM_TYPES.split(','),
            has_control_flow=args.has_control_flow,
            inconsistency_type=args.inconsistency_type,
            similarity_threshold=args.similarity_threshold,
            granularity=args.granularity.split(','),
            dependency=args.dependency,
            call_inconsistency=args.call_inconsistency.split(','),
            type_inconsistency=args.type_inconsistency.split(','),
            store_inconsistency=args.store_inconsistency.split(','),
            inconsistency_query_options=args.inconsistency_query_options,
            ssh=args.ssh,
            filtering=args.filtering,
            count_cpu=args.count_cpu,
            ids=args.ids.split(','),
            starting_report_item=args.starting_report_item,
            prepare=args.prepare
        )

    def init_arguments(self):
        self.parser.add_argument(
            '--actions',
            '-a',
            type=str,
            default=ACTIONS,
            help='Action must be among these: {}'.format(ActionType.get_detail())
        )

        self.parser.add_argument(
            '--languages',
            '-l',
            type=str,
            default=LANGUAGES,
            help='Target language must be among these: {}'.format(LanguageType.get_detail())
        )

        self.parser.add_argument(
            '--data_dir',
            '-dd',
            type=str,
            default=DATA_DIR,
            help='Base directory of the data'
        )

        self.parser.add_argument(
            '--projects_dir',
            '-pd',
            type=str,
            default=PROJECTS_DIR,
            help='Base directory of the projects'
        )

        self.parser.add_argument(
            '--asts_dir',
            '-ad',
            type=str,
            default=ASTS_DIR,
            help='Base directory of the ast of files'
        )

        self.parser.add_argument(
            '--clang_lib_dir',
            '-cld',
            type=str,
            default=CLANG_LIB_DIR,
            help='Base directory of the clang library files'
        )

        self.parser.add_argument(
            '--projects',
            '-p',
            type=str,
            default=PROJECTS,
            help='An array containing list of checking projects'
        )

        self.parser.add_argument(
            '--clustering_algs',
            '-ca',
            type=str,
            default=CLUSTERING_ALGS,
            help='An array containing list of clustering algorithms and their thresholds'
        )

        self.parser.add_argument(
            '--clustering_feat',
            '-cf',
            type=str,
            default=CLUSTERING_FEAT,
            help='An array containing list of clustering features'
        )

        self.parser.add_argument(
            '--second_clustering',
            '-sc',
            type=str,
            default=SECOND_CLUSTERING,
            help='Type of second clustering, online vs offline'
        )

        self.parser.add_argument(
            '--cose_similarity_chunk_size',
            '-cscs',
            type=int,
            default=COSE_SIMILARITY_CHUNK_SIZE,
            help='Batch size when compute cosine similarity, depends to available RAM'
        )

        self.parser.add_argument(
            '--big_clusters_ignore',
            '-bci',
            type=int,
            default=BIG_CLUSTERS_IGNORE,
            help='Size of big clusters that should be ignored from the first step clustering'
        )

        self.parser.add_argument(
            '--chunk_window_size',
            '-cws',
            type=int,
            default=CHUNK_WINDOW_SIZE,
            help='Size of basic block window from data flows'
        )

        self.parser.add_argument(
            '--split',
            '-s',
            type=str,
            default=SPLIT,
            help='A boolean value use for splitting a project'
        )

        self.parser.add_argument(
            '--feature_types',
            '-ft',
            type=str,
            default=FEATURE_TYPES,
            help='An array containing list of feature types'
        )

        self.parser.add_argument(
            '--includes',
            '-i',
            type=str,
            default=INCLUDES,
            help='An array containing list of checking projects'
        )

        self.parser.add_argument(
            '--has_control_flow',
            '-hcf',
            action='store_true',
            help='If true, it considers control flow as well during construct extraction'
        )

        self.parser.add_argument(
            '--inconsistency_type',
            '-it',
            type=str,
            default=INCONSISTENCY_TYPE,
            help='show the result of a type of inconsistency'
        )

        self.parser.add_argument(
            '--similarity_threshold',
            '-st',
            type=float,
            default=SIMILARITY_THRESHOLD,
            help='Only show the inconsistencies having a similarity greater than a threshold'
        )

        self.parser.add_argument(
            '--granularity',
            '-g',
            type=str,
            default=GRANULARITY,
            help='Granularity of the construct'
        )

        self.parser.add_argument(
            '--dependency',
            '-d',
            type=str,
            default=DEPENDENCY,
            help='Dependency of the construct'
        )

        self.parser.add_argument(
            '--call_inconsistency',
            '-ci',
            type=str,
            default=CALL_INCONSISTENCY,
            help='Select the inconsistencies containing specific calls'
        )

        self.parser.add_argument(
            '--type_inconsistency',
            '-ti',
            type=str,
            default=TYPE_INCONSISTENCY,
            help='Select the inconsistencies containing specific types'
        )

        self.parser.add_argument(
            '--store_inconsistency',
            '-sti',
            type=str,
            default=STORE_INCONSISTENCY,
            help='Select the inconsistencies containing specific stores'
        )

        self.parser.add_argument(
            '--inconsistency_query_options',
            '-iqo',
            type=str,
            default=INCONSISTENCY_QUERY_OPTIONS,
            help='Set specific options during querying the inconsistencies'
        )

        self.parser.add_argument(
            '--ssh',
            '-ssh',
            action='store_true',
            help='If it needs to connect to a remote mongodb server'
        )

        self.parser.add_argument(
            '--filtering',
            '-f',
            action='store_true',
            help='Filter the less potential inconsistencies'
        )

        self.parser.add_argument(
            '--count_cpu',
            '-cc',
            type=str,
            default=COUNT_CPU,
            help='Number of cores'
        )

        self.parser.add_argument(
            '--ids',
            '-ids',
            type=str,
            default='',
            help='IDs of inconsistencies'
        )

        self.parser.add_argument(
            '--starting_report_item',
            '-si',
            type=int,
            default=1,
            help='Show inconsistencies starting from specific item'
        )

        self.parser.add_argument(
            '--prepare',
            '-pp',
            action='store_true',
            help='If bitcodes are given, prepare them for pdg extraction'
        )

    def do_basic_checks(self):

        possible_actions = ActionType.get_names()
        for action in self.arguments.actions:
            if action not in possible_actions:
                self.parser.print_help()
                inout.show_error('action argument is wrong!\n')

        possible_languages = LanguageType.get_names()
        for language in self.arguments.languages:
            if language not in possible_languages:
                self.parser.print_help()
                inout.show_error('language argument is wrong!\n')

        if self.arguments.data_dir is None or self.arguments.data_dir == '' or \
                not inout.exist_dir(self.arguments.data_dir):
            self.parser.print_help()
            inout.show_error('data_dir argument is not valid!\n')

        if self.arguments.projects_dir is None or self.arguments.projects_dir == '' or \
                not inout.exist_dir(inout.join_path(self.arguments.data_dir, self.arguments.projects_dir)):
            self.parser.print_help()
            inout.show_error('projects_dir argument is not valid!\n')

