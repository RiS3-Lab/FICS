from act import Act
from sample.projectcode import ProjectCode
from utils.inout import *
from timeit import default_timer


class FeatureExtractor(Act):

    def start(self):
        projects_dir = join_path(self.arguments.data_dir, self.arguments.bcs_dir)
        datasets_dir = join_path(self.arguments.data_dir, self.arguments.datasets_dir)
        dir_names = get_directories(projects_dir)
        # feature_types = self.arguments.feature_types.split(',')
        for feature_type in self.arguments.feature_types:
            for dir_name in dir_names:
                for project_name in self.arguments.projects:
                    if get_basename(dir_name) == project_name or len(self.arguments.projects) == 0:
                        if self.arguments.split != 'True':
                            print 'Extracting {} features for {}'.format(feature_type, get_basename(dir_name))
                            project_code = ProjectCode(project_dir=dir_name, arguments=self.arguments,
                                                       feature_type=feature_type)
                            start_time = default_timer()
                            project_code.extract_features(save=True)
                            elapsed_time = default_timer() - start_time
                            time_file = join_path(datasets_dir, get_basename(dir_name),
                                                  '{}.feature_extraction.time.txt'.format(
                                                      feature_type))
                            print 'Feature Extraction Time:', elapsed_time
                            write_file(time_file, '{}'.format(elapsed_time))
                            # project_code.save_features()
                        else:
                            for module in get_directories(dir_name):
                                print 'Module:', get_basename(module)
                                project_code = ProjectCode(project_dir=dir_name, arguments=self.arguments,
                                                           feature_type=feature_type, module_name=get_basename(module))

                                start_time = default_timer()
                                project_code.extract_features(save=True)
                                elapsed_time = default_timer() - start_time
                                if project_code.num_abstract_slices != 0:
                                    time_file = join_path(datasets_dir, get_basename(dir_name),
                                                          '{}.{}.feature_extraction.time.txt'.format(
                                                              get_basename(module), feature_type))
                                    print 'Feature Extraction Time:', elapsed_time
                                    write_file(time_file, '{}'.format(elapsed_time))
                                    # project_code.save_features()
