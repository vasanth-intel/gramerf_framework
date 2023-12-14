import os
import pytest
from common.libs.gramerf_wrapper import run_test

yaml_file_name = "specpower_performance_tests.yaml"
tests_yaml_path = os.path.join(os.getcwd(), 'data', yaml_file_name)


@pytest.mark.usefixtures("gramerf_setup")
class TestClass:

    @pytest.mark.specpower_perf
    def test_specpower_perf_throughput(self):

        test_result = run_test(self, tests_yaml_path)
        assert test_result
