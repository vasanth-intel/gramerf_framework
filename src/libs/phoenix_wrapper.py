from configparser import SafeConfigParser
from src.config_files import constants
#from src.libs import utils
from src.libs import launch_validate_methods
#from src.libs import efficacy_methods
#import time
import os
# import allure
# import sys
# import traceback
# from src.libs.DB_Write import WRITE
# import logging
import json
import yaml
import inspect
import conftest
#from conftest import test_config_dict
#from conftest import tco

# logging.getLogger().setLevel(logging.INFO)
# logger=logging.getLogger(__name__)

# ENV_WORKLOAD_DB = os.environ.get('ENV_WORKLOAD_DB',{})
# ENV_WORKLOAD_DB['testapp_result'] = "No TestApp Result"
# ENV_WORKLOAD_DB['performance_result'] = "No Performance"
# ENV_WORKLOAD_DB['baseline_result'] = "No Baseline"

class test_config:
    # constructor
    def __init__(self, dict_obj):
        self.__dict__.update(dict_obj)
   
def dict2obj(dict_instance):
    # using json.loads method and passing json.dumps
    # method and custom object hook as arguments
    return json.loads(json.dumps(dict_instance), object_hook=test_config)

def read_config(tests_yaml_path):
    # Reading test specific configurations
    default_test_config={}
    #tmp_test_config = {}
    #test_config['test_name'] = test_name
    #test_config['testid'] = testid
    test_name = inspect.stack()[1].function

    with open(tests_yaml_path, "r") as fd:
        try:
            yaml_test_config = yaml.safe_load(fd)
        except yaml.YAMLError as exc:
            print(exc)

    print(conftest.test_config_dict)
    
    #tmp_test_config = default_test_config['Default']
    conftest.test_config_dict.update(yaml_test_config['Default'])
    #print("\nFirst assignment ", ret_test_config)
    # print(ret_test_config['testid'])
    # parser = SafeConfigParser()
    # parser.read(tests_ini_path)

    # if parser.has_section(testid):
    #     for key,value in parser.items(testid):
    #         test_config[key] = value
    # else:
    #     print ("testid doesn't exist in .ini file")
    # # Reading suite specific configurations
    # parser = SafeConfigParser()
    # parser.read(os.path.join(os.getcwd(),'src','config_files','config.ini'))
    # if "test_type" in test_config:
    #     if parser.has_section(test_config["test_type"]):
    #         for key,value in parser.items(test_config["test_type"]):
    #             if key not in test_config.keys():
    #                 test_config[key] = value

    # TEST_CONFIG = launch_validate_methods.test_config_sc(test_config)
    if yaml_test_config.get(test_name):
        conftest.test_config_dict.update(yaml_test_config[test_name])
        conftest.test_config_dict['test_name'] = test_name
        print ("\n\n Test Name = ", conftest.test_config_dict['test_name'])
    # for test in test_config:
    #     if test['test_name'] == test_name:
    #         ret_test_config.update(test)

    # print(test_config[0]['testid'])
    # print(test_config[1])
    # print(test_config[2])
    #print("\n",test_config)
    #return test_config_dict

def run_test(test_obj):
    #global tco
#     ENV_WORKLOAD_DB['QC_ID'] = TEST_CONFIG.testid
#     ENV_WORKLOAD_DB['TEST_NAME'] = TEST_CONFIG.test_name

    #Update final test config from command line arguments
    test_obj.update_test_config_from_cmd_line()

    test_config_obj = dict2obj(conftest.test_config_dict)
    #tco = test_config_obj
    #print ("\n ########## Local ###########", tco.iterations)

    test_obj.pre_actions(test_config_obj)

    #print("\n\n", test_config_obj.iterations)
    #print("\n\n", test_config_obj.metrics[0])
    #print("\n\n", test_config_obj.model_dir)
    #print("\n\n", test_config_dict['model_dir'])
    #print("\n\n", test_config_dict)


        
    #TEST_CONFIG.test_timed_out = False

#     with allure.step("Initialize Workload Class"):
#         TEST_CONFIG.WORKLOAD = launch_validate_methods.get_workload(TEST_CONFIG)
#         ENV_WORKLOAD_DB['WORKLOAD_OBJ'] = TEST_CONFIG.WORKLOAD

