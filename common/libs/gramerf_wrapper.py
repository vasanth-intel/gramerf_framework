import inspect
import time
from common.libs.workload import Workload
from common.config_files.constants import *
from common.libs import utils
from conftest import trd


def read_perf_suite_config(test_instance, test_yaml_file, test_name):
    # Reading workload specific data.
    test_config_dict = {}
    yaml_test_config = utils.read_config_yaml(test_yaml_file)
    test_config_dict.update(yaml_test_config['Default'])

    # Updating config for test specific data.
    if yaml_test_config.get(test_name):
        test_config_dict.update(yaml_test_config[test_name])
        test_config_dict['test_name'] = test_name

    test_config_dict['iterations'] = int(os.environ['iterations'])
    test_config_dict['exec_mode'] = os.environ['exec_mode'].split(",")

    print("\n-- Read the following Test Configuration Data : \n\n", test_config_dict)

    return test_config_dict


def run_test(test_instance, test_yaml_file):
    global trd
    test_name = inspect.stack()[1].function
    print(f"\n********** Executing {test_name} **********\n")
    test_config_dict = read_perf_suite_config(test_instance, test_yaml_file, test_name)
    utils.clear_system_cache()

    test_obj = Workload(test_config_dict)
    test_obj.pre_actions(test_config_dict)
    test_obj.setup_workload(test_config_dict)
    
    test_dict = {}
    time_dict = {}
    trd[test_config_dict['workload_name']] = trd.get(test_config_dict['workload_name'], {})
    for e_mode in test_config_dict['exec_mode']:
        print(f"\n-- Executing {test_config_dict['test_name']} in {e_mode} mode")
        test_dict[e_mode] = []
        start_time = time.time()
        test_obj.execute_workload(test_config_dict, e_mode, test_dict)
        time_dict[e_mode] = (time.time() - start_time) / 60
        trd[test_config_dict['workload_name']].update({test_config_dict['test_name']+'_time': time_dict})

    if len(test_dict[test_config_dict['exec_mode'][0]]) > 0:
        test_obj.update_test_results_in_global_dict(test_config_dict, test_dict)
    else:
        test_obj.process_results(test_config_dict)

    os.chdir(FRAMEWORK_HOME_DIR)
    
    return True
