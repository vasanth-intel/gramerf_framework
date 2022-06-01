import sys
import os
import shutil
import subprocess
import lsb_release
from src.config_files import constants

def exec_shell_cmd(cmd):
     cmd_stdout = subprocess.run([cmd], shell=True, stdout=subprocess.PIPE, check=True, text=True)
     return cmd_stdout
     
def str_to_bool(s):
    if s == 'True':
         return True
    elif s == 'False':
         return False


def get_distro_and_version():
     distro = lsb_release.get_lsb_information().get('ID').lower()
     distro_version = lsb_release.get_lsb_information().get('RELEASE')
     return distro, distro_version


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
    $PATH => <build_prefix>/bin
    $PYTHONPATH => <prefix>/lib/python<version>/site-packages
    $PKG_CONFIG_PATH => <prefix>/<libdir>/pkgconfig
'''
def update_env_variables(build_prefix):
     # Update environment 'PATH' variable to the path (<prefix>/bin) where gramine
     # binaries would be installed.
     os.environ["PATH"] = build_prefix + "/bin" + os.pathsep + os.environ["PATH"]
     print(f"\n-- Updated environment PATH variable to the following..\n", os.environ["PATH"])

     # Update environment 'PKG_CONFIG_PATH' variable to <prefix>/<libdir>/pkgconfig.
     libdir_path_cmd = "meson introspect " + constants.GRAMINE_HOME_DIR + \
                    "/build/ --buildoptions | jq -r '(map(select(.name == \"libdir\"))) | map(.value) | join(\"/\")'"
     libdir_path = subprocess.getoutput(libdir_path_cmd)

     os.environ["PKG_CONFIG_PATH"] = build_prefix + "/" + libdir_path + "/pkgconfig" + os.pathsep + os.environ.get('PKG_CONFIG_PATH', '')
     print(f"\n-- Updated environment PKG_CONFIG_PATH variable to the following..\n", os.environ["PKG_CONFIG_PATH"])

     # Update environment 'PYTHONPATH' variable to <prefix>/lib/python<version>/site-packages.
     if not os.path.exists("gramine/Scripts/get-python-platlib.py"):
          print(f"\n-- Failure to update 'PYTHONPATH' env variable. get-python-platlib.py does not exist..\n")
          return

     print(f"\n-- PYTHONPATH command\n", constants.PYTHONPATH_CMD)
     pythonpath_cmd_output =  exec_shell_cmd(constants.PYTHONPATH_CMD)
     if pythonpath_cmd_output.returncode != 0:
          print(f"\n-- Failure: Setting 'PYTHONPATH' env variable command returned non-zero error code..\n")
          return

     os.environ["PYTHONPATH"] = pythonpath_cmd_output.stdout
     print(f"\n-- Updated environment PYTHONPATH variable to the following..\n", os.environ["PYTHONPATH"])


'''
Function to set environment http and https proxies.
'''
def set_http_proxies():
    os.environ['http_proxy'] = constants.HTTP_PROXY
    os.environ['HTTP_PROXY'] = constants.HTTP_PROXY
    os.environ['https_proxy'] = constants.HTTPS_PROXY
    os.environ['HTTPS_PROXY'] = constants.HTTPS_PROXY
    print("\n-- Setting http_proxy : \n", os.environ['http_proxy'])
    print("\n-- Setting https_proxy : \n", os.environ['https_proxy'])


'''
Function to set the CPU frequency scaling governor to 'performance' mode.
'''
def set_cpu_freq_scaling_governor():
     print ("\n-- Setting CPU frequency scaling governor to 'performance' mode..")
     cpu_freq_file = os.path.join(constants.FRAMEWORK_HOME_DIR, 'src/config_files', 'set_cpu_freq_scaling_governor.sh')
     
     chmod_cmd = 'chmod +x ' + cpu_freq_file
     set_cpu_freq_cmd = 'sudo ' + cpu_freq_file
     
     if exec_shell_cmd(chmod_cmd).returncode != 0:
          print ("\n-- Failure: Changing permissions of scaling governor script failed..")
          return False
     
     if exec_shell_cmd(set_cpu_freq_cmd).returncode != 0:
          print ("\n-- Failure: Setting CPU frequency scaling governor to 'performance' mode failed..")
          return False
     
     return True

'''
Function to determine and set 'THREADS_CNT' env var.
'''
def set_threads_cnt_env_var():
     lscpu_output = subprocess.getoutput('lscpu')
     lines = lscpu_output.splitlines()
     core_per_socket, threads_per_core = 0, 0
     for line in lines:
          if ('Core(s) per socket:' in line):
               core_per_socket = int(line.split(':')[-1].strip())
          if ('Thread(s) per core:' in line):
               threads_per_core =  int(line.split(':')[-1].strip())
          if (core_per_socket and threads_per_core):
               break
     os.environ['THREADS_CNT'] = str(core_per_socket * threads_per_core)
     
     print("\n-- Setting the THREADS_CNT env variable to ", os.environ['THREADS_CNT'])