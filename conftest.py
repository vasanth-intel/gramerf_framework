import pytest
from common.config_files.constants import *
from common.libs import utils
from baremetal_benchmarking import gramine_libs
from docker_benchmarking import curated_apps_lib
from collections import defaultdict


# Global dictionary to hold the results of all the tests in the following format.
# Tests_results_dictionary (trd)
# {
#   Workload_name1: 
#       { test_name1: {native:[], direct:[], sgx:[], native-avg, direct-avg, sgx-avg, direct_degradation, sgx_degradation} }
#       { test_name2: {native:[], direct:[], sgx:[], native-avg, direct-avg, sgx-avg, direct_degradation, sgx_degradation} }
#   Workload_name2: 
#       { test_name1: {native:[], direct:[], sgx:[], native-avg, direct-avg, sgx-avg, direct_degradation, sgx_degradation} }
#       { test_name2: {native:[], direct:[], sgx:[], native-avg, direct-avg, sgx-avg, direct_degradation, sgx_degradation} }
#  }
trd = defaultdict(dict)


@pytest.fixture(scope="session")
def gramerf_setup(request):
    config = request.config
    perf_config = config.option.perf_config
    print("\n###### Executing in {} mode".format(perf_config))

    os.environ["perf_config"] = perf_config

    print("\n###### In gramerf_setup #####\n")
    
    cmd_out = utils.exec_shell_cmd('cc -dumpmachine')
    os.environ['ARCH_LIBDIR'] = "/lib/" + cmd_out
    # Delete old logs if any and create new logs directory.
    if os.path.exists(LOGS_DIR):
        del_logs_cmd = 'rm -rf ' + LOGS_DIR
        os.system(del_logs_cmd)
        del_logs_cmd = 'rm -rf ' + PERF_RESULTS_DIR
        os.system(del_logs_cmd)

    os.makedirs(LOGS_DIR, exist_ok=True)
    os.makedirs(PERF_RESULTS_DIR, exist_ok=True)

    # Setting up the node environment and clearing cache.    
    utils.set_http_proxies()
    utils.clear_system_cache()

    if perf_config == "baremetal":
        # Checkout gramine source and build the same.
        gramine_libs.install_gramine_binaries()
    else:
        curated_apps_lib.curated_setup()
        curated_apps_lib.copy_repo()

    yield

    # Generate the report using the global results dict.
    utils.generate_performance_report(trd)


def pytest_addoption(parser):
    print("\n##### In pytest_addoption #####\n")
    parser.addoption("--perf_config", action="store", type=str, default="baremetal")

