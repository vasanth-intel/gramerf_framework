import os
import pytest
from common.config_files.constants import *
from common.libs.gramerf_wrapper import run_test
from docker_benchmarking.workloads.db_workloads_utils import *

yaml_file_name = "nginx_performance_tests.yaml"
tests_yaml_path = os.path.join(os.getcwd(), 'data', yaml_file_name)


@pytest.mark.usefixtures("gramerf_setup")
class TestClass:

    @pytest.mark.nginx_perf
    @pytest.mark.nginx_perf_10K
    @pytest.mark.nginx_perf_10K_data_size_1_threads
    def test_nginx_perf_10K_data_size_1_threads(self):

        test_result = run_test(self, tests_yaml_path)
        assert test_result

    @pytest.mark.nginx_perf
    @pytest.mark.nginx_perf_10K
    @pytest.mark.nginx_perf_10K_data_size_8_threads
    def test_nginx_perf_10K_data_size_8_threads(self):

        test_result = run_test(self, tests_yaml_path)
        assert test_result

    @pytest.mark.nginx_perf
    @pytest.mark.nginx_perf_10K
    @pytest.mark.nginx_perf_10K_data_size_32_threads
    def test_nginx_perf_10K_data_size_32_threads(self):

        test_result = run_test(self, tests_yaml_path)
        assert test_result

    @pytest.mark.nginx_perf
    @pytest.mark.nginx_perf_1M
    @pytest.mark.nginx_perf_1M_data_size_1_threads
    def test_nginx_perf_1M_data_size_1_threads(self):

        test_result = run_test(self, tests_yaml_path)
        assert test_result

    @pytest.mark.nginx_perf
    @pytest.mark.nginx_perf_1M
    @pytest.mark.nginx_perf_1M_data_size_8_threads
    def test_nginx_perf_1M_data_size_8_threads(self):

        test_result = run_test(self, tests_yaml_path)
        assert test_result

    @pytest.mark.nginx_perf
    @pytest.mark.nginx_perf_1M
    @pytest.mark.nginx_perf_1M_data_size_32_threads
    def test_nginx_perf_1M_data_size_32_threads(self):

        test_result = run_test(self, tests_yaml_path)
        assert test_result
