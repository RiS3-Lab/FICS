import json
import os
import shutil
import sys
from cgitb import grey
from os.path import join, normpath
from shutil import move, copy

import pandas as pd


def exist_file(file_path):
    return os.path.isfile(file_path)


def exist_dir(path):
    return os.path.isdir(path)


def make_dir_if_not_exist(path):
    if not exist_dir(path):
        os.makedirs(path)


def get_basename(file_path):
    return os.path.basename(file_path)


def join_path(*args):
    return normpath(join(*args))


def get_dataframe(file_path, columns=''):
    try:
        dataframe = pd.read_csv(file_path)
    except:
        with open(file_path, 'w') as f:
            f.write(columns)
            f.close()
        dataframe = pd.read_csv(file_path)
    return dataframe


def show_error(message):
    print
    print '*' * 50
    print 'Error: {}'.format(message)
    sys.exit(2)


def get_current_directory():
    current_path = os.getcwd()
    return current_path


def change_directory(directory):
    os.chdir(directory)


def load_from_csv(modes_files_path, file_path, separated=False):
    mode_file_path = modes_files_path + '/' + file_path
    mode_file = pd.read_csv(mode_file_path, delimiter=',')
    if separated is True:
        mode_feature_vectors = mode_file.ix[:, :-1]
        mode_class_labels = mode_file.ix[:, -1]

        return mode_feature_vectors, mode_class_labels
    else:
        return mode_file


def get_directories(directory_path):
    return [join_path(directory_path, i) for i in os.listdir(directory_path) if not i.startswith('.')]


def remove_file(file_name):
    os.remove(file_name)


def remove_directory(dir_name):
    if exist_dir(dir_name):
        shutil.rmtree(dir_name)


def move_file(src_file, dst_file):
    move(src_file, dst_file)


def copy_file(src_file, dst_file):
    copy(src_file, dst_file)


def get_parent_dir(file_name):
    return os.path.dirname(file_name)


def is_file(file_name):
    return os.path.isfile(file_name)


def get_files_in_dir(dir, ext='', search_spaces=[], start=''):
    files = []
    for path, sub_dirs, file_names in os.walk(dir):

        for file_name in file_names:
            if file_name.endswith(ext) and file_name.startswith(start):
                in_search_space = False
                if len(search_spaces) == 0:
                    in_search_space = True
                for search_space in search_spaces:
                    if search_space in path:
                        in_search_space = True
                if not in_search_space:
                    continue
                files.append(join_path(path, file_name))

    return files


def get_cfiles_compile_db(compile_db):
    cfiles = {}
    for json_values in compile_db:
        if 'file' in json_values:
            file_path = join_path(json_values['directory'], json_values['file'])
            # print file_path
            if file_path.endswith(".c"):
                final_args = []
                if 'arguments' in json_values:
		    args = list(json_values['arguments'])
		else:
		    args = [item for item in json_values['command'].split() if not item.endswith('.o') and not item.endswith('.c')]
                remove_items = ('-c', 'cc', '-o', '-g')
                for remove_item in remove_items:
                    if remove_item in args:
                        args.remove(remove_item)

                for i in range(len(args)):
                    arg = args[i]
                    if arg.startswith('-I.') or arg.startswith('-I..'):
                        arg = '-I' + join_path(json_values['directory'], arg[2:])
                    if arg == '.' or arg == '..':
                        arg = join_path(json_values['directory'], arg)
                    final_args.append(arg)

                cfiles[file_path] = final_args
		# print file_path, final_args
            else:
                print "Not a C file:", file_path

    return cfiles


def read_file(file_name):
    with open(file_name, 'r') as f:
        return f.read()


def write_file(file_name, content):
    with open(file_name, 'w') as f:
        f.write(content)
        f.close()


def write_file_json(file_name, content):
    with open(file_name, 'w') as f:
        json.dump(content, f)
        f.close()


def get_filename_without_ext(file_name):
    return os.path.splitext(file_name)[0]


def load_json(file_path):
    return json.load(open(file_path))


def load_json_file(file_path):
    with open(file_path) as f:
        json_content = eval(f.read())
        return json_content


def get_arguments(file_path, json_data):
    for json_values in json_data:
        if 'file' in json_values:
            if join_path(json_values['directory'], json_values['file']) == file_path:
                args = list(json_values['arguments'])
                for i in range(len(args)):
                    arg = args[i]
                    if arg.startswith('-I./'):
                        arg = '-I{}'.format(arg[4:])
                    if arg.startswith('-I..'):
                        parent_include = json_values['directory']
                        include_path = arg[2:]
                        for item in range(arg.count('..')):
                            parent_include = get_parent_dir(parent_include)
                            include_path = include_path[3:]
                        parent_include = join_path(parent_include, include_path)
                        args[i] = '-I{}'.format(parent_include)
                remove_items = ('-c', 'cc', '-o')
                for item in remove_items:
                    if item in args:
                        args.remove(item)
                return args

    # print file_path
    return None


def check_missing_files(c_files, json_data):
    for json_values in json_data:
        flag = 0
        for c_file in c_files:
            if 'file' in json_values:
                if join_path(json_values['directory'], json_values['file']) == c_file:
                    flag = 1
        if flag == 0:
            if 'file' in json_values:
                print join_path(json_values['directory'], json_values['file'])
            elif 'files' in json_values:
                print json_values['directory'], json_values['files']


def read_lines(file_path):
    with open(file_path) as f:
        content = f.readlines()
    return [x.strip() for x in content]


def read_csv_header(file_path):
    first_row = pd.read_csv(file_path, index_col=0, nrows=1)
    return first_row.columns.values


class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    GREY = '\033[90m'
