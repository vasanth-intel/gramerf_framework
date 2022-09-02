import time
import docker
import shutil
import glob
from common.config_files.constants import *
from docker_benchmarking import curated_apps_lib
from common.libs import utils
from conftest import trd


class RedisWorkload:
    def __init__(self, test_config_dict):
        # Redis home dir => "~/gramerf_framework/gramine/CI-Examples/redis"
        self.workload_home_dir = os.path.join(FRAMEWORK_HOME_DIR, test_config_dict['workload_home_dir'])
        # Redis build dir => "~/gramerf_framework/gramine/CI-Examples/redis/redis-6.0.5"
        self.workload_bld_dir = os.path.join(self.workload_home_dir, "redis-6.0.5")
        self.server_ip_addr = utils.determine_host_ip_addr()
        self.command = None

    def update_server_ip_in_client(self, tcd):
        # Setting 'SSHPASS' env variable for ssh commands
        print(f"\n-- Updating 'SSHPASS' env-var\n")
        os.environ['SSHPASS'] = "intel@123"
        client_name = tcd['client_username'] + "@" + tcd['client_ip']
        client_file_path = os.path.join(tcd['client_scripts_path'], "instance_benchmark.sh")
        sed_cmd = f"sed -i 's/^export HOST.*/export HOST=\"{self.server_ip_addr}\"/' {client_file_path}"
        update_server_ip_cmd = f"sshpass -e ssh {client_name} \"{sed_cmd}\""
        print("\n-- Updating server IP within redis client script..")  
        print(update_server_ip_cmd)

        utils.exec_shell_cmd(update_server_ip_cmd)

    def pre_actions(self, test_config_dict):
        utils.set_threads_cnt_env_var()
        utils.set_cpu_freq_scaling_governor()
        self.update_server_ip_in_client(test_config_dict)

    def setup_workload(self, test_config_dict):
        workload_name = utils.get_workload_name(test_config_dict['docker_image'])
        curation_output = curated_apps_lib.generate_curated_image(test_config_dict)

    def construct_server_workload_exec_cmd(self, test_config_dict, exec_mode = 'native'):
        redis_exec_cmd = None

        server_size = test_config_dict['server_size'] * 1024 * 1024 * 1024
        exec_bin_str = './redis-server' if exec_mode == 'native' else 'redis-server'

        tmp_exec_cmd = f"{exec_bin_str} --port {test_config_dict['server_port']} --maxmemory {server_size} --maxmemory-policy allkeys-lru --appendonly no --protected-mode no --save '' &"
        
        if exec_mode == 'native':
            redis_exec_cmd = "numactl -C 1 " + tmp_exec_cmd
        elif exec_mode == 'gramine-direct':
            redis_exec_cmd = "numactl -C 1 gramine-direct " + tmp_exec_cmd
        elif exec_mode == 'gramine-sgx':
            redis_exec_cmd = "numactl -C 1,2 gramine-sgx " + tmp_exec_cmd
        else:
            raise Exception(f"\nInvalid execution mode specified in config yaml!")

        print("\n-- Server command name = \n", redis_exec_cmd)
        return redis_exec_cmd

    def free_redis_server_port(self, tcd):
        container_id = None
        workload_docker_image_name = utils.get_workload_name(tcd['docker_image'])
        print(f"\n-- Killing docker container with image name: {workload_docker_image_name} to free the server port..")
        if e_mode == 'gramine-sgx':
            workload_docker_image_name = "gsc-" + workload_docker_image_name + "x"
        docker_container_list = utils.exec_shell_cmd("docker ps").splitlines()
        for container_item in docker_container_list:
            if container_item.split()[1] == workload_docker_image_name:
                container_id = container_item.split()[0]
                break
        
        if container_id is None:
            raise Exception(f"\n-- Could not find Container ID for {workload_docker_image_name}")
        
        docker_kill_cmd = f"docker kill {container_id}"
        utils.exec_shell_cmd(docker_kill_cmd)

    
    # Build the workload execution command based on execution params and execute it.
    def execute_workload(self, tcd):
        print("\n##### In execute_workload #####\n")

        print("\n-- Deleting older test results from client..")
        test_res_path = os.path.join(tcd['client_results_path'], tcd['test_name'])
        client_name = tcd['client_username'] + "@" + tcd['client_ip']
        test_res_del_cmd = f"sshpass -e ssh {client_name} 'rm -rf {test_res_path}'"
        print(test_res_del_cmd)
        utils.exec_shell_cmd(test_res_del_cmd)

        self.free_redis_server_port(tcd, e_mode)

        for e_mode in tcd['exec_mode']:
            print(f"\n-- Executing {tcd['test_name']} in {e_mode} mode")

            if e_mode == 'native':
                # Bring up the native redis server.
                workload_docker_image_name = utils.get_workload_name(tcd['docker_image'])
                docker_native_cmd = f"docker run --rm --net=host -t {workload_docker_image_name} &"
                utils.exec_shell_cmd(docker_native_cmd, None)
            else:
                docker_run_cmd = curated_apps_lib.get_docker_run_command(workload_name)
                result = curated_apps_lib.run_curated_image(docker_run_cmd)
            
            time.sleep(5)

            # Construct and execute memtier benchmark command within client.
            client_ssh_cmd = self.construct_client_exec_cmd(tcd, e_mode)
            utils.exec_shell_cmd(client_ssh_cmd, None)
            
            time.sleep(5)

            time.sleep(TEST_SLEEP_TIME_BW_ITERATIONS)
        
        self.process_results(tcd)
