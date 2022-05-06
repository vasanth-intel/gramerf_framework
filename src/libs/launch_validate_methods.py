import os
import sys
# import time
# from Queue import Queue, Empty
# import EAGLE
# import PQT
import src.libs.utils
# import yaml

from src.config_files import constants
import src.libs.phoenix_wrapper

# from src.libs.testapp_launch import BitShovelApp
# from src.libs.sc_simthreat import SideChannelSim
# from src.libs.mining_simthreat import MiningSim
# from src.libs.coinhive_threat import CoinHiveSim


class test_config_sc(object):
    def __init__(self,test_config):
        self.test_name = test_config.get("test_name")
        self.app_mode = test_config.get("app_mode","DETECTION")
        self.baseline_run = src.libs.utils.str_to_bool(test_config.get("run_baseline","False"))
        self.testapp_run = src.libs.utils.str_to_bool(test_config.get("run_testapp","True"))
        self.threat_run = src.libs.utils.str_to_bool(test_config.get("run_threat","True"))
        self.iterations = int(test_config.get("iterations","1")) # THIS IS THE THREATSIM ITERATIONS
        self.testapp_exec_message = test_config.get("testapp_exec_message","Executing...").strip('"')
        self.threatsim_exec_message = test_config.get("threatsim_exec_message","Start to simulate").strip('"')
        self.burst_size = int(test_config.get("burst_size","1"))
        self.throttle_delay = int(test_config.get("throttle_delay","0"))
        self.key_length = int(test_config.get("key_length","16"))
        self.threat_mode = test_config.get("threat_mode")
        self.profile = test_config.get("profile")
        self.workload = test_config.get("workload")
        self.test_type = test_config.get("test_type")
        self.timeout = int(test_config.get("timeout","2000"))
        self.result_folder = test_config.get("result_folder")
        self.efficacy_kpi = int(test_config.get("efficacy_kpi","100"))
        self.workload_args = test_config.get("workload_args")
        self.hardkill_workload = src.libs.utils.str_to_bool(test_config.get("hardkill_workload","True"))
        self.result_path = test_config.get("result_path")
        self.testid = test_config.get("testid")
        self.kpi = test_config.get("performance_kpi")
        self.fixed_delay = src.libs.utils.str_to_bool(test_config.get("fixed_delay")) # whether or not to use FIXED delays
        self.timeout_ms = test_config.get("timeout_ms","5000") # number of milliseconds per run of the threatsim before it cancels itself
        self.end_test_if_workload_exits = src.libs.utils.str_to_bool(test_config.get("end_test_if_workload_exits","True"))
        self.end_test_after_timeout = src.libs.utils.str_to_bool(test_config.get("end_test_after_timeout","True"))

        self.burst_size_start = test_config.get("burst_size_start","2")
        # the upper limit of bursts we want to test
        self.burst_size_stop = test_config.get("burst_size_stop","10")
        # whether or not the key length gets scaled by 1 / burst size
        # (ex: key length 250 in the config, but with burst size 2 would run 2 bursts with key length 125)
        self.enable_burst_scaling = src.libs.utils.str_to_bool(test_config.get("enable_burst_scaling","True"))
        self.burst_size_step=test_config.get("burst_size_step","1")

        self.key_length_start = test_config.get("key_length_start","100")
        self.key_length_stop = test_config.get("key_length_stop", "300")
        self.key_length_step = test_config.get("key_length_step", "50")

        self.throttle = test_config.get("throttle_delay","0")
        self.throttle_delay_start = test_config.get("throttle_delay_start", "100")
        self.throttle_delay_stop = test_config.get("throttle_delay_stop", "1000")
        self.throttle_delay_step = test_config.get("throttle_delay_step", "150")

        self.enable_efficacy_parsing = src.libs.utils.str_to_bool(test_config.get("enable_efficacy_parsing", "False"))
        self.enable_efficacy_comparison = src.libs.utils.str_to_bool(test_config.get("enable_efficacy_comparison", "False"))
        self.enable_false_positive_assertion = src.libs.utils.str_to_bool(test_config.get("enable_false_positive_assertion", "False"))
        self.enable_performance_parsing = src.libs.utils.str_to_bool(test_config.get("enable_performance_parsing", "False"))

        self.threads = test_config.get("threads","1")
        self.threads_start = test_config.get("threads_start", "1")
        self.threads_stop = test_config.get("threads_stop", "4")
        self.threads_step = test_config.get("threads_step", "1")

        self.hashes = test_config.get("hashes","20")
        self.hashes_start = test_config.get("hashes_start", "10")
        self.hashes_stop = test_config.get("hashes_stop", "120")
        self.hashes_step = test_config.get("hashes_step", "10")

        self.duration = test_config.get("duration","0")
        self.duration_start = test_config.get("duration_start", "30000")
        self.duration_stop = test_config.get("duration_stop", "50000")
        self.duration_step = test_config.get("duration_step", "10000")

        self.threat_type = test_config.get("threat_type")
        self.coinhive_browser = test_config.get("coinhive_browser")
        self.is_baseline = False




