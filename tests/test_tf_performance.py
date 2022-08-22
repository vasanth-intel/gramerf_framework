import os
import pytest
import src.libs.gramerf_wrapper


yaml_file_name = "tf_performance_tests.yaml"
tests_yaml_path = os.path.join(os.getcwd(), 'data', yaml_file_name)


@pytest.mark.usefixtures("gramerf_setup")
class TestClass:

    # In order to use command line values within pytest, using 'pytest.config' global
    # is deprecated from pytest version 4.0 onwards. Instead, we need to pass the config 
    # instance via an autouse fixture in order to access it.
    @pytest.fixture(autouse=True)
    def inject_config(self, request):
        self.config = request.config

    @pytest.mark.tf_perf
    @pytest.mark.tf_perf_bert
    def test_tf_perf_bert_throughput(self):

        test_result = src.libs.gramerf_wrapper.run_test(self, tests_yaml_path)
        assert test_result

    @pytest.mark.tf_perf
    @pytest.mark.tf_perf_resnet
    @pytest.mark.tf_perf_resnet_bs_1
    def test_tf_perf_resnet_bs_1_throughput(self):

        test_result = src.libs.gramerf_wrapper.run_test(self, tests_yaml_path)
        assert test_result

    @pytest.mark.tf_perf
    @pytest.mark.tf_perf_resnet
    @pytest.mark.tf_perf_resnet_bs_16
    def test_tf_perf_resnet_bs_16_throughput(self):

        test_result = src.libs.gramerf_wrapper.run_test(self, tests_yaml_path)
        assert test_result

    @pytest.mark.tf_perf
    @pytest.mark.tf_perf_resnet
    @pytest.mark.tf_perf_resnet_bs_512
    def test_tf_perf_resnet_bs_512_throughput(self):

        test_result = src.libs.gramerf_wrapper.run_test(self, tests_yaml_path)
        assert test_result
