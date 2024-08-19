import sys
import yaml
import time
import shutil
import socket
import psutil
import subprocess
import lsb_release
import csv
from datetime import datetime as dt
import collections
import pkg_resources
import pandas as pd
import socket
import netifaces as ni
import re
from common.config_files.constants import *


def verify_output(cmd_output, search_str): return re.search(search_str, cmd_output, re.IGNORECASE)


# calculate the percent degradation
def percent_degradation(tcd, baseline, testapp, throughput = False):
    if float(baseline) == 0:
        return 0
    if 'throughput' in tcd['test_name'] or throughput:
        return '{:0.3f}'.format(100 * (float(baseline) - float(testapp)) / float(baseline))
    else:
        return '{:0.3f}'.format(100 * (float(testapp) - float(baseline)) / float(baseline))


def run_to_run_variation(tpt_lat_list):
    max_val = max(tpt_lat_list)
    min_val = min(tpt_lat_list)
    if min_val == 0:
        return 0
    return round(((max_val/min_val) - 1) * 100)


def exec_shell_cmd(cmd, stdout_val=subprocess.PIPE):
    try:
        cmd_stdout = subprocess.run([cmd], shell=True, check=True, stdout=stdout_val, stderr=subprocess.STDOUT, universal_newlines=True)

        if stdout_val is not None and cmd_stdout.stdout is not None:
            return cmd_stdout.stdout.strip()

        return cmd_stdout

    except subprocess.CalledProcessError as e:
        print(e.output)


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
    exec_shell_cmd(clear_cache_cmd, None)


def clean_up_system():
    """
    Function to cleanup to remove unwanted packages and their dependencies, pagecache,
    dentries, inodes and apt cache.
    :return:
    """
    # Cleanup existing gramine binaries (if any) before starting a fresh build.
    # Passing prefix path as argument, so that user installed (if any) gramine
    # binaries are also removed.
    check_and_cleanup_gramine()

    try:
        print("\n-- Removing unnecessary packages and dependencies..")
        exec_shell_cmd("sudo apt-get -y autoremove", None)
    except:
        print("\n-- Executing apt --fix-broken cmd..\n", APT_FIX_BROKEN_CMD)
        exec_shell_cmd(APT_FIX_BROKEN_CMD, None)
    print("\n-- Clearing thumbnail cache..")
    exec_shell_cmd("sudo rm -rf ~/.cache/thumbnails/*", None)
    print("\n-- Clearing apt cache..")
    exec_shell_cmd("sudo apt-get -y clean", None)
    if os.path.exists("/var/run/docker.sock"):
        print("\n-- Removing all docker images..")
        exec_shell_cmd("docker system prune -f", None)
        if os.environ["perf_config"] == "baremetal":
            print("\n-- Stopping docker service..")
            exec_shell_cmd("sudo systemctl stop docker", None)
        else:
            print("\n-- Restarting docker service..")
            exec_shell_cmd("sudo systemctl daemon-reload", None)
            exec_shell_cmd("sudo systemctl restart docker", None)

    clear_system_cache()

    print("\n-- Clearing swap memory..")
    exec_shell_cmd("sudo sh -c 'swapoff -a && swapon -a'", None)


def set_permissions():
    """
    Funciton to set appropriate permissions before tirggering the perf runs.
    :return:
    """
    print("\n-- Setting required device persmissions :")
    if os.path.exists("/dev/sgx_enclave") and os.path.exists("/dev/sgx_provision"):
        exec_shell_cmd("sudo chmod 777 /dev/sgx_enclave /dev/sgx_provision")
    else:
        print("\n-- Warning - Unable to find SGX dev files. May not be able to execute workload with SGX..")
    
    logged_in_user = os.getlogin()
    if os.path.exists("/dev/cpu_dma_latency"):
        exec_shell_cmd(f"sudo chown {logged_in_user} /dev/cpu_dma_latency")
        exec_shell_cmd("sudo chmod 0666 /dev/cpu_dma_latency")

    if os.path.exists("/var/run/docker.sock"):
        exec_shell_cmd(f"sudo chown {logged_in_user} /var/run/docker.sock", None)
        exec_shell_cmd("sudo chmod 666 /var/run/docker.sock")
    
    exec_shell_cmd("sudo mount -o remount,exec /dev")