# def get_workload(TEST_CONFIG):
#     if TEST_CONFIG.workload == "DUMMY":
#         WORKLOAD = EAGLE.Workload("Dummy", None, "no exe name for dummy workload")
#     else:
#         workload_script = TEST_CONFIG.workload + "_WORKLOAD"
#         current_path = os.getcwd()
#         sys.path.append(os.path.join(current_path, "src", "workloads"))
#         WORKLOAD = getattr(__import__(workload_script), 'WORKLOAD')
#     return WORKLOAD

# def launch_workload(TEST_CONFIG):
#     # create subfolder for TestApp results
#     if TEST_CONFIG.is_baseline:
#         TEST_CONFIG.result_folder = os.path.join(TEST_CONFIG.WORKLOAD.log_dir, TEST_CONFIG.result_path, TEST_CONFIG.test_name, TEST_CONFIG.WORKLOAD.baseline_subdir)
#     else:
#         TEST_CONFIG.result_folder = os.path.join(TEST_CONFIG.WORKLOAD.log_dir, TEST_CONFIG.result_path, TEST_CONFIG.test_name, TEST_CONFIG.WORKLOAD.testapp_subdir)

#     if not os.path.isdir(TEST_CONFIG.result_folder):
#         os.makedirs( TEST_CONFIG.result_folder )

#     TEST_CONFIG.WORKLOAD.result_type_folder = TEST_CONFIG.result_folder
#     TEST_CONFIG.WORKLOAD.pre_actions(TEST_CONFIG)

#     if TEST_CONFIG.workload == "DUMMY":
#         workload_pqt = PQT.dummy_PQT()
#     else:
#         workload_pqt = PQT.create_PQT(TEST_CONFIG.WORKLOAD.working_dir, TEST_CONFIG.WORKLOAD.command, "workloadData.txt", TEST_CONFIG.WORKLOAD.exe_name)

#     TEST_CONFIG.WORKLOAD.pqt = workload_pqt
#     time.sleep(constants.POST_WORKLOAD_DELAY)
#     TEST_CONFIG.PQT_List.append(workload_pqt)


# def get_test_app(TEST_CONFIG):
#     TESTAPP = BitShovelApp(TEST_CONFIG.app_mode, TEST_CONFIG.test_name)
#     return TESTAPP

# def launch_test_app(TEST_CONFIG):
#     command = TEST_CONFIG.TESTAPP.launch_test_app(TEST_CONFIG)
#     TEST_CONFIG.TESTAPP.pre_actions(TEST_CONFIG)
#     testapp_pqt = PQT.create_PQT(constants.sdk_package, command, constants.Testapp_OutputFile, TEST_CONFIG.TESTAPP.exe_name)

#     TEST_CONFIG.TESTAPP.pqt = testapp_pqt
#     TEST_CONFIG.TESTAPP.increment_iteration()  # increments a counter to keep data collection csvs separate
#     TEST_CONFIG.PQT_List.append(testapp_pqt)

#     # sleep a moment after the test app has started
#     time.sleep(constants.POST_TESTAPP_DELAY)

# def validate_testapp(TEST_CONFIG):
#     TESTAPP_FILE_PARSE = False
#     TEST_CONFIG.TESTAPP.post_actions(TEST_CONFIG)
#     TEST_CONFIG.TESTAPP.kill()
#     time.sleep(2)
#     testapp_file_path = os.path.join(TEST_CONFIG.result_folder, constants.Testapp_OutputFile)
#     output_list = []
#     queue = TEST_CONFIG.TESTAPP.pqt.queue
#     while not queue.empty():
#         try:
#             line = queue.get_nowait()
#             output_list.append(line)
#         except Exception as e:
#             print str(e)
#     for i in output_list:
#         queue.put(i)
#         if TEST_CONFIG.testapp_exec_message in i:
#             TESTAPP_FILE_PARSE = True

