import statistics
import shutil
import time
from common.config_files.constants import *
from docker_benchmarking import curated_apps_lib
from common.libs import utils
from conftest import trd
import re

class OpenVinoModelServerWorkload:
    def __init__(self, test_config_dict):
        self.workload_home_dir = FRAMEWORK_HOME_DIR

    def get_workload_home_dir(self):
        return self.workload_home_dir

    def pull_workload_default_image(self, test_config_dict):
        workload_docker_image_name = utils.get_workload_name(test_config_dict['docker_image'])
        workload_docker_pull_cmd = f"docker pull {workload_docker_image_name}"
        print(f"\n-- Pulling latest OVMS docker image from docker hub..\n", workload_docker_pull_cmd)
        utils.exec_shell_cmd(workload_docker_pull_cmd, None)

    def encrypt_db(self, test_config_dict):
        workload_name = test_config_dict["docker_image"].split(" ")[0]
        if "openvino-model-server" in workload_name:
            workload_name = "ovms"
        output = utils.popen_subprocess(eval(workload_name.upper()+"_TEST_ENCRYPTION_KEY"), CURATED_APPS_PATH)
        if os.environ["encryption"] == "1":
            print(f"\n-- Encrypting model/s..")
            output = utils.popen_subprocess(f"sudo rm -rf {OVMS_ENCRYPTED_DB_PATH}", CURATED_APPS_PATH)
            utils.exec_shell_cmd(f"sudo mkdir -p /mnt/tmpfs && sudo mount -t tmpfs tmpfs /mnt/tmpfs && mkdir -p {OVMS_ENCRYPTED_DB_PATH}")
            encryption_output = utils.popen_subprocess(OVMS_ENCRYPT_DB_CMD, CURATED_APPS_PATH)
            print(encryption_output)

    def pre_actions(self, test_config_dict):
        utils.set_cpu_freq_scaling_governor()

    # Function to copy the respective model file from downloaded path to actual test folder.
    def copy_model_files(self, test_config_dict):
        workload_name = test_config_dict["docker_image"].split(" ")[0]
        if "openvino-model-server" in workload_name:
            workload_name = "ovms"

        # Deleting old models from previous runs.
        model_bin_file = os.path.join(eval(workload_name.upper()+"_TESTDB_PATH"), 'model.bin')
        model_xml_file = os.path.join(eval(workload_name.upper()+"_TESTDB_PATH"), 'model.xml')
        if os.path.exists(model_bin_file):
            os.remove(model_bin_file)
        if os.path.exists(model_xml_file):
            os.remove(model_xml_file)

        src_file = os.path.join(eval(workload_name.upper()+"_MODEL_FILES_PATH"), test_config_dict['model_name']+'.bin')
        print(f"\n Copying {src_file} to {model_bin_file}") 
        shutil.copy2(src_file, model_bin_file)

        src_file = os.path.join(eval(workload_name.upper()+"_MODEL_FILES_PATH"), test_config_dict['model_name']+'.xml')
        print(f"\n Copying {src_file} to {model_xml_file}")
        shutil.copy2(src_file, model_xml_file)

    def setup_workload(self, test_config_dict):
        # Pull default workload image for native run.
        self.pull_workload_default_image(test_config_dict)
        self.copy_model_files(test_config_dict)
        manifest_file = os.path.join(CURATED_APPS_PATH, "workloads/openvino-model-server/openvino-model-server.manifest.template")
        utils.check_and_enable_edmm_in_manifest(manifest_file)

    def generate_curated_image(self, test_config_dict):
        # Create graminized image for gramine direct and sgx runs.
        if os.environ["exec_mode"] != "native":
            print(f"\n-- Creating graminized image for SGX runs..")
            curation_output = curated_apps_lib.generate_curated_image(test_config_dict)
            decode_curation_output = curation_output.decode('utf-8')
            curation_output_result = curated_apps_lib.verify_image_creation(decode_curation_output)
            if curation_output_result == False:
                raise Exception("\n-- Failed to create the curated image!!")
            print(f"\n-- Successfully created graminized image..")
    
    def get_server_exec_cmd(self, tcd, e_mode, container_name):
        workload_docker_image_name = utils.get_workload_name(tcd['docker_image'])
        if e_mode == 'native':
            init_db_cmd = f"docker run --net=host --name {container_name} -u $(id -u):$(id -g) -v $(pwd)/workloads/openvino-model-server/test_model:/model \
                            -p 9001:9001 openvino/model_server:latest --model_path /model {tcd['docker_arguments']}"
        elif e_mode == 'gramine-sgx':
            if os.environ['encryption'] == '1':
                init_db_cmd = f"docker run --rm --net=host --name {container_name} -u 0:0 -p 9001:9001 --device=/dev/sgx/enclave \
                                -v {OVMS_ENCRYPTED_DB_PATH}:{OVMS_ENCRYPTED_DB_PATH} \
                                -t gsc-{workload_docker_image_name} --model_path {OVMS_ENCRYPTED_DB_PATH} {tcd['docker_arguments']}"
            else:
                init_db_cmd = f"docker run --rm --net=host --name {container_name} -u 0:0 -p 9001:9001 --device=/dev/sgx/enclave \
                                -v $(pwd)/workloads/openvino-model-server/test_model:$(pwd)/workloads/openvino-model-server/test_model \
                                -t gsc-{workload_docker_image_name} --model_path $(pwd)/workloads/openvino-model-server/test_model {tcd['docker_arguments']}"
        return init_db_cmd
    
    def get_container_name(self, e_mode):
        if e_mode == 'native':
            return "init_native_test_db"
        elif e_mode == 'gramine-sgx':
            if os.environ['encryption'] == '1':
                return "init_sgx_enc_test_db"
            else:
                return "init_sgx_wo_enc_test_db"
        else:
            raise Exception("\n-- Invalid execution mode!!")

    def benchmark_execution(self, tcd):
        print("Inside benchmark execution")
        os.chdir(CURATED_APPS_PATH)
        if not os.path.exists("model_server"):
            utils.exec_shell_cmd("git clone https://github.com/openvinotoolkit/model_server.git", None)
            os.chdir(os.path.join(CURATED_APPS_PATH, "model_server/demos/benchmark/cpp"))
            utils.exec_shell_cmd("make", None)
        benchmark_exec_cmd = f'docker run --rm --network host -e "no_proxy=localhost" ovms_cpp_benchmark \
                             ./synthetic_client_async_benchmark --model_name={tcd["model_name"]} --grpc_port=9001 --iterations=2000 \
                             --max_parallel_requests=100 --consumers=8 --producers=1'
        print("\n Executing below benchmark command..\n", benchmark_exec_cmd)
        client_output = utils.exec_shell_cmd(benchmark_exec_cmd)
        return client_output
    
    def exec_workload_perf_cmd(self, test_config_dict, test_dict, exec_mode = 'native'):
        utils.set_no_proxy()
        for i in range(test_config_dict['iterations']):
            run_cmd_output = self.benchmark_execution(test_config_dict)
            print(run_cmd_output)
            time.sleep(TEST_SLEEP_TIME_BW_ITERATIONS)
            print(re.findall(r'Avg FPS:* \d+.\d+', run_cmd_output))
            result = float(re.findall(r'Avg FPS:* \d+.\d+', run_cmd_output)[0].split(":")[1].strip())
            test_dict[exec_mode].append(result)

    # Build the workload execution command based on execution params and execute it.
    def execute_workload(self, test_config_dict, e_mode, test_dict):
        print("\n##### In execute_workload #####\n")
        print(f"\n-- Executing {test_config_dict['test_name']} in {e_mode} mode")

        if e_mode != "native":
            self.encrypt_db(test_config_dict)
            self.generate_curated_image(test_config_dict)

        workload_name = test_config_dict['docker_image'].split(" ")[0]
        container_name = self.get_container_name(e_mode)

        print(f"Kill any existing containers with {container_name} name")
        utils.popen_subprocess(f"docker rm -f {container_name}")
        init_db_cmd = self.get_server_exec_cmd(test_config_dict, e_mode, container_name)
        print(f"\n-- Launching {workload_name} server in {e_mode} mode..\n", init_db_cmd)

        print("\n\n", os.getcwd())
        
        process = utils.popen_subprocess(init_db_cmd, CURATED_APPS_PATH)
        time.sleep(10)
        if curated_apps_lib.verify_process(test_config_dict, process, 60*10) == False:
            raise Exception(f"\n-- Failure - Couldn't launch {workload_name} server in {e_mode} mode!!")
        
        self.exec_workload_perf_cmd(test_config_dict, test_dict, e_mode)
        print(test_dict)
        
        # workload cleanup
        if e_mode == 'native':
            output = utils.exec_shell_cmd("docker stop $(docker ps -a -q)")
            print(output)
        else:
            utils.cleanup_after_test(workload_name)
    
    def update_test_results_in_global_dict(self, tcd, test_dict):
        global trd
        if 'native' in tcd['exec_mode']:
            test_dict['native-avg'] = '{:0.3f}'.format(statistics.median(test_dict['native']))
        
        if 'gramine-sgx' in tcd['exec_mode']:
            test_dict['sgx-avg'] = '{:0.3f}'.format(statistics.median(test_dict['gramine-sgx']))
            if 'native' in tcd['exec_mode']:
                test_dict['sgx-deg'] = utils.percent_degradation(tcd, test_dict['native-avg'], test_dict['sgx-avg'])

        utils.write_to_csv(tcd, test_dict)

        trd[tcd['workload_name']] = trd.get(tcd['workload_name'], {})
        trd[tcd['workload_name']].update({tcd['test_name']: test_dict})
