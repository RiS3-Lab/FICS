import hashlib
from sre_parse import Pattern
from tokenize import String

import paramiko
import re
from utils.inout import *
import sys
from settings import BENCHMARK_GROUNDTRUTH_PATH
sys.path.append(join_path(sys.path[0], BENCHMARK_GROUNDTRUTH_PATH))
print sys.path[0]
import sshtunnel
from collections import defaultdict
from pymongo import MongoClient
from sshtunnel import SSHTunnelForwarder
from act import Act
from groundtruth import ground_truth
from ssh_private_key_password import ip, username, password
from bson.objectid import ObjectId


class QueryInconsistency(Act):
    server = None
    ssh_client = None
    mongodb_client = None
    current_project = None
    ground_truth_items = 0

    def start(self):
        try:
            if self.arguments.ssh:
                self.establish_ssh_tunnel()
                self.mongodb_client = MongoClient('mongodb://localhost', self.server.local_bind_port)
            else:
                self.mongodb_client = MongoClient('mongodb://localhost:27017')
            fics_db = self.mongodb_client["fics"]
            for project_name in self.arguments.projects:
                print 'Project:', project_name
                self.current_project = project_name
                collection = fics_db[project_name]

                if len(self.arguments.ids) > 0 and '' not in self.arguments.ids:
                    self.arguments.inconsistency_type = 'all'
                    results = self.get_results_ids(collection=collection)
                    self.process_results(results)
                else:
                    print 'Inconsistency Type:', self.arguments.inconsistency_type
                    results = self.get_results(collection=collection)
                    self.process_results(results)

                if self.arguments.ssh:
                    self.ssh_client.close()

        except Exception, e:
            print e.message
            if self.arguments.ssh:
                self.server.stop()
            # client.close()
            # self.ssh_client.close()

    def establish_ssh_tunnel(self):

        remote_server_ip = ip

        self.server = SSHTunnelForwarder(
            remote_server_ip,
            ssh_username=username,
            ssh_pkey="~/.ssh/id_rsa",
            ssh_private_key_password=password,
            remote_bind_address=('127.0.0.1', 27017)
        )

        self.server.start()

    def establish_ssh_client(self):

        if self.ssh_client is None:
            remote_server_ip = ip
            self.ssh_client = paramiko.SSHClient()
            self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.ssh_client.connect(remote_server_ip, port=22, username=username, password=password,
                                    key_filename='{}/.ssh/id_rsa'.format(os.getenv("HOME")))

    def get_results_ids(self, collection):

        granularity_queries = []
        for inconsistency_id in self.arguments.ids:
            query = {'_id': ObjectId(inconsistency_id)}
            granularity_queries.append(query)
        query = {'$or': granularity_queries}

        return collection.find(query)

    def get_results(self, collection):
        threshold = self.arguments.similarity_threshold

        dependency = ''
        if self.arguments.dependency.upper() == 'ODD' or self.arguments.dependency.upper() == 'CDD':
            dependency = '_{}_'.format(self.arguments.dependency.upper())

        granularity_queries = []
        for granularity in self.arguments.granularity:
            query = {'firststep_threshold': {'$gte': threshold},
                     'construct_type': granularity}
            if dependency != '':
                query['dependency'] = dependency
            granularity_queries.append(query)
        query = {'$or': granularity_queries}

        print 'Total Number of reported inconsistencies:', \
            collection.find(query).count()
        if self.arguments.inconsistency_type == 'check':
            # db.getCollection('benchmark').find({subclusters: {$elemMatch: {constructs:{$elemMatch: {node_diffs:{
            # $elemMatch: {node_name:{$regex : "icmp .*"}}}}}}}})
            granularity_queries = []
            for granularity in self.arguments.granularity:
                query = {'subclusters': {'$elemMatch':
                    {'constructs': {'$elemMatch':
                        {'node_diffs': {'$elemMatch':
                            {'node_name': {
                                '$regex': "^icmp .*"}}}}}}}, 'firststep_threshold': {'$gte': threshold},
                    'construct_type': granularity}
                if dependency != '':
                    query['dependency'] = dependency
                granularity_queries.append(query)
            query = {'$or': granularity_queries}

        elif self.arguments.inconsistency_type == 'store':
            # db.getCollection('benchmark').find({subclusters: {$elemMatch: {constructs:{$elemMatch: {node_diffs:{
            # $elemMatch: {node_name:{$regex : "icmp .*"}}}}}}}})
            granularity_queries = []
            for granularity in self.arguments.granularity:
                for store_inconsistency in self.arguments.store_inconsistency:
                    query = {'subclusters': {'$elemMatch':
                        {'constructs': {'$elemMatch':
                            {'node_diffs': {'$elemMatch':
                                {'node_name': {
                                    '$regex': "^store.* {} .*".format(store_inconsistency)}}}}}}},
                        'firststep_threshold': {'$gte': threshold},
                        'construct_type': granularity}
                    if dependency != '':
                        query['dependency'] = dependency
                    granularity_queries.append(query)
            query = {'$or': granularity_queries}

        elif self.arguments.inconsistency_type == 'call':
            queries = []
            for granularity in self.arguments.granularity:
                for call_inconsistency in self.arguments.call_inconsistency:
                    regex = "call .*@.*?{}.*?.*".format(call_inconsistency)
                    # regex = ".*{}.*".format(call_inconsistency)
                    single_query = {'subclusters': {'$elemMatch':
                        {'constructs': {'$elemMatch':
                            {'node_diffs': {'$elemMatch':
                                {'node_name': re.compile(
                                    regex, re.IGNORECASE)
                                    # {'$regex': regex}
                                }}}}}},
                        'firststep_threshold': {'$gte': threshold}, 'construct_type': granularity}
                    if dependency != '':
                        single_query['dependency'] = dependency
                    queries.append(single_query)
            query = {'$or': queries}

        elif self.arguments.inconsistency_type == 'type':
            queries = []
            for granularity in self.arguments.granularity:
                for type_inconsistency in self.arguments.type_inconsistency:
                    single_query = {'subclusters': {'$elemMatch':
                        {'constructs': {'$elemMatch':
                            {'node_diffs': {'$elemMatch':
                                {'node_name': {
                                    '$regex': "^{} .*".format(type_inconsistency)}}}}}}}
                        , 'firststep_threshold': {'$gte': threshold}, 'construct_type': granularity}
                    if dependency != '':
                        single_query['dependency'] = dependency
                    queries.append(single_query)
            query = {'$or': queries}

        elif self.arguments.inconsistency_type == 'order':
            granularity_queries = []
            for granularity in self.arguments.granularity:
                query = {'subclusters': {'$elemMatch':
                                             {'constructs': {'$elemMatch':
                                                                 {'node_diffs': {'$size': 0}}}}},
                         'firststep_threshold': {'$gte': threshold}, 'construct_type': granularity}
                if dependency != '':
                    query['dependency'] = dependency
                granularity_queries.append(query)
            query = {'$or': granularity_queries}

        elif self.arguments.inconsistency_type == 'all':
            granularity_queries = []
            for granularity in self.arguments.granularity:
                query = {'firststep_threshold': {'$gte': threshold}, 'construct_type': granularity}
                if dependency != '':
                    query['dependency'] = dependency
                granularity_queries.append(query)
            query = {'$or': granularity_queries}

        else:
            print 'Inconsistency Type is unknown.'
            return None

        return collection.find(query)

    def process_results(self, results):
        print 'Total Number of {} inconsistencies (No filtering): {}'.format(self.arguments.inconsistency_type,
                                                                             results.count())
        local_results = self.filter_results(results)
        if self.arguments.ssh:
            self.server.stop()
            self.establish_ssh_client()
        self.mongodb_client.close()
        raw_input("Press Enter to show the inconsistencies...")
        os.system('clear')

        count = 1
        for result in local_results:
            if count < self.arguments.starting_report_item:
                count += 1
                continue
            if result['dependency'] == '_ODD_':
                dependency = 'Data Flow'
            else:
                dependency = 'Control&Data Flow'
            print
            print 'Inconsistency #{} , '.format(count), \
                'Total subclusters: ({}) , '.format(len(result['subclusters'])), \
                'Granularity: ({}) , '.format(result['construct_type']), \
                'Similarity: ({}) , '.format(result['firststep_threshold']), \
                'ID: {} , '.format(result['_id']), \
                'Dependency: {}'.format(dependency)
            print '=' * 80
            subcluster_count = 0

            for subcluster in result['subclusters']:
                print 'Subcluster #{} , '.format(subcluster_count), \
                    'Total items: ({})'.format(subcluster['constructs_total'])
                construct_counter = 1
                for construct in subcluster['constructs']:
                    # print construct['graph_path']
                    # get_basename(construct['graph_path']).split('.pdg_')[0])
                    # print construct['lines']

                    if construct_counter > 1:
                        self.read_lines_of_code(construct, True)
                    else:
                        print '-' * 50
                        self.read_lines_of_code(construct)
                        print '-' * 50
                    # We break here because we only show one construct in each cluster to make the output more readable
                    # break
                    # We just show the line numbers of the rest of constructs
                    construct_counter += 1
                subcluster_count += 1
                print '+' * 80
            # if count % 2 == 0:
            raw_input("Press Enter to continue...")
            os.system('clear')
            count += 1

    def filter_results(self, results):
        existing_inconsistencies = self.get_ground_truth()
        found_inconsistencies = defaultdict(list)
        missed_bugs_ids = {}
        filtered_results = []
        count = 0
        # Benchmark
        # many_subclusters_threshold = 7
        # important_number_of_diffs_threshold = 2
        # important_number_of_diffs_lines_threshold = 2

        # Real program
        many_subclusters_threshold = 5
        important_number_of_diffs_threshold = 2
        important_number_of_diffs_lines_threshold = 2

        unique_result_hashes = []
        for result in results:
            important_number_of_diffs = 0
            important_number_of_diffs_lines = 0
            result['skip'] = False
            result_string = ''
            result_string_source_files = list()
            result_string_function_names = list()
            result_string_lines = list()
            if len(result['subclusters']) > many_subclusters_threshold:
                result['skip'] = True
                # continue
            source_codes = set()
            function_names = set()
            variable_names = set()
            code_lines = []
            node_diff_lines = set()
            all_code_lines = set()
            max_len = 0
            code_lines_intersection = set()
            for subcluster in result['subclusters']:
                for construct in subcluster['constructs']:
                    source_codes.add(construct['source_file_path'])
                    names = get_basename(construct['graph_path']).split('.pdg_')
                    function_name = names[0]
                    function_names.add(function_name[5:])
                    variable_name = names[1].split('.afs')[0]
                    variable_name = variable_name.split('_0x')[0]
                    variable_name = variable_name[5:]
                    variable_names.add(variable_name)
                    lines = set(construct['lines'])
                    if max_len == 0:
                        code_lines_intersection = lines
                    else:
                        code_lines_intersection = code_lines_intersection.intersection(lines)
                    if len(lines) > max_len:
                        max_len = len(lines)
                    code_lines.append(set(construct['lines']))
                    all_code_lines.update(set(construct['lines']))
                    important_number_of_diffs = 0

                    for node_diff in construct['node_diffs']:
                        for line in node_diff['lines']:
                            node_diff_lines.add(int(line))
                        if self.is_important(node_diff['node_name']):
                            important_number_of_diffs += 1
                            if len(node_diff['lines']) > important_number_of_diffs_lines:
                                important_number_of_diffs_lines = len(node_diff['lines'])

                    result_string_source_files.append(construct['source_file_path'])
                    result_string_function_names.append(function_name[5:])
                    result_string_lines += construct['lines']

                    # print '-' * 100
            # print source_codes
            # print function_names
            # print variable_names

            if important_number_of_diffs > important_number_of_diffs_threshold or \
                    important_number_of_diffs_lines > important_number_of_diffs_lines_threshold:
                result['skip'] = True
                # continue

            if len(source_codes) == 1 and len(function_names) == 1:
                # print len(code_lines_intersection), max_len
                ratio = len(code_lines_intersection) * 1.0 / max_len
                # print ratio
                # ratio is the threshold.
                if ratio > 0:
                    result['skip'] = True
                    # continue

            result_string_source_files.sort()
            result_string_function_names.sort()
            result_string_lines.sort()

            result_string += ', '.join(result_string_source_files)
            result_string += ', '.join(result_string_function_names)
            result_string += ', '.join(str(result_string_lines))

            result_hash = hashlib.sha1(result_string).hexdigest()
            if result_hash in unique_result_hashes:
                result['skip'] = True
                # continue
            else:
                unique_result_hashes.append(result_hash)

            if self.arguments.inconsistency_type == 'order':
                if self.check_same_inconsistencies(result):
                    result['skip'] = True
                    # continue

            if (not result['skip'] and self.arguments.filtering) or (not self.arguments.filtering):
                count += 1
                for item in existing_inconsistencies:
                    result1 = all(elem in node_diff_lines for elem in item['line_diffs'])
                    result2 = all(elem in source_codes for elem in item['files'])
                    result3 = all(elem in function_names for elem in item['functions'])
                    result4 = all(elem in all_code_lines for elem in item['lines_no_diff'])

                    if result1 and result2 and result3 and result4:
                        found_inconsistencies[item['id']].append(str(result['_id']))
                    else:
                        missed_bugs_ids[item['id']] = 0
                filtered_results.append(result)
            # If the results before filtering should be shown, you can comment the below else
            # else:
            #     continue

        if self.ground_truth_items > 0:
            print '{} bugs found by our system'.format(len(found_inconsistencies))
            found_ids = found_inconsistencies.keys()
            found_ids.sort()
            print '-' * 20
            print 'Ids of detected bugs:'
            print '-' * 20
            print
            for found_id in found_ids:
                found_ids_tmp = found_inconsistencies[found_id]
                print found_id, ':', ','.join(found_ids_tmp)

            missed_bugs = missed_bugs_ids.keys()
            missed_bugs = list(set(missed_bugs) - set(found_ids))
            print '-' * 20
            print 'Ids of missed bugs:'
            print '-' * 20
            print missed_bugs

        if self.arguments.filtering:
            print 'Total Number of inconsistencies after filtering:', count

        return filtered_results

    def check_same_inconsistencies(self, result):
        source_code_hashes = set()
        for subcluster in result['subclusters']:
            for construct in subcluster['constructs']:

                source_code_string = ''
                source_file_path = construct['source_file_path']

                if self.arguments.ssh:
                    self.establish_ssh_client()
                    sftp_client = self.ssh_client.open_sftp()
                    remote_file = sftp_client.open(source_file_path)
                    try:
                        line_numbers = construct['lines']
                        line_number = 1
                        for line in remote_file:
                            if line_number in line_numbers:
                                source_code_string += line.strip()
                            line_number += 1
                    finally:
                        remote_file.close()
                else:
                    local_file = open(source_file_path)
                    try:
                        line_numbers = construct['lines']
                        line_number = 1
                        for line in local_file:
                            if line_number in line_numbers:
                                source_code_string += line.strip()
                            line_number += 1
                    except:
                        pass

                source_code_hash = hashlib.sha1(source_code_string).hexdigest()
                source_code_hashes.add(source_code_hash)

        if len(source_code_hashes) == 1:
            return True
        return False

    def read_lines_of_code(self, construct, only_line_number=False):

        file_info = '{} ({}) ({})'.format(construct['source_file_path'], construct['function_name'],
                                          construct['variable_name'])
        print construct['graph_path']
        if only_line_number:
            print file_info, construct['lines']
            return
        else:
            print file_info

        if self.arguments.ssh:
            sftp_client = self.ssh_client.open_sftp()
            remote_file = sftp_client.open(construct['source_file_path'])
            try:
                line_numbers = construct['lines']
                margin_line_numbers = set()
                for line in line_numbers:
                    line_before = line - 1
                    line_after = line + 1
                    margin_line_numbers.add(line_after)
                    margin_line_numbers.add(line_before)
                margin_line_numbers = list(margin_line_numbers - set(line_numbers))
                line_number = 1
                for line in remote_file:
                    if line_number in line_numbers:
                        self.print_line(line, line_number, construct)
                    if line_number in margin_line_numbers:
                        self.print_line(line, line_number, construct, margin=True)
                    line_number += 1
            finally:
                remote_file.close()
        else:
            local_file = open(construct['source_file_path'])
            try:
                line_numbers = construct['lines']
                margin_line_numbers = set()
                for line in line_numbers:
                    line_before = line - 1
                    line_after = line + 1
                    margin_line_numbers.add(line_after)
                    margin_line_numbers.add(line_before)
                margin_line_numbers = list(margin_line_numbers - set(line_numbers))
                line_number = 1
                for line in local_file:
                    if line_number in line_numbers:
                        self.print_line(line, line_number, construct)
                    if line_number in margin_line_numbers:
                        self.print_line(line, line_number, construct, margin=True)
                    line_number += 1
            except:
                pass

    def print_line(self, line, line_number, construct, margin=False):
        line = line.strip()
        if line == '':
            return

        if margin:
            print bcolors.GREY + '{}: {}'.format(line_number, line.strip()) + bcolors.ENDC
            return

        if self.arguments.inconsistency_type == 'check':
            for node_diff in construct['node_diffs']:
                # print node_diff
                if node_diff['node_name'].startswith('icmp'):
                    if str(line_number) in node_diff['lines']:
                        print bcolors.FAIL + '{}: {}'.format(line_number, line) + bcolors.ENDC
                        return
        elif self.arguments.inconsistency_type == 'store':
            for node_diff in construct['node_diffs']:
                # print node_diff
                for store_inconsistency in self.arguments.store_inconsistency:
                    if node_diff['node_name'].startswith('store') and \
                            store_inconsistency in node_diff['node_name']:
                        if str(line_number) in node_diff['lines']:
                            print bcolors.FAIL + '{}: {}'.format(line_number, line) + bcolors.ENDC
                            return
        elif self.arguments.inconsistency_type == 'call':
            for call_inconsistency in self.arguments.call_inconsistency:
                for node_diff in construct['node_diffs']:
                    node_diff_name = node_diff['node_name'].lower()
                    result = re.search('call .*@.*{}.*'.format(call_inconsistency), node_diff_name)
                    if result is not None:
                        if str(line_number) in node_diff['lines']:
                            print bcolors.FAIL + '{}: {}'.format(line_number, line) + bcolors.ENDC
                            return

        elif self.arguments.inconsistency_type == 'type':
            for node_diff in construct['node_diffs']:
                for type_inconsistency in self.arguments.type_inconsistency:
                    if node_diff['node_name'].startswith(type_inconsistency):
                        if str(line_number) in node_diff['lines']:
                            print bcolors.FAIL + '{}: {}'.format(line_number, line) + bcolors.ENDC
                            return

        print bcolors.OKBLUE + '{}: {}'.format(line_number, line.strip()) + bcolors.ENDC

    def get_ground_truth(self):
        items = []
        for item in ground_truth:
            if self.arguments.inconsistency_type == item['type'] and item['benchmark'] == self.current_project:
                items.append(item)
        self.ground_truth_items = len(items)
        if self.ground_truth_items > 0:
            print '{} bugs in the ground-truth dataset'.format(len(items))
        return items

    def is_important(self, node_diff_label):
        node_diff_label = node_diff_label.lower()
        if self.arguments.inconsistency_type == 'type':
            for type_inconsistency in self.arguments.type_inconsistency:
                if node_diff_label.startswith(type_inconsistency):
                    return True

        if self.arguments.inconsistency_type == 'check':
            if node_diff_label.startswith('icmp'):
                return True

        if self.arguments.inconsistency_type == 'store':
            if node_diff_label.startswith('store'):
                return True

        if self.arguments.inconsistency_type == 'call':
            for call_inconsistency in self.arguments.call_inconsistency:
                result = re.search('call .*@.*{}.*'.format(call_inconsistency), node_diff_label)
                if result is not None:
                    return True

        return False