#     TEST_CONFIG.TESTAPP.pqt.flushOutput(TEST_CONFIG.result_folder)
#     return TESTAPP_FILE_PARSE

# def get_threat_sim(TEST_CONFIG):
#     if TEST_CONFIG.threat_type == "SC":
#         THREATSIM = SideChannelSim()
#     elif TEST_CONFIG.threat_type == "COINHIVE":
#         THREATSIM = CoinHiveSim()
#     elif TEST_CONFIG.threat_type == "MINING_SIM":
#         THREATSIM = MiningSim()
#     return THREATSIM

# def launch_threat_sim(TEST_CONFIG):
#     command = TEST_CONFIG.THREATSIM.get_command(TEST_CONFIG)

#     TEST_CONFIG.THREATSIM.pre_actions(TEST_CONFIG)
#     threatsim_pqt = PQT.create_PQT(TEST_CONFIG.THREATSIM.root_directory, command, constants.ThreatSim_OutputFile,
#                                    TEST_CONFIG.THREATSIM.exe_name, False)
#     TEST_CONFIG.THREATSIM.set_threat_pid(threatsim_pqt.pid)

#     TEST_CONFIG.THREATSIM.pqt = threatsim_pqt
#     TEST_CONFIG.PQT_List.append(threatsim_pqt)
#     TEST_CONFIG.THREATSIM.increment_iteration()

# def validate_threatsim(TEST_CONFIG):
#     THREATSIM_FILE_PARSE = False
#     TEST_CONFIG.THREATSIM.post_actions(TEST_CONFIG)
#     TEST_CONFIG.THREATSIM.kill()
#     time.sleep(2)
#     threatsim_file_path = os.path.join(TEST_CONFIG.result_folder, constants.ThreatSim_OutputFile)
#     output_list = []
#     queue = TEST_CONFIG.THREATSIM.pqt.queue
#     while not queue.empty():
#         try:
#             line = queue.get_nowait()
#             output_list.append(line)
#         except Exception as e:
#             print str(e)
#     for i in output_list:
#         queue.put(i)
#         if TEST_CONFIG.threatsim_exec_message in i:
#             THREATSIM_FILE_PARSE = True

#     if (TEST_CONFIG.threat_type == "COINHIVE") and (TEST_CONFIG.threatsim_exec_message == ""):
#         print "parse the Threat Sim file and Threat Sim message of coinhive simulator"
#         THREATSIM_FILE_PARSE = True

#     TEST_CONFIG.THREATSIM.pqt.flushOutput(TEST_CONFIG.result_folder)
#     return THREATSIM_FILE_PARSE


# def check_process(TEST_CONFIG):
#     (pqt_finished, exit_code) = utils.check_process_list(TEST_CONFIG.PQT_List, TEST_CONFIG)
#     return (pqt_finished, exit_code)

# def check_for_timeout(pqt_finished, exit_code, TEST_CONFIG):
#     if exit_code == None and pqt_finished == None:
#         TEST_CONFIG.test_timed_out = True
#         print "Job-Imposed workload timeout hit at " + str(TEST_CONFIG.timeout) + " seconds"
#         print "#" * 100
#         return True
#     else:
#         return False

# def parse_exit_code(pqt_finished, exit_code, TEST_CONFIG):
#     if exit_code != 0:
#         print "ERROR in execution with PQT "

#         if exit_code == None:
#             print "No exit code provided."
#         else:
#             print "Exit code: " + str(exit_code)

#         if pqt_finished == None:
#             print "No exiting PQT Command."
#         else:
#             print "PQT Command that exited: " + str(pqt_finished.command)
#             pqt_finished.print_output()

#         print "#" * 100
#         return False
#     # Everything is OK
#     else:
#         return True

