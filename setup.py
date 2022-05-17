import os
import yaml
import pytest
from src.config_files import constants

def read_global_config():
    config_file_name = "config.yaml"
    config_file_path = os.path.join(constants.FRAMEWORK_HOME_DIR, 'src/config_files', config_file_name)
    with open(config_file_path, "r") as fd:
        try:
            test_config_dict = yaml.safe_load(fd)
        except yaml.YAMLError as exc:
            print(exc)

    return test_config_dict
    