#
# Imports
#
import json
import yaml
import inspect
import conftest

class test_config:
    # constructor
    def __init__(self, dict_obj):
        self.__dict__.update(dict_obj)

   
def dict2obj(dict_instance):
    # using json.loads method and passing json.dumps
    # method and custom object hook as arguments
    return json.loads(json.dumps(dict_instance), object_hook=test_config)


def read_config(tests_yaml_path):
    # Reading test specific configurations
    test_name = inspect.stack()[1].function

    with open(tests_yaml_path, "r") as fd:
        try:
            yaml_test_config = yaml.safe_load(fd)
        except yaml.YAMLError as exc:
            print(exc)

    print(conftest.test_config_dict)
    
    conftest.test_config_dict.update(yaml_test_config['Default'])

    if yaml_test_config.get(test_name):
        conftest.test_config_dict.update(yaml_test_config[test_name])
        conftest.test_config_dict['test_name'] = test_name
        print ("\n\n Test Name = ", conftest.test_config_dict['test_name'])


def run_test(test_obj):
    #Update final test config from command line arguments
    test_obj.update_test_config_from_cmd_line()

    test_config_obj = dict2obj(conftest.test_config_dict)
    #tco = test_config_obj
    #print ("\n ########## Local ###########", tco.iterations)

    test_obj.pre_actions(test_config_obj)

    #print("\n\n", test_config_obj.iterations)
    #print("\n\n", test_config_obj.metrics[0])
    #print("\n\n", test_config_obj.model_dir)
    #print("\n\n", test_config_dict['model_dir'])
    #print("\n\n", test_config_dict)





