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
    os.environ["gramine_repo"] = config.option.gramine_repo
    os.environ["gramine_commit"] = config.option.gramine_commit
    os.environ["gsc_repo"] = config.option.gsc_repo
    os.environ["gsc_commit"] = config.option.gsc_commit
    os.environ["iterations"] = config.option.iterations
    os.environ["exec_mode"] = config.option.exec_mode
    os.environ["EDMM"] = config.option.edmm
    os.environ["encryption"] = config.option.encryption
    os.environ["tmpfs"] = config.option.tmpfs
    os.environ["jenkins_build_num"] = config.option.jenkins_build_num
    os.environ["client_username"] = config.option.client_username
    os.environ["client_ip_addr"] = config.option.client_ip_addr


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
        curated_apps_lib.curated_setup()
        curated_apps_lib.copy_repo()

    yield

    # Generate the report using the global results dict.
    utils.generate_performance_report(trd)


def pytest_addoption(parser):
    print("\n##### In pytest_addoption #####\n")
    parser.addoption("--perf_config", action="store", type=str, default="baremetal", help="Bare-metal or Docker based execution.")
    parser.addoption("--build_gramine", action="store", type=str, default="source", help="Package or source based installation of Gramine.")
    # *********** For baremetal workloads **************
    # If 'gramine_commit' is passed, corresponding gramine commit will be checked out
    # to build gramine from source. If 'gramine_commit' is not specified, latest
    # master will be used to build gramine.
    # ************** For container workloads **************
    # If both 'gramine_commit' or 'gsc_commit' are not passed as parameters, v1.6.1 would be
    # used as default for both commits.
    # If 'gramine_commit' is master/any other commit, 'gsc_commit' must be passed as master.
    parser.addoption("--gramine_repo", action="store", type=str, default="", help="Gramine repo to be used.")
    parser.addoption("--gramine_commit", action="store", type=str, default="master", help="Gramine commit/branch to be checked out.")
    parser.addoption("--gsc_repo", action="store", type=str, default="", help="Gramine GSC repo to be used.")
    parser.addoption("--gsc_commit", action="store", type=str, default="master", help="Gramine GSC commit/branch to be checked out.")
    parser.addoption("--iterations", action="store", type=str, default='3', help="Number of times workload/benchmark app needs to be launched/executed.")
    # Following will be value of 'exec_mode' that would be expected by the framework.
    # For Redis workload: "native,gramine-direct,gramine-sgx,gramine-sgx-exitless"
    # For other workloads: "native,gramine-direct,gramine-sgx"
    parser.addoption("--exec_mode", action="store", type=str, default="native,gramine-direct,gramine-sgx", help="Workload execution modes.")
    parser.addoption("--edmm", action="store", type=str, default="0", help="EDMM mode")
    parser.addoption("--encryption", action="store", type=str, default='0', help="Enable encryption for model/s before workload command execution.")
    parser.addoption("--tmpfs", action="store", type=str, default='0', help="Use tmpfs path for DB.")
    # Following option is the build number of the 'gramerf_performance_banehmarking' Jenkins job.
    # This number is used within the filename of the final report generated for the workload.
    parser.addoption("--jenkins_build_num", action="store", type=str, default="", help="Build number of Jenkins CI perf job")
    # Following option is the username with which the system (client) needs to be rebooted.
    # Applicable on for few workloads like Redis and Memcached.
    parser.addoption("--client_username", action="store", type=str, default="", help="User name of the system to be rebooted")
    # Following option is the IP address of the system (client) that needs to be rebooted.
    # Applicable on for few workloads like Redis and Memcached.
    parser.addoption("--client_ip_addr", action="store", type=str, default="", help="User name of the system to be rebooted")


@pytest.fixture(scope="session", autouse=True)
def test_gramine_gsc_version():
    yield
    if os.environ["perf_config"] == "container":
      test_result = utils.verify_build_env_details()
      assert test_result
