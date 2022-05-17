#
# Imports
#
import os
import yaml
import subprocess
import shutil
import time
import pytest
from src.config_files import constants
from src.libs import utils

'''
     Function to perform a fresh checkout of gramine repo.
'''
def fresh_gramine_checkout():
    print("\n###### In fresh_gramine_checkout #####\n")
    # Check if gramine folder exists. Delete it if exists, change directory to
    # user's home directory and git clone gramine within user's home dir.
    # Note: No need to create 'gramine' dir explicitly, as git clone will
    # automatically create one.
    # Also, note that we are checking out gramine everytime we execute the
    # performance framework, so that we execute it on the latest source.
    if os.path.exists(constants.GRAMINE_HOME_DIR):
        shutil.rmtree(constants.GRAMINE_HOME_DIR)
    
    os.chdir(constants.HOME_DIR)
    git_clone_cmd = 'git clone ' + constants.GRAMINE_CLONE_URL
    print("\n-- Gramine git clone command..\n", git_clone_cmd)
    os.system(git_clone_cmd)

    # Git clone the examples repo too for workloads download.
    os.chdir(constants.GRAMINE_HOME_DIR)
    git_clone_cmd = 'git clone ' + constants.GRAMINE_EXAMPLES_CLONE_URL
    print("\n-- Gramine examples git clone command..\n", git_clone_cmd)
    os.system(git_clone_cmd)


def install_gramine_dependencies():
    print("\n###### In install_gramine_dependencies #####\n")

    cwd = os.getcwd()
    # Installing dependencies from User's home directory
    os.chdir(constants.HOME_DIR)

    # Determine the distro and the corresponding version.
    # Choose the respective packages.txt based on the distro version.
    distro, distro_version = utils.get_distro_and_version()
    print(f"\n-- Installing gramine dependencies for Distro: {distro}  Version: {distro_version}\n")
    
    if distro == 'ubuntu':
        # Read the system packages yaml file and update the actual system_packages string
        system_packages_path = os.path.join(constants.FRAMEWORK_HOME_DIR, 'src/config_files', constants.SYSTEM_PACKAGES_FILE)
        with open(system_packages_path, "r") as sys_pack_fd:
            try:
                yaml_system_packages = yaml.safe_load(sys_pack_fd)
            except yaml.YAMLError as exc:
                print(exc)
            #system_packages_dict.update(yaml_system_packages['Default'])
            system_packages_str = yaml_system_packages['Default']

        # Read the python packages yaml file and update the actual python_packages string
        python_packages_path = os.path.join(constants.FRAMEWORK_HOME_DIR, 'src/config_files', constants.PYTHON_PACKAGES_FILE)
        with open(python_packages_path, "r") as py_pack_fd:
            try:
                yaml_python_packages = yaml.safe_load(py_pack_fd)
            except yaml.YAMLError as exc:
                print(exc)
            #python_packages_dict.update(yaml_python_packages['Default'])
            python_packages_str = yaml_python_packages['Default']

        if distro_version == '18.04':
            if yaml_system_packages.get(distro_version):
                system_packages_str = system_packages_str + ' ' + yaml_system_packages[distro_version]
            if yaml_python_packages.get(distro_version):
                python_packages_str = python_packages_str + ' ' + yaml_python_packages[distro_version]
        elif distro_version == '20.04':
            if yaml_system_packages.get(distro_version):
                system_packages_str = system_packages_str + ' ' + yaml_system_packages[distro_version]
            # We need not update the python packages string here as we do not have any 20.04 distro
            # specific package dependencies. Refer python_packages.yaml file for more clarity.
        elif distro_version == '21.04' or distro_version == '21.10':
            if yaml_system_packages.get(distro_version):
                system_packages_str = system_packages_str + ' ' + yaml_system_packages[distro_version]
            # We need not update the python packages string here as we do not have any 21.04/21.10 distro
            # specific package dependencies. Refer python_packages.yaml file for more clarity.
        else:
            os.chdir(cwd)
            pytest.exit("\n***** Unknown / Unsupported Distro version.. Exiting test session. *****")
    else:
        os.chdir(cwd)
        pytest.exit("\n***** Unknown / Unsupported Distro.. Exiting test session. *****")

    #system_packages_cmd = 'xargs sudo -H apt-get update && env DEBIAN_FRONTEND=noninteractive apt-get install -y <' + system_packages_file
    # Have separated 'apt-get update' from the below main command to suppress the lock error.
    subprocess.run('sudo apt-get update', shell=True, check=True)
    time.sleep(constants.SUBPROCESS_SLEEP_TIME)
    
    system_packages_cmd = 'sudo env DEBIAN_FRONTEND=noninteractive apt-get install -y ' + system_packages_str
    print("\n-- Executing below mentioned system packages installation cmd..\n", system_packages_cmd)
    subprocess.run(system_packages_cmd, shell=True, check=True)
    time.sleep(constants.SUBPROCESS_SLEEP_TIME)

    # Providing -H option to sudo to suppress the pip home directory warning.
    # -U option is to install the latest package (if upgrade is available).
    python_packages_cmd = 'sudo -H python3 -m pip install -U ' + python_packages_str
    print("\n-- Executing below mentioned Python packages installation cmd..\n", python_packages_cmd)
    subprocess.run(python_packages_cmd, shell=True, check=True)
    time.sleep(constants.SUBPROCESS_SLEEP_TIME)

    os.chdir(cwd)
    

