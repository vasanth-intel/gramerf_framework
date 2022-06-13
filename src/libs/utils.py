import sys
import yaml
import shutil
import subprocess
import lsb_release
from src.config_files.constants import *

verify_output = lambda cmd_output, search_str: True if search_str in cmd_output else False


def exec_shell_cmd(cmd, std_pipe=subprocess.PIPE):
    pipe = subprocess.Popen([cmd], stdout=std_pipe, shell=True)
    pipe.wait()
    if pipe.returncode != 0:
        raise Exception(f"\n-- Failed to execute the process cmd: {cmd}")
    else:
        cmd_stdout = pipe.communicate()[0]
        if cmd_stdout is not None:
            cmd_stdout = cmd_stdout.decode("utf-8").strip()

    return cmd_stdout


def read_config_yaml(config_file_path):
    with open(config_file_path, "r") as config_fd:
        try:
            config_dict = yaml.safe_load(config_fd)
        except yaml.YAMLError as exc:
            raise Exception(exc)
    return config_dict


def get_distro_and_version():
    distro = lsb_release.get_distro_information().get('ID').lower()
    distro_version = lsb_release.get_distro_information().get('RELEASE')
    return distro, distro_version


def clear_system_cache():
    """
    Function to clear pagecache, dentries, and inodes. We need to clear system cache to get
    consistent results. This function can be removed after we implement the restart logic.
    :return:
    """
    echo_cmd_path = exec_shell_cmd('which echo')
    clear_cache_cmd = "sudo sh -c \"" + echo_cmd_path + " 3 > /proc/sys/vm/drop_caches\""
    print("\n-- Executing clear cache command..", clear_cache_cmd)
    exec_shell_cmd(clear_cache_cmd)


def cleanup_gramine_binaries(build_prefix):
    """
    Function to clean up gramine binaries from standard system paths
    and user defined installed paths (installed via "--build_prefix" option)
    :param build_prefix:
    :return:
    """
    if os.path.exists(build_prefix): shutil.rmtree(build_prefix)

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


def update_env_variables(build_prefix):
    """
    Function to update the following environment variables to below respective locations,
    as the gramine binaries can be installed at some other place other than '/usr/local'.
    $PATH => <build_prefix>/bin
    $PYTHONPATH => <prefix>/lib/python<version>/site-packages
    $PKG_CONFIG_PATH => <prefix>/<libdir>/pkgconfig
    :param build_prefix:
    :return:
    """

    # Update environment 'PATH' variable to the path (<prefix>/bin) where gramine
    # binaries would be installed.
    os.environ["PATH"] = build_prefix + "/bin" + os.pathsep + os.environ["PATH"]
    print(f"\n-- Updated environment PATH variable to the following..\n", os.environ["PATH"])

    # Update environment 'PKG_CONFIG_PATH' variable to <prefix>/<libdir>/pkgconfig.
    libdir_path_cmd = "meson introspect " + GRAMINE_HOME_DIR + \
                      "/build/ --buildoptions | jq -r '(map(select(.name == \"libdir\"))) | map(.value) | join(\"/\")'"
    libdir_path = exec_shell_cmd(libdir_path_cmd)

    os.environ["PKG_CONFIG_PATH"] = build_prefix + "/" + libdir_path + "/pkgconfig" + os.pathsep + os.environ.get(
        'PKG_CONFIG_PATH', '')
    print(f"\n-- Updated environment PKG_CONFIG_PATH variable to the following..\n", os.environ["PKG_CONFIG_PATH"])

    # Update environment 'PYTHONPATH' variable to <prefix>/lib/python<version>/site-packages.
    if not os.path.exists("gramine/Scripts/get-python-platlib.py"):
        print(f"\n-- Failure to update 'PYTHONPATH' env variable. get-python-platlib.py does not exist..\n")
        return

    print(f"\n-- PYTHONPATH command\n", PYTHONPATH_CMD)
    os.environ["PYTHONPATH"] = exec_shell_cmd(PYTHONPATH_CMD)
    print(f"\n-- Updated environment PYTHONPATH variable to the following..\n", os.environ["PYTHONPATH"])


def set_http_proxies():
    """
    Function to set environment http and https proxies.
    :return:
    """
    os.environ['http_proxy'] = HTTP_PROXY
    os.environ['HTTP_PROXY'] = HTTP_PROXY
    os.environ['https_proxy'] = HTTPS_PROXY
    os.environ['HTTPS_PROXY'] = HTTPS_PROXY
    print("\n-- Setting http_proxy : \n", os.environ['http_proxy'])
    print("\n-- Setting https_proxy : \n", os.environ['https_proxy'])


def set_cpu_freq_scaling_governor():
    """
    Function to set the CPU frequency scaling governor to 'performance' mode.
    :return:
    """
    print("\n-- Setting CPU frequency scaling governor to 'performance' mode..")
    cpu_freq_file = os.path.join(FRAMEWORK_HOME_DIR, 'src/config_files', 'set_cpu_freq_scaling_governor.sh')

    chmod_cmd = 'chmod +x ' + cpu_freq_file
    set_cpu_freq_cmd = 'sudo ' + cpu_freq_file

    exec_shell_cmd(chmod_cmd)

    exec_shell_cmd(set_cpu_freq_cmd)


def set_threads_cnt_env_var():
    """
    Function to determine and set 'THREADS_CNT' env var.
    :return:
    """
    lscpu_output = exec_shell_cmd('lscpu')
    lines = lscpu_output.splitlines()
    core_per_socket, threads_per_core = 0, 0
    for line in lines:
        if 'Core(s) per socket:' in line:
            core_per_socket = int(line.split(':')[-1].strip())
        if 'Thread(s) per core:' in line:
            threads_per_core = int(line.split(':')[-1].strip())
        if core_per_socket and threads_per_core:
            break
    os.environ['THREADS_CNT'] = str(core_per_socket * threads_per_core)

    print("\n-- Setting the THREADS_CNT env variable to ", os.environ['THREADS_CNT'])
