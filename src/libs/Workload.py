import time
from src.config_files.constants import *
from src.libs import utils
import src.workloads as workloads
from conftest import trd


class Workload(object):
    """
    Base class for all workloads. Generic actions are taken here.
    All workload specific actions would be implemented in the respective
    derived workload class.
    """
    def __init__(self,
                 test_config_dict):
        self.name = test_config_dict['workload_name']
        self.command = None

        workload_script = test_config_dict['workload_name'] + "Workload"
        self.workload_class = getattr(globals()["workloads"], workload_script)
        self.workload_obj = self.workload_class(test_config_dict)

    def pre_actions(self, test_config_dict):
        """
        Performs pre-actions for the workload.
        :param test_config_dict: Test config data
        :return:
        """
        self.workload_obj.pre_actions(test_config_dict)

    # setup_workload - implement in a subclass if needed
    def setup_workload(self, test_config_dict):
        return self.workload_obj.setup_workload(test_config_dict)

    # Build the workload execution command based on execution params and execute it.
    def execute_workload(self, tcd):
        print("\n##### In execute_workload #####\n")
        test_dict = {}
        global trd

        for e_mode in tcd['exec_mode']:
            print(f"\n-- Executing {tcd['test_name']} in {e_mode} mode")
            test_dict[e_mode] = []
            for j in range(tcd['iterations']):
                self.command = self.workload_obj.construct_workload_exec_cmd(tcd, e_mode, j + 1)

                if self.command is None:
                    raise Exception(
                        f"\n-- Failure: Unable to construct command for {tcd['test_name']} Exec_mode: {e_mode}")

                cmd_output = utils.exec_shell_cmd(self.command)
                print(cmd_output)
                if cmd_output is None or utils.verify_output(cmd_output, tcd['metric']) is False:
                    raise Exception(
                        f"\n-- Failure: Test workload execution failed for {tcd['test_name']} Exec_mode: {e_mode}")

                test_file_name = LOGS_DIR + '/' + tcd['test_name'] + '_' + e_mode + '_' + str(j+1) + '.log'
                if not os.path.exists(test_file_name):
                    raise Exception(f"\nFailure: File {test_file_name} does not exist for parsing performance..")
                metric_val = float(self.workload_obj.get_metric_value(tcd, test_file_name))
                test_dict[e_mode].append(metric_val)
                
                time.sleep(TEST_SLEEP_TIME_BW_ITERATIONS)

        if 'native' in tcd['exec_mode']:
            test_dict['native-avg'] = '{:0.3f}'.format(sum(test_dict['native'])/len(test_dict['native']))

            if 'gramine-direct' in tcd['exec_mode']:
                test_dict['direct-avg'] = '{:0.3f}'.format(
                    sum(test_dict['gramine-direct'])/len(test_dict['gramine-direct']))
                test_dict['direct-deg'] = self.percent_degradation(test_dict['native-avg'], test_dict['direct-avg'])

            if 'gramine-sgx' in tcd['exec_mode']:
                test_dict['sgx-avg'] = '{:0.3f}'.format(sum(test_dict['gramine-sgx'])/len(test_dict['gramine-sgx']))
                test_dict['sgx-deg'] = self.percent_degradation(test_dict['native-avg'], test_dict['sgx-avg'])

        trd[tcd['workload_name']] = trd.get(tcd['workload_name'], {})
        trd[tcd['workload_name']].update({tcd['test_name']: test_dict})

    # calculate the percent degradation
    @staticmethod
    def percent_degradation(baseline, testapp):
        return '{:0.3f}'.format(100 * (float(baseline) - float(testapp)) / float(baseline))