def cleanup_local_gramine(prefix, os_flavour):
    libdir = subprocess.run("cc -dumpmachine", shell=True, stdout=subprocess.PIPE,
                            encoding="utf-8").stdout.strip()
    arch_libdir = f"/lib/{libdir}"
    if os_flavour == "fedora":
        arch_libdir = "/lib64"
    python_proc = subprocess.run(f"python3 get-python-platlib.py {prefix}", shell=True, stdout=subprocess.PIPE,
                                 encoding="utf-8")
    python_path = python_proc.stdout.strip()
    subprocess.run(f"sudo rm -rf {prefix}/bin/gramine*", shell=True)
    subprocess.run(f"sudo rm -rf {prefix}/bin/is-sgx-available", shell=True)
    subprocess.run(f"sudo rm -rf {python_path}/*graminelibos*", shell=True)
    subprocess.run(f"sudo rm -rf {prefix}/{arch_libdir}/*gramine*", shell=True)
    subprocess.run(f"sudo rm -rf {prefix}/{arch_libdir}/libsgx_util.a", shell=True)
    subprocess.run(f"sudo rm -rf {prefix}/{arch_libdir}/libra_tls_attest.so", shell=True)
    subprocess.run(f"sudo rm -rf {prefix}/{arch_libdir}/libra_tls_verify.a", shell=True)
    subprocess.run(f"sudo rm -rf {prefix}/{arch_libdir}/libra_tls_verify_epid.so", shell=True)
    subprocess.run(f"sudo rm -rf {prefix}/{arch_libdir}/libsecret_prov_attest.so", shell=True)
    subprocess.run(f"sudo rm -rf {prefix}/{arch_libdir}/libsecret_prov_verify.a", shell=True)
    subprocess.run(f"sudo rm -rf {prefix}/{arch_libdir}/libsecret_prov_verify_epid.so", shell=True)
    subprocess.run(f"sudo rm -rf {prefix}/{arch_libdir}/libra_tls_verify_dcap*", shell=True)
    subprocess.run(f"sudo rm -rf {prefix}/{arch_libdir}/libsecret_prov_verify_dcap.so", shell=True)
    subprocess.run(f"sudo rm -rf {prefix}/{arch_libdir}/pkgconfig/*gramine*", shell=True)
    subprocess.run(f"sudo rm -rf {prefix}/share/doc/gramine*", shell=True)
    subprocess.run(f"sudo rm -rf {prefix}/include/gramine", shell=True)
    print(f"Cleaned Gramine Installation at {prefix}")


def clean_gramine(gramine_path, os_flavour):
    if gramine_path == "/usr":
        pkg_mgr = "apt-get"
        if os_flavour == "fedora":
            pkg_mgr = "yum"
        print("Removing Gramine Installation Using Package Manager")
        subprocess.run(f"sudo {pkg_mgr} autoremove gramine -y > /dev/null", shell=True)
        subprocess.run(f"sudo {pkg_mgr} autoremove gramine-dcap -y > /dev/null", shell=True)

    cleanup_local_gramine(gramine_path, os_flavour)


def get_os_details():
    proc = subprocess.run("grep '^NAME' /etc/os-release", shell=True, stdout=subprocess.PIPE,
                            encoding="utf-8")
    os_details = proc.stdout.strip()
    os_flavour = "ubuntu"
    if ("Ubuntu" not in os_details) and ("Debian" not in os_details):
        os_flavour = "fedora"
    return os_flavour


