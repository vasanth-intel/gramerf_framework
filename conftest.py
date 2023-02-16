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


def read_command_line_args(config):
    os.environ["perf_config"] = config.option.perf_config
    os.environ["build_gramine"] = config.option.build_gramine
    os.environ["commit_id"] = config.option.commit_id
    os.environ["iterations"] = config.option.iterations
    os.environ["exec_mode"] = config.option.exec_mode
    os.environ["encryption"] = config.option.encryption


@pytest.fixture(scope="session")
def gramerf_setup(request):
    print("\n###### In gramerf_setup #####\n")
    read_command_line_args(request.config)

    # Delete old logs if any and create new logs directory.
    if os.path.exists(LOGS_DIR):
        del_logs_cmd = 'rm -rf ' + LOGS_DIR
        os.system(del_logs_cmd)
    if os.path.exists(PERF_RESULTS_DIR):
        del_logs_cmd = 'rm -rf ' + PERF_RESULTS_DIR
        os.system(del_logs_cmd)

    os.makedirs(LOGS_DIR, exist_ok=True)
    os.makedirs(PERF_RESULTS_DIR, exist_ok=True)

    # Setting up the node environment and clearing cache.
    utils.set_permissions()
    utils.set_http_proxies()
    utils.clean_up_system()
    
    if os.environ['perf_config'] == "baremetal":
        # Checkout gramine source and build the same.
        gramine_libs.install_gramine_binaries()
    else:
        print(f"\n-- Updating 'SSHPASS' env-var\n")
        os.environ['SSHPASS'] = "intel@123"

        curated_apps_lib.curated_setup()
        curated_apps_lib.copy_repo()

    yield

    # Generate the report using the global results dict.
    utils.generate_performance_report(trd)


def pytest_addoption(parser):
    print("\n##### In pytest_addoption #####\n")
    parser.addoption("--perf_config", action="store", type=str, default="baremetal", help="Bare-metal or Docker based execution.")
    parser.addoption("--build_gramine", action="store", type=str, default="source", help="Package or source based installation of Gramine.")
    parser.addoption("--commit_id", action="store", type=str, default="", help="Any specific commit-id for source based installation.")
    parser.addoption("--iterations", action="store", type=str, default='3', help="Number of times workload/benchmark app needs to be launched/executed.")
    # Following will be value of 'exec_mode' that would be expected by the framework.
    # For Redis workload: "native,gramine-direct,gramine-sgx-single-thread-non-exitless,gramine-sgx-diff-core-exitless"
    # For other workloads: "native,gramine-direct,gramine-sgx"
    parser.addoption("--exec_mode", action="store", type=str, default="native,gramine-direct,gramine-sgx", help="Workload execution modes.")
    parser.addoption("--encryption", action="store", type=str, default='0', help="Enable encryption for model/s before workload command execution.")
