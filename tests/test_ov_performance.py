#
# Imports
#
import os
import pytest
import src.libs.gramerf_wrapper
from setup import read_perf_suite_config

@pytest.fixture(scope="class")
def tests_setup_fixture():
    print ("\n##### In tests_setup_fixture #####\n")
    yaml_file_name = "ov_performance_tests.yaml"
    tests_yaml_path = os.path.join(os.getcwd(), 'data', yaml_file_name)
    return tests_yaml_path


@pytest.mark.usefixtures("tests_setup_fixture")
@pytest.mark.usefixtures("gramerf_setup")
class TestClass:
    # In order to use command line values within pytest, using 'pytest.config' global
    # is deprecated from pytest version 4.0 onwards. Instead, we need to pass the config 
    # instance via an autouse fixture in order to access it.
    @pytest.fixture(autouse=True)
    def inject_config(self, request):
        print ("\n##### In inject_config #####\n")
        self._config = request.config

    @pytest.mark.ov_perf
    @pytest.mark.ov_perf_bert_large
    def test_ov_perf_bert_large(self, tests_setup_fixture):
        print("\n##### In test_ov_perf_bert_large #####\n")

        test_config_dict = read_perf_suite_config(self, tests_setup_fixture)
        test_result = src.libs.gramerf_wrapper.run_test(test_config_dict)
        
        assert test_result


    @pytest.mark.ov_perf
    @pytest.mark.ov_perf_brain_tumor_seg_0001
    def test_ov_perf_brain_tumor_seg_0001(self, tests_setup_fixture):
        print ("\n##### In test_ov_perf_brain_tumor_seg_0001 #####\n")

        test_config_dict = read_perf_suite_config(self, tests_setup_fixture)
        test_result = src.libs.gramerf_wrapper.run_test(test_config_dict)
        
        assert test_result


    @pytest.mark.ov_perf
    @pytest.mark.ov_perf_brain_tumor_seg_0002
    def test_ov_perf_brain_tumor_seg_0002(self, tests_setup_fixture):
        print ("\n##### In test_ov_perf_brain_tumor_seg_0002 #####\n")

        test_config_dict = read_perf_suite_config(self, tests_setup_fixture)
        test_result = src.libs.gramerf_wrapper.run_test(test_config_dict)
        
        assert test_result


    @pytest.mark.ov_perf
    @pytest.mark.ov_perf_resnet
    def test_ov_perf_resnet(self, tests_setup_fixture):
        print ("\n##### In test_ov_perf_resnet #####\n")

        test_config_dict = read_perf_suite_config(self, tests_setup_fixture)
        test_result = src.libs.gramerf_wrapper.run_test(test_config_dict)
        
        assert test_result


    @pytest.mark.ov_perf
    @pytest.mark.ov_perf_ssd_mobilenet
    def test_ov_perf_ssd_mobilenet(self, tests_setup_fixture):
        print ("\n##### In test_ov_perf_ssd_mobilenet #####\n")

        test_config_dict = read_perf_suite_config(self, tests_setup_fixture)
        test_result = src.libs.gramerf_wrapper.run_test(test_config_dict)
        
        assert test_result