#     with allure.step("Initialize Test App Class"):
#         TEST_CONFIG.TESTAPP = launch_validate_methods.get_test_app(TEST_CONFIG)
#         ENV_WORKLOAD_DB['TEST_APP_OBJ'] = TEST_CONFIG.TESTAPP

#     with allure.step("Initialize Threat Sim Class"):
#         if TEST_CONFIG.threat_run:
#             TEST_CONFIG.THREATSIM = launch_validate_methods.get_threat_sim(TEST_CONFIG)
#         else:
#             TEST_CONFIG.THREATSIM = None

#     print "#" * 60
#     print "# Running: " + ENV_WORKLOAD_DB['TEST_NAME']
#     print "#" * 60
#     testapp_result = False
#     if TEST_CONFIG.baseline_run:
#         baseline_result = baseline_runner(TEST_CONFIG)
#     else:
#         baseline_result = True

#     TEST_CONFIG.test_timed_out = False
#     if TEST_CONFIG.testapp_run:
#         testapp_result = testapp_runner(TEST_CONFIG)

#     ENV_WORKLOAD_DB['baseline_result'] = utils.bool_to_pass_fail(baseline_result)
#     ENV_WORKLOAD_DB['testapp_result'] = utils.bool_to_pass_fail(testapp_result)
#     ENV_WORKLOAD_DB['TEST_RESULT'] = (testapp_result and baseline_result)
#     try:
#         print "WRITING TO DATABASE"
#         db_write = WRITE(ENV_WORKLOAD_DB, TEST_CONFIG)
#         db_write.workload()
#     except Exception as e:
#         print "ERROR in writing to the DB! " + str(e)
#         e1, e2, e3 = sys.exc_info()
#         traceback.print_tb(e3)
#         print (str(e2))
#         print (str(e1))

#     return testapp_result and baseline_result


# def baseline_runner(TEST_CONFIG):
#     print "STARTING BASELINE RUN"
#     TEST_CONFIG.is_baseline = True
#     TEST_CONFIG.PQT_List = []
#     with allure.step("Running in baseline mode without Testing App"):

#         with allure.step("Launching workload"):
#             launch_validate_methods.launch_workload(TEST_CONFIG)

#         with allure.step("Wait for PQT processes to finish"):
#             (pqt_finished, exit_code) = launch_validate_methods.check_process(TEST_CONFIG)

#         with allure.step("Validate Test Run"):
#             test_timed_out = launch_validate_methods.check_for_timeout(pqt_finished, exit_code, TEST_CONFIG)

#         with allure.step("Close workload"):
#             workload_result = launch_validate_methods.close_workload(TEST_CONFIG)

#         with allure.step("Baseline Verdict"):
#             if not TEST_CONFIG.hardkill_workload:
#                 with allure.step("Check for Workload Timeout"):
#                     if test_timed_out:
#                         assert False

#                 with allure.step("Check for Workload Exit code"):
#                     assert workload_result
#     return True

# def testapp_runner(TEST_CONFIG):
#     print "STARTING TESTING RUN"
#     DETECTION_RESULTS_ARRAY = []
#     TEST_CONFIG.is_baseline = False
#     efficacy_result = False
#     TEST_CONFIG.PQT_List = []
#     test_timed_out = False
#     threatsim_result = True
#     testapp_result = True
#     valid_exit_code = True
#     valid_exit_process = True
#     false_positives_passing = True
#     with allure.step("Running with Testing App"):

#         with allure.step("Launching workload"):
#             launch_validate_methods.launch_workload(TEST_CONFIG)

#         test_is_over = False
#         threatsim_result = False
#         ENV_WORKLOAD_DB['iterations_completed'] = None
#         with allure.step("Run the TestApp and ThreatSim for multiple iterations"):

#             for i in range(0,int(TEST_CONFIG.iterations)):
#                 if (not test_is_over) and (TEST_CONFIG.WORKLOAD.pqt.isRunning()):
#                     print "\n" + "- " * 50
#                     print "STARTING TEST ITERATION " + str(i+1) + " OF " + str(TEST_CONFIG.iterations)
#                     TEST_CONFIG.PQT_List = [TEST_CONFIG.WORKLOAD.pqt]

