import pytest
from src.config_files.constants import *
from src.libs import utils
from src.libs import gramine_libs


@pytest.fixture(scope="session")
def gramerf_setup():
    print("\n###### In gramerf_setup #####\n")
    
    cmd_out = utils.exec_shell_cmd('cc -dumpmachine')
    os.environ['ARCH_LIBDIR'] = "/lib/" + cmd_out
    # Delete old logs if any and create new logs directory.
    if os.path.exists(LOGS_DIR):
        del_logs_cmd = 'rm -rf ' + LOGS_DIR
        os.system(del_logs_cmd)
    
    os.makedirs(LOGS_DIR, exist_ok=True)
 
    # Setting up the node environment and clearing cache.    
    utils.set_http_proxies()
    utils.clear_system_cache()

    # Checkout gramine source and build the same.
    gramine_libs.build_gramine_binaries()


def pytest_addoption(parser):
    print("\n##### In pytest_addoption #####\n")
    parser.addoption("--iterations", action="store", type=int, default=1)
    parser.addoption("--exec_mode", action="store", type=str, default="None")
