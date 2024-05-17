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
    utils.exec_shell_cmd(CONTRIB_GIT_CMD)
    update_curation_verifier_scripts()
    if os.environ["gramine_commit"]:
        # This is to update the 'gramine_commit' env var with
        # the commit id to support perf dashboard implementation.
        if os.environ["gramine_commit"] == "master":
            git_commit_cmd = "git ls-remote https://github.com/gramineproject/gramine master"
            master_commit = utils.exec_shell_cmd(git_commit_cmd)
            os.environ["gramine_commit"] = master_commit.split()[0][:7]
        if os.environ["gsc_commit"] == "master":
            gsc_commit_cmd = "git ls-remote https://github.com/gramineproject/gsc.git master"
            gsc_commit = utils.exec_shell_cmd(gsc_commit_cmd)
            os.environ['gsc_commit'] = gsc_commit.split()[0][:7]
    print("\n -- Gramine Commit: ", os.environ.get("gramine_commit", ""))
    print("\n -- GSC Commit: ", os.environ.get("gsc_commit", ""))


def copy_repo():
    copy_cmd = "cp -rf {} {}".format(ORIG_CURATED_PATH, REPO_PATH)
    utils.exec_shell_cmd("sudo rm -rf contrib_repo")
    utils.exec_shell_cmd(copy_cmd)


def update_curation_verifier_scripts():
    # If both 'gramine_commit' or 'gsc_commit' are not passed as parameters, v1.6.1 would be
    # used as default for both commits.
    # If 'gramine_commit' is master/any other commit, 'gsc_commit' must be passed as master.
    if os.environ["gramine_repo"] or os.environ["gramine_commit"]:
        update_gramine_branch(os.environ["gramine_repo"], os.environ["gramine_commit"])
    if os.environ["gsc_repo"] or os.environ["gsc_commit"]:
        update_gsc(os.environ["gsc_repo"], os.environ["gsc_commit"])


def update_gramine_branch(gramine_repo='', gramine_commit=''):
    if gramine_repo == '': gramine_repo = GRAMINE_DEFAULT_REPO
    if gramine_commit == '': gramine_commit = 'v1.6.1'
    commit_str = f" && cd gramine && git checkout {gramine_commit} && cd .."
    copy_cmd = "cp -f config.yaml.template config.yaml"
    gramine_string = GRAMINE_DEPTH_STR + GRAMINE_DEFAULT_REPO
    helper_file = os.path.join(ORIG_BASE_PATH, "verifier", "helper.sh")
    if not "v1" in gramine_commit:
        utils.exec_shell_cmd(f"cp -rf helper-files/{VERIFIER_TEMPLATE} {VERIFIER_DOCKERFILE}")
    utils.update_file_contents(copy_cmd,
                               copy_cmd + "\nsed -i 's|Branch:.*master|Branch: \"{}|' config.yaml".format(gramine_commit), CURATION_SCRIPT)
    utils.update_file_contents(copy_cmd,
                               copy_cmd + "\nsed -i 's|{}|{}|' config.yaml".format(GRAMINE_DEFAULT_REPO, gramine_repo), CURATION_SCRIPT)
    utils.update_file_contents(gramine_string, gramine_repo + commit_str,
                                   VERIFIER_DOCKERFILE)
    utils.update_file_contents(gramine_string, gramine_repo + commit_str, helper_file)


def update_gsc(gsc_repo='', gsc_commit=''):
    if gsc_commit: checkout_str = f" && cd gsc && git checkout {gsc_commit} && cd .."
    if gsc_repo: repo_str = f"git clone {gsc_repo}"
    if gsc_repo and gsc_commit:
        utils.update_file_contents(GSC_CLONE, repo_str + checkout_str, CURATION_SCRIPT)
    elif gsc_repo and not gsc_commit:
        utils.update_file_contents(GSC_CLONE, repo_str, CURATION_SCRIPT)
    elif gsc_commit:
        utils.update_file_contents(GSC_CLONE, GSC_CLONE.replace(GSC_DEPTH_STR, "") + checkout_str, CURATION_SCRIPT)


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

