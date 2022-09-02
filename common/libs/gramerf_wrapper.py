import inspect
from baremetal_benchmarking import gramine_libs
from docker_benchmarking import curated_apps_lib
from common.libs.workload import Workload
from common.config_files.constants import *
from common.libs import utils


def read_perf_suite_config(test_instance, test_yaml_file, test_name):
    # Reading global config data.
    config_file_name = "config.yaml"
    config_file_path = os.path.join(FRAMEWORK_HOME_DIR, 'common/config_files', config_file_name)

    # Reading global config and workload specific data.
    test_config_dict = utils.read_config_yaml(config_file_path)
    yaml_test_config = utils.read_config_yaml(test_yaml_file)
    test_config_dict.update(yaml_test_config['Default'])

    # Updating config for test specific data.
    if yaml_test_config.get(test_name):
        test_config_dict.update(yaml_test_config[test_name])
        test_config_dict['test_name'] = test_name

    print("\n-- Read the following Test Configuration Data : \n\n", test_config_dict)

    return test_config_dict


def run_test(test_instance, test_yaml_file):
    perf_config = os.getenv("perf_config")
    test_name = inspect.stack()[1].function
    print(f"\n********** Executing {test_name} **********\n")
    test_config_dict = read_perf_suite_config(test_instance, test_yaml_file, test_name)
    test_config_dict["perf_config"] = perf_config
    test_obj = Workload(test_config_dict)
    workload_home_dir = os.path.join(FRAMEWORK_HOME_DIR, test_config_dict['workload_home_dir'])
    os.chdir(workload_home_dir)
    test_obj.pre_actions(test_config_dict)
    test_obj.setup_workload(test_config_dict)
    test_obj.execute_workload(test_config_dict)
    os.chdir(FRAMEWORK_HOME_DIR)
    
    return True
