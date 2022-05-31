#
# Imports
#
import os
import pytest
import src.libs.gramerf_wrapper

yaml_file_name = "ov_performance_tests.yaml"
tests_yaml_path = os.path.join(os.getcwd(), 'data', yaml_file_name)

@pytest.mark.usefixtures("gramerf_setup")
class TestClass:

    # In order to use command line values within pytest, using 'pytest.config' global
    # is deprecated from pytest version 4.0 onwards. Instead, we need to pass the config 
    # instance via an autouse fixture in order to access it.
    @pytest.fixture(autouse=True)
    def inject_config(self, request):
        print ("\n##### In inject_config #####\n")
        self._config = request.config

#######################################################################################

    @pytest.mark.ov_perf
    @pytest.mark.ov_perf_throughput
    @pytest.mark.ov_perf_bert_large_throughput
    @pytest.mark.ov_perf_bert_large_fp16_throughput
    def test_ov_perf_bert_large_fp16_throughput(self):
        print ("\n##### In test_ov_perf_bert_large_fp16_throughput #####\n")

        test_result = src.libs.gramerf_wrapper.run_test(self, tests_yaml_path)
        
        assert test_result

    @pytest.mark.ov_perf
    @pytest.mark.ov_perf_throughput
    @pytest.mark.ov_perf_bert_large_throughput
    @pytest.mark.ov_perf_bert_large_fp32_throughput
    def test_ov_perf_bert_large_fp32_throughput(self):
        print ("\n##### In test_ov_perf_bert_large_fp32_throughput #####\n")

        test_result = src.libs.gramerf_wrapper.run_test(self, tests_yaml_path)
        
        assert test_result

    @pytest.mark.ov_perf
    @pytest.mark.ov_perf_latency
    @pytest.mark.ov_perf_bert_large_latency
    @pytest.mark.ov_perf_bert_large_fp16_latency
    def test_ov_perf_bert_large_fp16_latency(self):
        print ("\n##### In test_ov_perf_bert_large_fp16_latency #####\n")

        test_result = src.libs.gramerf_wrapper.run_test(self, tests_yaml_path)
        
        assert test_result

    @pytest.mark.ov_perf
    @pytest.mark.ov_perf_latency
    @pytest.mark.ov_perf_bert_large_latency
    @pytest.mark.ov_perf_bert_large_fp32_latency
    def test_ov_perf_bert_large_fp32_latency(self):
        print ("\n##### In test_ov_perf_bert_large_fp32_latency #####\n")

        test_result = src.libs.gramerf_wrapper.run_test(self, tests_yaml_path)
        
        assert test_result

#######################################################################################

    @pytest.mark.ov_perf
    @pytest.mark.ov_perf_throughput
    @pytest.mark.ov_perf_bert_large_int8_throughput
    def test_ov_perf_bert_large_int8_throughput(self):
        print ("\n##### In test_ov_perf_bert_large_int8_throughput #####\n")

        test_result = src.libs.gramerf_wrapper.run_test(self, tests_yaml_path)
        
        assert test_result

    @pytest.mark.ov_perf
    @pytest.mark.ov_perf_latency
    @pytest.mark.ov_perf_bert_large_int8_latency
    def test_ov_perf_bert_large_int8_latency(self):
        print ("\n##### In test_ov_perf_bert_large_int8_latency #####\n")

        test_result = src.libs.gramerf_wrapper.run_test(self, tests_yaml_path)
        
        assert test_result

