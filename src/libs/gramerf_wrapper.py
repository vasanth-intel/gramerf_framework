#
# Imports
#
import inspect
from setup import read_perf_suite_config
from src.libs.Workload import Workload


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