def check_and_cleanup_gramine():
    """
    Function to clean up gramine binaries from standard system paths
    and user defined installed paths (installed via "--build_prefix" option)
    :return:
    """
    os_flavour = get_os_details()
    subprocess.run("wget https://github.com/gramineproject/gramine/raw/master/scripts/get-python-platlib.py",
                   shell=True)
    prefix_path = ["/usr", "/usr/local"]
    for paths in prefix_path:
        clean_gramine(paths, os_flavour)
    while True:
        proc_1 = subprocess.run("which gramine-sgx", shell=True, stdout=subprocess.PIPE,
                                encoding="utf-8")
        output = proc_1.stdout.strip()
        if output in ["", None]:
            break
        print("Gramine Installation Found at : ", output)
        gramine_path = output.split("/bin/gramine-sgx")[0]
        cleanup_local_gramine(gramine_path, os_flavour)
    subprocess.run("sudo rm -rf get-python-platlib.py", shell=True)


def gramine_package_install():
    if os.path.exists("/usr/bin/gramine-sgx"):
        print("\n-- Gramine already installed.. Returning without installation..\n")
        return

    print("\n--Installing latest Gramine package\n")
    distro, distro_version = get_distro_and_version()
    if distro == 'rhel':
        exec_shell_cmd("sudo curl -fsSLo /etc/yum.repos.d/gramine.repo https://packages.gramineproject.io/rpm/gramine.repo")
        exec_shell_cmd("sudo dnf -y install gramine")
        return

    linux_release = exec_shell_cmd("lsb_release -sc")
    exec_shell_cmd("sudo curl -fsSLo /usr/share/keyrings/gramine-keyring.gpg https://packages.gramineproject.io/gramine-keyring.gpg")
    exec_shell_cmd(f"echo 'deb [arch=amd64 signed-by=/usr/share/keyrings/gramine-keyring.gpg] https://packages.gramineproject.io/ {linux_release} main' | sudo tee /etc/apt/sources.list.d/gramine.list")

    exec_shell_cmd("sudo curl -fsSLo /usr/share/keyrings/intel-sgx-deb.asc https://download.01.org/intel-sgx/sgx_repo/ubuntu/intel-sgx-deb.key")
    exec_shell_cmd(f"echo 'deb [arch=amd64 signed-by=/usr/share/keyrings/intel-sgx-deb.asc] https://download.01.org/intel-sgx/sgx_repo/ubuntu {linux_release} main' | sudo tee /etc/apt/sources.list.d/intel-sgx.list")

    exec_shell_cmd(APT_UPDATE_CMD)
    exec_shell_cmd("sudo apt-get -y install gramine")


def update_env_variables():
    """
    Function to update the following environment variables to below respective locations,
    as the gramine binaries can be installed at some other place other than '/usr/local'.
    $PATH => <build_prefix>/bin
    $PYTHONPATH => <prefix>/lib/python<version>/site-packages
    $PKG_CONFIG_PATH => <prefix>/<libdir>/pkgconfig
    :param build_prefix:
    :return:
    """
    if os.environ["build_gramine"] != "package" and USE_PREFIX:
        # Update environment 'PATH' variable to the path (<prefix>/bin) where gramine
        # binaries would be installed.
        os.environ["PATH"] = BUILD_PREFIX + "/bin" + os.pathsep + os.environ["PATH"]
        print(f"\n-- Updated environment PATH variable to the following..\n", os.environ["PATH"])

        # Update environment 'PKG_CONFIG_PATH' variable to <prefix>/<libdir>/pkgconfig.
        libdir_path_cmd = "meson introspect " + GRAMINE_HOME_DIR + "/build/ --buildoptions | jq -r '(map(select(.name == \"libdir\"))) | map(.value) | join(\"/\")'"
        libdir_path = exec_shell_cmd(libdir_path_cmd)

        os.environ["PKG_CONFIG_PATH"] = BUILD_PREFIX + "/" + libdir_path + "/pkgconfig" + os.pathsep + os.environ.get(
            'PKG_CONFIG_PATH', '')
        print(f"\n-- Updated environment PKG_CONFIG_PATH variable to the following..\n", os.environ["PKG_CONFIG_PATH"])

        print(f"\n-- PYTHONPATH command\n", PYTHONPATH_CMD)
        os.environ["PYTHONPATH"] = subprocess.check_output(PYTHONPATH_CMD, encoding='utf-8', shell=True)
        print(f"\n-- Updated environment PYTHONPATH variable to the following..\n", os.environ["PYTHONPATH"])

    print(f"\n-- Updating 'SSHPASS' env-var\n")
    os.environ['SSHPASS'] = "intel@123"

    print(f"\n-- Updating 'ARCH_LIBDIR' env-var\n")
    cmd_out = exec_shell_cmd('cc -dumpmachine')
    os.environ['ARCH_LIBDIR'] = "/lib/" + cmd_out

    print(f"\n-- Updating 'LC_ALL' env-var\n")
    os.environ['LC_ALL'] = "C.UTF-8"

    print(f"\n-- Updating 'LANG' env-var\n")
    os.environ['LANG'] = "C.UTF-8"
	
    os.environ['ENV_USER_UID'] = exec_shell_cmd('id -u')
    os.environ['ENV_USER_GID'] = exec_shell_cmd('id -g')


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