#                     with allure.step("Launching Testapp"):
#                         launch_validate_methods.launch_test_app(TEST_CONFIG)
#                         time.sleep(constants.POST_TESTAPP_DELAY)

#                     ENV_WORKLOAD_DB['THREAT_SIM_OBJ'] = None
#                     if TEST_CONFIG.threat_run:
#                         with allure.step("Launching ThreatSim"):
#                             launch_validate_methods.launch_threat_sim(TEST_CONFIG)
#                             TEST_CONFIG.TESTAPP.most_active_threat_sim_pid = TEST_CONFIG.THREATSIM.iter_pids[TEST_CONFIG.THREATSIM.iteration - 1]
#                             ENV_WORKLOAD_DB['THREAT_SIM_OBJ'] = TEST_CONFIG.THREATSIM

#                     with allure.step("Wait for PQT processes to finish"):
#                         (pqt_finished, exit_code) = launch_validate_methods.check_process(TEST_CONFIG)

#                     with allure.step("Validate Test Run"):
#                         test_timed_out = launch_validate_methods.check_for_timeout(pqt_finished, exit_code, TEST_CONFIG)
#                         if test_timed_out:
#                             valid_exit_code = True
#                             valid_exit_process = True
#                             if TEST_CONFIG.end_test_after_timeout == False:
#                                 test_timed_out = False
#                         else:
#                             valid_exit_code = launch_validate_methods.parse_exit_code(pqt_finished, exit_code,TEST_CONFIG)
#                             valid_exit_process = launch_validate_methods.check_for_valid_process_exit(pqt_finished,exit_code,TEST_CONFIG)

#                     with allure.step("Determine if Test should end"):
#                         should_end = launch_validate_methods.check_if_test_should_end(pqt_finished, TEST_CONFIG)
#                         test_is_over = test_timed_out or should_end or (not valid_exit_code) or (not valid_exit_process)
#                         print "TEST SHOULD END AFTER THIS ITERATION: " + str(test_is_over)

#                     with allure.step("Close Test App"):
#                         testapp_result = launch_validate_methods.validate_testapp(TEST_CONFIG)

#                         with allure.step("Check for Testapp success"):
#                             if not testapp_result:
#                                 logger.error("test failed in subtest:" + TEST_CONFIG.test_name)
#                             assert testapp_result

#                     if TEST_CONFIG.threat_run:
#                         if TEST_CONFIG.WORKLOAD.pqt.isRunning():
#                             with allure.step("Close Threat Sim"):
#                                 threatsim_result = launch_validate_methods.validate_threatsim(TEST_CONFIG)

#                             if TEST_CONFIG.enable_efficacy_parsing:
#                                 with allure.step("Efficacy parsing"):
#                                     fp_result, efficacy_result = efficacy_methods.parse_efficacy(TEST_CONFIG)
#                                     false_positives_passing = false_positives_passing and fp_result
#                                     DETECTION_RESULTS_ARRAY.append(efficacy_result)

#                             ENV_WORKLOAD_DB['iterations_completed'] = str(i + 1)
#                         else:
#                             unused_threatsim_result = launch_validate_methods.validate_threatsim(TEST_CONFIG)

#         with allure.step("Post Test Cleanup"):

#             with allure.step("Close workload"):
#                 workload_result = launch_validate_methods.close_workload(TEST_CONFIG)

#             with allure.step("Check for Timeout"):
#                 assert (not test_timed_out)

#             with allure.step("Check for valid exit process"):
#                 assert valid_exit_process

#             with allure.step("Check for valid exit code"):
#                 assert valid_exit_code

#             if TEST_CONFIG.threat_run:
#                 with allure.step("Check for Threatsim success"):
#                     if not threatsim_result:
#                         logger.error("test failed in subtest:" + TEST_CONFIG.test_name)
#                     assert threatsim_result

