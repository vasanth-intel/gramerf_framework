import re
import sys
import subprocess
import time
from common.libs import utils
from common.config_files.constants import *


def curated_setup():
    utils.gramine_package_install()
    print("Cleaning old contrib repo")
    rm_cmd = "sudo rm -rf {}".format(ORIG_CURATED_PATH)
    utils.exec_shell_cmd(rm_cmd)
    print("Cloning and checking out Contrib Git Repo")
    utils.run_subprocess(CONTRIB_GIT_CMD)
    utils.run_subprocess(GIT_CHECKOUT_CMD, ORIG_CURATED_PATH)
    os.environ["gramine_commit"] = os.environ.get("gramine_commit", "")
    os.environ["gsc_repo"]       = os.environ.get("gsc_repo", "")
    os.environ["gsc_commit"]     = os.environ.get("gsc_commit", "")
    os.environ["contrib_repo"]   = os.environ.get("contrib_repo", "")
    os.environ["contrib_branch"] = os.environ.get("contrib_branch", "")
    print("\n\n############################################################################")
    print("Printing the environment variables before curation")
    print("Gramine Commit: ", os.environ["gramine_commit"])
    print("GSC Repo:       ", os.environ["gsc_repo"])
    print("GSC Commit:     ", os.environ["gsc_commit"])
    print("Contrib Repo:   ", os.environ["contrib_repo"])
    print("Contrib Commit: ", os.environ["contrib_branch"])
    print("############################################################################\n\n")
    update_curation_verifier_scripts()


def copy_repo():
    copy_cmd = "cp -rf {} {}".format(ORIG_CURATED_PATH, REPO_PATH)
    utils.exec_shell_cmd("sudo rm -rf contrib_repo")
    utils.exec_shell_cmd(copy_cmd)


def update_curation_verifier_scripts():
    # If both 'gramine_commit' or 'gsc_commit' are not passed as parameters, v1.6.1 would be
    # used as default for both commits.
    # If 'gramine_commit' is master/any other commit, 'gsc_commit' must be passed as master.
    if os.environ["gramine_commit"] or os.environ["gramine_repo"]:
        update_gramine_branch(os.environ["gramine_commit"], os.environ["gramine_repo"])
    if os.environ["gsc_repo"] or os.environ["gsc_commit"]:
        update_gsc(os.environ["gsc_commit"], os.environ["gsc_repo"])


def update_gramine_branch(gramine_commit='', gramine_repo=''):
    copy_cmd = "cp -f config.yaml.template config.yaml"
    if gramine_commit:
        gsc_tag = utils.run_subprocess(f"git ls-remote --sort='version:refname' --tags  {GSC_MAIN_REPO} | tail --lines=1 | cut --delimiter=\"/\" --fields=3")
        if not "v1" in gramine_commit:
            utils.run_subprocess(f"cp -rf helper-files/{VERIFIER_TEMPLATE} {VERIFIER_DOCKERFILE}")
        sed_string = "sed -i \"s/Branch.*master.*\\|Branch.*{}.*/Branch: '{}'/\" config.yaml".format(gsc_tag, gramine_commit.replace('/', '\\/'))
        utils.update_file_contents(copy_cmd, (copy_cmd + "\n" + sed_string), CURATION_SCRIPT)
        utils.update_file_contents("git checkout(.*)", f"git checkout {gramine_commit}", VERIFIER_DOCKERFILE)
    if gramine_repo:
        sed_string = "sed -i \"s|Repository.*gramine.git.*|Repository: '{}'|\" config.yaml".format(gramine_repo.replace('/', '\\/'))
        utils.update_file_contents(copy_cmd, (copy_cmd + "\n" + sed_string), CURATION_SCRIPT)
        utils.update_file_contents("git clone(.*)gramine.git", f"git clone {gramine_repo}", VERIFIER_DOCKERFILE)


def update_gsc(gsc_commit='', gsc_repo=''):
    if gsc_repo:
        utils.update_file_contents(GSC_MAIN_REPO, gsc_repo, CURATION_SCRIPT)
    if gsc_commit:
        utils.update_file_contents("git checkout(.*)", f"git checkout {gsc_commit}", CURATION_SCRIPT)


def verify_image_creation(curation_output):
    if re.search("The curated GSC image gsc-(.*) is ready", curation_output) or \
            re.search("docker run", curation_output):
        return True
    return False


def generate_curated_image(test_config_dict):
    curation_output = ''
    workload_image = test_config_dict["docker_image"]
    logged_in_user = os.getlogin()
    cwd = os.getcwd()
    
    # The following ssh command is to mitigate the curses error faced while launching the command through Jenkins.
    curation_cmd = f"ssh -tt {logged_in_user}@localhost 'cd {CURATED_APPS_PATH} && python3 curate.py {workload_image} --test'"

    print("Curation cmd ", curation_cmd)

    result = subprocess.run([curation_cmd], input=b'\x07', shell=True, check=True, stdout=subprocess.PIPE)
    os.chdir(cwd)
      
    curation_output = result.stdout.strip()
    print(curation_output.strip())

    return curation_output


def get_docker_run_command(workload_name):
    output = ''
    wrapper_image = "gsc-{}".format(workload_name)
    gsc_workload = "docker run --rm --net=host --device=/dev/sgx/enclave -t {}".format(wrapper_image)
    output += gsc_workload
    return output


def run_curated_image(test_config_dict, docker_run_cmd):
    process = utils.popen_subprocess(docker_run_cmd)
    return utils.verify_process(test_config_dict, process)

