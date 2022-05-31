#
# Imports
#
import os
import yaml
import inspect
from src.libs.Workload import Workload
from src.config_files import constants

def read_perf_suite_config(test_instance, test_yaml_file, test_name):
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
    if yaml_test_config.get(test_name):
        test_config_dict.update(yaml_test_config[test_name])
        test_config_dict['test_name'] = test_name

    # Reading command line overrides.
    if test_instance._config.getoption('--iterations') != 1:
        test_config_dict['iterations'] = test_instance._config.getoption('iterations')
    
    if test_instance._config.getoption('--exec_mode') != '' and test_instance._config.getoption('--exec_mode') != 'None':
        test_config_dict['exec_mode'] = test_instance._config.getoption('exec_mode').split(' ')

    print("\n-- Read the following Test Configuration Data : \n\n", test_config_dict)

    return test_config_dict


def run_test(test_instance, test_yaml_file):

    test_name = inspect.stack()[1].function

    test_config_dict = read_perf_suite_config(test_instance, test_yaml_file, test_name)
    
    test_obj = Workload(test_config_dict)
    
    # Install and build workload.
    if not test_obj.pre_actions(test_config_dict):
        return False

    if test_obj.execute_workload(test_config_dict) == None:
        return False

    return True

    #return test_obj


# def calculate_perf_degradation(test_obj):

#     result = test_obj.parse_performance()

#     gramine_direct_degradation = result['native']/result['gramine-direct']

#     gramine_sgx_degradation = result['native']/result['gramine-sgx']

#     return 0