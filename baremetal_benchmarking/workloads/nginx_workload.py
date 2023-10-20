import time
import shutil
import glob
import statistics
from pathlib import Path
from common.config_files.constants import *
from baremetal_benchmarking import gramine_libs
from common.libs import utils
from common.perf_benchmarks import memtier_benchmark
from conftest import trd


class NginxWorkload:
    def __init__(self, test_config_dict):
        # Memcached home dir => "~/gramerf_framework/gramine/CI-Examples/nginx"
        self.workload_home_dir = os.path.join(FRAMEWORK_HOME_DIR, test_config_dict['workload_home_dir'])
        # Memcached build dir => "~/gramerf_framework/gramine/CI-Examples/nginx/nginx-1.22.0"
        self.workload_bld_dir = os.path.join(self.workload_home_dir, NGINX_VERSION)

    def get_workload_home_dir(self):
        return self.workload_home_dir

    def download_workload(self):
        # We would not build if dir already exists.
        if os.path.exists(self.workload_bld_dir):
            print("\n-- Nginx already downloaded. Not fetching from source..")
            return True

        print("\n-- Fetching and extracting Nginx workload from source..")
        utils.exec_shell_cmd(NGINX_DOWNLOAD_CMD)
        tar_file_name = os.path.basename(NGINX_DOWNLOAD_CMD.split()[1])
        untar_cmd = f"tar --touch -xzf {tar_file_name}"
        utils.exec_shell_cmd(untar_cmd)

    def build_and_install_workload(self, test_config_dict):
        print("\n###### In build_and_install_workload #####\n")

        bin_file_name = os.path.join(self.workload_home_dir, "install", "sbin", "nginx")
        if os.path.exists(bin_file_name):
            print(f"\n-- Nginx binary already built. Proceeding without building..\n")
            return

        if os.path.exists(self.workload_bld_dir):
            os.chdir(self.workload_bld_dir)
            configure_cmd = f"./configure --prefix={self.workload_home_dir}/install --without-http_rewrite_module \
                                --with-poll_module --with-threads --with-http_ssl_module"
            print(f"\n-- Configuring install directory..\n", configure_cmd)
            utils.exec_shell_cmd(configure_cmd, None)
            
            os.chdir(self.workload_home_dir)
            disable_eventfd_sed_cmd = 'sed -e "s|#define NGX_HAVE_EVENTFD[[:space:]]\+1|#define NGX_HAVE_EVENTFD 0|g" \
                                            -e "s|#define NGX_HAVE_SYS_EVENTFD_H[[:space:]]\+1|#define NGX_HAVE_SYS_EVENTFD_H 0|g" \
                                            -e "s|#define NGX_HAVE_PR_SET_DUMPABLE[[:space:]]\+1|#define NGX_HAVE_PR_SET_DUMPABLE 0|g" \
                                            -i ./nginx-1.22.0/objs/ngx_auto_config.h'

            print(f"\n-- Executing sed cmd to disable eventfd..\n", disable_eventfd_sed_cmd)
            utils.exec_shell_cmd(disable_eventfd_sed_cmd, None)

            nginx_bld_cmd = f"make -C ./{NGINX_VERSION}"
            print(f"\n-- Building nginx workload..\n", nginx_bld_cmd)
            nginx_make_log = LOGS_DIR + "/nginx" + '_make.log'
            make_log_fd = open(nginx_make_log, "w")
            utils.exec_shell_cmd(nginx_bld_cmd, make_log_fd)
            make_log_fd.close()

            nginx_install_cmd = f"make -C ./{NGINX_VERSION} install"
            print(f"\n-- Installing nginx workload..\n", nginx_install_cmd)
            nginx_install_log = LOGS_DIR + "/nginx" + '_install.log'
            install_log_fd = open(nginx_install_log, "w")
            utils.exec_shell_cmd(nginx_install_cmd, install_log_fd)
            install_log_fd.close()
        else:
            raise Exception(f"\n{self.workload_bld_dir} does not exist!")
            
    def generate_manifest(self):
        install_abs_path = os.path.join(self.workload_home_dir, "install")
        manifest_cmd = "gramine-manifest -Dlog_level={} -Darch_libdir={} -Dinstall_dir=./install -Dinstall_dir_abspath={} \
                            nginx.manifest.template > nginx.manifest".format(LOG_LEVEL, os.environ.get('ARCH_LIBDIR'), install_abs_path)
        
        utils.exec_shell_cmd(manifest_cmd, None)

    def generate_test_data(self, tcd):
        update_conf_file_cmd = "sed -e 's|$(LISTEN_PORT)|8002|g' \
                                -e 's|$(LISTEN_SSL_PORT)|8444|g' \
                                -e 's|$(LISTEN_HOST)|127.0.0.1|g' \
                                nginx-gramine.conf.template > install/conf/nginx-gramine.conf"
        print(f"\n-- Updating and copying nginx gramine conf file..\n", update_conf_file_cmd)
        utils.exec_shell_cmd(update_conf_file_cmd, None)

        test_data_path = os.path.join(self.workload_home_dir, "install", "html", "random")
        os.makedirs(test_data_path,exist_ok=True)

        # Creating random test files of size specified in yaml file.
        create_random_file = f"dd if=/dev/urandom of=install/html/random/{tcd['http_filename']} count=1 bs={tcd['http_filesize']} status=none"
        print(f"\n-- Generating test data..\n{create_random_file}")
        utils.exec_shell_cmd(create_random_file, None)

    def generate_ssl_data(self):
        print(f"\n-- Generating SSL data..\n")
        utils.exec_shell_cmd("openssl genrsa -out ssl/ca.key 2048", None)
        utils.exec_shell_cmd("openssl req -x509 -new -nodes -key ssl/ca.key -sha256 -days 1024 -out ssl/ca.crt -config ssl/ca_config.conf", None)
        utils.exec_shell_cmd("openssl genrsa -out ssl/server.key 2048", None)
        utils.exec_shell_cmd("openssl req -new -key ssl/server.key -out ssl/server.csr -config ssl/ca_config.conf", None)
        utils.exec_shell_cmd("openssl x509 -req -days 360 -in ssl/server.csr -CA ssl/ca.crt -CAkey ssl/ca.key -CAcreateserial -out ssl/server.crt", None)
        utils.exec_shell_cmd("cp -f ssl/* ./install/conf/", None)
        utils.exec_shell_cmd("gramine-argv-serializer 'nginx' '-c' 'conf/nginx-gramine.conf' > nginx_args", None)

    def copy_libs(self):
        # The following libraries were given by dev team, which should be present in /usr/lib as per manifest.
        # If the libs are not copied, it will lead to following warning in direct/sgx execution modes.
        # "Emulating a raw system/supervisor call. This degrades performance,
        #  consider patching your application to use Gramine syscall API."
        tcmalloc_lib = os.path.join(Path.home(),"Do_not_delete_gramerf_dependencies/nginx/libtcmalloc.so")
        iomp_lib = os.path.join(Path.home(),"Do_not_delete_gramerf_dependencies/nginx/libiomp5.so")
        if not os.path.exists(tcmalloc_lib) and not os.path.exists(iomp_lib):
            raise Exception(f"\n-- Either of pre-requisite libs not present!\n{tcmalloc_lib}\nOR\n{iomp_lib}")
        utils.exec_shell_cmd(f"sudo cp -f {tcmalloc_lib} /usr/lib/", None)
        utils.exec_shell_cmd(f"sudo cp -f {iomp_lib} /usr/lib/", None)

    def build_wrk_benchmark(self):
        wrk_filename = os.path.join(self.workload_home_dir, "wrk", "wrk")
        if not os.path.exists(wrk_filename):
            print(f"\n-- Cloning and building 'wrk' HTTP benchmarking tool..\n")
            utils.exec_shell_cmd("git clone https://github.com/giltene/wrk.git", None)
            wrk_build_dir = os.path.join(self.workload_home_dir, "wrk")
            os.chdir(wrk_build_dir)
            utils.exec_shell_cmd("make", None)
            if not os.path.exists(wrk_filename):
                raise Exception(f"\n--Failure - Unable to build 'wrk' HTTP benchmarking tool!!")
            os.chdir(self.workload_home_dir)

    def pre_actions(self, test_config_dict):
        os.chdir(self.get_workload_home_dir())
        utils.set_cpu_freq_scaling_governor()
        gramine_libs.update_manifest_file(test_config_dict)

    def setup_workload(self, test_config_dict):
        self.copy_libs()
        self.download_workload()
        self.build_and_install_workload(test_config_dict)
        self.generate_manifest()
        self.generate_test_data(test_config_dict)
        self.generate_ssl_data()
        gramine_libs.generate_sgx_token_and_sig(test_config_dict)
        self.build_wrk_benchmark()

    def launch_server(self, exec_mode = 'native'):
        print(f"\n-- Launching NGINX server in {exec_mode} mode..\n")
        if exec_mode == 'native':
            utils.exec_shell_cmd("./install/sbin/nginx -c conf/nginx-gramine.conf &", None)
        elif exec_mode == 'gramine-direct':
            utils.exec_shell_cmd("gramine-direct ./nginx &", None)
        elif exec_mode == 'gramine-sgx':
            utils.exec_shell_cmd("gramine-sgx ./nginx &", None)
        else:
            raise Exception(f"\nInvalid execution mode specified in config yaml!")

    def free_nginx_server_ports(self, tcd):
        print(f"\n-- Killing Nginx server process..")
        # Dev team suggested to kill even '80' tcp port in addition to the actual running port.
        utils.exec_shell_cmd("sudo fuser -k 80/tcp", None)
        utils.exec_shell_cmd(f"sudo fuser -k {tcd['server_port']}/tcp", None)

    def construct_wrk_http_request(self, tcd, e_mode='native', iteration=1):
        wrk_http_req = ''
        results_dir = os.path.join(PERF_RESULTS_DIR, tcd['workload_name'], tcd['test_name'])
        output_file_name = results_dir + "/" + e_mode + '_' + str(iteration) + '.log'
        benchmark_file = os.path.join(self.workload_home_dir, "wrk", "wrk")
        http_str = 'https' if tcd['server_port'] == 8444 else 'http'
        wrk_http_req = f"{benchmark_file} -t{tcd['threads']} -c300 -d180s {http_str}://127.0.0.1:{tcd['server_port']}/random/{tcd['http_filename']} | tee {output_file_name}"
        
        return wrk_http_req

    # Build the workload execution command based on execution params and execute it.
    def execute_workload(self, tcd, e_mode, test_dict=None):
        print("\n##### In execute_workload #####\n")

        print(f"\n-- Executing {tcd['test_name']} in {e_mode} mode")
        
        results_dir = os.path.join(PERF_RESULTS_DIR, tcd['workload_name'], tcd['test_name'])
        os.makedirs(results_dir, exist_ok=True)

        self.launch_server(e_mode)

        time.sleep(60)

        for i in range(tcd['iterations']):
            wrk_http_req = self.construct_wrk_http_request(tcd, e_mode, i + 1)
            print(f"\n-- Invoking below benchmark command..\n{wrk_http_req}\n")
            benchmark_output = utils.exec_shell_cmd(wrk_http_req)
            print(benchmark_output)
            time.sleep(TEST_SLEEP_TIME_BW_ITERATIONS*2)
        
        self.free_nginx_server_ports(tcd)

        time.sleep(60)

    def process_results(self, tcd):
        results_dir = os.path.join(PERF_RESULTS_DIR, tcd['workload_name'], tcd['test_name'])
        os.chdir(results_dir)
        log_files = glob.glob1(results_dir, "*.log")
        
        if len(log_files) != (len(tcd['exec_mode']) * tcd['iterations']):
            raise Exception(f"\n-- Number of test result files - {len(log_files)} is not equal to the expected number - {len(tcd['exec_mode']) * tcd['iterations']}.\n")

        global trd
        test_dict_throughput = {}
        for e_mode in tcd['exec_mode']:
            test_dict_throughput[e_mode] = []
        
        avg_throughput = 0
        for filename in log_files:
            with open(filename, "r") as f:
                for row in f.readlines():
                    if "Requests/sec:" in row:
                        avg_throughput = row.split()[1]
                        break
                if "native" in filename:
                    test_dict_throughput['native'].append(float(avg_throughput))
                elif "gramine-sgx" in filename:
                    test_dict_throughput['gramine-sgx'].append(float(avg_throughput))
                else:
                    test_dict_throughput['gramine-direct'].append(float(avg_throughput))

        if 'native' in tcd['exec_mode']:
            test_dict_throughput['native-avg'] = '{:0.3f}'.format(statistics.median(test_dict_throughput['native']))

        if 'gramine-direct' in tcd['exec_mode']:
            test_dict_throughput['direct-avg'] = '{:0.3f}'.format(statistics.median(test_dict_throughput['gramine-direct']))
            if 'native' in tcd['exec_mode']:
                test_dict_throughput['direct-deg'] = utils.percent_degradation(tcd, test_dict_throughput['native-avg'], test_dict_throughput['direct-avg'], True)

        if 'gramine-sgx' in tcd['exec_mode']:
            test_dict_throughput['sgx-avg'] = '{:0.3f}'.format(statistics.median(test_dict_throughput['gramine-sgx']))
            if 'native' in tcd['exec_mode']:
                test_dict_throughput['sgx-deg'] = utils.percent_degradation(tcd, test_dict_throughput['native-avg'], test_dict_throughput['sgx-avg'], True)

        trd[tcd['workload_name']] = trd.get(tcd['workload_name'], {})
        trd[tcd['workload_name']].update({tcd['test_name']+'_throughput': test_dict_throughput})

        os.chdir(self.workload_home_dir)
