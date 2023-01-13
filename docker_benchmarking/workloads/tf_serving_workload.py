import time
import glob
import statistics
from common.config_files.constants import *
from docker_benchmarking import curated_apps_lib
from common.libs import utils
from common.perf_benchmarks import memtier_benchmark
from conftest import trd

class RedisWorkload:
    def __init__(self, test_config_dict):
        # Redis home dir => "~/gramerf_framework"
        # Setting the workload home dir to framework root dir.
        # Changing to home dir is required for bare-metal case as we build
        # the workload by downloading its source.
        # In container case, we would just pull the docker image from the repo
        # and not build it. So, we do not require any workload home dir here.
        # Hence, assigning the home dir as framework dir itself and not
        # changing to it within pre-actions in container case, as we would 
        # anyways be executing from framework dir.
        self.workload_home_dir = FRAMEWORK_HOME_DIR
        self.server_ip_addr = utils.determine_host_ip_addr()

    def get_workload_home_dir(self):
        return self.workload_home_dir

    def pull_workload_default_image(self, test_config_dict):
        #Place the code to generate the base_image -> execute helper.sh

    def pre_actions(self, test_config_dict):
        utils.set_cpu_freq_scaling_governor()
        self.update_server_details_in_client(test_config_dict)

    def setup_workload(self, test_config_dict):
        # Pull default workload image for native run.
        self.pull_workload_default_image(test_config_dict)
        # Create graminized image for gramine direct and sgx runs.
        curation_output = curated_apps_lib.generate_curated_image(test_config_dict)
        decode_curation_output = curation_output.decode('utf-8')
        curation_output_result = curated_apps_lib.verify_image_creation(decode_curation_output)
        if curation_output_result == False:
            raise Exception("\n-- Failed to create the curated image!!")
    
    # Build the workload execution command based on execution params and execute it.
    def execute_workload(self, tcd, e_mode, test_dict=None):
        print("\n##### In execute_workload #####\n")

        print(f"\n-- Executing {tcd['test_name']} in {e_mode} mode")

        workload_docker_image_name = utils.get_workload_name(tcd['docker_image'])
        if e_mode == 'native':
            # Pull and bring up the native redis server.
            # docker run --net=host -it tf-serving-base --model_name="resnet" --model_base_path="/models/resnet"
            docker_native_cmd = f"docker run --rm --net=host -t {workload_docker_image_name} &"
            utils.exec_shell_cmd(docker_native_cmd, None)
        else:
            docker_run_cmd = curated_apps_lib.get_docker_run_command(workload_docker_image_name)
            result = curated_apps_lib.run_curated_image(docker_run_cmd)
            if result == False:
                raise Exception(f"\n-- Failure - Couldn't launch redis server in {e_mode} mode!!")

        time.sleep(5)

        # Construct and execute memtier benchmark command within client.
        client_ssh_cmd = memtier_benchmark.construct_client_exec_cmd(tcd, e_mode)
        utils.exec_shell_cmd(client_ssh_cmd, None)
        
        time.sleep(5)

        self.free_redis_server_port(tcd, e_mode)
        if 'gramine-sgx' in tcd['exec_mode']:
                workload_docker_image_name = utils.get_workload_name(tcd['docker_image'])
                utils.cleanup_after_test(workload_docker_image_name)

        time.sleep(TEST_SLEEP_TIME_BW_ITERATIONS)

    def parse_csv_res_files(self, tcd):
        csv_test_res_folder = os.path.join(PERF_RESULTS_DIR, tcd['workload_name'], tcd['test_name'])
        os.chdir(csv_test_res_folder)
        csv_files = glob.glob1(csv_test_res_folder, "*.csv")
        
        if len(csv_files) != (len(tcd['exec_mode']) * tcd['iterations']):
            raise Exception(f"\n-- Number of test result files - {len(csv_files)} is not equal to the expected number - {len(tcd['exec_mode']) * tcd['iterations']}.\n")

        global trd
        test_dict_throughput = {}
        test_dict_latency = {}
        for e_mode in tcd['exec_mode']:
            test_dict_throughput[e_mode] = []
            test_dict_latency[e_mode] = []
        
        avg_latency = 0
        avg_throughput = 0
        for filename in csv_files:
            with open(filename, "r") as f:
                for row in f.readlines():
                    row = row.split()
                    if row:
                        if "Totals" in row[0]:
                            avg_latency = row[4]
                            avg_throughput = row[-1]
                            break

                if "native" in filename:
                    test_dict_latency['native'].append(float(avg_latency))
                    test_dict_throughput['native'].append(float(avg_throughput))
                elif "graphene_sgx_single_thread" in filename:
                    test_dict_latency['gramine-sgx-single-thread-non-exitless'].append(float(avg_latency))
                    test_dict_throughput['gramine-sgx-single-thread-non-exitless'].append(float(avg_throughput))
                elif "graphene_sgx_diff_core" in filename:
                    test_dict_latency['gramine-sgx-diff-core-exitless'].append(float(avg_latency))
                    test_dict_throughput['gramine-sgx-diff-core-exitless'].append(float(avg_throughput))
                else:
                    test_dict_latency['gramine-direct'].append(float(avg_latency))
                    test_dict_throughput['gramine-direct'].append(float(avg_throughput))

        if 'native' in tcd['exec_mode']:
            test_dict_latency['native-avg'] = '{:0.3f}'.format(statistics.median(test_dict_latency['native']))
            test_dict_throughput['native-avg'] = '{:0.3f}'.format(statistics.median(test_dict_throughput['native']))

        if 'gramine-direct' in tcd['exec_mode']:
            test_dict_latency['direct-avg'] = '{:0.3f}'.format(statistics.median(test_dict_latency['gramine-direct']))
            test_dict_throughput['direct-avg'] = '{:0.3f}'.format(statistics.median(test_dict_throughput['gramine-direct']))
            if 'native' in tcd['exec_mode']:
                test_dict_latency['direct-deg'] = utils.percent_degradation(tcd, test_dict_latency['native-avg'], test_dict_latency['direct-avg'])
                test_dict_throughput['direct-deg'] = utils.percent_degradation(tcd, test_dict_throughput['native-avg'], test_dict_throughput['direct-avg'], True)

        if 'gramine-sgx-single-thread-non-exitless' in tcd['exec_mode']:
            test_dict_latency['sgx-single-thread-avg'] = '{:0.3f}'.format(statistics.median(test_dict_latency['gramine-sgx-single-thread-non-exitless']))
            test_dict_throughput['sgx-single-thread-avg'] = '{:0.3f}'.format(statistics.median(test_dict_throughput['gramine-sgx-single-thread-non-exitless']))
            if 'native' in tcd['exec_mode']:
                test_dict_latency['sgx-single-thread-deg'] = utils.percent_degradation(tcd, test_dict_latency['native-avg'], test_dict_latency['sgx-single-thread-avg'])
                test_dict_throughput['sgx-single-thread-deg'] = utils.percent_degradation(tcd, test_dict_throughput['native-avg'], test_dict_throughput['sgx-single-thread-avg'], True)

        if 'gramine-sgx-diff-core-exitless' in tcd['exec_mode']:
            test_dict_latency['sgx-diff-core-exitless-avg'] = '{:0.3f}'.format(statistics.median(test_dict_latency['gramine-sgx-diff-core-exitless']))
            test_dict_throughput['sgx-diff-core-exitless-avg'] = '{:0.3f}'.format(statistics.median(test_dict_throughput['gramine-sgx-diff-core-exitless']))
            if 'native' in tcd['exec_mode']:
                test_dict_latency['sgx-diff-core-exitless-deg'] = utils.percent_degradation(tcd, test_dict_latency['native-avg'], test_dict_latency['sgx-diff-core-exitless-avg'])
                test_dict_throughput['sgx-diff-core-exitless-deg'] = utils.percent_degradation(tcd, test_dict_throughput['native-avg'], test_dict_throughput['sgx-diff-core-exitless-avg'], True)

        trd[tcd['workload_name']] = trd.get(tcd['workload_name'], {})
        trd[tcd['workload_name']].update({tcd['test_name']+'_latency': test_dict_latency})
        trd[tcd['workload_name']].update({tcd['test_name']+'_throughput': test_dict_throughput})

        os.chdir(self.workload_home_dir)
        
    def process_results(self, tcd):
        csv_res_folder = os.path.join(PERF_RESULTS_DIR, tcd['workload_name'])
        if not os.path.exists(csv_res_folder): os.makedirs(csv_res_folder)

        # Copy test results folder from client to local server results folder.
        client_res_folder = os.path.join(tcd['client_results_path'], tcd['test_name'])
        client_scp_path = tcd['client_username'] + "@" + tcd['client_ip'] + ":" + client_res_folder
        copy_client_to_server_cmd = f"sshpass -e scp -r {client_scp_path} {csv_res_folder}"
        utils.exec_shell_cmd(copy_client_to_server_cmd)

        # Parse the individual csv result files and update the global test results dict.
        self.parse_csv_res_files(tcd)
