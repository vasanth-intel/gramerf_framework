#
# Imports
#
from tkinter.filedialog import test
import pytest
import os
from setup import read_global_config
from src.config_files import constants
from src.libs import utils
from src.libs import build_gramine

@pytest.fixture(scope="session")
def gramerf_setup():
    print("\n###### In gramerf_setup #####\n")

    test_config_dict = read_global_config()
    print("\n-- Following configuration read from global config..\n", test_config_dict)    

    # Delete old logs if any and create new logs directory.
    if os.path.exists(constants.LOGS_DIR):
        del_logs_cmd = 'rm -rf ' + constants.LOGS_DIR
        os.system(del_logs_cmd)
    
    os.makedirs(constants.LOGS_DIR, exist_ok=True)
 
    # Set http and https proxies.
    utils.set_http_proxies(test_config_dict)

    # Checkout gramine source and build the same.
    build_gramine.build_gramine_binaries(test_config_dict)
    
       
def pytest_addoption(parser):
    print("\n##### In pytest_addoption #####\n")
    parser.addoption("--iterations", action="store", type=int, default=1)
    parser.addoption("--exec_mode", action="store", type=str, default="None")