def build_and_install_gramine(test_config_dict):
    print("\n###### In build_and_install_gramine #####\n")
    
    cwd = os.getcwd()

    # Checkout fresh gramine source
    fresh_gramine_checkout()

    # Change dir to above checked out gramine folder and
    # start building the same.
    os.chdir(constants.GRAMINE_HOME_DIR)

    build_type = test_config_dict['build_type']
    build_prefix = test_config_dict['build_prefix']

    # Cleanup existing gramine binaries (if any) before starting a fresh build.
    # Passing prefix path as argument, so that user installed (if any) gramine
    # binaries are also removed.
    utils.cleaup_gramine_binaries(build_prefix)

    # Create prefix dir
    print(f"\n-- Creating build prefix directory '{build_prefix}'..\n")
    # In the below makedirs call, if the target directory already exists an OSError is raised
    # if 'exist_ok' value is False. Otherwise, True value leaves the directory unaltered. 
    os.makedirs(build_prefix, exist_ok=True)

    build_type_prefix_str = "--prefix=" + build_prefix + " --buildtype=" + build_type

    gramine_sgx_sed_cmd = "sed -i \"/uname/ a '/usr/src/linux-headers-@0@/arch/x86/include/uapi'.format(run_command('uname', '-r').stdout().split('-generic')[0].strip()),\" meson.build"

    gramine_build_meson_cmd = "meson setup build/ --werror " + \
                            build_type_prefix_str + \
                            " -Ddirect=enabled -Dsgx=enabled -Dtests=enabled > " + \
                            constants.LOGS_DIR + "/gramine_build_meson_cmd_output.txt"

    gramine_ninja_build_cmd = "ninja -vC build > " + constants.LOGS_DIR + "/gramine_ninja_build_cmd_output.txt"

    gramine_ninja_install_cmd = "ninja -vC build install > " + constants.LOGS_DIR + "/gramine_ninja_install_cmd_output.txt"

    print("\n-- Executing below mentioned gramine-sgx sed cmd..\n", gramine_sgx_sed_cmd)
    subprocess.run(gramine_sgx_sed_cmd, shell=True, check=True)
    
    print("\n-- Executing below mentioned gramine build meson build cmd..\n", gramine_build_meson_cmd)
    subprocess.run(gramine_build_meson_cmd, shell=True, check=True)
    time.sleep(constants.SUBPROCESS_SLEEP_TIME)
    
    print("\n-- Executing below mentioned gramine ninja build cmd..\n", gramine_ninja_build_cmd)
    subprocess.run(gramine_ninja_build_cmd, shell=True, check=True)
    time.sleep(constants.SUBPROCESS_SLEEP_TIME)

    print("\n-- Executing below mentioned gramine ninja build install cmd..\n", gramine_ninja_install_cmd)
    subprocess.run(gramine_ninja_install_cmd, shell=True, check=True)
    time.sleep(constants.SUBPROCESS_SLEEP_TIME)
 
    os.chdir(cwd)

def setup_gramine_environment(test_config_dict):
    # Update the following environment variables as the gramine binaries can be
    # installed at some other place other than '/usr/local'
    # PATH, PYTHONPATH and PKG_CONFIG_PATH
    # Need to update these variables only after building gramine as there would be some
    # dereferences of few path values which are created only after successful build.
    utils.update_env_variables(test_config_dict['build_prefix'])

    gramine_sgx_gen_private_key_cmd = "gramine-sgx-gen-private-key -f"

    print("\n-- Generating gramine-sgx private key..\n", gramine_sgx_gen_private_key_cmd)
    subprocess.run(gramine_sgx_gen_private_key_cmd, shell=True, check=True)
    time.sleep(constants.SUBPROCESS_SLEEP_TIME)


def build_gramine_binaries(test_config_dict):

    print("\n###### In build_gramine #####\n")

    # Install Gramine dependencies
    install_gramine_dependencies()

    # Build and Install Gramine
    build_and_install_gramine(test_config_dict)

    # Setup gramine env variables and generate sgx private key
    setup_gramine_environment(test_config_dict)
    