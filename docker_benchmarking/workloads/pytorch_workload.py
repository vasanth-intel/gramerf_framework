import time
import shutil
import glob
import statistics
from pathlib import Path
from common.config_files.constants import *
from common.libs import utils
from conftest import trd

class PytorchWorkload:
    def __init__(self, test_config_dict):
        # Workloads home dir => "~/gramerf_framework/"
        # Ideally, changing to home dir is required for bare-metal case as we build
        # the workload by downloading its source.
        # In curated workloads we are setting the workload home dir to CURATED_APPS_PATH.
        # But, in this workload we are not using or depending on any source from contrib repo.
        # Instead, we are depending on the native and graminized images from the platform
        # performance team. Hence, setting the workload home dir to FRAMEWORK_HOME_DIR.
        self.workload_home_dir = FRAMEWORK_HOME_DIR

    def get_workload_home_dir(self):
        return self.workload_home_dir

    def pre_actions(self, test_config_dict):
        utils.set_threads_cnt_env_var()
        utils.set_cpu_freq_scaling_governor()

    def setup_workload(self, test_config_dict):
        # Deleting old logs if any.
        results_dir = PERF_RESULTS_DIR + '/' + test_config_dict['test_name']
        if os.path.exists(results_dir):
            shutil.rmtree(results_dir)
        os.makedirs(results_dir, exist_ok=True)

    def check_and_kill_container(self, container_name):
        running_container_count = utils.exec_shell_cmd(f"docker ps | grep -c -w {container_name}")
        print("\n Running conts", running_container_count)
        if running_container_count > 0:
            print(f"\n -- Stopping and killing any existing container with name {container_name}")
            utils.exec_shell_cmd(f"docker stop {container_name}")
            utils.exec_shell_cmd(f"docker rm {container_name}")

    def launch_container(self, tcd, e_mode):
        container_name = f"pytorch_{tcd['model_name']}_{e_mode}_{tcd['metric']}_container"
        results_dir = PERF_RESULTS_DIR + '/' + tcd['test_name']

        print(f"\n-- Launching container {container_name} in {e_mode} mode")
        gramine_args = ""
        if e_mode == "gramine-direct":
            gramine_args = "--env GSC_PAL=Linux --security-opt seccomp=unconfined"
        elif e_mode == "gramine-sgx":
            gramine_args = "--device=/dev/sgx_enclave"

        # We need to set the base execution path within the container before executing any perf
        # benchmarking commands. We are setting the same during the launch of container itself.
        # For both Resnet50 and DLRM models this path is set to "/" for native execution
        # mode and set to "/gramine/app_files" for gramine direct/sgx execution modes.
        container_exec_path = "/"
        if e_mode != "native":
            container_exec_path = "/gramine/app_files"

        env_file = os.path.join(FRAMEWORK_HOME_DIR, "docker_benchmarking/config_files", tcd['env_file'])

        if tcd['model_name'] == "resnet50":
            container_launch_cmd = f"docker run -td --rm --privileged --network host -w {container_exec_path} --env-file {env_file} --name {container_name} \
                                    {gramine_args} -v {results_dir}:/home/logs --entrypoint /bin/bash {tcd[e_mode + '_docker_image']}"
        
        elif tcd['model_name'] == "dlrm":
            # Before executing DLRM tests, DLRM models need to be copied and extracted at "~/Do_not_delete_gramerf_dependencies/pytorch".
            dlrm_model_path = os.path.join(Path.home(),"Do_not_delete_gramerf_dependencies/pytorch")
            container_launch_cmd = f"docker run --rm -td --privileged --net host --shm-size 4g -w {container_exec_path} --env-file {env_file} --name {container_name} \
                                    {gramine_args} -v {dlrm_model_path}:/home/dataset/pytorch -v {results_dir}:/home/logs \
                                    --entrypoint /bin/bash {tcd[e_mode + '_docker_image']}"
        else:
            raise Exception("\n-- Failure in launch_container: Invalid pytorch model passed from yaml file..\n")

        print("\nContainer launch cmd :\n", container_launch_cmd)
        utils.exec_shell_cmd(container_launch_cmd, None)

    def set_container_env_vars(self, tcd, e_mode):
        env_vars_str = ""
        # For DLRM model, env variables are same irrespective of execution modes or metrics(Throughput or Latency)
        # But, there is slight difference in env variables for Resnet50 model:
        # All environment variables present in pytorch_rn50_docker_env_variables.env should be set, which are common for 
        # throughput and latency for all execution modes with the following exceptions.
        # - For 'throughput' OMP_NUM_THREADS should be set/overwritten as ${cores_per_socket} and not hardcoded to 4.
        # - When executing in SGX mode and for 'latency', the value of LD_PRELOAD should be set/overwritten as 
        #   "/root/lib/jemalloc/lib/libjemalloc.so:/gramine/meson_build_output/lib64/gramine/runtime/glibc/libgomp.so.1"
        # - All 'AVX' tests require ONEDNN_MAX_CPU_ISA to be set to 'avx512_core_vnni'.
        if tcd['model_name'] == "resnet50":
            if tcd['metric'] == 'throughput':
                env_vars_str = f"-e OMP_NUM_THREADS={os.environ['CORES_PER_SOCKET']}"
            elif tcd['metric'] == 'latency' and e_mode == 'gramine-sgx':
                env_vars_str = f"-e LD_PRELOAD=/root/lib/jemalloc/lib/libjemalloc.so:/gramine/meson_build_output/lib64/gramine/runtime/glibc/libgomp.so.1"
        if 'avx' in tcd['test_name']:
            env_vars_str = f"-e ONEDNN_MAX_CPU_ISA=avx512_core_vnni {env_vars_str}"

        return env_vars_str

    def get_resnet50_throughput_common_cmd(self, tcd, e_mode):
        common_cmd = ""
        if 'int8' in tcd['test_name']:
            common_cmd = "/root/anaconda3/envs/pytorch/bin/python3 -u /home/workspace/pytorch_model/models/image_recognition/pytorch/common/main.py \
                -e -a resnet50 ../ --dummy --int8 --configure-dir /home/workspace/pytorch_model/models/image_recognition/pytorch/common/resnet50_configure_sym.json \
                --steps 2000 --dummy --ipex --seed 2020 -j 0 -b 116"
        elif 'fp32' in tcd['test_name']:
            common_cmd = "/root/anaconda3/envs/pytorch/bin/python3 -u /home/workspace/pytorch_model/models/image_recognition/pytorch/common/main.py \
                -e -a resnet50 ../ --dummy --jit --steps 2000 --dummy --ipex --seed 2020 -j 0 -b 116"
        elif 'bfloat16' in tcd['test_name']:
            common_cmd = "/root/anaconda3/envs/pytorch/bin/python3 -u /home/workspace/pytorch_model/models/image_recognition/pytorch/common/main.py \
                -e -a resnet50 ../ --dummy --bf16 --jit --steps 2000 --dummy --ipex --seed 2020 -j 0 -b 116"
        else:
            raise Exception("\n-- Failure in get_resnet50_throughput_common_cmd: Unknown precision or precision not specified in test name..\n")
        
        if e_mode == 'gramine-sgx' or e_mode == 'gramine-direct':
            common_cmd = rf"./apploader.sh -c \"{common_cmd}\""
        
        return common_cmd

    def get_resnet50_latency_common_cmd(self, tcd, e_mode):
        common_cmd = ""
        total_instance = int(int(os.environ['CORES_PER_SOCKET']) / 4)
        if 'int8' in tcd['test_name']:
            common_cmd = f"/root/anaconda3/envs/pytorch/bin/python3 -u /home/workspace/pytorch_model/models/image_recognition/pytorch/common/main.py \
                --configure-dir /home/workspace/pytorch_model/models/image_recognition/pytorch/common/resnet50_configure_sym.json --dummy --int8 --ipex \
                --number-instance {total_instance} --steps 35000 --weight-sharing -a resnet50 -b 1 -e -j 0 /home/dataset/pytorch/resnet50"
        elif 'fp32' in tcd['test_name']:
            common_cmd = f"/root/anaconda3/envs/pytorch/bin/python3 -u /home/workspace/pytorch_model/models/image_recognition/pytorch/common/main.py \
                --dummy --ipex --jit --number-instance {total_instance} --steps 5000 --weight-sharing -a resnet50 -b 1 -e -j 0 /home/dataset/pytorch/resnet50"
        elif 'bfloat16' in tcd['test_name']:
            common_cmd = f"/root/anaconda3/envs/pytorch/bin/python3 -u /home/workspace/pytorch_model/models/image_recognition/pytorch/common/main.py --bf16 \
                --dummy --ipex --jit --number-instance {total_instance} --steps 20000 --weight-sharing -a resnet50 -b 1 -e -j 0 /home/dataset/pytorch/resnet50"
        else:
            raise Exception("\n-- Failure in get_resnet50_throughput_common_cmd: Unknown precision or precision not specified in test name..\n")
        
        if e_mode == 'gramine-sgx' or e_mode == 'gramine-direct':
            common_cmd = rf"./apploader.sh -c \"{common_cmd}\""
            
        return common_cmd

    def exec_cont_cmds_for_resnet50(self, tcd, e_mode):
        container_name = f"pytorch_{tcd['model_name']}_{e_mode}_{tcd['metric']}_container"

        if tcd['metric'] == 'throughput':
            common_cmd = self.get_resnet50_throughput_common_cmd(tcd, e_mode)
            cores_per_socket_minus_1 = int(os.environ['CORES_PER_SOCKET']) - 1
            cmd1 = f"numactl -C 0-{cores_per_socket_minus_1} -m 0 {common_cmd}"
            if os.environ['SOCKETS'] == "2":
                cores_per_socket_cmd2 = int(os.environ['CORES_PER_SOCKET']) * 2 - 1
                cmd2 = f"numactl -C {os.environ['CORES_PER_SOCKET']}-{cores_per_socket_cmd2} -m 1 {common_cmd}"
        elif tcd['metric'] == 'latency':
            common_cmd = self.get_resnet50_latency_common_cmd(tcd, e_mode)
            total_instance = int(int(os.environ['CORES_PER_SOCKET']) / 4)
            total_instance_x_4_minus_1 = total_instance * 4 - 1
            cmd1 = f"numactl -C 0-{total_instance_x_4_minus_1} -m 0 {common_cmd}"
            if os.environ['SOCKETS'] == "2":
                cores_per_socket_cmd2 = int(os.environ['CORES_PER_SOCKET']) + total_instance_x_4_minus_1
                cmd2 = f"numactl -C {os.environ['CORES_PER_SOCKET']}-{cores_per_socket_cmd2} -m 1 {common_cmd}"
        else:
            raise Exception("\n-- Failure in exec_cont_cmds_for_resnet50: Unknown metric specified in yaml file for the test..\n")
        
        env_vars_str = self.set_container_env_vars(tcd, e_mode)

        framework_shell_script_path = os.path.join(FRAMEWORK_HOME_DIR, "docker_benchmarking/config_files", "pytorch_cmds.sh")
        utils.exec_shell_cmd(f"chmod +x {framework_shell_script_path}", None)
        utils.exec_shell_cmd(f"docker cp {framework_shell_script_path} {container_name}:/home/workspace/benchmark", None)
        container_shell_script_path = "/home/workspace/benchmark/pytorch_cmds.sh"

        res_filename = f"/home/logs/{tcd['test_name']}_{e_mode}"
        if os.environ['SOCKETS'] == "2":
            print(f"\nCommand is - docker exec {env_vars_str} -t {container_name} bash -c '{container_shell_script_path} {tcd['iterations']} \"{cmd1}\" \"{cmd2}\" {res_filename}'\n")
            utils.exec_shell_cmd(f"docker exec {env_vars_str} -t {container_name} bash -c '{container_shell_script_path} {tcd['iterations']} \"{cmd1}\" \"{cmd2}\" {res_filename}'", None)
        else:
            print(f"\nCommand is\n docker exec {env_vars_str} -t {container_name} bash -c '{container_shell_script_path} {tcd['iterations']} \"{cmd1}\" {res_filename}'\n\n")
            utils.exec_shell_cmd(f"docker exec {env_vars_str} -t {container_name} bash -c '{container_shell_script_path} {tcd['iterations']} \"{cmd1}\" {res_filename}'", None)

    def get_dlrm_throughput_common_cmd(self, tcd, e_mode):
        common_cmd = ""
        if 'int8' in tcd['test_name']:
            common_cmd = f"/root/anaconda3/envs/pytorch/bin/python3 -u /home/workspace/pytorch_model/models/recommendation/pytorch/dlrm/product/dlrm_s_pytorch.py \
                --raw-data-file=/home/dataset/pytorch/dlrm/input/day --processed-data-file=/home/dataset/pytorch/dlrm/input/terabyte_processed.npz \
                --data-set=terabyte --memory-map --mlperf-bin-loader --round-targets=True --learning-rate=1.0 --arch-mlp-bot=13-512-256-128 \
                --arch-mlp-top=1024-1024-512-256-1 --arch-sparse-feature-size=128 --max-ind-range=4000 --ipex-interaction --numpy-rand-seed=727 --inference-only \
                --num-batches=100000 --print-freq=10 --print-time --mini-batch-size=128 --share-weight-instance={os.environ['CORES_PER_SOCKET']} --int8 \
                --int8-configure=/home/workspace/pytorch_model/models/recommendation/pytorch/dlrm/product/int8_configure.json"
        elif 'fp32' in tcd['test_name']:
            common_cmd = f"/root/anaconda3/envs/pytorch/bin/python3 -u /home/workspace/pytorch_model/models/recommendation/pytorch/dlrm/product/dlrm_s_pytorch.py \
                --raw-data-file=/home/dataset/pytorch/dlrm/input/day --processed-data-file=/home/dataset/pytorch/dlrm/input/terabyte_processed.npz \
                --data-set=terabyte --memory-map --mlperf-bin-loader --round-targets=True --learning-rate=1.0 --arch-mlp-bot=13-512-256-128 \
                --arch-mlp-top=1024-1024-512-256-1 --arch-sparse-feature-size=128 --max-ind-range=4000 --ipex-interaction --numpy-rand-seed=727 --inference-only \
                --num-batches=100000 --print-freq=10 --print-time --mini-batch-size=128 --share-weight-instance={os.environ['CORES_PER_SOCKET']}"
        elif 'bfloat16' in tcd['test_name']:
            common_cmd = f"/root/anaconda3/envs/pytorch/bin/python3 -u /home/workspace/pytorch_model/models/recommendation/pytorch/dlrm/product/dlrm_s_pytorch.py \
                --raw-data-file=/home/dataset/pytorch/dlrm/input/day --processed-data-file=/home/dataset/pytorch/dlrm/input/terabyte_processed.npz \
                --data-set=terabyte --memory-map --mlperf-bin-loader --round-targets=True --learning-rate=1.0 --arch-mlp-bot=13-512-256-128 \
                --arch-mlp-top=1024-1024-512-256-1 --arch-sparse-feature-size=128 --max-ind-range=4000 --ipex-interaction --numpy-rand-seed=727 --inference-only \
                --num-batches=100000 --print-freq=10 --print-time --mini-batch-size=128 --share-weight-instance={os.environ['CORES_PER_SOCKET']} --bf16"
        else:
            raise Exception("\n-- Failure in get_resnet50_throughput_common_cmd: Unknown precision or precision not specified in test name..\n")
        
        if e_mode == 'gramine-sgx' or e_mode == 'gramine-direct':
            common_cmd = rf"./apploader.sh -c \"{common_cmd}\""
        
        return common_cmd

    def exec_cont_cmds_for_dlrm(self, tcd, e_mode):
        container_name = f"pytorch_{tcd['model_name']}_{e_mode}_{tcd['metric']}_container"

        # We have only throughput calculation for DLRM model.
        common_cmd = self.get_dlrm_throughput_common_cmd(tcd, e_mode)
        cmd = f"numactl -N 0 {common_cmd}"

        framework_shell_script_path = os.path.join(FRAMEWORK_HOME_DIR, "docker_benchmarking/config_files", "pytorch_cmds.sh")
        utils.exec_shell_cmd(f"chmod +x {framework_shell_script_path}", None)
        utils.exec_shell_cmd(f"docker cp {framework_shell_script_path} {container_name}:/home/workspace/benchmark", None)
        container_shell_script_path = "/home/workspace/benchmark/pytorch_cmds.sh"

        res_filename = f"/home/logs/{tcd['test_name']}_{e_mode}"
        utils.exec_shell_cmd(f"docker exec -t {container_name} bash -c '{container_shell_script_path} {tcd['iterations']} \"{cmd}\" {res_filename}'", None)
        
    # Build the workload execution command based on execution params and execute it.
    def execute_workload(self, tcd, e_mode, test_dict=None):
        print("\n##### In execute_workload #####\n")
        print(f"\n-- Executing {tcd['test_name']} in {e_mode} mode")

        # Launch the container in the respective execution mode with appropriate arguments.
        self.launch_container(tcd, e_mode)

        if tcd['model_name'] == 'resnet50':
            self.exec_cont_cmds_for_resnet50(tcd, e_mode)
        elif tcd['model_name'] == 'dlrm':
            self.exec_cont_cmds_for_dlrm(tcd, e_mode)
        else:
            raise Exception("\n-- Failure in execute_workload: Invalid pytorch model passed from yaml file..\n")

        output = utils.exec_shell_cmd("docker stop $(docker ps -a -q)")
        print(output)

        utils.exec_shell_cmd('sudo sh -c "echo 3 > /proc/sys/vm/drop_caches"')
        time.sleep(TEST_SLEEP_TIME_BW_ITERATIONS)
    
    def get_metric_from_file(self, tcd, filename):
        throughput = 0.0
        if tcd['metric'] == 'throughput':
            with open(filename, "r") as f:
                for row in f.readlines():
                    if row and 'Throughput:' in row:
                        throughput = float(row.split()[1])
                        break
        elif tcd['metric'] == 'latency':
            with open(filename, "r") as f:
                for row in f.readlines():
                    if row and 'Throughput:' in row:
                        tpt_count = row.count('Throughput:')
                        for i in range(tpt_count):
                            throughput = throughput + float(row.split('Throughput: ')[i+1].split()[0])
        else:
            raise Exception("\n-- Failure in get_metric_from_file: Unknown metric specified in yaml file for the test..\n")

        return throughput

    def push_metric_to_dict(self, tcd, filename, e_mode, metric, test_dict_throughput, test_dict_latency):
        if "s0" in filename:
            if tcd['metric'] == 'throughput':
                test_dict_throughput[e_mode+"_s0"].append(metric)
            else:
                test_dict_latency[e_mode+"_s0"].append(metric)
        else:
            if tcd['metric'] == 'throughput':
                test_dict_throughput[e_mode+"_s1"].append(metric)
            else:
                test_dict_latency[e_mode+"_s1"].append(metric)

    def compute_average_and_r2r_variation(self, tcd, e_mode, test_dict_throughput, test_dict_latency):
        if tcd['metric'] == 'throughput':
            test_dict_throughput[e_mode+"_s0_avg"] = '{:0.3f}'.format(statistics.mean(test_dict_throughput[e_mode+"_s0"]))
            test_dict_throughput[e_mode+"_s0_r2r_var"] = utils.run_to_run_variation(test_dict_throughput[e_mode+"_s0"])
        else:
            test_dict_latency[e_mode+"_s0_avg"] = '{:0.3f}'.format(statistics.mean(test_dict_latency[e_mode+"_s0"]))
            test_dict_latency[e_mode+"_s0_r2r_var"] = utils.run_to_run_variation(test_dict_latency[e_mode+"_s0"])

        if os.environ['SOCKETS'] == "2" and tcd['model_name'] == "resnet50":
            if tcd['metric'] == 'throughput':
                test_dict_throughput[e_mode+"_s1_avg"] = '{:0.3f}'.format(statistics.mean(test_dict_throughput[e_mode+"_s1"]))
                test_dict_throughput[e_mode+"_s1_r2r_var"] = utils.run_to_run_variation(test_dict_throughput[e_mode+"_s1"])
            else:
                test_dict_latency[e_mode+"_s1_avg"] = '{:0.3f}'.format(statistics.mean(test_dict_latency[e_mode+"_s1"]))
                test_dict_latency[e_mode+"_s1_r2r_var"] = utils.run_to_run_variation(test_dict_latency[e_mode+"_s1"])

    def compute_degradation(self, tcd, e_mode, test_dict_throughput, test_dict_latency):
        if tcd['metric'] == 'throughput':
            test_dict_throughput[e_mode+"_s0_Deg"] = utils.percent_degradation(tcd, test_dict_throughput['native_s0_avg'], test_dict_throughput[e_mode+"_s0_avg"])
        else:
            # Even though the test is for latency, we are passing 'True' to the last argument in the below call. This is intentional as the output of the command
            # executed for latency gives results as 'Throughput' and not 'Latency'. The 'percent_degradation' function in the above 'if' condition automatically
            # takes care for throughput and we need not pass 'True' explicitly as the function checks if 'throughput' is present in the test name.
            test_dict_latency[e_mode+"_s0_Deg"] = utils.percent_degradation(tcd, test_dict_latency['native_s0_avg'], test_dict_latency[e_mode+"_s0_avg"], True)

        if os.environ['SOCKETS'] == "2" and tcd['model_name'] == "resnet50":
            if tcd['metric'] == 'throughput':
                test_dict_throughput[e_mode+"_s1_Deg"] = utils.percent_degradation(tcd, test_dict_throughput['native_s1_avg'], test_dict_throughput[e_mode+"_s1_avg"])
            else:
                # Even though the test is for latency, we are passing 'True' to the last argument in the below call. This is intentional as the output of the command
                # executed for latency gives results as 'Throughput' and not 'Latency'. The 'percent_degradation' function in the above 'if' condition automatically
                # takes care for throughput and we need not pass 'True' explicitly as the function checks if 'throughput' is present in the test name.
                test_dict_latency[e_mode+"_s1_Deg"] = utils.percent_degradation(tcd, test_dict_latency['native_s1_avg'], test_dict_latency[e_mode+"_s1_avg"], True)

    def process_results(self, tcd):
        results_dir = PERF_RESULTS_DIR + '/' + tcd['test_name']
        os.chdir(results_dir)
        txt_files = glob.glob1(results_dir, "*.txt")
        
        expected_num_files = len(tcd['exec_mode']) * tcd['iterations']
        if os.environ['SOCKETS'] == "2" and tcd['model_name'] == "resnet50":
            expected_num_files = expected_num_files * 2
        if len(txt_files) != expected_num_files:
            raise Exception(f"\n-- Number of test result files - {len(txt_files)} is not equal to the expected number - {expected_num_files}.\n")

        global trd
        test_dict_throughput = {}
        test_dict_latency = {}
        for e_mode in tcd['exec_mode']:
            test_dict_throughput[e_mode+"_s0"] = []
            test_dict_latency[e_mode+"_s0"] = []
            if os.environ['SOCKETS'] == "2" and tcd['model_name'] == "resnet50":
                test_dict_throughput[e_mode+"_s1"] = []
                test_dict_latency[e_mode+"_s1"] = []
        
        for filename in txt_files:
            metric_val = self.get_metric_from_file(tcd, filename)

            if "native" in filename:
                self.push_metric_to_dict(tcd, filename, "native", metric_val, test_dict_throughput, test_dict_latency)
            elif "gramine-direct" in filename:
                self.push_metric_to_dict(tcd, filename, "gramine-direct", metric_val, test_dict_throughput, test_dict_latency)
            elif "gramine-sgx" in filename:
                self.push_metric_to_dict(tcd, filename, "gramine-sgx", metric_val, test_dict_throughput, test_dict_latency)
            else:
                raise Exception(f"\n-- Failure in parse_resent50_tpt_txt_files: Unknown execution mode found in filename..\n")

        if 'native' in tcd['exec_mode']:
            self.compute_average_and_r2r_variation(tcd, "native", test_dict_throughput, test_dict_latency)

        if 'gramine-direct' in tcd['exec_mode']:
            self.compute_average_and_r2r_variation(tcd, "gramine-direct", test_dict_throughput, test_dict_latency)
            if 'native' in tcd['exec_mode']:
                self.compute_degradation(tcd, "gramine-direct", test_dict_throughput, test_dict_latency)

        if 'gramine-sgx' in tcd['exec_mode']:
            self.compute_average_and_r2r_variation(tcd, "gramine-sgx", test_dict_throughput, test_dict_latency)
            if 'native' in tcd['exec_mode']:
                self.compute_degradation(tcd, "gramine-sgx", test_dict_throughput, test_dict_latency)

        trd[tcd['workload_name']] = trd.get(tcd['workload_name'], {})
        if tcd['metric'] == 'throughput':
            trd[tcd['workload_name']].update({tcd['test_name']: test_dict_throughput})
        else:
            trd[tcd['workload_name']].update({tcd['test_name']: test_dict_latency})

        os.chdir(self.workload_home_dir)
