#
# Imports
#
import json
import yaml
import inspect
from src.libs.Workload import Workload

def read_config(tests_yaml_path, test_config_dict):
    # Reading test specific configurations
    test_name = inspect.stack()[1].function

    with open(tests_yaml_path, "r") as fd:
        try:
            yaml_test_config = yaml.safe_load(fd)
        except yaml.YAMLError as exc:
            print(exc)

    test_config_dict.update(yaml_test_config['Default'])

    if yaml_test_config.get(test_name):
        test_config_dict.update(yaml_test_config[test_name])
        test_config_dict['test_name'] = test_name
    
    print("\n-- Updated Test Configuration Data : \n", test_config_dict)


def run_test(test_config_dict):

    test_obj = Workload(test_config_dict)
    
    #Update final test config from command line arguments
    test_obj.update_test_config_from_cmd_line(test_config_dict)
    
    test_obj.pre_actions(test_config_dict)