#######################################################################################

    @pytest.mark.ov_perf
    @pytest.mark.ov_perf_throughput
    @pytest.mark.ov_perf_brain_tumor_seg_0001_throughput
    @pytest.mark.ov_perf_brain_tumor_seg_0001_fp16_throughput
    def test_ov_perf_brain_tumor_seg_0001_fp16_throughput(self):
        print ("\n##### In test_ov_perf_brain_tumor_seg_0001_fp16_throughput #####\n")

        test_result = src.libs.gramerf_wrapper.run_test(self, tests_yaml_path)
        
        assert test_result

    @pytest.mark.ov_perf
    @pytest.mark.ov_perf_throughput
    @pytest.mark.ov_perf_brain_tumor_seg_0001_throughput
    @pytest.mark.ov_perf_brain_tumor_seg_0001_fp32_throughput
    def test_ov_perf_brain_tumor_seg_0001_fp32_throughput(self):
        print ("\n##### In test_ov_perf_brain_tumor_seg_0001_fp32_throughput #####\n")

        test_result = src.libs.gramerf_wrapper.run_test(self, tests_yaml_path)
        
        assert test_result

    @pytest.mark.ov_perf
    @pytest.mark.ov_perf_latency
    @pytest.mark.ov_perf_brain_tumor_seg_0001_latency
    @pytest.mark.ov_perf_brain_tumor_seg_0001_fp16_latency
    def test_ov_perf_brain_tumor_seg_0001_fp16_latency(self):
        print ("\n##### In test_ov_perf_brain_tumor_seg_0001_fp16_latency #####\n")

        test_result = src.libs.gramerf_wrapper.run_test(self, tests_yaml_path)
        
        assert test_result

    @pytest.mark.ov_perf
    @pytest.mark.ov_perf_latency
    @pytest.mark.ov_perf_brain_tumor_seg_0001_latency
    @pytest.mark.ov_perf_brain_tumor_seg_0001_fp32_latency
    def test_ov_perf_brain_tumor_seg_0001_fp32_latency(self):
        print ("\n##### In test_ov_perf_brain_tumor_seg_0001_fp32_latency #####\n")

        test_result = src.libs.gramerf_wrapper.run_test(self, tests_yaml_path)
        
        assert test_result

#######################################################################################

    @pytest.mark.ov_perf
    @pytest.mark.ov_perf_throughput
    @pytest.mark.ov_perf_brain_tumor_seg_0002_throughput
    @pytest.mark.ov_perf_brain_tumor_seg_0002_fp16_throughput
    def test_ov_perf_brain_tumor_seg_0002_fp16_throughput(self):
        print ("\n##### In test_ov_perf_brain_tumor_seg_0002_fp16_throughput #####\n")

        test_result = src.libs.gramerf_wrapper.run_test(self, tests_yaml_path)
        
        assert test_result

    @pytest.mark.ov_perf
    @pytest.mark.ov_perf_throughput
    @pytest.mark.ov_perf_brain_tumor_seg_0002_throughput
    @pytest.mark.ov_perf_brain_tumor_seg_0002_fp32_throughput
    def test_ov_perf_brain_tumor_seg_0002_fp32_throughput(self):
        print ("\n##### In test_ov_perf_brain_tumor_seg_0002_fp32_throughput #####\n")

        test_result = src.libs.gramerf_wrapper.run_test(self, tests_yaml_path)
        
        assert test_result

    @pytest.mark.ov_perf
    @pytest.mark.ov_perf_latency
    @pytest.mark.ov_perf_brain_tumor_seg_0002_latency
    @pytest.mark.ov_perf_brain_tumor_seg_0002_fp16_latency
    def test_ov_perf_brain_tumor_seg_0002_fp16_latency(self):
        print ("\n##### In test_ov_perf_brain_tumor_seg_0002_fp16_latency #####\n")

        test_result = src.libs.gramerf_wrapper.run_test(self, tests_yaml_path)
        
        assert test_result

    @pytest.mark.ov_perf
    @pytest.mark.ov_perf_latency
    @pytest.mark.ov_perf_brain_tumor_seg_0002_latency
    @pytest.mark.ov_perf_brain_tumor_seg_0002_fp32_latency
    def test_ov_perf_brain_tumor_seg_0002_fp32_latency(self):
        print ("\n##### In test_ov_perf_brain_tumor_seg_0002_fp32_latency #####\n")

        test_result = src.libs.gramerf_wrapper.run_test(self, tests_yaml_path)
        
        assert test_result