def set_no_proxy():
    os.environ['no_proxy'] = NO_PROXY
    os.environ['NO_PROXY'] = NO_PROXY
    print("\n-- Setting no_proxy : \n", os.environ['no_proxy'])


def set_cpu_freq_scaling_governor():
    """
    Function to set the CPU frequency scaling governor to 'performance' mode.
    :return:
    """
    print("\n-- Setting CPU frequency scaling governor to 'performance' mode..")
    cpu_freq_file = os.path.join(FRAMEWORK_HOME_DIR, 'common/config_files', 'set_cpu_freq_scaling_governor.sh')

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
    cores_count, core_per_socket, threads_per_core, sockets = 0, 0, 0, 0
    for line in lines:
        if 'CPU(s):' in line:
            cores_count = int(line.split(':')[-1].strip())
        if 'Core(s) per socket:' in line:
            core_per_socket = int(line.split(':')[-1].strip())
        if 'Thread(s) per core:' in line:
            threads_per_core = int(line.split(':')[-1].strip())
        if 'Socket(s):' in line:
            sockets = int(line.split(':')[-1].strip())
        if cores_count and core_per_socket and threads_per_core and sockets:
            break
    
    os.environ['CORES_COUNT'] = str(cores_count)
    os.environ['THREADS_CNT'] = str(core_per_socket * threads_per_core)
    os.environ['CORES_PER_SOCKET'] = str(core_per_socket)
    os.environ['SOCKETS'] = str(sockets)

    print("\n-- Setting the CORES_COUNT env variable to ", os.environ['CORES_COUNT'])
    print("\n-- Setting the THREADS_CNT env variable to ", os.environ['THREADS_CNT'])
    print("\n-- Setting the CORES_PER_SOCKET env variable to ", os.environ['CORES_PER_SOCKET'])
    print("\n-- Setting the SOCKETS env variable to ", os.environ['SOCKETS'])


def determine_host_ip_addr():
    host_IP = socket.gethostbyname(socket.gethostname())
    
    if host_IP.startswith("127."):
        sock_obj = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # The IP address specified in below connect call doesn't have to be reachable..
        sock_obj.connect(('10.255.255.255', 1))
        host_IP = sock_obj.getsockname()[0]
        
    for ifaceName in ni.interfaces():
        if ni.ifaddresses(ifaceName).setdefault(ni.AF_INET) is not None and \
                ni.ifaddresses(ifaceName).setdefault(ni.AF_INET)[0]['addr'].startswith('192.168'):
            host_IP = ni.ifaddresses(ifaceName).setdefault(ni.AF_INET)[0]['addr']
            break

    return host_IP


