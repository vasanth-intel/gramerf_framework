#
# Imports
#
import sys
import os
from src.config_files.constants import *
from src.libs import utils

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
        # result is the overall results for the workload
        # it is a dict containing { test, {native, direct, sgx, direct_degradation, sgx_degradation} }
        self.result = dict()
                        
        workload_script = test_config_dict['workload_name'] + "_Workload"
        sys.path.append(os.path.join(FRAMEWORK_HOME_DIR, "src", "workloads"))
        self.workload_obj = getattr(__import__(workload_script), 'WORKLOAD')

    # pre_actions - implement in a subclass if needed
    def pre_actions(self, test_config_dict):
        self.workload_obj.pre_actions(test_config_dict)
        
    # setup_workload - implement in a subclass if needed
    def setup_workload(self, test_config_dict):
        return self.workload_obj.setup_workload(test_config_dict)
        

    # Build the workload execution command based on execution params and execute it.
    def execute_workload(self, test_config_dict):
        print("\n##### In execute_workload #####\n")

        for i in range(len(test_config_dict['exec_mode'])):
            print(f"\n-- Executing {test_config_dict['test_name']} in {test_config_dict['exec_mode'][i]} mode")
            for j in range(test_config_dict['iterations']):
                self.command = self.workload_obj.construct_workload_exec_cmd(test_config_dict, test_config_dict['exec_mode'][i], j+1)

                if self.command == None:
                    raise Exception(f"\n-- Failure: Unable to construct command for {test_config_dict['test_name']} Exec_mode: {test_config_dict['exec_mode'][i]}")

                cmd_output = utils.exec_shell_cmd(self.command)
                print(cmd_output)
                if cmd_output == None or utils.verify_output(cmd_output, test_config_dict['metric']) == False:
                    raise Exception(f"\n-- Failure: Test workload execution failed for {test_config_dict['test_name']} Exec_mode: {test_config_dict['exec_mode'][i]}")
                #subprocess.run(self.command, shell=True, check=True)


    # calculate the percent degradation
    @staticmethod
    def percent_degradation(baseline, testapp):
        return '{:0.3f}'.format(100 * (float(baseline) - float(testapp)) / float(baseline))


    def get_test_average(self, test_config_dict, exec_mode):
        metric_sum = 0
        for j in range(1, test_config_dict['iterations']+1):
            test_file_name = test_config_dict['test_name'] + '_' + exec_mode + '_' + str(j) + '.log'
            if not os.path.exists(test_file_name):
                raise Exception(f"\nFailure: File {test_file_name} does not exist for parsing performance..")

            metric_sum += float(self.workload_obj.get_metric_value(test_config_dict, test_file_name))

        return float(metric_sum / test_config_dict['iterations'])


    '''
    Read logs and capture the metrics values in a dictionary.
    '''
    def parse_performance(self, test_config_dict):
        print("\n###### In parse_performance #####\n")
        print(f"\n-- Performance results for {test_config_dict['test_name']}\n")
        os.chdir(LOGS_DIR)
        self.result[test_config_dict['test_name']] = dict()

        for i in range(len(test_config_dict['exec_mode'])):
            test_average = '{:0.3f}'.format(self.get_test_average(test_config_dict, test_config_dict['exec_mode'][i]))
            self.result[test_config_dict['test_name']][test_config_dict['exec_mode'][i]] = test_average

        os.chdir(FRAMEWORK_HOME_DIR)


    def calculate_degradation(self, test_config_dict):
        if 'native' in test_config_dict['exec_mode']:
            exec_mode = [y for y in test_config_dict['exec_mode'] if y != "native"]
            for y in exec_mode:
                deg_index = y + "-degradation"
                self.result[test_config_dict['test_name']][deg_index] = \
                    self.percent_degradation(self.result[test_config_dict['test_name']]['native'], \
                                            self.result[test_config_dict['test_name']][y])
        else:
            print(f"\n-- Workload not executed in 'native' mode. Cannot calculate performance degradation for {test_config_dict['test_name']}.")
            return

        print(self.result[test_config_dict['test_name']])


    # post_actions - implement in a subclass if needed
    def post_actions(self, TEST_CONFIG):
        pass


