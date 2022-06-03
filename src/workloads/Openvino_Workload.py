#
# Imports
#
import os
from src.libs.Workload import Workload
from src.config_files.constants import *
from src.libs import utils


# convert environment variable to boolean
def is_true(env):
    value = os.environ.get(env, 'false').lower()
    return value == 'true'

class OpenvinoWorkload(Workload):
    def __init__(self):
        pass
        
    def download_workload(self, test_config_dict):
        # Installing Openvino within "/home/intel/test/gramine/examples/openvino/openvino_2021"
        install_dir = os.path.join(self.workload_home_dir, 'openvino_2021')
        
        # We would not install if the installation dir already exists.
        if os.path.exists(install_dir):
            print("\n-- Openvino already installed. Not fetching from source..")
            return True
        os.makedirs(install_dir, exist_ok=True)
        
        distro, distro_version = utils.get_distro_and_version()
        if distro == 'ubuntu' and distro_version in ["18.04", "20.04"]:
            if distro_version == '18.04':
                toolkit_name = "l_openvino_toolkit_dev_ubuntu18_p_2021.4.752"
            else:
                toolkit_name = "l_openvino_toolkit_dev_ubuntu20_p_2021.4.752"
        elif distro == 'rhel':
            toolkit_name = "l_openvino_toolkit_dev_rhel8_p_2021.4.752"
        else:
            raise Exception("Unsupported distro for Openvino installation")
        
        wget_cmd = "wget https://storage.openvinotoolkit.org/repositories/openvino/packages/2021.4.2/" + toolkit_name + ".tgz"
        untar_cmd = "tar xzf " + toolkit_name  + ".tgz"

        print("\n-- Fetching Openvino workload from source..")
        if utils.exec_shell_cmd(wget_cmd).returncode != 0:
            raise Exception("Failure: Openvino workload download failed..")

        print("\n-- Extracting Openvino workload..")
        if utils.exec_shell_cmd(untar_cmd).returncode != 0:
            raise Exception("Failure: Openvino workload extraction failed..")

        os.rename(toolkit_name, 'openvino_2021')       

    def build_and_install_workload(self, test_config_dict):
        print("\n###### In build_and_install_workload #####\n")

        self.setupvars_path = os.path.join(self.workload_home_dir, 'openvino_2021/bin', 'setupvars.sh')

        if os.path.exists(self.setupvars_path):
            print(f"\n-- Building workload model '{test_config_dict['model_name']}'..\n")
            ov_env_var_bld_cmd = f"bash -c 'source {self.setupvars_path} && make benchmark_app openvino/.INSTALLATION_OK intel_models public_models'"
            print("\n-- Setting up OpenVINO environment variables and building Openvino..\n", ov_env_var_bld_cmd)

            if utils.exec_shell_cmd(ov_env_var_bld_cmd).returncode != 0: 
                raise Exception("Failed in Openvino build and install workload")
            
        # Check for build status by verifying the existence of model.xml file and return accordingly.
        model_file_path = os.path.join(FRAMEWORK_HOME_DIR, test_config_dict['model_dir'], test_config_dict['fp'], 
                            test_config_dict['model_name']+'.xml')
        if not os.path.exists(model_file_path):
            raise Exception(f"\n-- Failure: Model {model_file_path} not found/built. Returning without building the model.")

    def generate_manifest(self, test_config_dict):
        openvino_path = os.path.join(self.workload_home_dir, 'openvino_2021')
        inference_path = os.path.join(self.workload_home_dir, 'inference_engine_cpp_samples_build')

        manifest_cmd = "gramine-manifest -Dlog_level={} -Darch_libdir={} -Dopenvino_dir={} -Dinference_engine_cpp_samples_build={} \
                            benchmark_app.manifest.template > benchmark_app.manifest".format(
            LOG_LEVEL, os.environ.get('ARCH_LIBDIR'), openvino_path, inference_path
        )
        
        if utils.exec_shell_cmd(manifest_cmd).returncode != 0:
            raise Exception("Failed to generate manifest file for openvino workload")
        
    def pre_actions(self, test_config_dict):
        return utils.set_cpu_freq_scaling_governor()
        
    def setup_workload(self, test_config_dict):
        self.workload_home_dir = os.path.join(FRAMEWORK_HOME_DIR,test_config_dict['workload_home_dir'])

        self.download_workload(test_config_dict)
        self.build_and_install_workload(test_config_dict)
        self.generate_manifest(test_config_dict)

    def construct_workload_exec_cmd(self, test_config_dict, exec_mode = 'native', iteration=1):
        ov_exec_cmd = None
        exec_mode_str = './benchmark_app' if exec_mode == 'native' else exec_mode + ' benchmark_app'
        
        model_file_path = test_config_dict['model_dir'].split(test_config_dict['workload_home_dir'] + '/')[1]
        model_str = ' -m ' + os.path.join(model_file_path, 
                                test_config_dict['fp'],test_config_dict['model_name']+'.xml')

        output_file_name = LOGS_DIR + "/" + test_config_dict['test_name'] + '_' + exec_mode + '_' + str(iteration) + '.txt'

        print("\nOutput file name = ", output_file_name)
        if test_config_dict['metric'] == 'throughput':
            ov_exec_cmd = "KMP_AFFINITY=granularity=fine,noverbose,compact,1,0 " + \
                            exec_mode_str + model_str + \
                            " -d CPU -b 1 -t 20" + \
                            " -nstreams " + os.environ['THREADS_CNT'] + " -nthreads " + os.environ['THREADS_CNT'] + \
                            " -nireq " + os.environ['THREADS_CNT'] + " | tee " + output_file_name

        elif test_config_dict['metric'] == 'latency':
            ov_exec_cmd = "KMP_AFFINITY=granularity=fine,noverbose,compact,1,0 " + \
                            exec_mode_str + model_str + \
                            " -d CPU -b 1 -t 20" + \
                            " -api sync | tee " + output_file_name

        else:
            print("\n-- Failure: Internal error! Execution metric no set..")

        ov_exec_cmd = f"bash -c 'source {self.setupvars_path} && " + ov_exec_cmd + "'"
        print("\nCommand name = ", ov_exec_cmd)
        return ov_exec_cmd                           

    def execute_workload(self, test_config_dict, execForThroughput = True):
        pass

       
    def post_actions(self, TEST_CONFIG):
        pass

    def get_command(self, TEST_CONFIG):
        pass

    def get_metric_value(self, test_config_dict, test_file_name):
        with open(test_file_name, 'r') as test_fd:
            for line in test_fd:
                if test_config_dict['metric'].capitalize() in line:
                    return line.strip().split(': ')[1].split(' ')[0]
                        


    

WORKLOAD = OpenvinoWorkload()

#eof