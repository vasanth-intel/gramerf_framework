import os
import pytest
import sys
from common.config_files.constants import *
from common.libs.gramerf_wrapper import run_test
from docker_benchmarking.workloads.db_workloads_utils import *

yaml_file_name = "ovms_performance_tests.yaml"
tests_yaml_path = os.path.join(os.getcwd(), 'data', yaml_file_name)

@pytest.fixture(scope="session")
def execute_workload_setup():
    os.makedirs(OVMS_MODEL_FILES_PATH, exist_ok=True)
    init_result = init_db("ovms")
    if init_result == False:
        sys.exit("DB initialization failed")

@pytest.mark.usefixtures("execute_workload_setup")
@pytest.mark.usefixtures("gramerf_setup")
class TestClass:
    
    @pytest.mark.ovms_perf
    @pytest.mark.ovms_perf_resnet
    def test_ovms_perf_resnet_throughput(self):
        test_result = run_test(self, tests_yaml_path)
        assert test_result

    @pytest.mark.ovms_perf
    @pytest.mark.ovms_perf_face_detection
    def test_ovms_perf_face_detection_throughput(self):
        test_result = run_test(self, tests_yaml_path)
        assert test_result

    @pytest.mark.ovms_perf
    @pytest.mark.ovms_perf_faster_rcnn_resnet
    def test_ovms_perf_faster_rcnn_resnet_throughput(self):
        test_result = run_test(self, tests_yaml_path)
        assert test_result
