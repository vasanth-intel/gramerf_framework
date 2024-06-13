import time
import statistics
import glob
from common.config_files.constants import *
from common.libs import utils
from baremetal_benchmarking import gramine_libs
from conftest import trd


class MongoDBWorkload():
    def __init__(self, test_config_dict):
        self.workload_home_dir = os.path.join(FRAMEWORK_HOME_DIR, test_config_dict['workload_home_dir'])
        os.makedirs(self.workload_home_dir, exist_ok=True)
        self.mongo_benchmark_path = os.path.join(self.workload_home_dir, "mongo-perf")

    def get_workload_home_dir(self):
        return self.workload_home_dir

    def generate_manifest(self):
        mongod_path = utils.exec_shell_cmd("which mongod")
        exec_dir = utils.exec_shell_cmd(f"dirname {mongod_path}")

        manifest_cmd = "gramine-manifest -Dlog_level={} -Darch_libdir={} -Dexecdir={} \
                            mongod.manifest.template > mongod.manifest".format(LOG_LEVEL, os.environ.get('ARCH_LIBDIR'), exec_dir)
        print("\n-- Generating manifest..\n", manifest_cmd)

        utils.exec_shell_cmd(manifest_cmd, None)

    def pre_actions(self, test_config_dict):
        os.chdir(self.get_workload_home_dir())
        utils.set_threads_cnt_env_var()
        utils.set_cpu_freq_scaling_governor()
        gramine_libs.update_manifest_file(test_config_dict)

    def build_and_install_workload(self):
        if not utils.is_program_installed("mongod"):
            # MongoDB pre-requisites and installation
            utils.exec_shell_cmd("sudo apt-get install gnupg curl", None)
            time.sleep(5)
            utils.exec_shell_cmd("curl -fsSL https://pgp.mongodb.com/server-7.0.asc | \
                                 sudo gpg -o /usr/share/keyrings/mongodb-server-7.0.gpg --dearmor", None)
            utils.exec_shell_cmd('echo "deb [ arch=amd64,arm64 signed-by=/usr/share/keyrings/mongodb-server-7.0.gpg ] https://repo.mongodb.org/apt/ubuntu jammy/mongodb-org/7.0 multiverse" | \
                                    sudo tee /etc/apt/sources.list.d/mongodb-org-7.0.list', None)
            utils.exec_shell_cmd("sudo apt-get update", None)
            print(f"\n\n-- Installing MongoDB..\n")
            time.sleep(5)
            utils.exec_shell_cmd("sudo apt-get install -y mongodb-org", None)
            time.sleep(5)
        if not os.path.exists(self.mongo_benchmark_path):
            print(f"\n\n-- Fetching and installing MongoDB benchmark..\n")
            utils.exec_shell_cmd("git clone https://github.com/mongodb/mongo-perf.git", None)
            os.chdir(self.mongo_benchmark_path)
            utils.exec_shell_cmd('echo "deb http://security.ubuntu.com/ubuntu focal-security main" | sudo tee /etc/apt/sources.list.d/focal-security.list', None)
            utils.exec_shell_cmd("sudo apt-get update", None)
            utils.exec_shell_cmd("sudo apt-get install libssl1.1", None)
            utils.exec_shell_cmd("wget https://repo.mongodb.org/apt/ubuntu/dists/focal/mongodb-org/5.0/multiverse/binary-amd64/mongodb-org-shell_5.0.21_amd64.deb", None)
            utils.exec_shell_cmd("sudo dpkg -i mongodb-org-shell_5.0.21_amd64.deb", None)
            os.chdir(self.get_workload_home_dir())

    def setup_workload(self, test_config_dict):
        self.build_and_install_workload()
        self.generate_manifest()
        gramine_libs.generate_sgx_token_and_sig(test_config_dict)

    def get_server_exec_cmd(self, e_mode):
        server_exec_cmd = f"mongod --nounixsocket --dbpath {MONGO_DB_PATH}"
        
        if e_mode == 'gramine-sgx':
            server_exec_cmd = f"gramine-sgx {server_exec_cmd}"
        elif e_mode == 'gramine-direct':
            server_exec_cmd = f"gramine-direct {server_exec_cmd}"
        elif e_mode != 'native':
            raise Exception(f"\n-- Invalid execution mode specified: {e_mode}!!")

        return server_exec_cmd

    # Build the workload execution command based on execution params and execute it.
    def execute_workload(self, test_config_dict, e_mode, test_dict):
        print("\n##### In execute_workload #####\n")
        print(f"\n-- Executing {test_config_dict['test_name']} in {e_mode} mode")

        results_dir = os.path.join(PERF_RESULTS_DIR, test_config_dict['workload_name'], test_config_dict['test_name'])
        os.makedirs(results_dir, exist_ok=True)

        workload_name = test_config_dict['workload_name']
        server_exec_cmd = self.get_server_exec_cmd(e_mode)
        print(f"\n-- Launching {workload_name} in {e_mode} mode..\n", server_exec_cmd)

        print("\n\n", os.getcwd())
        
        server_process = utils.popen_subprocess(server_exec_cmd)
        time.sleep(5)
        if utils.verify_process(test_config_dict, server_process, 60*10) == False:
            raise Exception(f"\n-- Failure - Couldn't launch {workload_name} server in {e_mode} mode!!")

        if not os.path.exists(self.mongo_benchmark_path):
            utils.kill(server_process.pid)
            time.sleep(5)
            raise Exception(f"\n-- Failure: Mongo perf directory '{self.mongo_benchmark_path}' does not exist!!")
        os.chdir(self.mongo_benchmark_path)

        for i in range(test_config_dict['iterations']):
            results_dir = os.path.join(PERF_RESULTS_DIR, test_config_dict['workload_name'], test_config_dict['test_name'])
            output_file_name = results_dir + "/" + test_config_dict['test_name'] + '_' + e_mode + '_' + str(i+1) + '.log'
            benchmark_cmd = f"python3 benchrun.py -f testcases/complex_update.js -t {test_config_dict['threads']} | tee {output_file_name}"
            print(f"\n-- Invoking benchmark for iteration {i}..\n", benchmark_cmd)
            run_cmd_output = utils.exec_shell_cmd(benchmark_cmd)
            print(run_cmd_output)
            time.sleep(TEST_SLEEP_TIME_BW_ITERATIONS)

        print(f"\n\n-- Stopping {workload_name} server running in {e_mode} mode..\n")
        utils.kill(server_process.pid)
        time.sleep(5)

        os.chdir(self.get_workload_home_dir())

    def update_tpt_dict(self, test_tpt_dict, mongod_res_dict, file_des, e_mode, max_params):
        param_count = 0
        for row in file_des.readlines():
            if '"ops_per_sec":' in row:
                row = row.split()
                throughput = '{:0.3f}'.format(float(row[1].strip(',')))
                mongod_res_dict[param_count].append(float(throughput))
                param_count += 1
                if param_count == (max_params):
                    break
        test_tpt_dict[e_mode].update(mongod_res_dict)
        if param_count != max_params:
            print(f"\n\n-- Warning: Not all parameters of the workload are present in result file {file_des.name}..\n")

    def process_results(self, tcd):
        log_test_res_folder = os.path.join(PERF_RESULTS_DIR, tcd['workload_name'], tcd['test_name'])
        os.chdir(log_test_res_folder)
        log_files = glob.glob1(log_test_res_folder, "*.log")
        
        if len(log_files) != (len(tcd['exec_mode']) * tcd['iterations']):
            raise Exception(f"\n-- Number of test result files - {len(log_files)} is not equal to the expected number - {len(tcd['exec_mode']) * tcd['iterations']}.\n")

        global trd
        test_tpt_dict = {}
        mongod_native_res_dict, mongod_direct_res_dict, mongod_sgx_res_dict = {}, {}, {}
        max_params = 5
        for i in range(max_params):
            mongod_native_res_dict[i] = []
            mongod_direct_res_dict[i] = []
            mongod_sgx_res_dict[i] = []

        for e_mode in tcd['exec_mode']:
            if e_mode == 'native':
                test_tpt_dict[e_mode], test_tpt_dict[e_mode + '-med'] = {}, []
            elif e_mode == 'gramine-direct':
                test_tpt_dict[e_mode], test_tpt_dict['direct-med'], test_tpt_dict['direct-deg'] = {}, [], []
            elif e_mode == 'gramine-sgx':
                test_tpt_dict[e_mode], test_tpt_dict['sgx-med'], test_tpt_dict['sgx-deg'] = {}, [], []

        for filename in log_files:
            with open(filename, "r") as f:
                if "native" in filename:
                    self.update_tpt_dict(test_tpt_dict, mongod_native_res_dict, f, 'native', max_params)
                elif "gramine-direct" in filename:
                    self.update_tpt_dict(test_tpt_dict, mongod_direct_res_dict, f, 'gramine-direct', max_params)
                elif "gramine-sgx" in filename:
                    self.update_tpt_dict(test_tpt_dict, mongod_sgx_res_dict, f, 'gramine-sgx', max_params)
                else:
                    raise Exception(f"\n-- Incorrect results file present in test results folder.\n")

        if 'native' in tcd['exec_mode']:
            for i in range(max_params):
                test_tpt_dict['native-med'].append(statistics.median(test_tpt_dict['native'][i]))

        if 'gramine-direct' in tcd['exec_mode']:
            for i in range(max_params):
                test_tpt_dict['direct-med'].append(statistics.median(test_tpt_dict['gramine-direct'][i]))
                if 'native' in tcd['exec_mode']:
                    test_tpt_dict['direct-deg'].append(float(utils.percent_degradation(tcd, test_tpt_dict['native-med'][i], test_tpt_dict['direct-med'][i], True)))

        if 'gramine-sgx' in tcd['exec_mode']:
            for i in range(max_params):
                test_tpt_dict['sgx-med'].append(statistics.median(test_tpt_dict['gramine-sgx'][i]))
                if 'native' in tcd['exec_mode']:
                    test_tpt_dict['sgx-deg'].append(float(utils.percent_degradation(tcd, test_tpt_dict['native-med'][i], test_tpt_dict['sgx-med'][i], True)))

        trd[tcd['workload_name']] = trd.get(tcd['workload_name'], {})
        trd[tcd['workload_name']].update({tcd['test_name']+'_throughput': test_tpt_dict})

        os.chdir(self.workload_home_dir)
