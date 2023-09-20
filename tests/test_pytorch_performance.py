import os
import pytest
from common.libs.gramerf_wrapper import run_test
from docker_benchmarking.workloads.pytorch_workload import *

yaml_file_name = "pytorch_performance_tests.yaml"
tests_yaml_path = os.path.join(os.getcwd(), 'data', yaml_file_name)

@pytest.mark.usefixtures("gramerf_setup")
class TestClass:

    @pytest.mark.pytorch_perf
    @pytest.mark.pytorch_perf_throughput
    @pytest.mark.pytorch_perf_resnet50
    @pytest.mark.pytorch_perf_resnet50_throughput
    @pytest.mark.pytorch_perf_resnet50_avx_throughput
    @pytest.mark.pytorch_perf_resnet50_avx_int8_throughput
    def test_pytorch_perf_resnet50_avx_int8_throughput(self):

        test_result = run_test(self, tests_yaml_path)
        assert test_result

    @pytest.mark.pytorch_perf
    @pytest.mark.pytorch_perf_amx
    @pytest.mark.pytorch_perf_throughput
    @pytest.mark.pytorch_perf_resnet50
    @pytest.mark.pytorch_perf_resnet50_throughput
    @pytest.mark.pytorch_perf_resnet50_amx_throughput
    @pytest.mark.pytorch_perf_resnet50_amx_int8_throughput
    def test_pytorch_perf_resnet50_amx_int8_throughput(self):

        test_result = run_test(self, tests_yaml_path)
        assert test_result

    @pytest.mark.pytorch_perf
    @pytest.mark.pytorch_perf_throughput
    @pytest.mark.pytorch_perf_resnet50
    @pytest.mark.pytorch_perf_resnet50_throughput
    @pytest.mark.pytorch_perf_resnet50_avx_throughput
    @pytest.mark.pytorch_perf_resnet50_avx_fp32_throughput
    def test_pytorch_perf_resnet50_avx_fp32_throughput(self):

        test_result = run_test(self, tests_yaml_path)
        assert test_result

    @pytest.mark.pytorch_perf
    @pytest.mark.pytorch_perf_amx
    @pytest.mark.pytorch_perf_throughput
    @pytest.mark.pytorch_perf_resnet50
    @pytest.mark.pytorch_perf_resnet50_throughput
    @pytest.mark.pytorch_perf_resnet50_amx_throughput
    @pytest.mark.pytorch_perf_resnet50_amx_bfloat16_throughput
    def test_pytorch_perf_resnet50_amx_bfloat16_throughput(self):

        test_result = run_test(self, tests_yaml_path)
        assert test_result

    @pytest.mark.pytorch_perf
    @pytest.mark.pytorch_perf_latency
    @pytest.mark.pytorch_perf_resnet50
    @pytest.mark.pytorch_perf_resnet50_latency
    @pytest.mark.pytorch_perf_resnet50_avx_latency
    @pytest.mark.pytorch_perf_resnet50_avx_int8_latency
    def test_pytorch_perf_resnet50_avx_int8_latency(self):

        test_result = run_test(self, tests_yaml_path)
        assert test_result

    @pytest.mark.pytorch_perf
    @pytest.mark.pytorch_perf_amx
    @pytest.mark.pytorch_perf_latency
    @pytest.mark.pytorch_perf_resnet50
    @pytest.mark.pytorch_perf_resnet50_latency
    @pytest.mark.pytorch_perf_resnet50_amx_latency
    @pytest.mark.pytorch_perf_resnet50_amx_int8_latency
    def test_pytorch_perf_resnet50_amx_int8_latency(self):

        test_result = run_test(self, tests_yaml_path)
        assert test_result

    @pytest.mark.pytorch_perf
    @pytest.mark.pytorch_perf_latency
    @pytest.mark.pytorch_perf_resnet50
    @pytest.mark.pytorch_perf_resnet50_latency
    @pytest.mark.pytorch_perf_resnet50_avx_latency
    @pytest.mark.pytorch_perf_resnet50_avx_fp32_latency
    def test_pytorch_perf_resnet50_avx_fp32_latency(self):

        test_result = run_test(self, tests_yaml_path)
        assert test_result

    @pytest.mark.pytorch_perf
    @pytest.mark.pytorch_perf_amx
    @pytest.mark.pytorch_perf_latency
    @pytest.mark.pytorch_perf_resnet50
    @pytest.mark.pytorch_perf_resnet50_latency
    @pytest.mark.pytorch_perf_resnet50_amx_latency
    @pytest.mark.pytorch_perf_resnet50_amx_bfloat16_latency
    def test_pytorch_perf_resnet50_amx_bfloat16_latency(self):

        test_result = run_test(self, tests_yaml_path)
        assert test_result

    @pytest.mark.pytorch_perf
    @pytest.mark.pytorch_perf_throughput
    @pytest.mark.pytorch_perf_dlrm
    @pytest.mark.pytorch_perf_dlrm_throughput
    @pytest.mark.pytorch_perf_dlrm_avx_throughput
    @pytest.mark.pytorch_perf_dlrm_avx_int8_throughput
    def test_pytorch_perf_dlrm_avx_int8_throughput(self):

        test_result = run_test(self, tests_yaml_path)
        assert test_result

    @pytest.mark.pytorch_perf
    @pytest.mark.pytorch_perf_amx
    @pytest.mark.pytorch_perf_throughput
    @pytest.mark.pytorch_perf_dlrm
    @pytest.mark.pytorch_perf_dlrm_throughput
    @pytest.mark.pytorch_perf_dlrm_amx_throughput
    @pytest.mark.pytorch_perf_dlrm_amx_int8_throughput
    def test_pytorch_perf_dlrm_amx_int8_throughput(self):

        test_result = run_test(self, tests_yaml_path)
        assert test_result

    @pytest.mark.pytorch_perf
    @pytest.mark.pytorch_perf_throughput
    @pytest.mark.pytorch_perf_dlrm
    @pytest.mark.pytorch_perf_dlrm_throughput
    @pytest.mark.pytorch_perf_dlrm_avx_throughput
    @pytest.mark.pytorch_perf_dlrm_avx_fp32_throughput
    def test_pytorch_perf_dlrm_avx_fp32_throughput(self):

        test_result = run_test(self, tests_yaml_path)
        assert test_result

    @pytest.mark.pytorch_perf
    @pytest.mark.pytorch_perf_amx
    @pytest.mark.pytorch_perf_throughput
    @pytest.mark.pytorch_perf_dlrm
    @pytest.mark.pytorch_perf_dlrm_throughput
    @pytest.mark.pytorch_perf_dlrm_amx_throughput
    @pytest.mark.pytorch_perf_dlrm_amx_bfloat16_throughput
    def test_pytorch_perf_dlrm_amx_bfloat16_throughput(self):

        test_result = run_test(self, tests_yaml_path)
        assert test_result
