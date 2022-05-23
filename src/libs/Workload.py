#
# Imports
#
import sys
import os
from src.config_files import constants


class Workload(object):
    # Initializer parameters
    #   name             Workload name, e.g. DiskSpd or PCMARK (required)
    #   command          Command to execute including the executable name and arguments (required)
    #   exe_name         Executable name, e.g. diskspd.exe or pcmark.exe (required)
    #                      used to kill the process
    def __init__(self,
                 test_config_dict):
        self.name = test_config_dict['workload_name']
        self.command = None
        self.degradation = None
        
        workload_script = test_config_dict['workload_name'] + "_Workload"
        sys.path.append(os.path.join(constants.FRAMEWORK_HOME_DIR, "src", "workloads"))
        self.workload_obj = getattr(__import__(workload_script), 'WORKLOAD')
        print(dir(self.workload_obj))


    # pre_actions - implement in a subclass if needed
    def pre_actions(self, test_config_dict):
        self.workload_obj.pre_actions(test_config_dict)
        return self.workload_obj.build_workload(test_config_dict)
        

    def construct_workload_exec_cmd(self):
        pass

    # post_actions - implement in a subclass if needed
    def post_actions(self, TEST_CONFIG):
        pass

    # parse_performance - implement in a subclass if needed
    def parse_performance(self, TEST_CONFIG):
        return True

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
