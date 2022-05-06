#
# Imports
#
import pytest
import src.libs.gramerf_wrapper
import os
#from pprint import pprint
from src.workloads.Openvino_Workload import OpenvinoWorkload

# @pytest.fixture(scope="session")
# def name(pytestconfig):
#     print ("\n**** In name fixture *****")
#     return pytestconfig.getoption("name")

# @pytest.mark.ov_perf_resnet
# def test_print_name(name):
#     print(f"\ncommand line param (name): {name}")

# @pytest.mark.ov_perf_resnet
# def test_print_name2(name):
#     print(f"\ncommand line param (name): {name}")

# @pytest.mark.ov_perf_resnet
# def test_print_name_2():
#     print(f"\ncommand line param (name): {name}")
#     print(f"test_print_name_2(name): {pytest.config.getoption('name')}")
#     print(f"test_print_name_21(exec_mode): {pytest.config.getoption('exec_mode')}")

    #print ("\nTest Config = ")
    #pprint (vars(test_config_obj))
    #print ("\nBenchmark = ", yaml.load(test_config_obj.workload_args)['BENCHMARKS'][1])

@pytest.fixture(scope="class")
def setup_fixture():
    #operating_system = "linux"
    #attack_type = "side_channel"
    print ("\n##### In setup_fixture #####\n")
    ini_file_name = "ov_performance_tests.yaml"
    tests_ini_path = os.path.join(os.getcwd(), 'data', ini_file_name)
    #print ("\nTest ini path = ", tests_ini_path)
    return tests_ini_path
    # yield tests_ini_path
    #print("teardown")


@pytest.mark.usefixtures("setup_fixture")
@pytest.mark.usefixtures("build_gramine")
#@pytest.mark.usefixtures("read_global_config")
class TestClass:
    test_obj = OpenvinoWorkload("Openvino", None, None, None)
    # @pytest.mark.ov_perf
    # @pytest.mark.ov_perf_bert_large
    # def test_ov_perf_bert_large(self, setup_fixture):
    #     print("\n##### In test_ov_perf_bert_large #####\n")
    #     test_name = "test_ov_perf_bert_large"
    #     testid = "1"
        
    #     test_config_obj = src.libs.gramerf_wrapper.read_config(testid, test_name, setup_fixture)
    #     #test_result = src.libs.gramerf_wrapper.run_test(test_config_obj)

    #     #assert test_result


    # @pytest.mark.ov_perf
    # @pytest.mark.ov_perf_brain_tumor_seg_0001
    # def test_ov_perf_brain_tumor_seg_0001(self, setup_fixture):
    #     print ("\n##### In test_ov_perf_brain_tumor_seg_0001 #####\n")
    #     test_name = "test_ov_perf_brain_tumor_seg_0001"
    #     testid = "2"

    #     test_config_obj = src.libs.gramerf_wrapper.read_config(testid, test_name, setup_fixture)
    #     #test_result = src.libs.gramerf_wrapper.run_test(test_config_obj)

    #     #assert test_result


    @pytest.mark.ov_perf
    @pytest.mark.ov_perf_brain_tumor_seg_0002
    def test_ov_perf_brain_tumor_seg_0002(self, setup_fixture):
        print ("\n##### In test_ov_perf_brain_tumor_seg_0002 #####\n")
        test_name = "test_ov_perf_brain_tumor_seg_0002"
        testid = "3"

        src.libs.gramerf_wrapper.read_config(setup_fixture)
        #print (test_config_dict)
        test_result = src.libs.gramerf_wrapper.run_test(self.test_obj)

    #     #assert test_result


    @pytest.mark.ov_perf
    @pytest.mark.ov_perf_resnet
    def test_ov_perf_resnet(self, setup_fixture):
        print ("\n##### In test_ov_perf_resnet #####\n")
        test_name = "test_ov_perf_resnet"
        testid = "4"
                
        src.libs.gramerf_wrapper.read_config(setup_fixture)
        #print (test_config_dict)
        test_result = src.libs.gramerf_wrapper.run_test(self.test_obj)

        #assert test_result


    # @pytest.mark.ov_perf
    # @pytest.mark.ov_perf_ssd_mobilenet
    # def test_ov_perf_ssd_mobilenet(self, setup_fixture):
    #     print ("\n##### In test_ov_perf_ssd_mobilenet #####\n")

    #     test_name = "test_ov_perf_ssd_mobilenet"
    #     testid = "5"

    #     test_config_obj = src.libs.gramerf_wrapper.read_config(testid, test_name, setup_fixture)
    #     #test_result = src.libs.gramerf_wrapper.run_test(test_config_obj)

    #     #assert test_result

