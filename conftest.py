#
# Imports
#
from xmlrpc.client import boolean
from pkg_resources import yield_lines
import pytest
import os
import sys
import subprocess
import time
import shutil
import platform
import yaml
import lsb_release
from src.config_files import constants
from src.libs import utils

test_config_dict = {}

@pytest.fixture(scope="session")
def read_global_config():
    global test_config_dict

    print("\n###### In read_global_config #####\n")
    #test_config_dict = {}
    config_file_name = "config.yaml"
    config_file_path = os.path.join(constants.FRAMEWORK_HOME_DIR, 'src/config_files', config_file_name)
    with open(config_file_path, "r") as fd:
        try:
            test_config_dict = yaml.safe_load(fd)
        except yaml.YAMLError as exc:
            print(exc)

    if pytest.config.getoption('--build_gramine') != '' and pytest.config.getoption('--build_gramine') != 'None':
        test_config_dict['build_gramine'] = pytest.config.getoption('build_gramine')

    if pytest.config.getoption('--build_type') != '' and pytest.config.getoption('--build_type') != 'None':
        test_config_dict['build_type'] = pytest.config.getoption('build_type')

    if pytest.config.getoption('--build_prefix') != '' and pytest.config.getoption('--build_prefix') != 'None':
        test_config_dict['build_prefix'] = pytest.config.getoption('build_prefix')

    print(test_config_dict['iterations'])
    print(test_config_dict['exec_mode'])
    print(test_config_dict)


def install_gramine_dependencies():
    print("\n###### In install_gramine_dependencies #####\n")

    cwd = os.getcwd()
    # Installing dependencies from User's home directory
    os.chdir(constants.HOME_DIR)

    # Determine the distro and the corresponding version.
    # Choose the respective packages.txt based on the distro version.
    distro = lsb_release.get_lsb_information().get('ID')
    distro_version = lsb_release.get_lsb_information().get('RELEASE')
    print(f"\n-- Installing gramine dependencies for Distro: {distro}  Version: {distro_version}\n")
    
    if distro == 'Ubuntu':
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
    

def build_and_install_gramine():
    print("\n###### In build_and_install_gramine #####\n")
    
    cwd = os.getcwd()

    # Checkout fresh gramine source
    utils.fresh_gramine_checkout()

    # Change dir to above checked out gramine folder and
    # start building the same.
    os.chdir(constants.GRAMINE_HOME_DIR)

    if pytest.config.getoption('--build_type') == '' or pytest.config.getoption('--build_type') == 'None' or \
        pytest.config.getoption('--build_prefix') == '' or pytest.config.getoption('--build_prefix') == 'None':
        print("\n-- Either build type or prefix values are invalid. Returning without building gramine..")
        os.chdir(cwd)
        return
    
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

    gramine_sgx_gen_private_key_cmd = "gramine-sgx-gen-private-key -f"
    
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
 
    # Update the following environment variables as the gramine binaries can be
    # installed at some other place other than '/usr/local'
    # PATH, PYTHONPATH and PKG_CONFIG_PATH
    # Need to update these variables only after building gramine as there would be some
    # dereferences of few path values which are created only after successful build.
    utils.update_env_variables(build_prefix)

    print("\n-- Generating gramine-sgx private key..\n", gramine_sgx_gen_private_key_cmd)
    subprocess.run(gramine_sgx_gen_private_key_cmd, shell=True, check=True)
    time.sleep(constants.SUBPROCESS_SLEEP_TIME)

    os.chdir(cwd)


@pytest.fixture(scope="session")
def build_gramine(read_global_config):
    # Delete old logs if any and create new logs directory.
    if os.path.exists(constants.LOGS_DIR):
        del_logs_cmd = 'rm -rf ' + constants.LOGS_DIR
        os.system(del_logs_cmd)
    
    os.makedirs(constants.LOGS_DIR, exist_ok=True)

    # If "--build_gramine" command line option is set to 'False',
    # return without doing anything.
    if pytest.config.getoption('--build_gramine') == '' or pytest.config.getoption('--build_gramine') == 'None' or \
        test_config_dict['build_gramine'] == 'False':
        return

    # In the above if condition, 'None' check is not required since we are having default value for '--build_gramine'.
    # But, if the default value (in pytest_addoption) is set to 'None' it will result in KeyError. Hence, added 'None' 
    # check as precaution. 
    # On the other hand, if '--build_gramine' was part of yaml file, it would have already been loaded within the dict,
    # and the 'None' check would not be required then.
    
    print("\n###### In build_gramine #####\n")

    cwd = os.getcwd()
    
    # Set http and https proxies
    utils.set_http_proxies()
    
    # Install Gramine dependencies
    install_gramine_dependencies()

    # Build and Install Gramine
    build_and_install_gramine()
    
    os.chdir(cwd)
    

def pytest_addoption(parser):
    print("\n##### In pytest_addoption #####\n")
    parser.addoption("--iterations", action="store", type=int, default=1)
    parser.addoption("--exec_mode", action="store", type=str, default="None")
    parser.addoption("--fp", action="store", type=str, default="None")
    parser.addoption("--build_gramine", action="store", type=str, default="True")
    parser.addoption("--build_type", action="store", type=str, default="release")
    parser.addoption("--build_prefix", action="store", type=str, default=constants.HOME_DIR + "/gramine_install/usr")