def write_to_csv(tcd, test_dict):
    csv_res_folder = os.path.join(PERF_RESULTS_DIR, tcd['workload_name'])
    if not os.path.exists(csv_res_folder): os.makedirs(csv_res_folder)
    csv_res_file = os.path.join(csv_res_folder, tcd['test_name']+'.csv')
    with open(csv_res_file, 'w') as csvfile:
        csvwriter = csv.DictWriter(csvfile, test_dict.keys())
        csvwriter.writeheader()
        csvwriter.writerow(test_dict)
    

def write_to_report(workload_name, test_results):
    throughput_dict = collections.defaultdict(dict)
    latency_dict = collections.defaultdict(dict)
    time_dict = collections.defaultdict(dict)
    generic_dict = collections.defaultdict(dict)

    for k in test_results:
        if 'time' in k:
            time_dict[k] = test_results[k]
        elif 'throughput' in k:
            throughput_dict[k] = test_results[k]
        elif 'latency' in k:
            latency_dict[k] = test_results[k]
        else:
            generic_dict[k] = test_results[k]

    now = dt.isoformat(dt.now()).replace(":","-").split('.')[0]
    if workload_name == 'Tensorflow' and os.environ['encryption'] == '1':
        workload_name = 'tensorflow_encrypted'
    elif workload_name == 'Openvino' and os.environ['EDMM'] == '1':
        workload_name = 'openvino_edmm'
    elif workload_name == 'Redis' and os.environ['perf_config'] == 'container':
        workload_name = 'redis_container'
    elif workload_name == 'MySql' and os.environ['perf_config'] == 'container':
        workload_name = 'mysql_container'
    gramine_commit = os.environ["gramine_commit"]
    if "/" in gramine_commit:
        gramine_commit = os.path.basename(gramine_commit)
    report_name = os.path.join(PERF_RESULTS_DIR, "gramine_" + workload_name.lower() + "_perf_data_" + os.environ["jenkins_build_num"] + "_" + now + "_" + gramine_commit[:7] + ".xlsx")
    print(f"\n-- Writing Gramine performance results to {report_name}\n")
    if not os.path.exists(PERF_RESULTS_DIR): os.makedirs(PERF_RESULTS_DIR)
    if os.path.exists(report_name):
        writer = pd.ExcelWriter(report_name, engine='openpyxl', mode='a')
    else:
        writer = pd.ExcelWriter(report_name, engine='openpyxl')
    
    if workload_name == 'Sklearnex':
        cols = ['data_type', 'dataset_name', 'rows', 'columns', 'classes', 'time', 'gramine-sgx', 'gramine-direct', 'gramine-sgx-deg', 'gramine-direct-deg']
    elif workload_name == 'Pytorch':
        cols = ['native_s0', 'native_s1', 'gramine-direct_s0', 'gramine-direct_s1', 'gramine-sgx_s0', 'gramine-sgx_s1', \
                'native_s0_avg', 'native_s1_avg', 'gramine-direct_s0_avg', 'gramine-direct_s1_avg', 'gramine-sgx_s0_avg', 'gramine-sgx_s1_avg', \
                'native_s0_r2r_var', 'native_s1_r2r_var', 'gramine-direct_s0_r2r_var', 'gramine-direct_s1_r2r_var', 'gramine-sgx_s0_r2r_var', 'gramine-sgx_s1_r2r_var', \
                'gramine-direct_s0_Deg', 'gramine-direct_s1_Deg', 'gramine-sgx_s0_Deg', 'gramine-sgx_s1_Deg']
    else:
        cols = ['native', 'gramine-sgx', 'gramine-sgx-exitless', 'gramine-direct', 'native-med', 'sgx-med', 'sgx-exitless-med', 'direct-med', 'sgx-deg', 'sgx-exitless-deg', 'direct-deg']

    if len(throughput_dict) > 0:
        if workload_name == 'Pytorch':
            throughput_df = pd.DataFrame.from_dict(throughput_dict, orient='index', columns=cols)
        else:
            throughput_df = pd.DataFrame.from_dict(throughput_dict, orient='index', columns=cols).dropna(axis=1)
        throughput_df.columns = throughput_df.columns.str.upper()
        throughput_df.to_excel(writer, sheet_name=workload_name)

    if len(latency_dict) > 0:
        if workload_name == 'Pytorch':
            latency_df = pd.DataFrame.from_dict(latency_dict, orient='index', columns=cols)
        else:
            latency_df = pd.DataFrame.from_dict(latency_dict, orient='index', columns=cols).dropna(axis=1)
        latency_df.columns = latency_df.columns.str.upper()
        if len(throughput_dict) > 0:
            if workload_name == 'Pytorch':
                latency_df.to_excel(writer, sheet_name=workload_name, header=None, startrow=throughput_df.shape[0]+1)
            else:
                latency_df.to_excel(writer, sheet_name=workload_name, startcol=throughput_df.shape[1]+2)
        else:
            latency_df.to_excel(writer, sheet_name=workload_name)
    
    if len(generic_dict) > 0:
        if workload_name == 'Sklearnex':
            generic_df = pd.DataFrame.from_dict({(i,j): generic_dict[i][j] for i in generic_dict.keys() for j in generic_dict[i].keys()},
                                                orient='index', columns=cols)
            generic_df.rename(columns={'time':'native'}, inplace=True)
        else:
            generic_df = pd.DataFrame.from_dict(generic_dict, orient='index', columns=cols).dropna(axis=1)
        generic_df.columns = generic_df.columns.str.upper()
        generic_df.to_excel(writer, sheet_name=workload_name)

    if len(time_dict) > 0:
        cols = os.environ['exec_mode'].split(",")
        time_df = pd.DataFrame.from_dict(time_dict, orient='index', columns=cols).dropna(axis=1)
        time_df.columns = time_df.columns.str.upper()
        time_df.to_excel(writer, sheet_name=workload_name+"_Time")

    writer._save()


