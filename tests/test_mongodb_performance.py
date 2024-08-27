import os
import pytest
from common.config_files.constants import *
from common.libs.gramerf_wrapper import run_test
from common.libs import utils

yaml_file_name = "mongodb_performance_tests.yaml"
tests_yaml_path = os.path.join(os.getcwd(), 'data', yaml_file_name)


@pytest.fixture(scope="session")
def setup_db():
    print("\n-- Deleting old datebase if present...")
    if os.path.exists(MONGO_DB_PATH):
        print("\n-- Deleting old datebase...")
        utils.exec_shell_cmd(MONGO_DB_CLEANUP_CMD, None)
    utils.exec_shell_cmd(f"sudo mkdir -p {MONGO_DB_PATH} && sudo chown -R $USER:$USER {MONGO_DB_PATH}", None)


@pytest.mark.usefixtures("setup_db")
@pytest.mark.usefixtures("gramerf_setup")
class TestClass:

    @pytest.mark.mongodb_perf
    @pytest.mark.mongodb_perf_set_operation
    @pytest.mark.mongodb_perf_set_operation_1_threads
    def test_mongodb_perf_set_operation_1_threads(self):

        test_result = run_test(self, tests_yaml_path)
        assert test_result

    @pytest.mark.mongodb_perf
    @pytest.mark.mongodb_perf_set_operation
    @pytest.mark.mongodb_perf_set_operation_2_threads
    def test_mongodb_perf_set_operation_2_threads(self):

        test_result = run_test(self, tests_yaml_path)
        assert test_result

    @pytest.mark.mongodb_perf
    @pytest.mark.mongodb_perf_set_operation
    @pytest.mark.mongodb_perf_set_operation_8_threads
    def test_mongodb_perf_set_operation_8_threads(self):

        test_result = run_test(self, tests_yaml_path)
        assert test_result

    @pytest.mark.mongodb_perf
    @pytest.mark.mongodb_perf_set_operation
    @pytest.mark.mongodb_perf_set_operation_16_threads
    def test_mongodb_perf_set_operation_16_threads(self):

        test_result = run_test(self, tests_yaml_path)
        assert test_result

    @pytest.mark.mongodb_perf
    @pytest.mark.mongodb_perf_set_operation
    @pytest.mark.mongodb_perf_set_operation_32_threads
    def test_mongodb_perf_set_operation_32_threads(self):

        test_result = run_test(self, tests_yaml_path)
        assert test_result

    @pytest.mark.mongodb_perf
    @pytest.mark.mongodb_perf_set_operation
    @pytest.mark.mongodb_perf_set_operation_64_threads
    def test_mongodb_perf_set_operation_64_threads(self):

        test_result = run_test(self, tests_yaml_path)
        assert test_result

    @pytest.mark.mongodb_perf
    @pytest.mark.mongodb_perf_get_operation
    @pytest.mark.mongodb_perf_get_operation_1_threads
    def test_mongodb_perf_get_operation_1_threads(self):

        test_result = run_test(self, tests_yaml_path)
        assert test_result

    @pytest.mark.mongodb_perf
    @pytest.mark.mongodb_perf_get_operation
    @pytest.mark.mongodb_perf_get_operation_2_threads
    def test_mongodb_perf_get_operation_2_threads(self):

        test_result = run_test(self, tests_yaml_path)
        assert test_result

    @pytest.mark.mongodb_perf
    @pytest.mark.mongodb_perf_get_operation
    @pytest.mark.mongodb_perf_get_operation_8_threads
    def test_mongodb_perf_get_operation_8_threads(self):

        test_result = run_test(self, tests_yaml_path)
        assert test_result

    @pytest.mark.mongodb_perf
    @pytest.mark.mongodb_perf_get_operation
    @pytest.mark.mongodb_perf_get_operation_16_threads
    def test_mongodb_perf_get_operation_16_threads(self):

        test_result = run_test(self, tests_yaml_path)
        assert test_result

    @pytest.mark.mongodb_perf
    @pytest.mark.mongodb_perf_get_operation
    @pytest.mark.mongodb_perf_get_operation_32_threads
    def test_mongodb_perf_get_operation_32_threads(self):

        test_result = run_test(self, tests_yaml_path)
        assert test_result

    @pytest.mark.mongodb_perf
    @pytest.mark.mongodb_perf_get_operation
    @pytest.mark.mongodb_perf_get_operation_64_threads
    def test_mongodb_perf_get_operation_64_threads(self):

        test_result = run_test(self, tests_yaml_path)
        assert test_result