# # was the exiting process not supposed to exit? For example, the Testapp should not be exiting here
# def check_for_valid_process_exit(pqt_finished, exit_code, TEST_CONFIG):
#     # we do not allow testapp to exit and cause the test to end
#     if pqt_finished == TEST_CONFIG.TESTAPP.pqt:
#         print "Testapp exitted with exit code " + str(exit_code) + " which is not allowed!"
#         return False
#     # for now, any other process which ends is valid.
#     else:
#         return True

# # should the test end now that a certain process has exited?
# def check_if_test_should_end(pqt_finished, TEST_CONFIG):
#     if pqt_finished == TEST_CONFIG.WORKLOAD.pqt:
#         print "WORKLOAD HAS FINISHED"
#         # we need a way to cancel threatsim runs once the workload ends
#         if TEST_CONFIG.end_test_if_workload_exits:
#             return True
#         else:
#             return False
#     return  False

# # ensures that the workload closes, either immediately or waiting for it to finish.
# def close_workload(TEST_CONFIG):
#     # END WORKLOAD RIGHT AWAY IN THESE CASES
#     if TEST_CONFIG.WORKLOAD.pqt.isRunning() and (TEST_CONFIG.hardkill_workload or TEST_CONFIG.test_timed_out):
#         print "WARNING: HARD KILLING WORKLOAD!"
#         workload_result = False
#     # OR PATIENTLY WAIT FOR THE WORKLOAD TO FINISH, REGARDLESS OF WHAT ELSE HAPPENED
#     else:
#         (pqt, exit_code) = utils.check_process_list([TEST_CONFIG.WORKLOAD.pqt], TEST_CONFIG)
#         workload_result = (exit_code == 0)
#     TEST_CONFIG.WORKLOAD.post_actions(TEST_CONFIG)

#     TEST_CONFIG.WORKLOAD.pqt.flushOutput(TEST_CONFIG.result_folder)
#     time.sleep(2)
#     TEST_CONFIG.WORKLOAD.kill()
#     return workload_result

# def launch_office(test_config_obj):
#     os.system("robocopy " + os.path.join(os.getcwd(), "src", "workloads", "AppTests", "Applications", "TestDocuments") +
#               " " + os.environ['USERPROFILE'] + "\Desktop\OfficeDocuments /Z /W:10 /NP /FFT")
#     test_name = test_config_obj.test_name
#     results = []
#     ENV_OFFICE_VERSION = yaml.load(test_config_obj.workload_args)['OFFICE_VERSION']
#     ENV_OFFICE_BITS = yaml.load(test_config_obj.workload_args)['OFFICE_BITS']
#     ENV_OS = yaml.load(test_config_obj.workload_args)['OS']
#     ENV_WORKLOAD = yaml.load(test_config_obj.workload_args)['WORKLOAD_NAME']

#     if ENV_WORKLOAD == "WINWORD":
#         if ENV_OS == "32":
#             WORKLOAD_SCENARIOS = ["PROPERTIES", "TABLE"]
#         else:
#             WORKLOAD_SCENARIOS = ["PROPERTIES", "TABLE", "MACRO"]
#     elif ENV_WORKLOAD == "EXCEL":
#         if ENV_OFFICE_BITS == "32":
#             if ENV_OFFICE_VERSION == "2007":
#                 if ENV_OS == "32":
#                     WORKLOAD_SCENARIOS = ["CHART", "FORMATTING", "FORMULA"]
#                 else:
#                     WORKLOAD_SCENARIOS = ["CHART", "FORMATTING", "FORMULA", "MACRO"]
#             elif ENV_OFFICE_VERSION == "2010":
#                 if ENV_OS == "32":
#                     WORKLOAD_SCENARIOS = ["CHART", "FORMATTING", "FORMULA"]
#                 else:
#                     WORKLOAD_SCENARIOS = ["CHART", "FORMATTING", "FORMULA", "MACRO", "OLE_FORMAT", "OLE_INSERT_PDF",
#                                           "OLE_INSERT_TABLE"]
#             elif ENV_OFFICE_VERSION == "2013":
#                 if ENV_OS == "32":
#                     WORKLOAD_SCENARIOS = ["CHART", "FORMATTING", "FORMULA"]
#                 else:
#                     WORKLOAD_SCENARIOS = ["CHART", "FORMATTING", "FORMULA", "MACRO", "OLE_FORMAT", "OLE_INSERT_PDF",
#                                           "OLE_INSERT_TABLE"]
#             elif ENV_OFFICE_VERSION == "2016":
#                 WORKLOAD_SCENARIOS = ["CHART", "FORMATTING", "FORMULA", "MACRO"]
#             else:
#                 WORKLOAD_SCENARIOS = ["CHART", "FORMATTING", "FORMULA", "MACRO"]
#     elif ENV_WORKLOAD == "OUTLOOK":
#         if ENV_OFFICE_BITS == "32":
#             if ENV_OFFICE_VERSION == "2007":
#                 if ENV_OS == "32":
#                     WORKLOAD_SCENARIOS = ["CreateContact", "DeleteContact", "ReadMail", "Folders"]
#                 else:
#                     WORKLOAD_SCENARIOS = ["CreateContact", "DeleteContact", "ReadMail", "Folders", "Attachments"]
#             else:
#                 WORKLOAD_SCENARIOS = ["CreateContact", "DeleteContact", "ReadMail", "Folders", "Attachments"]
#         else:
#             WORKLOAD_SCENARIOS = ["CreateContact", "DeleteContact", "ReadMail", "Folders", "Attachments"]

