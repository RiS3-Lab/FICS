from timeit import default_timer

import graphviz as gz
import networkx as nx
import pydot
from collections import defaultdict
from networkx.drawing.nx_agraph import write_dot

from utils.inout import *
from utils.computation import *
from graphviz import Graph
from timeit import default_timer


# warnings.filterwarnings('ignore')


class Slicer:

    def __init__(self, pdg_graph_file, arguments):
        self.pdg_graph_file = pdg_graph_file
        self.arguments = arguments
        self.slice_root_nodes = {}
        self.local_vars = []
        self.global_vars = []
        self.argument_vars = []
        self.orphan_functions = []
        self.error = False
        self.nodes_bb = {}
        self.bb_nodes = defaultdict(list)
        self.bb_first_last_nodes = defaultdict(list)
        self.control_edges_to_be_added = list()
        self.pdg_path = get_parent_dir(self.pdg_graph_file)
        self.start_time = -1

        try:
            self.pdg_graph = nx.drawing.nx_agraph.read_dot(self.pdg_graph_file)
            # self.find_basic_blocks_ids()
            self.find_basic_blocks_nodes()
            # self.add_bb_info()
            self.simplified_pdg_graph = self.pdg_graph.copy()
        except:
            print 'Error in reading: ', self.pdg_graph_file
            self.error = True

    def run(self):
        # self.render_pdf_graph(self.pdg_graph_file)
        try:
            # print 'Run ...', self.pdg_graph_file
            self.start_time = default_timer()
            if self.arguments.has_control_flow:
                self.find_control_flow_to_graph()

            self.remove_forward_control_dependency()
            if self.arguments.has_control_flow:
                self.add_control_flow_to_graph()
            modified_graph = '{}.modified.dot'.format(self.pdg_graph_file)
            # modified_graph = self.add_dependency_prefix(modified_graph)
            write_dot(self.simplified_pdg_graph, modified_graph)
            # write_dot(self.simplified_pdg_graph, '{}.modified.dot'.format(self.pdg_graph_file))
            self.find_slices_root_nodes()
            # print 'found root nodes'
            self.extract_slices()
            # print 'Extracted Slices', self.pdg_graph_file
        except Exception, e:
            print 'Error in slicing: ', self.pdg_graph_file
            print e.message
            self.error = True

    def render_pdf_graph(self, graph_file):
        # pass
        # Visualize dot graph
        dot = gz.Source.from_file(graph_file)
        dot.render(view=False)

    def get_variable(self, label):
        variable_name = label.split()[0][1:]
        if variable_name.isdigit():
            return ''
        self.local_vars.append(variable_name)
        return variable_name

    def get_argument(self, label):
        arg_name = label.split()[-1][1:]
        if not label.startswith('[f] IN ARG'):
            return ''
        if label.endswith('.coerce'):
            self.argument_vars.append(arg_name.split('.')[0])
            return ''
        self.argument_vars.append(arg_name)
        return arg_name

    def get_global_argument(self, label):
        variable_name = label.split()[-1][1:]
        self.global_vars.append(variable_name)
        return variable_name

    def get_call_name(self, label):
        call_name = label.split('(')[0].split('@')[-1]
        self.orphan_functions.append(call_name)
        return call_name

    def find_slices_root_nodes(self):
        for node in self.pdg_graph.nodes:
            # if self.pdg_graph.in_degree(node) == 0 or :
            if 'label' not in self.pdg_graph.node[node]:
                continue
            if self.pdg_graph.out_degree(node) == 0:
                continue
            node_label = self.pdg_graph.node[node]['label'].strip()
            node_label_parts = node_label.split('=')
            # Ignore function slices
            # if len(node_label_parts) < 2:
            #     if node_label_parts[0].strip().startswith('call ') and '%' not in node_label_parts[0].strip():
            #         call_name = self.get_call_name(node_label_parts[0])
            #         self.slice_root_nodes[node] = '{}'.format(call_name)
            #         continue
            # else:
            #     if node_label_parts[1].strip().startswith('call ') and '%' not in node_label_parts[1].strip():
            #         call_name = self.get_call_name(node_label_parts[1])
            #         self.slice_root_nodes[node] = '{}'.format(call_name)
            #         continue
            if len(node_label_parts) < 2 and not node_label_parts[0].strip().startswith('[f] IN ARG'):
                continue
            if not node_label_parts[0].strip().startswith('[f] IN ARG') and \
                    not node_label_parts[1].strip().startswith('alloca') and \
                    not node_label_parts[0].strip().startswith('[f] GLOB IN'):
                continue
            # if node_label.startswith('GLOB FUNC'):
            #    for succ_node in self.pdg_graph.successors(node):
            #        arg_info = self.get_argument(self.pdg_graph.node[succ_node]['label'])
            #        if arg_info != '' and not is_number(arg_info):
            #            self.slice_root_nodes[succ_node] = '{}'.format(arg_info)
            # arguments.append(arg_info)
            # else:
            if node_label.startswith('GLOB') or node_label.startswith('br') or node_label.startswith('ret'):
                continue
            if node_label_parts[0].strip().startswith('[f] IN ARG'):
                arg_info = self.get_argument(node_label)
                if arg_info != '' and not is_number(arg_info):
                    self.slice_root_nodes[node] = '{}'.format(arg_info)
            elif node_label_parts[0].strip().startswith('[f] GLOB IN'):
                global_arg_info = self.get_global_argument(node_label_parts[0].strip())
                if global_arg_info != '' and not is_number(global_arg_info):
                    self.slice_root_nodes[node] = '{}'.format(global_arg_info)
            else:
                var_info = self.get_variable(node_label)
                if var_info != '':
                    self.slice_root_nodes[node] = '{}'.format(var_info)

        for key, value in self.slice_root_nodes.iteritems():
            if value in self.argument_vars:
                self.slice_root_nodes[key] = 'ARG_{}'.format(value)
            elif value in self.local_vars:
                self.slice_root_nodes[key] = 'LCL_{}'.format(value)
            elif value in self.global_vars:
                self.slice_root_nodes[key] = 'GLB_{}'.format(value)
            if value in self.orphan_functions:
                self.slice_root_nodes[key] = 'FUN_{}'.format(value)

    def find_control_flow_to_graph(self):
        self.control_edges_to_be_added = list()
        for edge in self.simplified_pdg_graph.edges():
            edge_data = self.simplified_pdg_graph.get_edge_data(edge[0], edge[1])[0]
            if edge_data['color'] == 'blue' and 'lhead' in edge_data:
                head_bb = edge_data['lhead'].replace('cluster_bb_', '')
                tail_bb = edge_data['ltail'].replace('cluster_bb_', '')

                child_node = self.bb_first_last_nodes[head_bb][0]
                parent_node = self.bb_first_last_nodes[tail_bb][1]

                self.control_edges_to_be_added.append((parent_node, child_node))

        # print(len(self.simplified_pdg_graph.edges()))
        # self.simplified_pdg_graph.add_edges_from(control_edges_to_be_added, color='red')
        # print(len(self.simplified_pdg_graph.edges()))
        # print self.simplified_pdg_graph.edges()

    def add_control_flow_to_graph(self):
        self.simplified_pdg_graph.add_edges_from(self.control_edges_to_be_added, color='blue')

    def remove_forward_control_dependency(self):
        removed_edges = []
        for edge in self.simplified_pdg_graph.edges():
            if edge[0] == edge[1]:
                # print 'equal', edge
                removed_edges.append(edge)
            edge_data = self.simplified_pdg_graph.get_edge_data(edge[0], edge[1])[0]
            # print edge_data
            if edge_data['color'] == 'blue':
                removed_edges.append(edge)
                # print 'back_control', edge
            if edge_data['color'] == 'green':
                removed_edges.append(edge)
        self.simplified_pdg_graph.remove_edges_from(removed_edges)

    def extract_slices(self):
        function_name = get_filename_without_ext(self.pdg_graph_file)
        window_size = self.arguments.chunk_window_size
        if window_size == 0 or window_size < -1:
            show_error('Chunk window size cannot be 0 or less than -1')
        for slice_root_node in self.slice_root_nodes.keys():
            forward_slice_graph, slice_file, slice_name = self.extract_forward_slice(slice_root_node, function_name)

            if window_size != -1:
                self.start_time = default_timer()
                self.extract_forward_slice_chunk_bb(forward_slice_graph, slice_root_node, function_name,
                                                    window_size=window_size)
                elapsed_time = default_timer() - self.start_time
                afs_bb_time_file = join_path(self.pdg_path, '{}.afs.bb.time.txt'.format(slice_name))
                write_file(afs_bb_time_file, '{}'.format(elapsed_time))
            # comment forward backward slicing
            # self.extract_forward_backward_slices(forward_slice_graph, slice_root_node, function_name)

    def extract_forward_slice(self, slice_root_node, function_name):
        slice_graph = nx.ego_graph(self.simplified_pdg_graph, slice_root_node, radius=100000)
        forward_slice_graph = nx.DiGraph()
        forward_slice_graph.add_nodes_from(slice_graph.nodes(data=True))
        forward_slice_graph.add_weighted_edges_from(slice_graph.edges)
        slice_name = function_name + '_{}'.format(self.slice_root_nodes[slice_root_node])
        slice_file = self.add_dependency_prefix(slice_name + '.fs.dot')
        write_dot(forward_slice_graph, slice_file)

        # elapsed_time = default_timer() - self.start_time
        # write_file(self.fs_time_file.format(slice_name), '{}'.format(elapsed_time))

        # self.start_time = default_timer()
        self.get_abstract_slice(forward_slice_graph, slice_root_node, function_name,
                                self.slice_root_nodes[slice_root_node])
        elapsed_time = default_timer() - self.start_time
        afs_time_file = join_path(self.pdg_path, '{}.afs.time.txt'.format(slice_name))
        write_file(afs_time_file, '{}'.format(elapsed_time))
        # self.render_pdf_graph(slice_file)
        return forward_slice_graph, slice_file, slice_name

    def extract_forward_slice_chunk_bb(self, forward_slice_graph, slice_root_node, function_name,
                                       window_size):
        basic_block_data_flow_graph = nx.DiGraph()
        bb_nodes = defaultdict(list)
        # root_basic_block = forward_slice_graph.nodes[slice_root_node]['basic_block_id']
        # start_time = default_timer()
        # seen_nodes = []
        # print 'start building bb graph ...'
        for node in forward_slice_graph.nodes:
            #seen_nodes.append(node)
            if 'basic_block_id' in forward_slice_graph.nodes[node]:
                node_basic_block_id = forward_slice_graph.nodes[node]['basic_block_id']
                bb_nodes[str(node_basic_block_id)].append(node)
                basic_block_data_flow_graph.add_node(node_basic_block_id)
            for succ_node in forward_slice_graph.successors(node):
                #if su
                if 'basic_block_id' in forward_slice_graph.nodes[node]:
                    succ_node_basic_block_id = forward_slice_graph.nodes[succ_node]['basic_block_id']
                    if node_basic_block_id != succ_node_basic_block_id:
                        basic_block_data_flow_graph.add_edge(node_basic_block_id,
                                                             succ_node_basic_block_id)
        # elapsed_time = default_timer() - start_time
        # print 'BB graph finding', elapsed_time
        # print 'End building bb graph!'
        bbgraph_name = '{}_{}.bbgraph.dot'.format(self.pdg_graph_file, self.slice_root_nodes[slice_root_node])
        bbgraph_name = self.add_dependency_prefix(bbgraph_name)
        write_dot(basic_block_data_flow_graph, bbgraph_name)
        self.get_all_subgraphs_size(basic_block_data_flow_graph, forward_slice_graph, window_size,
                                    slice_root_node, function_name, bb_nodes)
        # for subgraph in self.get_all_subgraphs_size(basic_block_data_flow_graph, slice_root_node, window_size):
        #    slice_file = function_name + '_{}.afs.bb{}.dot'.format(self.slice_root_nodes[slice_root_node],
        #                                                           str(window_size))
        #    write_dot(subgraph, slice_file)

    def get_all_subgraphs_size(self, graph, forward_slice_graph, window_size, slice_root_node, function_name, bb_nodes):
        selected_blocks = list()
        org_window_size = window_size

        if window_size == 1:
            for node in graph.nodes:
                selected_blocks.append(node)
        elif window_size == 2:
            for edge in graph.edges:
                # if get_basename(function_name) == 'read_to_memory.pdg':
                #    if self.slice_root_nodes[slice_root_node] == 'LCL_src':
                #        print edge
                selected_blocks.append(edge)

        for blocks in selected_blocks:
            basic_block_nodes = set()
            blocks_name = ''
            # if get_basename(function_name) == 'read_to_memory.pdg':
            #    if self.slice_root_nodes[slice_root_node] == 'LCL_src':
            #        print blocks
            if isinstance(blocks, tuple):
                # if blocks == ('0x21f61d0', '0x21f7530'):
                #    print get_basename(function_name)
                #    print self.slice_root_nodes[slice_root_node]
                for block in blocks:
                    basic_block_nodes.update(bb_nodes[block])
                    blocks_name += '_' + str(block)
            elif isinstance(blocks, str):
                basic_block_nodes.update(bb_nodes[blocks])
                blocks_name += '_' + str(blocks)

            selected_graph_bb = forward_slice_graph.subgraph(basic_block_nodes)
            # if self.should_be_saved(blocks_name, selected_graph_bb):
            chunk_file = function_name + '_{}{}.afs.bb{}.dot'.format(self.slice_root_nodes[slice_root_node],
                                                                         blocks_name,
                                                                         str(org_window_size))
            chunk_file = self.add_dependency_prefix(chunk_file)
            write_dot(selected_graph_bb, chunk_file)


    def get_all_subgraphs_size_bk(self, graph, forward_slice_graph, window_size, slice_root_node, function_name,
                                  bb_nodes):
        selected_blocks = set()
        org_window_size = window_size

        if window_size == 1:
            for node in graph.nodes:
                selected_blocks.add(node)
        else:
            start_time = default_timer()
            leaf_nodes = [n for n, d in graph.out_degree() if d == 0]
            root_nodes = [n for n, d in graph.in_degree() if d == 0]
            if get_basename(function_name) == 'read_to_memory.pdg':
                if self.slice_root_nodes[slice_root_node] == 'LCL_src':
                    print leaf_nodes
                    print root_nodes

            all_paths = []
            max_path_len = 1
            for root_node in root_nodes:
                for leaf_node in leaf_nodes:
                    paths = nx.all_simple_paths(graph, source=root_node, target=leaf_node)
                    if get_basename(function_name) == 'read_to_memory.pdg':
                        if self.slice_root_nodes[slice_root_node] == 'LCL_src':
                            for path in paths:
                                print 'path', path
                    for path in paths:
                        print get_basename(function_name)
                        print self.slice_root_nodes[slice_root_node]
                        if get_basename(function_name) == 'read_to_memory.pdg':
                            if self.slice_root_nodes[slice_root_node] == 'LCL_src':
                                print 'len path', len(path)
                        all_paths.append(path)
                        if get_basename(function_name) == 'read_to_memory.pdg':
                            if self.slice_root_nodes[slice_root_node] == 'LCL_src':
                                print 'len path', len(path)
                        if len(path) > max_path_len:
                            max_path_len = len(path)
            elapsed_time = default_timer() - start_time
            print 'simple paths finding 1', elapsed_time
            if max_path_len < window_size:
                window_size = max_path_len
            if get_basename(function_name) == 'read_to_memory.pdg':
                if self.slice_root_nodes[slice_root_node] == 'LCL_src':
                    print window_size
                    print max_path_len
            if window_size == 1:
                for node in graph.nodes:
                    selected_blocks.add(node)
            else:
                for path in all_paths:
                    if get_basename(function_name) == 'read_to_memory.pdg':
                        if self.slice_root_nodes[slice_root_node] == 'LCL_src':
                            print 'reached here'
                    ngrams = self.find_ngrams(path, window_size)
                    if get_basename(function_name) == 'read_to_memory.pdg':
                        if self.slice_root_nodes[slice_root_node] == 'LCL_src':
                            print path
                            print ngrams
                    selected_blocks.update(ngrams)

        # start_time = default_timer()
        for blocks in list(selected_blocks):
            basic_block_nodes = set()
            blocks_name = ''
            if isinstance(blocks, tuple):
                for block in blocks:
                    basic_block_nodes.update(bb_nodes[block])
                    blocks_name += '_' + str(block)
            elif isinstance(blocks, str):
                basic_block_nodes.update(bb_nodes[blocks])
                blocks_name += '_' + str(blocks)

            selected_graph_bb = forward_slice_graph.subgraph(basic_block_nodes)
            if self.should_be_saved(blocks_name, selected_graph_bb):
                chunk_file = function_name + '_{}{}.afs.bb{}.dot'.format(self.slice_root_nodes[slice_root_node],
                                                                         blocks_name,
                                                                         str(org_window_size))
                chunk_file = self.add_dependency_prefix(chunk_file)
                write_dot(selected_graph_bb, chunk_file)
        # elapsed_time = default_timer() - start_time
        # print 'finding subgraphs', elapsed_time
        # return all_graphs

    def should_be_saved(self, blocks_name, selected_graph_bb):
        block_nodes = self.get_sorted_nodes(selected_graph_bb)
        for item in self.bb_nodes[blocks_name]:
            if item == block_nodes:
                return False
        self.bb_nodes[blocks_name].append(block_nodes)
        return True

    def get_sorted_nodes(self, selected_graph_bb):
        nodes = list(selected_graph_bb.nodes)
        nodes.sort()
        return nodes

    def find_ngrams(self, input_list, n):
        return zip(*[input_list[i:] for i in range(n)])

    def extract_forward_backward_slices(self, forward_slice_graph, slice_root_node, function_name):
        revere_simplified_pdg_graph = self.simplified_pdg_graph.reverse()
        # root_successors = revere_simplified_pdg_graph.successors(slice_root_node)
        # for succ_node in root_successors:
        #     revere_simplified_pdg_graph.remove_node(succ_node)
        leaf_nodes = [n for n, d in forward_slice_graph.out_degree() if d == 0]

        forward_backward_slice_graph = nx.DiGraph()
        for leaf_node in leaf_nodes:
            leaf_node_slice_graph = nx.ego_graph(revere_simplified_pdg_graph, leaf_node, radius=1000000000)
            forward_backward_slice_graph.add_nodes_from(leaf_node_slice_graph.nodes(data=True))
            forward_backward_slice_graph.add_weighted_edges_from(leaf_node_slice_graph.edges)
        slice_file = function_name + '_{}.fbs.dot'.format(self.slice_root_nodes[slice_root_node])
        slice_file = self.add_dependency_prefix(slice_file)
        write_dot(forward_backward_slice_graph.reverse(), slice_file)

    def get_abstract_slice(self, slice_graph, slice_root_node, function_name, var_name):
        # slice_graph.remove_node(slice_root_node)
        nodes = list(slice_graph.nodes)
        removed_nodes = []
        for node in nodes:
            node_info = slice_graph.node[node]
            if 'label' not in node_info:
                removed_nodes.append(node)
            else:
                label_parts = node_info['label']
                # if label_parts.startswith('[f] GLOB IN '):
                #    removed_nodes.append(node)
                #    continue
                label_parts = label_parts.replace('[f] GLOB IN', ' ')
                label_parts = label_parts.replace('[f] IN ARG', ' ')
                label_parts = label_parts.replace(',', ' ')
                label_parts = label_parts.replace('(', ' ')
                label_parts = label_parts.replace(')', ' ')
                label_parts = label_parts.replace('[', ' ')
                label_parts = label_parts.replace(']', ' ')
                label_parts = label_parts.replace('{', ' ')
                label_parts = label_parts.replace('}', ' ')
                label_parts = label_parts.replace('"', '')
                label_parts = label_parts.replace('=', '')
                label_parts = label_parts.replace(' metadata ', ' ')
                label_parts = label_parts.split()
                kept_parts = []
                removed_node_flag = False
                for i in range(len(label_parts)):
                    # label_part = str(label_part)
                    label_part = str(label_parts[i])
                    if label_part.startswith('@') and label_part[1:] in self.global_vars:
                        continue
                    if '%' in label_part:
                        if '%struct.' in label_part:
                            kept_parts.append(label_part)

                    #    removed_node_flag = True
                    #    removed_nodes.append(node)
                    #    break
                    # elif 'global' in label_part:
                    #    kept_parts.append('alloca')
                    elif '@.str.' in label_part:
                        kept_parts.append('@.str')
                    # elif is_number(label_part) and label_parts[1] == 'icmp':
                    #    kept_parts.append(label_part)
                    elif label_part != 'align' \
                            and not is_number(label_part) \
                            and 'subgraphs' != label_part and '!' not in label_part \
                            and '#' not in label_part and '...' not in label_part \
                            and '~' not in label_part and '$' not in label_part and not label_part.startswith('0x'):
                        # if i == len(label_parts) - 1:
                        #     if not label_part.startswith('0x'):
                        #         kept_parts.append(label_part)
                        # else:
                        #     kept_parts.append(label_part)
                        kept_parts.append(label_part)

                if not removed_node_flag:
                    slice_graph.node[node]['label'] = ' '.join(kept_parts)
                    # Save line number
                    if 'labelURL' in slice_graph.node[node]:
                        line_number = slice_graph.node[node]['labelURL'].split(':')[-2]
                        slice_graph.node[node]['line'] = line_number
                        del slice_graph.node[node]['labelURL']
                # print node_info['label']

        for node in removed_nodes:
            slice_graph.remove_node(node)
        afs_file = function_name + '_{}.afs.dot'.format(var_name)
        afs_file = self.add_dependency_prefix(afs_file)
        write_dot(slice_graph, afs_file)
        # self.render_pdf_graph(afs_file)

    def find_basic_blocks_nodes_pydot(self):
        graph = pydot.graph_from_dot_file(self.pdg_graph_file)
        # self.nodes_bb = {}
        for item in graph[0].get_subgraphs():
            if not item.obj_dict['name'].startswith('cluster_bb_'):
                for cluster in item.get_subgraphs():
                    if cluster.obj_dict['name'].startswith('cluster_bb_'):
                        basic_block_id = cluster.obj_dict['name'].split('_')[-1]
                        for node in cluster.obj_dict['nodes'].keys():
                            self.pdg_graph.nodes[node]['basic_block_id'] = str(basic_block_id)
                            # self.nodes_bb[node] = str(basic_block_id)
                    else:
                        print 'Dot file has a strange cluster', self.pdg_graph_file
            else:
                print 'Dot file has a strange subgraph', self.pdg_graph_file

    def find_basic_blocks_nodes(self):
        try:
            # lines = read_lines(file_path=self.pdg_graph_file)
            self.bb_first_last_nodes = defaultdict(list)
            node_counter = 0
            with open(self.pdg_graph_file) as fp:
                checked_one_bb = False
                basic_block_id = ''
                node = ''
                for cnt, line in enumerate(fp):
                    line_trimmed = line.strip()
                    if line_trimmed.startswith('subgraph'):
                        subgraph_name = line_trimmed.split()[1]
                        if subgraph_name.startswith('cluster_bb_'):
                            basic_block_id = subgraph_name.split('_')[-1]
                            checked_one_bb = True
                            node_counter = 0
                    elif line_trimmed == '} /* cluster_bb_' + basic_block_id + ' */':
                        self.bb_first_last_nodes[basic_block_id].append(node)
                        basic_block_id = ''

                    if basic_block_id != '':
                        if line_trimmed.startswith('NODE0x'):
                            node = line_trimmed.split()[0]
                            if node_counter == 0:
                                self.bb_first_last_nodes[basic_block_id].append(node)
                            # self.nodes_bb[str(basic_block_id)].append(node)
                            self.pdg_graph.nodes[node]['basic_block_id'] = str(basic_block_id)
                            node_counter += 1

                    if checked_one_bb is True and line_trimmed.startswith('/* -- node'):
                        # print self.bb_first_last_nodes
                        break
        except Exception, e:
            print e.message

    def add_dependency_prefix(self, graph_file):
        # if graph_file
        if self.arguments.has_control_flow:
            prefix = '_CDD_'
        else:
            prefix = '_ODD_'
        return join_path(get_parent_dir(graph_file), prefix + get_basename(graph_file))