def generate_performance_report(test_res_dict):
    print("\n###### In generate_performance_report #####\n")

    for workload, tests in test_res_dict.items():
        write_to_report(workload, tests)


def check_machine():
    service_cmd = "sudo systemctl --type=service --state=running"
    service_output = exec_shell_cmd(service_cmd)
    if "walinuxagent.service" in service_output:
        print("Running on Azure Linux Agent")
        return "Azure Linux Agent"
    elif "pccs.service" in service_output:
        print("Running on DCAP client")
        return "DCAP client"
    else:
        print("No Provisioning service found, cannot run tests with attestation.")
        return "No Provisioning enabled"


def kill(proc_pid):
    try:
        process = psutil.Process(proc_pid)
        for proc in process.children(recursive=True):
            proc.terminate()
        process.terminate()
    except:
        pass


def kill_process_by_name(processName):
    procs = [p.pid for p in psutil.process_iter() for c in p.cmdline() if processName in c]
    for process in procs:
        try:
            exec_shell_cmd("sudo kill -9 {}".format(process))
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass


def get_workload_name(docker_image):
    try:
        return docker_image.split(" ")[1]
    except Exception as e:
        return ''


def cleanup_after_test(workload):
    try:
        kill_process_by_name("secret_prov_server_dcap")
        kill_process_by_name("/gramine/app_files/apploader.sh")
        kill_process_by_name("/gramine/app_files/entrypoint")
        exec_shell_cmd('sudo sh -c "echo 3 > /proc/sys/vm/drop_caches"')
        exec_shell_cmd("docker rmi gsc-{} -f".format(workload))
        exec_shell_cmd("docker rmi gsc-{}-unsigned -f".format(workload))
        exec_shell_cmd("docker rmi {} -f".format(workload))
        exec_shell_cmd("docker rmi verifier_image:latest -f")
        exec_shell_cmd("docker system prune -f")
    except Exception as e:
        pass


def popen_subprocess(command, dest_dir=None):
    if dest_dir:
        cwd = os.getcwd()
        os.chdir(dest_dir)

    print("Starting Process ", command)
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True, encoding='utf-8')
    time.sleep(1)
   
    if dest_dir: os.chdir(cwd)
    return process