#     elif ENV_WORKLOAD == "POWERPOINT":
#         WORKLOAD_SCENARIOS = ["PICTURE"]
#     for scenario in WORKLOAD_SCENARIOS:
#         test_config_obj.test_scenario = scenario
#         test_config_obj.test_name = test_name + "_" + scenario
#         test_result = src.libs.phoenix_wrapper.run_test(test_config_obj)
#         results.append(test_result)

#     return results

# def launch_adobe(test_config_obj):
#     os.system("robocopy " + os.path.join(os.getcwd(), "src", "workloads", "AppTests", "Applications", "TestDocuments") +
#               " " + os.environ['USERPROFILE'] + "\Desktop\OfficeDocuments /Z /W:10 /NP /FFT")
#     ENV_ADOBE_VERSION = yaml.load(test_config_obj.workload_args)['ADOBE_VERSION']
#     ENV_OS = yaml.load(test_config_obj.workload_args)['OS']
#     ENV_WORKLOAD = yaml.load(test_config_obj.workload_args)['WORKLOAD_NAME']
#     test_name = test_config_obj.test_name
#     results = []
#     if ENV_ADOBE_VERSION == "9":
#         if ENV_OS == "32":
#             WORKLOAD_SCENARIOS = ["CountWords", "GetTitle", "MovePage"]
#         else:
#             WORKLOAD_SCENARIOS = ["CountWords", "GetTitle", "MovePage", "OpenClose", "Properties", "ReadFile",
#                                   "TextSelection"]
#     elif ENV_ADOBE_VERSION == "10":
#         if ENV_OS == "32":
#             WORKLOAD_SCENARIOS = ["GetTitle", "OpenClose", "Properties", "ReadFile", "TextSelection"]
#         else:
#             WORKLOAD_SCENARIOS = ["GetTitle", "MovePage", "OpenClose", "Properties", "ReadFile", "TextSelection"]
#     elif ENV_ADOBE_VERSION == "11":
#         if ENV_OS == "32":
#             WORKLOAD_SCENARIOS = ["GetTitle", "OpenClose", "Properties", "ReadFile", "TextSelection"]
#         else:
#             WORKLOAD_SCENARIOS = ["GetTitle", "MovePage", "OpenClose", "Properties", "ReadFile", "TextSelection"]
#     for scenario in WORKLOAD_SCENARIOS:
#         test_config_obj.test_scenario = scenario
#         test_config_obj.test_name = test_name + "_" + scenario
#         test_result = src.libs.phoenix_wrapper.run_test(test_config_obj)
#         results.append(test_result)

#     return results


# def launch_serverbenchmarks(test_config_obj, function_override=None):
#     tests = yaml.load(test_config_obj.workload_args)['BENCHMARKS']
#     results = []
#     test_name = test_config_obj.test_name
#     for scenario in tests:
#         print scenario
#         test_config_obj.test_scenario = scenario
#         test_config_obj.test_name = test_name + "_" + scenario
#         if function_override == None:
#             test_result = src.libs.phoenix_wrapper.run_test(test_config_obj)
#         else:
#             test_result = function_override(test_config_obj)
#         results.append(test_result)
#     return results
