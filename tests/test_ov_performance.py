#
# Imports
#
import os
import pytest
import src.libs.gramerf_wrapper
from setup import read_global_config

@pytest.fixture(scope="class")
def tests_setup_fixture():
    print ("\n##### In tests_setup_fixture #####\n")
    yaml_file_name = "ov_performance_tests.yaml"
    tests_yaml_path = os.path.join(os.getcwd(), 'data', yaml_file_name)
    test_config_dict = read_global_config()
    return tests_yaml_path, test_config_dict


@pytest.mark.usefixtures("tests_setup_fixture")
@pytest.mark.usefixtures("gramerf_setup")
class TestClass:

    @pytest.mark.ov_perf
    @pytest.mark.ov_perf_bert_large
    def test_ov_perf_bert_large(self, tests_setup_fixture):
        print("\n##### In test_ov_perf_bert_large #####\n")

        tests_yaml_path, test_config_dict = tests_setup_fixture
        src.libs.gramerf_wrapper.read_config(tests_yaml_path, test_config_dict)
        src.libs.gramerf_wrapper.run_test(test_config_dict)


    @pytest.mark.ov_perf
    @pytest.mark.ov_perf_brain_tumor_seg_0001
    def test_ov_perf_brain_tumor_seg_0001(self, tests_setup_fixture):
        print ("\n##### In test_ov_perf_brain_tumor_seg_0001 #####\n")

        tests_yaml_path, test_config_dict = tests_setup_fixture
        src.libs.gramerf_wrapper.read_config(tests_yaml_path, test_config_dict)
        src.libs.gramerf_wrapper.run_test(test_config_dict)


    @pytest.mark.ov_perf
    @pytest.mark.ov_perf_brain_tumor_seg_0002
    def test_ov_perf_brain_tumor_seg_0002(self, tests_setup_fixture):
        print ("\n##### In test_ov_perf_brain_tumor_seg_0002 #####\n")

        tests_yaml_path, test_config_dict = tests_setup_fixture
        src.libs.gramerf_wrapper.read_config(tests_yaml_path, test_config_dict)
        src.libs.gramerf_wrapper.run_test(test_config_dict)


    @pytest.mark.ov_perf
    @pytest.mark.ov_perf_resnet
    def test_ov_perf_resnet(self, tests_setup_fixture):
        print ("\n##### In test_ov_perf_resnet #####\n")

        tests_yaml_path, test_config_dict = tests_setup_fixture
        src.libs.gramerf_wrapper.read_config(tests_yaml_path, test_config_dict)
        src.libs.gramerf_wrapper.run_test(test_config_dict)



    @pytest.mark.ov_perf
    @pytest.mark.ov_perf_ssd_mobilenet
    def test_ov_perf_ssd_mobilenet(self, tests_setup_fixture):
        print ("\n##### In test_ov_perf_ssd_mobilenet #####\n")

        tests_yaml_path, test_config_dict = tests_setup_fixture
        src.libs.gramerf_wrapper.read_config(tests_yaml_path, test_config_dict)
        src.libs.gramerf_wrapper.run_test(test_config_dict)

