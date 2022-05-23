import os
import yaml
import inspect
from src.config_files import constants

def read_perf_suite_config(test_obj, test_yaml_file):
    # Reading global config data.
    config_file_name = "config.yaml"
    config_file_path = os.path.join(constants.FRAMEWORK_HOME_DIR, 'src/config_files', config_file_name)
    with open(config_file_path, "r") as config_fd:
        try:
            test_config_dict = yaml.safe_load(config_fd)
        except yaml.YAMLError as exc:
            print(exc)

    # Reading workload specific data.
    with open(test_yaml_file, "r") as test_default_fd:
        try:
            yaml_test_config = yaml.safe_load(test_default_fd)
        except yaml.YAMLError as exc:
            print(exc)

    test_config_dict.update(yaml_test_config['Default'])

    # Reading test specific data.
    test_name = inspect.stack()[1].function

    if yaml_test_config.get(test_name):
        test_config_dict.update(yaml_test_config[test_name])
        test_config_dict['test_name'] = test_name

    # Reading command line overrides.
    if test_obj._config.getoption('--iterations') != 1:
        test_config_dict['iterations'] = test_obj._config.getoption('iterations')
    
    if test_obj._config.getoption('--exec_mode') != '' and test_obj._config.getoption('--exec_mode') != 'None':
        test_config_dict['exec_mode'] = test_obj._config.getoption('exec_mode').split(' ')

    print("\n-- Read the following Test Configuration Data : \n\n", test_config_dict)

    return test_config_dict
    