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
        untar_cmd = "tar xzf " + toolkit_name + ".tgz"

        print("\n-- Fetching and extracting Openvino workload from source..")
        utils.exec_shell_cmd(wget_cmd)
        utils.exec_shell_cmd(untar_cmd)
        os.rename(toolkit_name, 'openvino_2021')

    def download_and_convert_model(self, test_config_dict, model_file_path):
        if not os.path.exists(model_file_path):
            os.chdir("openvino_2021/deployment_tools/open_model_zoo/tools/downloader")
            download_cmd = "python3 ./downloader.py --name {0} -o {1}/model".format(test_config_dict['model_name'], self.workload_home_dir)
            convert_cmd = "python3 ./converter.py --name {0} -d {1}/model -o {1}/model".format(test_config_dict['model_name'], self.workload_home_dir)
            convert_cmd = f"bash -c 'source {self.setupvars_path} && source {self.workload_home_dir}/openvino/bin/activate && {convert_cmd}'"
            print("\n-- Model download cmd:", download_cmd)
            utils.exec_shell_cmd(download_cmd)
            print("\n-- Model convert cmd:", convert_cmd)
            utils.exec_shell_cmd(convert_cmd)
        else:
            print("\n-- Models are already downloaded.")

        os.chdir(self.workload_home_dir)

    def build_and_install_workload(self, test_config_dict):
        print("\n###### In build_and_install_workload #####\n")

        self.setupvars_path = os.path.join(self.workload_home_dir, 'openvino_2021/bin', 'setupvars.sh')

        if os.path.exists(self.setupvars_path):
            print(f"\n-- Building workload model '{test_config_dict['model_name']}'..\n")
            ov_env_var_bld_cmd = f"bash -c 'source {self.setupvars_path} && make benchmark_app openvino/.INSTALLATION_OK'"
            print("\n-- Setting up OpenVINO environment variables and building Openvino..\n", ov_env_var_bld_cmd)

            openvino_make_log = LOGS_DIR + "/openvino" + test_config_dict['model_name'] + '_make.log'
            log_fd = open(openvino_make_log, "w")
            utils.exec_shell_cmd(ov_env_var_bld_cmd, log_fd)
            log_fd.close()
            
        model_file_path = os.path.join(FRAMEWORK_HOME_DIR, test_config_dict['model_dir'], test_config_dict['fp'], 
                            test_config_dict['model_name']+'.xml')

        self.download_and_convert_model(test_config_dict, model_file_path)

        # Check for build status by verifying the existence of model.xml file and return accordingly.
        if not os.path.exists(model_file_path):
            raise Exception(f"\n-- Failure: Model {model_file_path} not found/built. Returning without building the model.")

    def generate_manifest(self):
        openvino_path = os.path.join(self.workload_home_dir, 'openvino_2021')
        inference_path = os.path.join(self.workload_home_dir, 'inference_engine_cpp_samples_build')

        manifest_cmd = "gramine-manifest -Dlog_level={} -Darch_libdir={} -Dopenvino_dir={} -Dinference_engine_cpp_samples_build={} \
                            benchmark_app.manifest.template > benchmark_app.manifest".format(
            LOG_LEVEL, os.environ.get('ARCH_LIBDIR'), openvino_path, inference_path
        )
        
        utils.exec_shell_cmd(manifest_cmd)

    def install_mimalloc(self):
        if os.path.exists(MIMALLOC_INSTALL_PATH):
            print("\n-- Library 'mimalloc' already exists.. Returning without rebuilding.\n")
            return

        print("\n-- Setting up mimalloc for Openvino..\n", MIMALLOC_CLONE_CMD)
        utils.exec_shell_cmd(MIMALLOC_CLONE_CMD)
        mimalloc_dir = os.path.join(self.workload_home_dir, 'mimalloc')
        os.chdir(mimalloc_dir)
        mimalloc_make_dir_path = os.path.join(mimalloc_dir, 'out/release')
        os.makedirs(mimalloc_make_dir_path, exist_ok=True)
        os.chdir(mimalloc_make_dir_path)

        utils.exec_shell_cmd("cmake ../..")
        utils.exec_shell_cmd("make")
        utils.exec_shell_cmd("sudo make install")

        os.chdir(self.workload_home_dir)

        if not os.path.exists(MIMALLOC_INSTALL_PATH):
            raise Exception(f"\n-- Library {MIMALLOC_INSTALL_PATH} not generated/installed.\n")

    def pre_actions(self, test_config_dict):
        self.workload_home_dir = os.path.join(FRAMEWORK_HOME_DIR,test_config_dict['workload_home_dir'])

        utils.set_threads_cnt_env_var()
        utils.set_cpu_freq_scaling_governor()
        self.install_mimalloc()

    def setup_workload(self, test_config_dict):
        self.download_workload(test_config_dict)
        self.build_and_install_workload(test_config_dict)
        self.generate_manifest()

    def construct_workload_exec_cmd(self, test_config_dict, exec_mode = 'native', iteration=1):
        ov_exec_cmd = None
        exec_mode_str = './benchmark_app' if exec_mode == 'native' else exec_mode + ' benchmark_app'
        
        model_file_path = test_config_dict['model_dir'].split(test_config_dict['workload_home_dir'] + '/')[1]
        model_str = ' -m ' + os.path.join(model_file_path, 
                                test_config_dict['fp'],test_config_dict['model_name']+'.xml')

        output_file_name = LOGS_DIR + "/" + test_config_dict['test_name'] + '_' + exec_mode + '_' + str(iteration) + '.log'

        print("\nOutput file name = ", output_file_name)
        if test_config_dict['metric'] == 'Throughput':
            ov_exec_cmd = "KMP_AFFINITY=granularity=fine,noverbose,compact,1,0 " + \
                            exec_mode_str + model_str + \
                            " -d CPU -b 1 -t 20" + \
                            " -nstreams " + os.environ['THREADS_CNT'] + " -nthreads " + os.environ['THREADS_CNT'] + \
                            " -nireq " + os.environ['THREADS_CNT'] + " | tee " + output_file_name

            os.environ['LD_PRELOAD'] = TCMALLOC_INSTALL_PATH if exec_mode == 'native' else ''

        elif test_config_dict['metric'] == 'Latency':
            ov_exec_cmd = "KMP_AFFINITY=granularity=fine,noverbose,compact,1,0 " + \
                            exec_mode_str + model_str + \
                            " -d CPU -b 1 -t 20" + \
                            " -api sync | tee " + output_file_name

            os.environ['LD_PRELOAD'] = MIMALLOC_INSTALL_PATH if exec_mode == 'native' else ''

        else:
            print("\n-- Failure: Internal error! Execution metric no set..")

        ov_exec_cmd = f"bash -c 'source {self.setupvars_path} && " + ov_exec_cmd + "'"
        print("\nCommand name = ", ov_exec_cmd)
        return ov_exec_cmd

    @staticmethod
    def get_metric_value(test_config_dict, test_file_name):
        with open(test_file_name, 'r') as test_fd:
            for line in test_fd:
                if test_config_dict['metric'] in line:
                    return line.strip().split(': ')[1].split(' ')[0]
                        

WORKLOAD = OpenvinoWorkload()
