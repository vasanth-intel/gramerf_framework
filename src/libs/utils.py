import sys
import os
import shutil
import subprocess
import time
import conftest
from src.config_files import constants

def str_to_bool(s):
    if s == 'True':
         return True
    elif s == 'False':
         return False

'''
     Function to perform a fresh checkout of gramine repo.
'''
def fresh_gramine_checkout():
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

'''
     Function to clean up gramine binaries from standard system paths 
     and user defined installed paths (installed via "--build_prefix" option)
'''
def cleaup_gramine_binaries(build_prefix):
     if os.path.exists(build_prefix):
          shutil.rmtree(build_prefix)

     gramine_uninstall_cmd = "sudo apt remove gramine"
     python_version_str = "python" + str(sys.version_info.major) + "." + str(sys.version_info.minor)
     # The substring "x86_64-linux-gnu" within below path is for Ubuntu. It would be different
     # for other distros like CentOS or RHEL. Currently, hardcoding it for Ubuntu but needs to
     # be updated for other distros in future.
     gramine_user_installed_bin_rm_cmd = "sudo rm -rf /usr/local/bin/gramine* /usr/local/lib/" + \
                                        python_version_str + \
                                        "/dist-packages/graminelibos /usr/local/lib/x86_64-linux-gnu/*gramine*"

     print("\n-- Uninstalling gramine..\n", gramine_uninstall_cmd)
     os.system(gramine_uninstall_cmd)
     
     print("\n-- Removing user installed gramine binaries..\n", gramine_user_installed_bin_rm_cmd)
     os.system(gramine_user_installed_bin_rm_cmd)
     
'''
    Function to update the following environment variables to below respective locations,
    as the gramine binaries can be installed at some other place other than '/usr/local'.
    $PATH => <prefix>/bin
    $PYTHONPATH => <prefix>/lib/python<version>/site-packages
    $PKG_CONFIG_PATH => <prefix>/<libdir>/pkgconfig
'''
def update_env_variables(build_prefix):
     # Update environment 'PATH' variable to the path (<prefix>/bin) where gramine
     # binaries would be installed.
     os.environ["PATH"] = build_prefix + "/bin" + os.pathsep + os.environ["PATH"]
     print(f"\n-- Updated environment PATH variable to the following..\n", os.environ["PATH"])

     # Update environment 'PYTHONPATH' variable to <prefix>/lib/python<version>/site-packages.
     python_version_str = "python" + str(sys.version_info.major) + "." + str(sys.version_info.minor)
     os.environ["PYTHONPATH"] = build_prefix + "/lib/" + python_version_str + "/site-packages" + os.pathsep + os.environ.get('PYTHONPATH', '')
     print(f"\n-- Updated environment PYTHONPATH variable to the following..\n", os.environ["PYTHONPATH"])

     # Update environment 'PKG_CONFIG_PATH' variable to <prefix>/<libdir>/pkgconfig.
     libdir_path_cmd = "meson introspect " + constants.GRAMINE_HOME_DIR + \
                    "/build/ --buildoptions | jq -r '(map(select(.name == \"libdir\"))) | map(.value) | join(\"/\")'"
     libdir_path = subprocess.getoutput(libdir_path_cmd)

     os.environ["PKG_CONFIG_PATH"] = build_prefix + "/" + libdir_path + "/pkgconfig" + os.pathsep + os.environ.get('PKG_CONFIG_PATH', '')
     print(f"\n-- Updated environment PKG_CONFIG_PATH variable to the following..\n", os.environ["PKG_CONFIG_PATH"])


def set_http_proxies():
    os.environ['http_proxy'] = conftest.test_config_dict['http_proxy']
    os.environ['HTTP_PROXY'] = conftest.test_config_dict['http_proxy']
    os.environ['https_proxy'] = conftest.test_config_dict['https_proxy']
    os.environ['HTTPS_PROXY'] = conftest.test_config_dict['https_proxy']
    print("\n-- Setting http_proxy : \n", os.environ['http_proxy'])
    print("\n-- Setting https_proxy : \n", os.environ['https_proxy'])