#######################################################################################

    @pytest.mark.ov_perf
    @pytest.mark.ov_perf_throughput
    @pytest.mark.ov_perf_resnet_throughput
    @pytest.mark.ov_perf_resnet_fp16_throughput
    def test_ov_perf_resnet_fp16_throughput(self):
        print ("\n##### In test_ov_perf_resnet_fp16_throughput #####\n")

        test_result = src.libs.gramerf_wrapper.run_test(self, tests_yaml_path)
        
        assert test_result

    @pytest.mark.ov_perf
    @pytest.mark.ov_perf_throughput
    @pytest.mark.ov_perf_resnet_throughput
    @pytest.mark.ov_perf_resnet_fp32_throughput
    def test_ov_perf_resnet_fp32_throughput(self):
        print ("\n##### In test_ov_perf_resnet_fp32_throughput #####\n")

        test_result = src.libs.gramerf_wrapper.run_test(self, tests_yaml_path)
        
        assert test_result

    @pytest.mark.ov_perf
    @pytest.mark.ov_perf_latency
    @pytest.mark.ov_perf_resnet_latency
    @pytest.mark.ov_perf_resnet_fp16_latency
    def test_ov_perf_resnet_fp16_latency(self):
        print ("\n##### In test_ov_perf_resnet_fp16_latency #####\n")

        test_result = src.libs.gramerf_wrapper.run_test(self, tests_yaml_path)
        
        assert test_result

    @pytest.mark.ov_perf
    @pytest.mark.ov_perf_latency
    @pytest.mark.ov_perf_resnet_latency
    @pytest.mark.ov_perf_resnet_fp32_latency
    def test_ov_perf_resnet_fp32_latency(self):
        print ("\n##### In test_ov_perf_resnet_fp32_latency #####\n")

        test_result = src.libs.gramerf_wrapper.run_test(self, tests_yaml_path)
        
        assert test_result

#######################################################################################

    @pytest.mark.ov_perf
    @pytest.mark.ov_perf_throughput
    @pytest.mark.ov_perf_ssd_mobilenet_throughput
    @pytest.mark.ov_perf_ssd_mobilenet_fp16_throughput
    def test_ov_perf_ssd_mobilenet_fp16_throughput(self):
        print ("\n##### In test_ov_perf_ssd_mobilenet_fp16_throughput #####\n")

        test_result = src.libs.gramerf_wrapper.run_test(self, tests_yaml_path)

        #test_obj = src.libs.gramerf_wrapper.run_test(self, tests_yaml_path)
        #perf_result = src.libs.gramerf_wrapper.calculate_perf_degradation(test_obj)

        assert test_result

    @pytest.mark.ov_perf
    @pytest.mark.ov_perf_throughput
    @pytest.mark.ov_perf_ssd_mobilenet_throughput
    @pytest.mark.ov_perf_ssd_mobilenet_fp32_throughput
    def test_ov_perf_ssd_mobilenet_fp32_throughput(self):
        print ("\n##### In test_ov_perf_ssd_mobilenet_fp32_throughput #####\n")

        test_result = src.libs.gramerf_wrapper.run_test(self, tests_yaml_path)
        
        assert test_result

    @pytest.mark.ov_perf
    @pytest.mark.ov_perf_latency
    @pytest.mark.ov_perf_ssd_mobilenet_latency
    @pytest.mark.ov_perf_ssd_mobilenet_fp16_latency
    def test_ov_perf_ssd_mobilenet_fp16_latency(self):
        print ("\n##### In test_ov_perf_ssd_mobilenet_fp16_latency #####\n")

        test_result = src.libs.gramerf_wrapper.run_test(self, tests_yaml_path)
        
        assert test_result

    @pytest.mark.ov_perf
    @pytest.mark.ov_perf_latency
    @pytest.mark.ov_perf_ssd_mobilenet_latency
    @pytest.mark.ov_perf_ssd_mobilenet_fp32_latency
    def test_ov_perf_ssd_mobilenet_fp32_latency(self):
        print ("\n##### In test_ov_perf_ssd_mobilenet_fp32_latency #####\n")

        test_result = src.libs.gramerf_wrapper.run_test(self, tests_yaml_path)
        
        assert test_result

#######################################################################################