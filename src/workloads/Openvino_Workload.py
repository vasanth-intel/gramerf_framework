#
# Imports
#
import pytest
import collections
import os
import psutil
import time
import shutil
from src.libs.Workload import Workload
import conftest
from src.config_files import constants


# convert environment variable to boolean
def is_true(env):
    value = os.environ.get(env, 'false').lower()
    return value == 'true'

class OpenvinoWorkload(Workload):

    def update_test_config_from_cmd_line(self):
        if pytest.config.getoption('--iterations') != 1:
            conftest.test_config_dict['iterations'] = pytest.config.getoption('iterations')

        if pytest.config.getoption('--exec_mode') != '' and pytest.config.getoption('--exec_mode') != 'None':
            conftest.test_config_dict['exec_mode'] = pytest.config.getoption('exec_mode').split(' ')
                        
        if pytest.config.getoption('--fp') != '' and pytest.config.getoption('--fp') != 'None':
            conftest.test_config_dict['fp'] = pytest.config.getoption('fp').split(' ')

        print (conftest.test_config_dict)

    '''
    This method renames the existing manifest to original manifest (as '.ori'), copies
    the manifest (latency/throughput) that needs to be overridden into the workload home dir
    and renames the copied manifest to the expected name by the workload.
    '''
    def replace_manifest_file(self, test_config_obj, buildForThroughput = None):
        original_manifest_file = os.path.join(test_config_obj.workload_home_dir, test_config_obj.original_manifest_file)
        if buildForThroughput == True:
            override_manifest_file = os.path.join(constants.FRAMEWORK_HOME_DIR, test_config_obj.throughput_manifest_file)
        elif buildForThroughput == False:
            override_manifest_file = os.path.join(constants.FRAMEWORK_HOME_DIR, test_config_obj.latency_manifest_file)
        os.rename(original_manifest_file, original_manifest_file+'.ori')
        # Copy the workload specific manifest to workload dir and 
        # rename the same as per the expected original name
        shutil.copy2(override_manifest_file, test_config_obj.workload_home_dir)
        if buildForThroughput == True:
            tmp_original_file = os.path.join(test_config_obj.workload_home_dir, os.path.basename(test_config_obj.throughput_manifest_file))
        elif buildForThroughput == False:
            tmp_original_file = os.path.join(test_config_obj.workload_home_dir, os.path.basename(test_config_obj.latency_manifest_file))
        os.rename(tmp_original_file, original_manifest_file)

    def build_workload(self, test_config_obj, buildForThroughput = None):
        cwd = os.getcwd()

        if buildForThroughput == None:
            return
        elif buildForThroughput:
            self.replace_manifest_file(test_config_obj, True)
            
            #os.rename(override_manifest_file, original_manifest_file)
        else:
            self.replace_manifest_file(test_config_obj, False)

            #os.rename(override_manifest_file, original_manifest_file)

        #After the build is complete we need to del the existing overridden manifest and rename
        #manifest.ori to the expected original name by the workload
        os.chdir(cwd)


    def pre_actions(self, test_config_obj):
        #global tco

        #print(tco)
        if not os.path.exists(test_config_obj.model_dir):
            self.build_workload(test_config_obj, True)
            print("\n****** Model dir does not exist ******")
        else:
            # Model is present. Check for the existence of .xml
            print("\n****** Model dir exists ******", test_config_obj.model_dir)
            self.build_workload(test_config_obj, True)
            #print(test_config_obj.iterations)
            print(len(test_config_obj.metrics))
         #       os.mkdir(self.result_type_folder)
        #get command
        #self.command = self.get_command(TEST_CONFIG)


    def __init__(self,
                 name,
                 command,
                 exe_name,
                 working_dir=None,
                 log_dir=None,
                 baseline_subdir='baseline',
                 testapp_subdir='testapp'):

        self.preexisting_pids = psutil.pids()
        # if ENV_OperatingSystem == "Linux":
        #     self.exe_name=exe_name.split(".")[0]
        # elif ENV_OperatingSystem == "Windows":
        #     self.exe_name=exe_name


        # result is the overall score for all benchmarks
        # it is a list containing [baseline_score, testapp_score, percent_degradaton]
        self.result = []
        # self.records are the individual benchmark results
        # {benchmark, [baseline_score, testapp_score, percent_degradaton]}
        self.records = collections.OrderedDict()
        time.sleep(1)
        super(OpenvinoWorkload, self).__init__(name,
                                              command,
                                              exe_name,
                                              working_dir,
                                              log_dir,
                                              baseline_subdir,
                                              testapp_subdir)

    def post_actions(self, TEST_CONFIG):
        pass

    def get_command(self, TEST_CONFIG):
        pass

    # calculate the percent degradation
    @staticmethod
    def percent_degradation(baseline, testapp):
        return '{:0.3f}'.format(100 * (float(baseline) - float(testapp)) / float(baseline))

    def parse_performance(self, TEST_CONFIG):
        pass
    


#eof