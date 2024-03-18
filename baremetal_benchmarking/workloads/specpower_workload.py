import time
import shutil
import statistics
import re
from common.config_files.constants import *
from baremetal_benchmarking import gramine_libs
from common.libs import utils
from common.perf_benchmarks import memtier_benchmark
from conftest import trd


class SpecPowerWorkload:
    def __init__(self, test_config_dict):
        # SpecPower home dir => "SPECPOWER_ROOT_DIR"
        self.workload_home_dir = SPECPOWER_ROOT_DIR
        # SpecPower build/execution dir => "SPECPOWER_ROOT_DIR/ssj"
        self.workload_ssj_dir = os.path.join(self.workload_home_dir, "ssj")
        self.workload_power_dir = os.path.join(self.workload_home_dir, "PTDaemon")
        self.workload_ccs_dir = os.path.join(self.workload_home_dir, "ccs")
        self.power_sh = os.path.join(self.workload_power_dir, "runpower.sh")
        self.director_sh = os.path.join(self.workload_ssj_dir, "rundirector.sh")
        self.ccs_sh = os.path.join(self.workload_ccs_dir, "runCCS.sh")
        self.ssj_sh = os.path.join(self.workload_ssj_dir, "runssj.sh")

    def get_workload_home_dir(self):
        return self.workload_home_dir

    def build_and_install_workload(self):
        print("\n###### In build_and_install_workload #####\n")
        if not os.path.exists(self.workload_ssj_dir):
            raise Exception(f"\n{self.workload_ssj_dir} does not exist!")

        os.chdir(self.workload_ssj_dir)
        print(f"\n-- Building SpecPower workload..\n")
        utils.exec_shell_cmd("make clean", None)
        make_log = LOGS_DIR + "/SpecPower_Make.log"
        log_fd = open(make_log, "w")
        utils.exec_shell_cmd("make SGX=1", log_fd)
        log_fd.close()

    def delete_old_test_results(self):
        print("\n-- Deleting old test results..")
        results_folder = os.path.join(self.workload_ssj_dir, "SPECpower_results")
        if os.path.exists(results_folder):
            shutil.rmtree(results_folder)

    def pre_actions(self, test_config_dict):
        os.chdir(self.get_workload_home_dir())
        utils.set_cpu_freq_scaling_governor()

    def setup_workload(self, test_config_dict):
        self.build_and_install_workload()
        self.delete_old_test_results()

    def get_throughput(self, output):
        pattern_match = re.search("Actual ops =   (.*) ssj_ops@100%", output)
        if pattern_match:
            return float(pattern_match.groups()[0])
        else:
            return 0            

    # Build the workload execution command based on execution params and execute it.
    def execute_workload(self, tcd, e_mode, test_dict=None):
        os.chdir(self.workload_ssj_dir)
        print("\n##### In execute_workload #####\n")

        for i in range(tcd['iterations']):
            print(f"\n-- Executing SpecPower in {e_mode} mode. Iteration: {i}..\n")

            print(f"\n-- Launching PTDaemon (Power/Temperature Daemon)..\n")
            power_process = utils.popen_subprocess(f"{self.power_sh}", f"{self.workload_power_dir}")
                    
            time.sleep(TEST_SLEEP_TIME_BW_ITERATIONS - 10)

            print(f"\n-- Launching Director..\n")
            dir_process = utils.popen_subprocess(f"{self.director_sh}", f"{self.workload_ssj_dir}")
                    
            time.sleep(TEST_SLEEP_TIME_BW_ITERATIONS - 10)

            print(f"\n-- Launching CCS (Control and Collect System)..\n")
            ccs_process = utils.popen_subprocess(f"{self.ccs_sh}", f"{self.workload_ccs_dir}")
                    
            time.sleep(TEST_SLEEP_TIME_BW_ITERATIONS - 10)

            print(f"\n-- Launching SSJ (Server Side Java) in {e_mode} mode..\n")
            if e_mode == "native":
              ssj_process = utils.popen_subprocess(f"{self.ssj_sh}", f"{self.workload_ssj_dir}")
            else:
              ssj_process = utils.popen_subprocess(f"{self.ssj_sh} {e_mode}", f"{self.workload_ssj_dir}")
            
            ccs_status = ssj_status = False

            ccs_status, ccs_output = utils.track_process(tcd, ccs_process, "Connected")
            if ccs_status:
                ssj_status, ssj_output = utils.track_process(tcd, ssj_process, "Benchmark run complete")
                print(f"\n-- SpecPower {e_mode} mode iteration {i} complete.\n")
            else:
                # Invlidate the perf run
                test_dict[e_mode].append(0)

            if ssj_status:
                print(f"Sleeping for {TEST_SLEEP_TIME_BW_ITERATIONS - 5} seconds for processes to complete..")
                time.sleep(TEST_SLEEP_TIME_BW_ITERATIONS - 5)
                if power_process.poll() is None:
                    print("\n-- Killing PTDaemon process..")
                    utils.kill(power_process.pid)
                if dir_process.poll() is None:
                    print("\n-- Killing Director process..")
                    utils.kill(dir_process.pid)
                if ccs_process.poll() is None:
                    print("\n-- Killing CCS process..")
                    utils.kill(ccs_process.pid)
                if ssj_process.poll() is None:
                    print("\n-- Killing SSJ process..")
                    utils.kill(ssj_process.pid)
                
                test_dict[e_mode].append(self.get_throughput(ssj_output))
            
            time.sleep(TEST_SLEEP_TIME_BW_ITERATIONS)

        time.sleep(TEST_SLEEP_TIME_BW_ITERATIONS * 2)

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
