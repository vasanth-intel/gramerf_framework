import re
import sys
import subprocess
from common.libs import utils
from common.config_files.constants import *


def dcap_setup():
    copy_cmd = "cp /etc/sgx_default_qcnl.conf {}/verifier_image/".format(os.path.join(ORIG_CURATED_PATH, CURATED_PATH))
    utils.run_subprocess(copy_cmd)
    fd = open(VERIFIER_DOCKERFILE)
    fd_contents = fd.read()
    azure_dcap = "(.*)RUN wget https:\/\/packages.microsoft(.*)\n(.*)amd64.deb"
    updated_content = re.sub(azure_dcap, "", fd_contents)
    dcap_library = "RUN apt-get install -y gramine-dcap\nRUN apt install -y libsgx-dcap-default-qpl libsgx-dcap-default-qpl-dev\nCOPY sgx_default_qcnl.conf  /etc/sgx_default_qcnl.conf"
    new_data = re.sub("RUN apt-get install -y gramine-dcap", dcap_library, updated_content)
    fd.close()

    fd = open(VERIFIER_DOCKERFILE, "w+")
    fd.write(new_data)
    fd.close()


def curated_setup():
    print("Cleaning old contrib repo")
    rm_cmd = "rm -rf {}".format(ORIG_CURATED_PATH)
    utils.exec_shell_cmd(rm_cmd)
    print("Cloning and checking out Contrib Git Repo")
    utils.exec_shell_cmd(CONTRIB_GIT_CMD)
    # utils.exec_shell_cmd(GIT_CHECKOUT_CMD)
    if utils.check_machine() == "DCAP client":
        print("Configuring the contrib repo to setup DCAP client")
        dcap_setup()


def copy_repo():
    copy_cmd = "cp -rf {} {}".format(ORIG_CURATED_PATH, REPO_PATH)
    utils.exec_shell_cmd("rm -rf contrib_repo")
    utils.exec_shell_cmd(copy_cmd)


def verify_image_creation(curation_output):
    if re.search("The curated GSC image gsc-(.*) is ready", curation_output) or \
            re.search("docker run", curation_output):
        return True
    return False


def generate_curated_image(test_config_dict):
    curation_output = ''
    workload_image = test_config_dict["docker_image"]

    # The following ssh command is to mitigate the curses error faced while launching the command through Jenkins.
    curation_cmd = f"sshpass -e ssh -tt intel@localhost 'cd {CURATED_APPS_PATH} && python3 curate.py {workload_image} test'"

    print("Curation cmd ", curation_cmd)

    result = subprocess.run([curation_cmd], input=b'\x07', shell=True, check=True, stdout=subprocess.PIPE)
    os.chdir(FRAMEWORK_HOME_DIR)
      
    curation_output = result.stdout.strip()
    print(curation_output.strip())

    return curation_output


def get_docker_run_command(workload_name):
    output = []
    wrapper_image = "gsc-{}".format(workload_name)
    gsc_workload = "docker run --rm --net=host --device=/dev/sgx/enclave -t {}".format(wrapper_image)
    output.append(gsc_workload)
    return output

def get_workload_result(test_config_dict):
    if "workload_result" in test_config_dict.keys():
        workload_result = [test_config_dict["workload_result"]]
    elif "bash" in test_config_dict["docker_image"]:
        workload_result = ["total        used        free      shared  buff/cache   available"]
    elif "redis" in test_config_dict["docker_image"]:
        workload_result = ["Ready to accept connections"]
    elif "pytorch" in test_config_dict["docker_image"]:
        workload_result = ["Done. The result was written to `result.txt`."]
    elif "sklearn" in test_config_dict["docker_image"]:
        workload_result = "Kmeans perf evaluation finished"
    elif "tensorflow-serving" in test_config_dict["docker_image"]:
        workload_result = "Running gRPC ModelServer at 0.0.0.0:8500"
    return workload_result

def verify_process(test_config_dict, process=None):
    result = False
    debug_log = None
    workload_result = get_workload_result(test_config_dict)

    while True:
        nextline = process.stdout.readline()
        print(nextline.strip())
        if nextline == '' and process.poll() is not None:
            break
        if all(x in nextline for x in workload_result):
            process.stdout.close()
            sys.stdout.flush()
            result = True
            break
    return result

def run_curated_image(test_config_dict, docker_run_cmd):
    result = False
    gsc_docker_command = docker_run_cmd[-1]

    process = utils.popen_subprocess(gsc_docker_command)
    return verify_process(test_config_dict, process)
