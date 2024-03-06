import time
import shutil
import statistics
from pathlib import Path
from common.config_files.constants import *
from common.libs import utils
from baremetal_benchmarking import gramine_libs
from conftest import trd


# convert environment variable to boolean
def is_true(env):
    value = os.environ.get(env, 'false').lower()
    return value == 'true'


class OpenvinoWorkload():
    def __init__(self, test_config_dict):
        self.workload_home_dir = os.path.join(FRAMEWORK_HOME_DIR, test_config_dict['workload_home_dir'])
        self.ov_dir_str = 'openvino_2023'
        self.setupvars_path = os.path.join(self.workload_home_dir, self.ov_dir_str, 'setupvars.sh')
        self.command = None

    def get_workload_home_dir(self):
        return self.workload_home_dir
        
    def download_workload(self, test_config_dict):
        # Installing Openvino within "/home/intel/test/gramine/examples/openvino/openvino_2023"
        install_dir = os.path.join(self.workload_home_dir, self.ov_dir_str)

        # We would not install if the installation dir already exists.
        if os.path.exists(install_dir):
            print("\n-- Openvino already installed. Not fetching from source..")
            return True

        distro, distro_version = utils.get_distro_and_version()
        if distro == 'ubuntu' and distro_version == '22.04':
            toolkit_name = "l_openvino_toolkit_ubuntu22_2023.3.0.13775.ceeafaf64f3_x86_64"
        else:
            raise Exception("Unsupported distro for Openvino installation")

        wget_cmd = "wget https://storage.openvinotoolkit.org/repositories/openvino/packages/2023.3/linux/" + toolkit_name + ".tgz"
        untar_cmd = "tar xzf " + toolkit_name + ".tgz"

        print("\n-- Fetching and extracting Openvino workload from source..")
        utils.exec_shell_cmd(wget_cmd)
        utils.exec_shell_cmd(untar_cmd)
        os.rename(toolkit_name, self.ov_dir_str)

    def download_and_convert_model(self, test_config_dict, model_file_path):
        if not os.path.exists(model_file_path):
            venv_bin_path = os.path.join(self.workload_home_dir, 'openvino/bin/activate')
            out_model_dir = os.path.join(self.workload_home_dir, 'model')
            download_cmd = f"bash -c 'source {venv_bin_path} && omz_downloader --name {test_config_dict['model_name']} -o {out_model_dir} && deactivate'"
            convert_cmd = f"bash -c 'source {self.setupvars_path} && source {venv_bin_path} && omz_converter --name {test_config_dict['model_name']} -d {out_model_dir} -o {out_model_dir} && deactivate'"
            print("\n-- Model download cmd:", download_cmd)
            utils.exec_shell_cmd(download_cmd, None)
            print("\n-- Model convert cmd:", convert_cmd)
            utils.exec_shell_cmd(convert_cmd, None)
        else:
            print("\n-- Models are already downloaded.")

    def copy_makefile(self, test_config_dict):
        src_file = os.path.join(FRAMEWORK_HOME_DIR, "baremetal_benchmarking/config_files/openvino_makefile")
        dest_file = os.path.join(FRAMEWORK_HOME_DIR, test_config_dict['workload_home_dir'], "Makefile")

        shutil.copy2(src_file, dest_file)

    def build_and_install_workload(self, test_config_dict):
        print("\n###### In build_and_install_workload #####\n")

        benchmark_app_path = os.path.join(self.workload_home_dir, 'benchmark_app')
        venv_bin_path = os.path.join(self.workload_home_dir, 'openvino/bin/activate')
        if not (os.path.exists(benchmark_app_path) and os.path.exists(venv_bin_path)):
            # Below statement to copy of Makefile can be removed after the changes within the gramerf copy
            # of OpenVINO Makefile are merged to master of examples repo.
            self.copy_makefile(test_config_dict)
            print(f"\n-- Building benchmark_app and OpenVINO..\n")
            ov_env_var_bld_cmd = f"bash -c 'source {self.setupvars_path} && make benchmark_app openvino/.INSTALLATION_OK'"
            print("\n-- Setting up OpenVINO environment variables and building Openvino..\n", ov_env_var_bld_cmd)

            openvino_make_log = LOGS_DIR + "/openvino" + '_make.log'
            log_fd = open(openvino_make_log, "w")
            utils.exec_shell_cmd(ov_env_var_bld_cmd, log_fd)
            log_fd.close()
            
        model_file_path = os.path.join(FRAMEWORK_HOME_DIR, test_config_dict['model_dir'], test_config_dict['fp'], 
                            test_config_dict['model_name']+'.xml')

        self.download_and_convert_model(test_config_dict, model_file_path)

        # Check for build status by verifying the existence of model.xml file and return accordingly.
        if not os.path.exists(model_file_path):
            raise Exception(f"\n-- Failure: Model {model_file_path} not found/built. Returning without building the model.")

    def update_manifest(self, test_config_dict):
        if test_config_dict['metric'] == "Throughput":
            # We are not changing the enclave size for 'Resnet' and 'SSD' models as they are the default values
            # present within the manifest template.
            if 'resnet' in test_config_dict['model_name'] or 'ssd' in test_config_dict['model_name']:
                return

            filename = os.path.join(FRAMEWORK_HOME_DIR, test_config_dict['workload_home_dir'] , test_config_dict['manifest_name']) + ".manifest.template"

            with open(filename, 'r') as file:
                read_data = file.read()

            if 'bert' in test_config_dict['model_name'] or 'segmentation-0002' in test_config_dict['model_name']:
                write_data = read_data.replace('sgx.enclave_size = "32G"', 'sgx.enclave_size = "64G"')

            if 'segmentation-0001' in test_config_dict['model_name']:
                tmpdata = read_data.replace('sgx.enclave_size = "32G"', 'sgx.enclave_size = "128G"')
                write_data = tmpdata.replace('sgx.preheat_enclave = true', '')

            with open(filename, 'w') as file:
                file.write(write_data)

    def generate_manifest(self):
        openvino_path = os.path.join(self.workload_home_dir, self.ov_dir_str)
        inference_path = os.path.join(self.workload_home_dir, 'inference_engine_cpp_samples_build')

        manifest_cmd = "gramine-manifest -Dlog_level={} -Darch_libdir={} -Dopenvino_dir={} -Dinference_engine_cpp_samples_build={} \
                            benchmark_app.manifest.template > benchmark_app.manifest".format(
            LOG_LEVEL, os.environ.get('ARCH_LIBDIR'), openvino_path, inference_path
        )
        print("\n-- Generating manifest..\n", manifest_cmd)
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
        os.chdir(self.get_workload_home_dir())
        utils.set_threads_cnt_env_var()
        utils.set_cpu_freq_scaling_governor()
        self.install_mimalloc()
        gramine_libs.update_manifest_file(test_config_dict)

    def setup_workload(self, test_config_dict):
        self.download_workload(test_config_dict)
        self.build_and_install_workload(test_config_dict)
        self.update_manifest(test_config_dict)
        self.generate_manifest()
        gramine_libs.generate_sgx_token_and_sig(test_config_dict)

    def construct_workload_exec_cmd(self, test_config_dict, exec_mode = 'native', iteration=1):
        ov_exec_cmd = None
        exec_mode_str = './benchmark_app' if exec_mode == 'native' else exec_mode + ' benchmark_app'
        
        model_file_path = test_config_dict['model_dir'].split(test_config_dict['workload_home_dir'] + '/')[1]
        model_str = ' -m ' + os.path.join(model_file_path, 
                                test_config_dict['fp'],test_config_dict['model_name']+'.xml')

        output_file_name = LOGS_DIR + "/" + test_config_dict['test_name'] + '_' + exec_mode + '_' + str(iteration) + '.log'

        print("\nOutput file name = ", output_file_name)
        if test_config_dict['metric'] == 'Throughput':
            # 'hint' option must be specified as either 'throughput or 'none' as benchmark_app argument to get throughput data.
            # if -nstreams, -nthreads and -pin fine tune options are passed, then 'hint' must be explicitly specified as 'none'.
            ov_exec_cmd = "KMP_AFFINITY=granularity=fine,noverbose,compact,1,0 " + \
                            exec_mode_str + model_str + \
                            " -hint none -d CPU -b 1 -t 20" + \
                            " -nstreams " + os.environ['THREADS_CNT'] + " -nthreads " + os.environ['THREADS_CNT'] + \
                            " -nireq " + os.environ['THREADS_CNT'] + " | tee " + output_file_name

            os.environ['LD_PRELOAD'] = TCMALLOC_INSTALL_PATH if exec_mode == 'native' else ''

        elif test_config_dict['metric'] == 'Latency':
            # 'hint' option must be specified as 'latency' as benchmark_app argument to get latency data.
            ov_exec_cmd = "KMP_AFFINITY=granularity=fine,noverbose,compact,1,0 " + \
                            exec_mode_str + model_str + \
                            " -hint latency -d CPU -b 1 -t 20" + \
                            " -api sync | tee " + output_file_name

            os.environ['LD_PRELOAD'] = MIMALLOC_INSTALL_PATH if exec_mode == 'native' else ''

        else:
            print("\n-- Failure: Internal error! Execution metric no set..")

        ov_exec_cmd = f"bash -c 'source {self.setupvars_path} && " + ov_exec_cmd + "'"
        print("\nCommand name = ", ov_exec_cmd)
        return ov_exec_cmd

    @staticmethod
    def get_metric_value(test_file_name):
        search_str = ''
        if 'throughput' in test_file_name:
            search_str = 'Throughput:'
        elif 'latency' in test_file_name:
            search_str = 'Median:'
        else:
            return '0'
        with open(test_file_name, 'r') as test_fd:
            for line in test_fd:
                if search_str in line:
                    return line.strip().split()[4]

    # Build the workload execution command based on execution params and execute it.
    def execute_workload(self, tcd, e_mode, test_dict):
        print("\n##### In execute_workload #####\n")

        for j in range(tcd['iterations']):
            self.command = self.construct_workload_exec_cmd(tcd, e_mode, j + 1)

            if self.command is None:
                raise Exception(
                    f"\n-- Failure: Unable to construct command for {tcd['test_name']} Exec_mode: {e_mode}")

            cmd_output = utils.exec_shell_cmd(self.command)
            print(cmd_output)
            if cmd_output is None or utils.verify_output(cmd_output, tcd['metric']) is None:
                raise Exception(
                    f"\n-- Failure: Test workload execution failed for {tcd['test_name']} Exec_mode: {e_mode}")

            test_file_name = LOGS_DIR + '/' + tcd['test_name'] + '_' + e_mode + '_' + str(j+1) + '.log'
            if not os.path.exists(test_file_name):
                raise Exception(f"\nFailure: File {test_file_name} does not exist for parsing performance..")
            metric_val = float(self.get_metric_value(test_file_name))
            test_dict[e_mode].append(metric_val)
            
            time.sleep(TEST_SLEEP_TIME_BW_ITERATIONS)

    def update_test_results_in_global_dict(self, tcd, test_dict):
        global trd
        if 'native' in tcd['exec_mode']:
            test_dict['native-med'] = '{:0.3f}'.format(statistics.median(test_dict['native']))

        if 'gramine-direct' in tcd['exec_mode']:
            test_dict['direct-med'] = '{:0.3f}'.format(statistics.median(test_dict['gramine-direct']))
            if 'native' in tcd['exec_mode']:
                test_dict['direct-deg'] = utils.percent_degradation(tcd, test_dict['native-med'], test_dict['direct-med'])

        if 'gramine-sgx' in tcd['exec_mode']:
            test_dict['sgx-med'] = '{:0.3f}'.format(statistics.median(test_dict['gramine-sgx']))
            if 'native' in tcd['exec_mode']:
                test_dict['sgx-deg'] = utils.percent_degradation(tcd, test_dict['native-med'], test_dict['sgx-med'])

        utils.write_to_csv(tcd, test_dict)

        trd[tcd['workload_name']] = trd.get(tcd['workload_name'], {})
        trd[tcd['workload_name']].update({tcd['test_name']: test_dict})