def gen_encryption_key():
    enc_key_name = "encryption_key"
    exec_shell_cmd("gramine-sgx-pf-crypt gen-key -w " + enc_key_name)
    return enc_key_name


def get_encryption_key_dump(enc_key_name):
    hex_enc_key_dump = exec_shell_cmd("xxd -p " + enc_key_name)
    return hex_enc_key_dump


def is_package_installed(package_name):
    installed_packages = pkg_resources.working_set
    installed_packages_list = sorted(["%s==%s" % (i.key, i.version) for i in installed_packages])
    if any(package_name in j for j in installed_packages_list):
        return True
    else:
        return False

def read_file(filename):
    fd = open(filename)
    fd_contents = fd.read()
    fd.close()
    return fd_contents

def update_file_contents(old_contents, new_contents, filename, append=False):
    fd_contents = read_file(filename)
    if append:
        old_data = (old_contents).join(re.search("(.*){}(.*)".format(old_contents), fd_contents).groups())
        new_data = re.sub(old_data, new_contents+old_data, fd_contents)
    else:
        new_data = re.sub(old_contents, new_contents, fd_contents)
    fd = open(filename, "w")
    fd.write(new_data)
    fd.close()

def check_and_enable_edmm_in_manifest(manifest_file):
    if os.environ["EDMM"] == "1":
        add_edmm_enable = add_exinfo = False
        with open(manifest_file) as f:
            file_contents = f.read()
            if not 'edmm_enable' in file_contents:
                add_edmm_enable = True
            if not 'require_exinfo' in file_contents:
                add_exinfo = True
        if add_edmm_enable:
            edmm_string = '$ a sgx.edmm_enable = true'
            edmm_sed_cmd = f"sed -i -e '{edmm_string}' {manifest_file}"
            exec_shell_cmd(edmm_sed_cmd, None)
        if add_exinfo:
            exinfo_string = '$ a sgx.require_exinfo = true'
            exinfo_sed_cmd = f"sed -i -e '{exinfo_string}' {manifest_file}"
            exec_shell_cmd(exinfo_sed_cmd, None)

def track_process(test_config_dict, process=None, success_str='', timeout=0):
    result = False
    final_output = ''
    debug_log = None
    output = None

    # Redirecting the debug mode logs to file instead of console because
    # it consumes whole lot of console and makes difficult to debug
    if test_config_dict.get("debug_mode") == "y":
        console_log_file = f"{LOGS_DIR}/{test_config_dict['test_name']}_console.log"
        debug_log = open(console_log_file, "w+")

    if timeout != 0:
        timeout = time.time() + timeout
    while True:
        if process.poll() is not None and output == '':
            break

        output = process.stdout.readline()
        
        if debug_log:
            if output: debug_log.write(output)
        else:
            if output: print(output.strip())

        if output:
            if output:
                final_output += output
            if final_output.count(success_str) > 0:
                process.stdout.close()
                result = True
                break
            elif timeout != 0 and time.time() > timeout:
                break
    
    if debug_log: debug_log.close()
    return result, final_output

def reboot_client(username, sys_ip):
    # This method issues a command to reboot the system (sys_ip) and returns 
    # to the caller only after the system is rebooted.

    # Reboot the client and sleep for 2 mins.
    print(f"\n-- Rebooting client system '{sys_ip}' with username '{username}'..")
    ssh_reboot_cmd = f"ssh {username}@{sys_ip} sudo reboot"
    exec_shell_cmd(ssh_reboot_cmd, None)
    time.sleep(120)

    # Wait for the host to reboot..
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    while True:
        try:
            sock.connect((sys_ip, 22))
            print(f"\n-- Client system: '{sys_ip}' is rebooted..")
            break
        except socket.error as e:
            print("\n-- Still in process of rebooting..")
    time.sleep(60)
    sock.close()

def is_program_installed(program_name):
    from shutil import which
    return which(program_name) is not None

