#
# Imports
#
import pytest
import os
from src.config_files.constants import *
from src.libs import utils
from src.libs import build_gramine

@pytest.fixture(scope="session")
def gramerf_setup():
    print("\n###### In gramerf_setup #####\n")
    
    cmd_out = utils.exec_shell_cmd('cc -dumpmachine')
    os.environ['ARCH_LIBDIR'] = "/lib/" + cmd_out.stdout.strip()
    # Delete old logs if any and create new logs directory.
    if os.path.exists(LOGS_DIR):
        del_logs_cmd = 'rm -rf ' + LOGS_DIR
        os.system(del_logs_cmd)
    
    os.makedirs(LOGS_DIR, exist_ok=True)
 
    # Set http and https proxies.
    utils.set_http_proxies()

    # Checkout gramine source and build the same.
    build_gramine.build_gramine_binaries()

    # Setting 'THREADS_CNT' env variable
    utils.set_threads_cnt_env_var()
        
       
def pytest_addoption(parser):
    print("\n##### In pytest_addoption #####\n")
    parser.addoption("--iterations", action="store", type=int, default=1)
    parser.addoption("--exec_mode", action="store", type=str, default="None")
    

