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
    
    print("\n-- Cloning Gramine git repo..\n", constants.GRAMINE_CLONE_CMD)
    if utils.exec_shell_cmd(constants.GRAMINE_CLONE_CMD).returncode != 0:
        print("\n-- Failure: Gramine git clone command returned non-zero error code..\n")
    
    # Git clone the examples repo too for workloads download.
    os.chdir(constants.GRAMINE_HOME_DIR)

    print("\n-- Cloning Gramine examples git repo..\n", constants.EXAMPLES_REPO_CLONE_CMD)
    if utils.exec_shell_cmd(constants.EXAMPLES_REPO_CLONE_CMD).returncode != 0:
        print("\n-- Failure: Gramine examples git clone command returned non-zero error code..\n")

    os.chdir(constants.FRAMEWORK_HOME_DIR)


def install_gramine_dependencies():
    print("\n###### In install_gramine_dependencies #####\n")

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

        if yaml_system_packages.get(distro_version) != None:
            system_packages_str = system_packages_str + ' ' + yaml_system_packages[distro_version]
        if yaml_python_packages.get(distro_version) != None:
            python_packages_str = python_packages_str + ' ' + yaml_python_packages[distro_version]

    else:
        pytest.exit("\n***** Unknown / Unsupported Distro.. Exiting test session. *****")

    print("\n-- Executing below mentioned system update cmd..\n", constants.APT_UPDATE_CMD)
    if utils.exec_shell_cmd(constants.APT_UPDATE_CMD).returncode != 0:
        print("\n-- Failure: apt-get update command returned non-zero error code..\n")
    
    system_packages_cmd = constants.SYS_PACKAGES_CMD + system_packages_str
    print("\n-- Executing below mentioned system packages installation cmd..\n", system_packages_cmd)
    if utils.exec_shell_cmd(system_packages_cmd).returncode != 0:
        print("\n-- Failure: Cannot update system packages..\n")

    python_packages_cmd = constants.PYTHON_PACKAGES_CMD + python_packages_str
    print("\n-- Executing below mentioned Python packages installation cmd..\n", python_packages_cmd)
    if utils.exec_shell_cmd(python_packages_cmd).returncode != 0:
        print("\n-- Failure: Cannot update python packages..\n")
    

def build_and_install_gramine():
    print("\n###### In build_and_install_gramine #####\n")
    
    # Checkout fresh gramine source
    fresh_gramine_checkout()
    
    # Change dir to above checked out gramine folder and
    # start building the same.
    os.chdir(constants.GRAMINE_HOME_DIR)

    # Cleanup existing gramine binaries (if any) before starting a fresh build.
    # Passing prefix path as argument, so that user installed (if any) gramine
    # binaries are also removed.
    utils.cleaup_gramine_binaries(constants.BUILD_PREFIX)

    # Create prefix dir
    print(f"\n-- Creating build prefix directory '{constants.BUILD_PREFIX}'..\n")
    # In the below makedirs call, if the target directory already exists an OSError is raised
    # if 'exist_ok' value is False. Otherwise, True value leaves the directory unaltered. 
    os.makedirs(constants.BUILD_PREFIX, exist_ok=True)

    print("\n-- Executing below mentioned gramine-sgx sed cmd..\n", constants.GRAMINE_SGX_SED_CMD)
    if utils.exec_shell_cmd(constants.GRAMINE_SGX_SED_CMD).returncode != 0:
        pytest.exit("\n-- Failure: SED command returned non-zero error code..\n")
        
    print("\n-- Executing below mentioned gramine build meson build cmd..\n", constants.GRAMINE_BUILD_MESON_CMD)
    if utils.exec_shell_cmd(constants.GRAMINE_BUILD_MESON_CMD).returncode != 0:
        pytest.exit("\n-- Failure: Gramine build meson command returned non-zero error code..\n")
    
    print("\n-- Executing below mentioned gramine ninja build cmd..\n", constants.GRAMINE_NINJA_BUILD_CMD)
    if utils.exec_shell_cmd(constants.GRAMINE_NINJA_BUILD_CMD).returncode != 0:
        pytest.exit("\n-- Failure: Gramine ninja build command returned non-zero error code..\n")

    print("\n-- Executing below mentioned gramine ninja build install cmd..\n", constants.GRAMINE_NINJA_INSTALL_CMD)
    if utils.exec_shell_cmd(constants.GRAMINE_NINJA_INSTALL_CMD).returncode != 0:
        pytest.exit("\n-- Failure: Gramine ninja install command returned non-zero error code..\n")
     
    os.chdir(constants.FRAMEWORK_HOME_DIR)

def setup_gramine_environment():
    # Update the following environment variables as the gramine binaries can be
    # installed at some other place other than '/usr/local'
    # PATH, PYTHONPATH and PKG_CONFIG_PATH
    # Need to update these variables only after building gramine as there would be some
    # dereferences of few path values which are created only after successful build.
    utils.update_env_variables(constants.BUILD_PREFIX)

    print("\n-- Generating gramine-sgx private key..\n", constants.GRAMINE_SGX_GEN_PRIVATE_KEY_CMD)
    if utils.exec_shell_cmd(constants.GRAMINE_SGX_GEN_PRIVATE_KEY_CMD).returncode != 0:
        pytest.exit("\n-- Failure: Gramine sgx generate private key command returned non-zero error code..\n")


def build_gramine_binaries():

    print("\n###### In build_gramine #####\n")

    # Install Gramine dependencies
    install_gramine_dependencies()

    # Build and Install Gramine
    build_and_install_gramine()

    # Setup gramine env variables and generate sgx private key
    setup_gramine_environment()
    