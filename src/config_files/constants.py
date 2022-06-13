import os

FRAMEWORK_HOME_DIR = os.getcwd()
GRAMINE_HOME_DIR = FRAMEWORK_HOME_DIR + "/gramine"
LOGS_DIR =  FRAMEWORK_HOME_DIR + "/logs"
HTTP_PROXY = "http://proxy-dmz.intel.com:911/"
HTTPS_PROXY = "http://proxy-dmz.intel.com:912/"
SYSTEM_PACKAGES_FILE = "system_packages.yaml"
PYTHON_PACKAGES_FILE = "python_packages.yaml"
PKG_INSTALL_WAIT_TIME = 25
BUILD_TYPE = "release"
BUILD_PREFIX = FRAMEWORK_HOME_DIR + "/gramine_install/usr"

# Commands constants
GRAMINE_CLONE_CMD = "git clone https://github.com/gramineproject/gramine.git"

EXAMPLES_REPO_CLONE_CMD = "git clone https://github.com/gramineproject/examples.git"

MIMALLOC_CLONE_CMD = "git clone -b v1.7.6 https://github.com/microsoft/mimalloc.git"

MIMALLOC_INSTALL_PATH = "/usr/local/lib/libmimalloc.so.1.7"

TCMALLOC_INSTALL_PATH = "/usr/lib/x86_64-linux-gnu/libtcmalloc.so.4"

BUILD_TYPE_PREFIX_STRING = "--prefix=" + BUILD_PREFIX + " --buildtype=" + BUILD_TYPE

GRAMINE_SGX_SED_CMD = "sed -i \"/uname/ a '/usr/src/linux-headers-@0@/arch/x86/include/uapi'.format(run_command('uname', '-r').stdout().split('-generic')[0].strip()),\" meson.build"

GRAMINE_BUILD_MESON_CMD = "meson setup build/ --werror " + \
                        BUILD_TYPE_PREFIX_STRING + \
                        " -Ddirect=enabled -Dsgx=enabled -Dtests=enabled > " + \
                        LOGS_DIR + "/gramine_build_meson_cmd_output.txt"

GRAMINE_NINJA_BUILD_CMD = "ninja -vC build > " + LOGS_DIR + "/gramine_ninja_build_cmd_output.txt"

GRAMINE_NINJA_INSTALL_CMD = "ninja -vC build install > " + LOGS_DIR + "/gramine_ninja_install_cmd_output.txt"

PYTHONPATH_CMD = "gramine/Scripts/get-python-platlib.py " + BUILD_PREFIX

GRAMINE_SGX_GEN_PRIVATE_KEY_CMD = "gramine-sgx-gen-private-key -f"

APT_UPDATE_CMD = "sudo apt-get update"

APT_FIX_BROKEN_CMD = "sudo apt --fix-broken install -y"

SYS_PACKAGES_CMD = "sudo env DEBIAN_FRONTEND=noninteractive apt-get install -y "

# Providing -H option to sudo to suppress the pip home directory warning.
# -U option is to install the latest package (if upgrade is available).
PYTHON_PACKAGES_CMD = "sudo -H python3 -m pip install -U "

LOG_LEVEL = "error"