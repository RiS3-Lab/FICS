from act import Act
from learning.statistics import Statistics
from utils.inout import *


class GetStatistics(Act):

    def start(self):
        if self.arguments.stat_type == 'VI':
            datasets_dir = join_path(self.arguments.data_dir, self.arguments.datasets_dir)
            cluster_files = get_files_in_dir(datasets_dir, ext='.clusters.txt')
            for cluster_file in cluster_files:
                for project_name in self.arguments.projects:
                    if get_basename(get_parent_dir(get_parent_dir(cluster_file))) == project_name or \
                            len(self.arguments.projects) == 0:
                        print cluster_file
                        statistics = Statistics(arguments=self.arguments,
                                                project_clusters_info_file=cluster_file)
                        statistics.print_vul_info()

        elif self.arguments.stat_type == 'SI':
            projects_dir = join_path(self.arguments.data_dir, self.arguments.bcs_dir)
            dir_names = get_directories(projects_dir)
            for dir_name in dir_names:
                for project_name in self.arguments.projects:
                    if get_basename(dir_name) == project_name or len(self.arguments.projects) == 0:
                        statistics = Statistics(arguments=self.arguments, project_dir=dir_name)
                        statistics.print_slices_info()

        elif self.arguments.stat_type == 'SS':
            projects_dir = join_path(self.arguments.data_dir, self.arguments.projects_dir)
            dir_names = get_directories(projects_dir)
            for dir_name in dir_names:
                for project_name in self.arguments.projects:
                    if get_basename(dir_name) == project_name or len(self.arguments.projects) == 0:
                        statistics = Statistics(arguments=self.arguments, project_dir=dir_name)
                        statistics.print_slices_similarities()

        elif self.arguments.stat_type == 'ST':
            projects_dir = join_path(self.arguments.data_dir, self.arguments.projects_dir)
            time_data_min = {}
            time_data_hour = {}
            project_name_mapping = {'libpcap-545e77d8': 'libpcap', 'libtiff-19f6b70d': 'libtiff',
                                    'mbedtls-0592ea7': 'mbedtls', 'openssh-c2fa53c': 'openssh',
                                    'openssl-a75be9f': 'openssl', 'nginx-0098761': 'nginx',
                                    'wolfssl-c26cb53': 'wolfssl'}
            for project_name in self.arguments.projects:
                project_dir = join_path(projects_dir, project_name)
                statistics = Statistics(arguments=self.arguments, project_dir=project_dir)

                if project_name in project_name_mapping.keys():
                    project_name = project_name_mapping[project_name]
                time_data_min[project_name], time_data_hour[project_name] = statistics.print_performance_time()

            Statistics.draw_bar_chart(self.arguments, time_data_min, time_data_hour)
