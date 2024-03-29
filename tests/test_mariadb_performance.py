import os
import pytest
import sys
from common.config_files.constants import *
from common.libs.gramerf_wrapper import run_test
from docker_benchmarking.workloads.db_workloads_utils import *

yaml_file_name = "mariadb_performance_tests.yaml"
tests_yaml_path = os.path.join(os.getcwd(), 'data', yaml_file_name)

@pytest.fixture(scope="session")
def execute_workload_setup():
    init_result = init_db("mariadb")
    if init_result == False:
        sys.exit("DB initialization failed")

@pytest.mark.usefixtures("execute_workload_setup")
@pytest.mark.usefixtures("gramerf_setup")
class TestClass:

    @pytest.mark.mariadb_perf
    @pytest.mark.mariadb_perf_read_only
    @pytest.mark.mariadb_perf_read_only_1_threads
    def test_mariadb_perf_read_only_1_threads(self):

        test_result = run_test(self, tests_yaml_path)
        assert test_result

    @pytest.mark.mariadb_perf
    @pytest.mark.mariadb_perf_read_only
    @pytest.mark.mariadb_perf_read_only_8_threads
    def test_mariadb_perf_read_only_8_threads(self):

        test_result = run_test(self, tests_yaml_path)
        assert test_result

    @pytest.mark.mariadb_perf
    @pytest.mark.mariadb_perf_read_only
    @pytest.mark.mariadb_perf_read_only_16_threads
    def test_mariadb_perf_read_only_16_threads(self):

        test_result = run_test(self, tests_yaml_path)
        assert test_result

    @pytest.mark.mariadb_perf
    @pytest.mark.mariadb_perf_read_only
    @pytest.mark.mariadb_perf_read_only_32_threads
    def test_mariadb_perf_read_only_32_threads(self):

        test_result = run_test(self, tests_yaml_path)
        assert test_result

    @pytest.mark.mariadb_perf
    @pytest.mark.mariadb_perf_read_only
    @pytest.mark.mariadb_perf_read_only_64_threads
    def test_mariadb_perf_read_only_64_threads(self):

        test_result = run_test(self, tests_yaml_path)
        assert test_result

    @pytest.mark.mariadb_perf
    @pytest.mark.mariadb_perf_write_only
    @pytest.mark.mariadb_perf_write_only_1_threads
    def test_mariadb_perf_write_only_1_threads(self):

        test_result = run_test(self, tests_yaml_path)
        assert test_result

    @pytest.mark.mariadb_perf
    @pytest.mark.mariadb_perf_write_only
    @pytest.mark.mariadb_perf_write_only_8_threads
    def test_mariadb_perf_write_only_8_threads(self):

        test_result = run_test(self, tests_yaml_path)
        assert test_result

    @pytest.mark.mariadb_perf
    @pytest.mark.mariadb_perf_write_only
    @pytest.mark.mariadb_perf_write_only_16_threads
    def test_mariadb_perf_write_only_16_threads(self):

        test_result = run_test(self, tests_yaml_path)
        assert test_result

    @pytest.mark.mariadb_perf
    @pytest.mark.mariadb_perf_write_only
    @pytest.mark.mariadb_perf_write_only_32_threads
    def test_mariadb_perf_write_only_32_threads(self):

        test_result = run_test(self, tests_yaml_path)
        assert test_result

    @pytest.mark.mariadb_perf
    @pytest.mark.mariadb_perf_write_only
    @pytest.mark.mariadb_perf_write_only_64_threads
    def test_mariadb_perf_write_only_64_threads(self):

        test_result = run_test(self, tests_yaml_path)
        assert test_result

    @pytest.mark.mariadb_perf
    @pytest.mark.mariadb_perf_read_write
    @pytest.mark.mariadb_perf_read_write_1_threads
    def test_mariadb_perf_read_write_1_threads(self):

        test_result = run_test(self, tests_yaml_path)
        assert test_result

    @pytest.mark.mariadb_perf
    @pytest.mark.mariadb_perf_read_write
    @pytest.mark.mariadb_perf_read_write_8_threads
    def test_mariadb_perf_read_write_8_threads(self):

        test_result = run_test(self, tests_yaml_path)
        assert test_result

    @pytest.mark.mariadb_perf
    @pytest.mark.mariadb_perf_read_write
    @pytest.mark.mariadb_perf_read_write_16_threads
    def test_mariadb_perf_read_write_16_threads(self):

        test_result = run_test(self, tests_yaml_path)
        assert test_result

    @pytest.mark.mariadb_perf
    @pytest.mark.mariadb_perf_read_write
    @pytest.mark.mariadb_perf_read_write_32_threads
    def test_mariadb_perf_read_write_32_threads(self):

        test_result = run_test(self, tests_yaml_path)
        assert test_result

    @pytest.mark.mariadb_perf
    @pytest.mark.mariadb_perf_read_write
    @pytest.mark.mariadb_perf_read_write_64_threads
    def test_mariadb_perf_read_write_64_threads(self):

        test_result = run_test(self, tests_yaml_path)
        assert test_result