def get_workload_result(test_config_dict):
    if "workload_result" in test_config_dict.keys():
        workload_result = [test_config_dict["workload_result"]]
    elif "redis" in test_config_dict["workload_name"].lower():
        workload_result = "Ready to accept connections"
    elif "tensorflowserving" in test_config_dict["workload_name"].lower():
        workload_result = "Running gRPC ModelServer at 0.0.0.0:8500"
    elif "mysql" in test_config_dict["workload_name"].lower():
        workload_result = MYSQL_TESTDB_VERIFY
    elif "mariadb" in test_config_dict["workload_name"].lower():
        workload_result = MARIADB_TESTDB_VERIFY
    elif "openvinomodelserver" in test_config_dict["workload_name"].lower():
        workload_result = "ServableManagerModule started"
    elif "mongodb" == test_config_dict["workload_name"].lower():
        workload_result = "mongod startup complete"
    return workload_result


def verify_process(test_config_dict, process=None, timeout=0):
    result = False
    workload_output = ''
    debug_log = None
    output = None
    workload_result = get_workload_result(test_config_dict)
    print(workload_result)

    # Redirecting the debug mode logs to file instead of console because
    # it consumes whole lot of console and makes difficult to debug
    if test_config_dict.get("debug_mode") == "y":
        console_log_file = f"{LOGS_DIR}/{test_config_dict['test_name']}_console.log"
        debug_log = open(console_log_file, "w+")

    if timeout != 0:
        timeout = time.time() + timeout
    while True:
        if process.poll() is not None and output == '':
            break

        output = process.stdout.readline()
        
        if debug_log:
            if output: debug_log.write(output)
        else:
            if output: print(output.strip())

        if output:
            if output:
                workload_output += output
            if workload_output.count(workload_result) > 0:
                process.stdout.close()
                result = True
                break
            elif timeout != 0 and time.time() > timeout:
                break
    
    if debug_log: debug_log.close()
    return result

def run_subprocess(command, dest_dir=None):
    if dest_dir:
        os.chdir(dest_dir)

    print("Starting Process %s from %s" %(command, os.getcwd()))
    process = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                    universal_newlines=True, shell=True)
    try:
        if dest_dir: os.chdir(FRAMEWORK_HOME_DIR)
    except:
        print("Failed to change directory")

    if process.returncode != 0:
        print(process.stderr.strip())
        raise Exception("Failed to run command {}".format(command))
    
    return process.stdout.strip()

def verify_build_env_details():
    result = False
    out = []
    if os.environ["gramine_commit"] or os.environ["gsc_repo"] or os.environ["gsc_commit"]:
        print("\n\n############################################################################")
        os.chdir(os.path.join(CURATED_APPS_PATH, "gsc"))
        if os.environ["gramine_commit"]:
            fd = open("config.yaml", mode="r")
            fd_data = yaml.safe_load(fd.read())
            c_gramine_repo = fd_data["Gramine"]["Repository"]
            c_gramine_commit = fd_data["Gramine"]["Branch"]
            out.append(os.environ["gramine_commit"] == c_gramine_commit)
            print("\nGramine Repo: ", c_gramine_repo)
            print("Gramine Commit: ", c_gramine_commit)
        if os.environ["gsc_repo"]:
            c_gsc_url = run_subprocess("git config --get remote.origin.url")
            out.append(os.environ["gsc_repo"] == c_gsc_url)
            print("\nGSC Repo: ", c_gsc_url)
        if os.environ["gsc_commit"]:
            c_gsc_commit = run_subprocess("git branch --show-current")
            out.append(os.environ["gsc_commit"] == c_gsc_commit)
            print("\nGSC Commit: ", c_gsc_commit)
        print("\n\n############################################################################")
        result = all(out)
    else:
        print("No environment variable specified")
        result = True
    return result

def search_text_and_return_line_in_file(file_name, search_str):
    with open(file_name, "r") as fp:
        return [line for line in fp if search_str.lower() in line or search_str.capitalize() in line]
