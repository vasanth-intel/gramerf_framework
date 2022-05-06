#
# Imports
#
import sys
import os
import time
import psutil
from src.config_files import constants


class Workload(object):
    # Initializer parameters
    #   name             Workload name, e.g. DiskSpd or PCMARK (required)
    #   command          Command to execute including the executable name and arguments (required)
    #   exe_name         Executable name, e.g. diskspd.exe or pcmark.exe (required)
    #                      used to kill the process
    #   working_dir      Directory to set as the working directory before running the command
    #                      default: C:/VALIDATION/workloads/<name>
    #   log_dir          Root directory for logging
    #                      default: <JK_LOCAL_VAL_REPO>/tests/logs/results/<name>
    #   baseline_subdir  Logging subdirectory for baseline results
    #                      default: baseline
    #                      Note: variable baseline_dir is set to <log_dir>/<baseline_dir>
    #   testapp_subdir   Logging subdirectory for testapp results
    #                      default: testapp
    #                      Note: variable testapp_dir is set to <log_dir>/<testapp_dir>
    def __init__(self,
                 name,
                 command,
                 exe_name,
                 working_dir = None,
                 log_dir = None,
                 baseline_subdir ='baseline',
                 testapp_subdir = 'testapp'):
        self.name = name
        self.command = command
        self.exe_name = exe_name
        self.degradation = None

    # pre_actions - implement in a subclass if needed
    def pre_actions(self, TEST_CONFIG, resultsdir = None):
        pass

    # post_actions - implement in a subclass if needed
    def post_actions(self, TEST_CONFIG):
        pass

    # parse_performance - implement in a subclass if needed
    def parse_performance(self, TEST_CONFIG):
        return True

    # update_test_config_from_cmd_line - implement in a subclass if needed
    def update_test_config_from_cmd_line(self):
        pass

    def kill(self):
        pass
        #kill_exes([self.exe_name])

    def get_performance_degradation(self):
        return self.degradation

    @staticmethod
    def calculate_degradation(baseline, testapp, type):
        degradation = ""
        baseline = float(baseline)
        testapp = float(testapp)
        if testapp > 0 and (baseline == "" or baseline == 0):
            # Native Failure
            degradation = "NAT"
        elif baseline > 0 and (testapp == "" or testapp == 0):
            # BT Failure
            degradation = "BT"
        elif (baseline == "" or (baseline) == 0) and (testapp == "" or testapp == 0):
            # Test Failure
            degradation = "F"
        else:
            if type == "LIB":
                if baseline > 0:
                    degradation = str(((testapp / baseline) - 1) * 100)
            elif type == "HIB":
                if testapp > 0:
                    degradation = str(((baseline / testapp) - 1) * 100)
        if degradation == "":
            degradation = "F"
        return degradation
