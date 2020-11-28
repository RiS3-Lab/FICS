import subprocess
from pprint import pprint
from subprocess import call
from timeit import default_timer

# import clang.cindex as cl
import networkx as nx
import pandas

from utils.inout import *


def get_diagnostics_info(diagnostics):
    return {'severity': diagnostics.severity,
            'location': diagnostics.location,
            'spelling': diagnostics.spelling
            # 'ranges': diagnostics.ranges,
            # 'fixits': diagnostics.fixits
            }


class SourceFile:

    def __init__(self, source_file, arguments, project_dir='', compile_arguments=[], analysis_type=''):
        self.source_file = source_file
        self.source_file_ast_dir = ''
        self.source_file_bc_dir = ''
        self.project_dir = project_dir
        # self.project_includes = project_includes
        self.compile_arguments = compile_arguments
        self.arguments = arguments
        # if not cl.Config.loaded:
        #     cl.Config.set_library_path(self.arguments.clang_lib_dir)
        # self.index = cl.Index.create()
        self.index = None
        self.ast = None
        self.root_nodes = []
        self.function_count = 0
        self.function_name = ''
        self.file_ast_json = {}
        self.cursor_list = {}
        self.analysis_type = analysis_type
        # self.cursor_list = []

    def emit_llvm_bc(self):
        parent_dir = get_parent_dir(self.source_file).replace(self.arguments.projects_dir, self.arguments.bcs_dir)
        make_dir_if_not_exist(parent_dir)
        self.source_file_bc_dir = join_path(parent_dir, get_basename(self.source_file))
        make_dir_if_not_exist(self.source_file_bc_dir)
        bc_file = join_path(self.source_file_bc_dir, get_filename_without_ext(get_basename(self.source_file)) + '.bc')
        ll_file = join_path(self.source_file_bc_dir, get_filename_without_ext(get_basename(self.source_file)) + '.ll')
        llvm_log_file = join_path(self.source_file_bc_dir, 'llvm.log.txt')
        llvm_dis_log_file = join_path(self.source_file_bc_dir, 'llvm-dis.log.txt')
        function_names_file = join_path(self.source_file_bc_dir, 'functions.txt')
        time_file = join_path(self.source_file_bc_dir, 'bc.time.txt')

        args = []
        # print self.compile_arguments
        if self.compile_arguments is None and not self.arguments.ignore_compile_commands:
            return True
        self.compile_arguments = [ca for ca in self.compile_arguments if not ca.startswith('-O')] + ['-O0']
        if "-Wexpansion-to-defined" in self.compile_arguments:
            self.compile_arguments.remove("-Wexpansion-to-defined")
        # self.compile_arguments = [ca for ca in self.compile_arguments if ca.startswith('-I')] + ['-O0']
        args += self.compile_arguments
        args += ['-I/usr/lib/clang/3.8.0/include/']
        args += self.arguments.includes
        # print 'args', args

        cwd = get_current_directory()
        change_directory(self.project_dir)
        # print [self.arguments.clang, '-emit-llvm', '-c', '-g', self.source_file, '-o', bc_file] + args

        LOG = open(llvm_log_file, 'w')
        parse_start_time = default_timer()
        try:
            call([self.arguments.clang, '-emit-llvm', '-c', '-g', self.source_file, '-o', bc_file] + args,
                 stdout=LOG, stderr=subprocess.STDOUT, close_fds=True)
        except:
            print 'crash in clang', self.source_file
            return True
        parse_elapsed = default_timer() - parse_start_time
        write_file(time_file, '{}'.format(parse_elapsed))
        change_directory(cwd)
        # llvm_dis = join_path(self.arguments.llvm_config, 'llvm-dis')
        llvm_dis = 'llvm-dis-3.8'
	LOG = open(llvm_dis_log_file, 'w')
        try:
            if is_file(bc_file):
                call([llvm_dis, bc_file, '-o', ll_file],
                     stdout=LOG, stderr=subprocess.STDOUT, close_fds=True)
            else:
                print 'No bc file:', bc_file
                print [arg for arg in args if arg.startswith('-I')]
        except:
            print llvm_dis, ' cannot be found'
            return True
        functions = open(function_names_file, 'w')
        lines = read_lines(ll_file)
        functions_name = []
        prev_line = ''
        for line in lines:
            if line[0:6] == 'define':
                functions_name.append(line + prev_line + '\n')
            prev_line = line
        functions.writelines(functions_name)
        return True

    def emit_llvm_ll_and_functions(self, bitcode_file):
        bitcode_filename = get_basename(bitcode_file)
        sourcecode_filename = bitcode_filename[:-2] + 'c'
        ll_filename = bitcode_filename[:-2] + 'll'
        c_dir = join_path(get_parent_dir(bitcode_file), sourcecode_filename)
        make_dir_if_not_exist(c_dir)
        new_bitcode_file = join_path(c_dir, bitcode_filename)
        move_file(bitcode_file, new_bitcode_file)
        ll_file = join_path(c_dir, ll_filename)
        llvm_dis_log_file = join_path(c_dir, 'llvm-dis.log.txt')
        function_names_file = join_path(c_dir, 'functions.txt')

        llvm_dis = join_path(self.arguments.llvm_config, 'llvm-dis-3.8')
        LOG = open(llvm_dis_log_file, 'w')
        try:
            if is_file(new_bitcode_file):
                call([llvm_dis, new_bitcode_file, '-o', ll_file],
                     stdout=LOG, stderr=subprocess.STDOUT, close_fds=True)
            else:
                print 'No bc file:', new_bitcode_file
        except:
            print llvm_dis, ' cannot be found'
            return True
        functions = open(function_names_file, 'w')
        lines = read_lines(ll_file)
        functions_name = []
        prev_line = ''
        for line in lines:
            if line[0:6] == 'define':
                functions_name.append(line + prev_line + '\n')
            prev_line = line
        functions.writelines(functions_name)

    def emit_llvm_ast(self):
        # I commented the following lines to be able to run on conda
        # self.ast = ig.Graph(directed=True)
        # if not cl.Config.loaded:
        #     cl.Config.set_library_path(self.arguments.clang_lib_dir)
        # self.index = cl.Index.create()
        self.ast = nx.DiGraph()
        include_args = []
        parent_dir = get_parent_dir(self.source_file).replace(self.arguments.projects_dir, self.arguments.asts_dir)
        make_dir_if_not_exist(parent_dir)
        self.source_file_ast_dir = join_path(parent_dir, get_basename(self.source_file))
        make_dir_if_not_exist(self.source_file_ast_dir)
        # for include in self.project_includes:
        #     include_args.append('-I{}'.format(include))

        args = []
        # args += ['--no-standard-includes', '-nostdinc++', '-nobuiltininc']
        # args += ['-nostdinc','-nostdinc++']
        # args += include_args
        if len(self.compile_arguments) == 0 and not self.arguments.ignore_compile_commands:
            return True
        args += self.compile_arguments
        args += ['-I/usr/lib/clang/3.8.0/include/']
        # args += ['-S', '-emit-llvm', '-c', '-o', 'xx.bc']
        # args += ['-I/home/mansour/nfs/vulfinder/tools/clang+llvm-5.0.1-x86_64-linux-gnu-ubuntu-16.04/include/clang']

        parse_start_time = default_timer()
        cwd = get_current_directory()
        change_directory(self.project_dir)
        translation_unit = self.index.parse(self.source_file, args=args)
        change_directory(cwd)
        parse_elapsed = default_timer() - parse_start_time
        diagnostics = map(get_diagnostics_info, translation_unit.diagnostics)
        diag_file = join_path(self.source_file_ast_dir, '{}.diag.txt'.format(get_basename(self.source_file)))
        pandas.DataFrame(diagnostics).to_csv(diag_file, index=False)
        iteration_start_time = default_timer()
        # self.add_node(translation_unit.cursor)
        if self.arguments.save_format == 'graph':
            self.get_info_graph(translation_unit.cursor)
            self.save_ast(self.function_name)
        elif self.arguments.save_format == 'json':
            ast_json = self.get_info_json(translation_unit.cursor)
            self.save_ast_json(ast_json)
            pprint(ast_json)
        elif self.arguments.save_format == 'ast':
            self.save_tu(translation_unit)
        iteration_elapsed = default_timer() - iteration_start_time
        time_file = join_path(self.source_file_ast_dir, '{}.time.txt'.format(get_basename(self.source_file)))
        write_file(time_file, 'Parsed Time: {} , Iteration Time: {}'.format(parse_elapsed, iteration_elapsed))
        return True

    def analyze(self):
        if self.analysis_type == 'ast':
            return self.emit_llvm_ast()
        elif self.analysis_type == 'bc':
            return self.emit_llvm_bc()
        else:
            return False

    def get_info_graph(self, node, depth=0):

        flag = True if self.source_file in str(node.location) else False

        if flag:
            parent_vertex_id = self.add_node(node)

        # children_info = []
        for c in node.get_children():
            self.get_info_graph(c, depth + 1)
            if flag:
                child_vertex_id = self.add_node(c)
                if parent_vertex_id != child_vertex_id:
                    self.ast.add_edge(parent_vertex_id, child_vertex_id)

    # Should be tested
    def get_info_json(self, node, depth=0):
        node_kind = str(node.kind).split('.')[1]
        flag = True if self.source_file in str(node.location) or node_kind == 'TRANSLATION_UNIT' else False

        if not flag:
            return None

        children = [self.get_info_json(c, depth + 1) for c in node.get_children()]
        children = [c for c in children if c is not None]

        return {'id': self.get_cursor_id(node),
                'kind': node_kind,
                #'usr': node.get_usr(),
                'spelling': node.spelling,
                'location': str(node.location).split(',')[1:],
                #'extent.start': str(node.extent.start),
                #'extent.end': str(node.extent.end),
                'is_definition': node.is_definition(),
                # 'definition id': get_cursor_id(node.get_definition()),
                'children': children}

    def add_node(self, node):
        node_kind = str(node.kind).split('.')[1]
        if node_kind == 'FUNCTION_DECL':
            if self.function_count >= 1:
                self.save_ast(self.function_name)
                # self.ast = None
                self.ast = nx.DiGraph()
                self.cursor_list = {}
                # self.cursor_list = []
            self.function_count += 1
            self.function_name = node.spelling

        # node_id = self.get_cursor_id(node)
        node_id = self.get_cursor_id(self.get_unique_hash(node))
        self.ast.add_node(node_id,
                          type='"{}"'.format(node_kind),
                          usr='"{}"'.format(node.get_usr()),
                          spelling=u'"{}"'.format(str(node.spelling).replace('"', '')),
                          location='"{}"'.format(node.location),
                          extent_start='"{}"'.format(node.extent.start),
                          extent_end='"{}"'.format(node.extent.end),
                          is_definition=node.is_definition()
                          # definition_id = self.get_cursor_id(node.get_definition())
                          )

        return node_id

    def get_cursor_id_bk(self, cursor_hash):

        if cursor_hash is None:
            return None

        self.cursor_list.append(cursor_hash)
        index = self.cursor_list.index(cursor_hash)
        return index - 1

    def get_cursor_id(self, cursor_hash):

        if cursor_hash is None:
            return None

        for key, value in self.cursor_list.iteritems():
            if cursor_hash == value:
                return key
        len_cursor_list = len(self.cursor_list)
        self.cursor_list[len_cursor_list] = cursor_hash
        return len_cursor_list

    def get_unique_hash(self, cursor):
        return hash(('"{}"'.format(cursor.kind),
                     '"{}"'.format(cursor.get_usr()),
                     u'"{}"'.format(str(cursor.spelling).replace('"', '')),
                                    '"{}"'.format(cursor.location),
                                    '"{}"'.format(cursor.extent.start),
                                    '"{}"'.format(cursor.extent.end),
                                    cursor.is_definition()
                     ))

    def save_ast(self, function_name):
        existing_files = get_files_in_dir(self.source_file_ast_dir, ext='{}.graphml'.format(function_name))
        if len(existing_files) == 0:
            ast_file = join_path(self.source_file_ast_dir, '{}.graphml'.format(function_name))
        else:
            ast_file = join_path(self.source_file_ast_dir, '+{}'.format(get_basename(existing_files[0])))

        nx.write_graphml(self.ast, ast_file)

    def save_ast_json(self, ast_json):
        # pprint(ast_json)
        try:
            write_file_json(join_path(self.source_file_ast_dir, 'ast.json'), ast_json)
        except Exception as e:
            print e

    def save_tu(self, translation_unit):
        translation_unit.save(join_path(self.source_file_ast_dir, '{}.ast'.format(get_basename(self.source_file_ast_dir))))

