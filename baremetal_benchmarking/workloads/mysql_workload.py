import time
import statistics
import glob
from common.config_files.constants import *
from common.libs import utils
from baremetal_benchmarking import gramine_libs
from docker_benchmarking import curated_apps_lib
from conftest import trd


class MySqlWorkload():
    def __init__(self, test_config_dict):
        self.workload_home_dir = os.path.join(FRAMEWORK_HOME_DIR, test_config_dict['workload_home_dir'])
        os.makedirs(self.workload_home_dir, exist_ok=True)

    def get_workload_home_dir(self):
        return self.workload_home_dir

    def check_sgx_dirs(self, test_config_dict):
        if not 'gramine-sgx' in test_config_dict['exec_mode']:
            return
        if os.path.exists("/dev/sgx/enclave") and os.path.exists("/dev/sgx/provision"):
            utils.exec_shell_cmd("sudo chmod 777 /dev/sgx/enclave /dev/sgx/provision", None)
            return
        if not os.path.exists("/dev/sgx/enclave") and not os.path.exists("/dev/sgx_enclave"):
            raise Exception("\n-- Failure - Will not be able to run with SGX, due to absence of dev-enclave SGX folder")
        if not os.path.exists("/dev/sgx/provision") and not os.path.exists("/dev/sgx_provision"):
            raise Exception("\n-- Failure - Will not be able to run with SGX, due to absence of dev-provision SGX folder")
        utils.exec_shell_cmd("sudo mkdir /dev/sgx", None)
        utils.exec_shell_cmd("sudo cp -rf /dev/sgx_enclave /dev/sgx/enclave", None)
        utils.exec_shell_cmd("sudo cp -rf /dev/sgx_provision /dev/sgx/provision", None)
        utils.exec_shell_cmd("sudo chmod 777 /dev/sgx/enclave /dev/sgx/provision", None)

    def generate_manifest(self):
        entrypoint_path = utils.exec_shell_cmd("sh -c 'command -v mysqld'")

        manifest_cmd = "gramine-manifest -Dlog_level={} -Darch_libdir={} -Duid={} -Dgid={} -Dentrypoint={} \
                            mysqld.manifest.template > mysqld.manifest".format(
            LOG_LEVEL, os.environ.get('ARCH_LIBDIR'), os.environ.get('ENV_USER_UID'), os.environ.get('ENV_USER_GID'), entrypoint_path)
        print("\n-- Generating manifest..\n", manifest_cmd)

        utils.exec_shell_cmd(manifest_cmd, None)

    def update_manifest_entries(self, test_config_dict, hex_enc_key_dump):
        manifest_filename = test_config_dict['manifest_name'] + ".manifest.template"

        search_str = "# encrypted file mount"
        replace_str = "{ type = \"encrypted\", path = \"" + MYSQL_BM_ENCRYPTED_DB_TMPFS_PATH + "\", uri = \"file:" + MYSQL_BM_ENCRYPTED_DB_TMPFS_PATH + "\" },"
        enc_file_mount_cmd = f"sed -i 's|{search_str}|{replace_str}|' {manifest_filename}"
        utils.exec_shell_cmd(enc_file_mount_cmd, None)
        search_str = "# encrypted insecure__keys"
        replace_str = "fs.insecure__keys.default = \"" + hex_enc_key_dump + "\""
        enc_insecure_keys_cmd = f"sed -i 's|{search_str}|{replace_str}|' {manifest_filename}"
        utils.exec_shell_cmd(enc_insecure_keys_cmd, None)

    def pre_actions(self, test_config_dict):
        os.chdir(self.get_workload_home_dir())
        utils.set_threads_cnt_env_var()
        utils.set_cpu_freq_scaling_governor()
        self.check_sgx_dirs(test_config_dict)
        gramine_libs.update_manifest_file(test_config_dict)

    def setup_workload(self, test_config_dict):
        if os.environ['encryption'] == '1' and 'gramine-sgx' in os.environ["exec_mode"]:
            # We are passing file name as parameter to below function,
            # which was generated in 'init_baremetal_db' function earlier.
            hex_enc_key_dump = utils.get_encryption_key_dump("encryption_key")
            self.update_manifest_entries(test_config_dict, hex_enc_key_dump)
        self.generate_manifest()
        gramine_libs.generate_sgx_token_and_sig(test_config_dict)

    def get_server_exec_cmd(self, e_mode):
        if e_mode == 'native':
            server_exec_cmd = f"mysqld --datadir={MYSQL_BM_PLAIN_DB_TMPFS_PATH} --skip-log-bin"
        elif e_mode == 'gramine-sgx':
            if os.environ["encryption"] == '1':
                server_exec_cmd = f"gramine-sgx mysqld --datadir={MYSQL_BM_ENCRYPTED_DB_TMPFS_PATH} --skip-log-bin"
            else:
                server_exec_cmd = f"gramine-sgx mysqld --datadir={MYSQL_BM_PLAIN_DB_TMPFS_PATH} --skip-log-bin"
        else:
            raise Exception(f"\n-- Invalid execution mode specified: {e_mode}!!")

        return server_exec_cmd

    def construct_sysbench_operation(self, tcd, sysbench_cmd, e_mode='native', iteration=1):
        operation_cmd = ''
        if sysbench_cmd == 'prepare' or sysbench_cmd == 'cleanup':
            operation_cmd = f"sysbench --db-driver=mysql --mysql-host=127.0.0.1 --mysql-port=3306 --mysql-user=root --mysql-db=test_db \
                                --time=90 --report-interval=5 {tcd['operation']} --tables=8 --table_size=100000 \
                                --threads={os.environ['CORES_COUNT']} {sysbench_cmd}"
        elif sysbench_cmd == 'run':
            results_dir = os.path.join(PERF_RESULTS_DIR, tcd['workload_name'], tcd['test_name'])
            output_file_name = results_dir + "/" + tcd['test_name'] + '_' + e_mode + '_' + str(iteration) + '.log'
            operation_cmd = f"sysbench --db-driver=mysql --mysql-host=127.0.0.1 --mysql-port=3306 --mysql-user=root --mysql-db=test_db \
                                --time=90 --report-interval=5 {tcd['operation']} --tables=8 --table_size=100000 \
                                --threads={tcd['threads']} {sysbench_cmd} | tee {output_file_name}"
        else:
            raise Exception("\n-- Invalid MySql operation command requested!!")
        
        return operation_cmd

    # Build the workload execution command based on execution params and execute it.
    def execute_workload(self, test_config_dict, e_mode, test_dict):
        print("\n##### In execute_workload #####\n")
        print(f"\n-- Executing {test_config_dict['test_name']} in {e_mode} mode")

        results_dir = os.path.join(PERF_RESULTS_DIR, test_config_dict['workload_name'], test_config_dict['test_name'])
        os.makedirs(results_dir, exist_ok=True)

        workload_name = test_config_dict['workload_name']
        server_exec_cmd = self.get_server_exec_cmd(e_mode)
        print(f"\n-- Launching {workload_name} server in {e_mode} mode..\n", server_exec_cmd)

        print("\n\n", os.getcwd())
        
        server_process = utils.popen_subprocess(server_exec_cmd)
        time.sleep(5)
        if curated_apps_lib.verify_process(test_config_dict, server_process, 60*10) == False:
            raise Exception(f"\n-- Failure - Couldn't launch {workload_name} server in {e_mode} mode!!")

        print(f"\n-- Disabling INNODB REDO_LOG for {test_config_dict['test_name']} in {e_mode} mode")
        utils.exec_shell_cmd('mysql -P 3306 --protocol=tcp -u root -e "ALTER INSTANCE DISABLE INNODB REDO_LOG;"', None)
        
        print(f"\n-- Creating test_db for {test_config_dict['test_name']} in {e_mode} mode")
        utils.exec_shell_cmd("sudo mysqladmin -h 127.0.0.1 -P 3306 create test_db", None)

        # 'Prepare' and 'Cleanup' commands need to be performed only once per test.
        # Hence, not calling these commands in loop.
        prepare_op_cmd = self.construct_sysbench_operation(test_config_dict, "prepare")
        utils.exec_shell_cmd(prepare_op_cmd, None)
        time.sleep(5)

        for i in range(test_config_dict['iterations']):
            run_op_cmd = self.construct_sysbench_operation(test_config_dict, "run", e_mode, i + 1)
            run_cmd_output = utils.exec_shell_cmd(run_op_cmd)
            print(run_cmd_output)
            time.sleep(TEST_SLEEP_TIME_BW_ITERATIONS)

        cleanup_op_cmd = self.construct_sysbench_operation(test_config_dict, "cleanup")
        utils.exec_shell_cmd(cleanup_op_cmd, None)
        time.sleep(5)

        # workload cleanup
        print(f"\n-- Deleting test_db for {test_config_dict['test_name']} in {e_mode} mode")
        utils.exec_shell_cmd("sudo mysqladmin -h 127.0.0.1 -P 3306 drop -f test_db", None)
        time.sleep(5)

        print(f"\n-- Enabling INNODB REDO_LOG for {test_config_dict['test_name']} in {e_mode} mode")
        utils.exec_shell_cmd('mysql -P 3306 --protocol=tcp -u root -e "ALTER INSTANCE ENABLE INNODB REDO_LOG;"', None)

        print(f"\n\n-- Stopping {workload_name} Server DB running in {e_mode} mode..\n")
        utils.kill(server_process.pid)
        time.sleep(5)

    def process_results(self, tcd):
        log_test_res_folder = os.path.join(PERF_RESULTS_DIR, tcd['workload_name'], tcd['test_name'])
        os.chdir(log_test_res_folder)
        log_files = glob.glob1(log_test_res_folder, "*.log")
        
        if len(log_files) != (len(tcd['exec_mode']) * tcd['iterations']):
            raise Exception(f"\n-- Number of test result files - {len(log_files)} is not equal to the expected number - {len(tcd['exec_mode']) * tcd['iterations']}.\n")

        global trd
        test_read_tpt_dict = {}
        test_write_tpt_dict = {}
        test_avg_lat_dict = {}
        test_95_pcnt_lat_dict = {}
        for e_mode in tcd['exec_mode']:
            test_read_tpt_dict[e_mode] = []
            test_write_tpt_dict[e_mode] = []
            test_avg_lat_dict[e_mode] = []
            test_95_pcnt_lat_dict[e_mode] = []
        
        read_throughput, write_throughput, avg_latency, percentile_95_latency = 0, 0, 0, 0
        for filename in log_files:
            with open(filename, "r") as f:
                all_results_captured = False
                for row in f.readlines():
                    row = row.split()
                    if row:
                        if "queries:" in row[0] and ('read_only' in tcd['test_name'] or 'read_write' in tcd['test_name']):
                            read_throughput = row[2].split('(')[1]
                        elif "queries:" in row[0] and 'write_only' in tcd['test_name']:
                            write_throughput = row[2].split('(')[1]
                        elif "avg:" in row[0]:
                            avg_latency = row[1]
                        elif "95th" in row[0]:
                            percentile_95_latency = row[2]
                            all_results_captured = True
                            break

                if not all_results_captured:
                    if "native" in filename:
                        test_read_tpt_dict['native'].append(0)
                        test_write_tpt_dict['native'].append(0)
                        test_avg_lat_dict['native'].append(0)
                        test_95_pcnt_lat_dict['native'].append(0)
                    elif "gramine-sgx" in filename:
                        test_read_tpt_dict['gramine-sgx'].append(0)
                        test_write_tpt_dict['gramine-sgx'].append(0)
                        test_avg_lat_dict['gramine-sgx'].append(0)
                        test_95_pcnt_lat_dict['gramine-sgx'].append(0)
                    continue

                if "native" in filename:
                    test_read_tpt_dict['native'].append(float(read_throughput))
                    test_write_tpt_dict['native'].append(float(write_throughput))
                    test_avg_lat_dict['native'].append(float(avg_latency))
                    test_95_pcnt_lat_dict['native'].append(float(percentile_95_latency))
                elif "gramine-sgx" in filename:
                    test_read_tpt_dict['gramine-sgx'].append(float(read_throughput))
                    test_write_tpt_dict['gramine-sgx'].append(float(write_throughput))
                    test_avg_lat_dict['gramine-sgx'].append(float(avg_latency))
                    test_95_pcnt_lat_dict['gramine-sgx'].append(float(percentile_95_latency))
                else:
                    raise Exception(f"\n-- Incorrect results file present in test results folder.\n")

        if 'native' in tcd['exec_mode']:
            test_read_tpt_dict['native-med'] = '{:0.3f}'.format(statistics.median(test_read_tpt_dict['native']))
            test_write_tpt_dict['native-med'] = '{:0.3f}'.format(statistics.median(test_write_tpt_dict['native']))
            test_avg_lat_dict['native-med'] = '{:0.3f}'.format(statistics.median(test_avg_lat_dict['native']))
            test_95_pcnt_lat_dict['native-med'] = '{:0.3f}'.format(statistics.median(test_95_pcnt_lat_dict['native']))
            
        if 'gramine-sgx' in tcd['exec_mode']:
            test_read_tpt_dict['sgx-med'] = '{:0.3f}'.format(statistics.median(test_read_tpt_dict['gramine-sgx']))
            test_write_tpt_dict['sgx-med'] = '{:0.3f}'.format(statistics.median(test_write_tpt_dict['gramine-sgx']))
            test_avg_lat_dict['sgx-med'] = '{:0.3f}'.format(statistics.median(test_avg_lat_dict['gramine-sgx']))
            test_95_pcnt_lat_dict['sgx-med'] = '{:0.3f}'.format(statistics.median(test_95_pcnt_lat_dict['gramine-sgx']))
            if 'native' in tcd['exec_mode']:
                test_read_tpt_dict['sgx-deg'] = utils.percent_degradation(tcd, test_read_tpt_dict['native-med'], test_read_tpt_dict['sgx-med'], True)
                test_write_tpt_dict['sgx-deg'] = utils.percent_degradation(tcd, test_write_tpt_dict['native-med'], test_write_tpt_dict['sgx-med'], True)
                test_avg_lat_dict['sgx-deg'] = utils.percent_degradation(tcd, test_avg_lat_dict['native-med'], test_avg_lat_dict['sgx-med'])
                test_95_pcnt_lat_dict['sgx-deg'] = utils.percent_degradation(tcd, test_95_pcnt_lat_dict['native-med'], test_95_pcnt_lat_dict['sgx-med'])

        trd[tcd['workload_name']] = trd.get(tcd['workload_name'], {})
        if 'read_only' in tcd['test_name']:
            trd[tcd['workload_name']].update({tcd['test_name']+'_throughput': test_read_tpt_dict})
        elif 'write_only' in tcd['test_name']:
            trd[tcd['workload_name']].update({tcd['test_name']+'_throughput': test_write_tpt_dict})
        elif 'read_write' in tcd['test_name']:
            # In this case we can read from either read or write dictionaries, as the corresponding
            # values for both read and write are same. Hence, currently reading from read dict.
            trd[tcd['workload_name']].update({tcd['test_name']+'_throughput': test_read_tpt_dict})
        else:
            raise Exception(f"\n-- Test name does not contain right DB actions ('read_only'/'write_only'/'read_write') to be performed.\n")
        # Not displaying below latency and 95th percentile data within the final report, 
        # due to inconsistent perf numbers.
        #trd[tcd['workload_name']].update({tcd['test_name']+'_avg': test_avg_lat_dict})
        #trd[tcd['workload_name']].update({tcd['test_name']+'_95th_percentile': test_95_pcnt_lat_dict})

        os.chdir(self.workload_home_dir)