#             if not TEST_CONFIG.hardkill_workload:
#                 with allure.step("Check for Workload process exit code"):
#                     if not workload_result:
#                         logger.error("test failed in subtest:" + TEST_CONFIG.test_name)                
#                     assert workload_result

#         ENV_WORKLOAD_DB['detection_percent'] = "None"

#         END_RESULT = True
#         if TEST_CONFIG.enable_performance_parsing:
#             with allure.step("Performance Parsing"):
#                 perf_result = TEST_CONFIG.WORKLOAD.parse_performance(TEST_CONFIG)
#                 ENV_WORKLOAD_DB['performance_result'] = utils.bool_to_pass_fail(perf_result)
#                 try:
#                     print "DEGRADATION: " + str(TEST_CONFIG.WORKLOAD.degradation)
#                     print "KPI: " + str(TEST_CONFIG.kpi)
#                     performance_comparison = (float(TEST_CONFIG.WORKLOAD.degradation) <= float(TEST_CONFIG.kpi))
#                     print "PERFORMANCE VERDICT: " + utils.bool_to_pass_fail(performance_comparison)
#                     END_RESULT = END_RESULT and performance_comparison
#                     with allure.step("PERFORMANCE VERDICT: " + utils.bool_to_pass_fail(performance_comparison)):
#                         pass
#                     if not performance_comparison:
#                        logger.error("PERFORMANCE VERDICT: " + utils.bool_to_pass_fail(performance_comparison))
                        
                                           
#                 except:
#                     print "FAILED TO COMPUTE PERFORMANCE VERDICT"
#                     END_RESULT = False

#         if TEST_CONFIG.enable_false_positive_assertion:
#             with allure.step("Check for False Positive Failure"):
#                 END_RESULT = END_RESULT and false_positives_passing 
#                 print "FALSE POSITIVE VERDICT: " + utils.bool_to_pass_fail(false_positives_passing)
#                 with allure.step("FALSE POSITIVE VERDICT: " + utils.bool_to_pass_fail(false_positives_passing)):
#                     pass
#                 if not false_positives_passing:
#                     logger.error("FALSE POSITIVE VERDICT: " + utils.bool_to_pass_fail(false_positives_passing))
                    

#         if TEST_CONFIG.threat_run:
#             with allure.step("Record and Print efficacy results"):
#                 print DETECTION_RESULTS_ARRAY
#                 detection_percent = TEST_CONFIG.THREATSIM.record_results(DETECTION_RESULTS_ARRAY)
#                 ENV_WORKLOAD_DB['detection_percent'] = detection_percent
#                 TEST_CONFIG.THREATSIM.print_results(TEST_CONFIG)
#                 TEST_CONFIG.THREATSIM.write_threat_config(TEST_CONFIG)
#         else:
#             detection_percent = "Undefined"

#         if TEST_CONFIG.enable_efficacy_comparison:
#             with allure.step("KPI Comparison"):
#                 kpi = TEST_CONFIG.efficacy_kpi

#                 ENV_WORKLOAD_DB['kpi'] = str(kpi)
#                 print "Detection percent is " + str(detection_percent) + " and KPI is " + str(kpi)

#                 efficacy_comparison = int(detection_percent) >= int(kpi)
#                 ENV_WORKLOAD_DB['passed_efficacy'] = efficacy_comparison
#                 print "EFFICACY COMPARISON VERDICT: " + utils.bool_to_pass_fail(efficacy_comparison)
#                 END_RESULT = END_RESULT and efficacy_comparison
#                 with allure.step("EFFICACY COMPARISON VERDICT: " + utils.bool_to_pass_fail(efficacy_comparison)):
#                     pass
#                 if not efficacy_comparison:
#                     logger.error("EFFICACY COMPARISON VERDICT: " + utils.bool_to_pass_fail(efficacy_comparison) + "in" + str(TEST_CONFIG.test_name))


#         print "TEST RUN END RESULT: " + str(utils.bool_to_pass_fail(END_RESULT))
#         if constants.DEBUG_MODE:
#             print "DEBUG MODE ENABLED. TEST RESULT WILL RETURN TRUE BY DEFAULT. "
#             return True
#         else:
#             return END_RESULT


