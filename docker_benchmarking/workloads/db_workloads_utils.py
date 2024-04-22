import os
import time
import subprocess
import shutil
from common.config_files.constants import *
from common.libs import utils

def init_db(workload_name):
    if os.environ["perf_config"] == "container":
        return init_container_db(workload_name)
    else:
        return init_baremetal_db(workload_name)

def init_container_db(workload_name):
    # We need to stop the baremetal MySql service if we are running container MySql.
    # Otherwise, we would not be able to run container MySql, as it uses the same port(3306).
    if utils.is_program_installed(workload_name.lower()):
        print("\n -- Stopping MySQL service..\n")
        utils.exec_shell_cmd("sudo systemctl stop mysql.service", None)
    docker_output = ''
    output = None
    init_result = False
    timeout = time.time() + 60*10
    try:
        os.makedirs(eval(workload_name.upper()+"_TESTDB_PATH"), exist_ok=True)
        process = subprocess.Popen(eval(workload_name.upper()+"_INIT_DB_CMD"), cwd=CURATED_APPS_PATH, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding="utf-8")
        print(f"Initializing {workload_name.upper()} DB")
        while True:
            if process.poll() is not None and output == '':
                if "ovms" in workload_name:
                    time.sleep(30)
                    expected_file_list = ['resnet50-binary-0001.bin', 'resnet50-binary-0001.xml', 'face-detection-retail-0005.bin', 
                                          'face-detection-retail-0005.xml', 'faster-rcnn-resnet101-coco-sparse-60-0001.bin',
                                          'faster-rcnn-resnet101-coco-sparse-60-0001.xml']
                    present_file_list = [f for f in expected_file_list if os.path.isfile(os.path.join(OVMS_MODEL_FILES_PATH,f))]
                    if len(present_file_list) == len(expected_file_list):
                        print(f"{workload_name.upper()} DB is initialized\n")
                        init_result = True
                        break
                else:
                    break
            output = process.stderr.readline()
            print(output)
            if output:
                docker_output += output
                if "mysql" in workload_name or "mariadb" in workload_name:
                    if (docker_output.count(eval(workload_name.upper()+"_TESTDB_VERIFY")) == 2):
                        print(f"{workload_name.upper()} DB is initialized\n")
                        init_result = True
                        break
                    elif time.time() > timeout:
                        break
    finally:
        process.stdout.close()
        process.stderr.close()
        utils.kill(process.pid)
    if init_result:
        if "mysql" in workload_name or "mariadb" in workload_name:
            utils.exec_shell_cmd(STOP_TEST_DB_CMD)
        if "mariadb" in workload_name:
            utils.exec_shell_cmd(MARIADB_CHMOD)
    return init_result

def init_baremetal_db(workload_name):
    if not utils.is_program_installed(workload_name.lower()):
        print("\n -- Installing MySQL..\n")
        utils.exec_shell_cmd("sudo apt-get install -y mysql-server", None)
        utils.exec_shell_cmd('sudo sed -i "s|^\(log_error.*\)|#\1|g" /etc/mysql/mysql.conf.d/mysqld.cnf')
    print("\n -- Stopping MySQL service..\n")
    utils.exec_shell_cmd("sudo systemctl stop mysql.service", None)
    utils.exec_shell_cmd("sudo chown -R $USER:$USER /var/lib/mysql-files", None)
    utils.exec_shell_cmd("sudo mkdir -p /var/run/mysqld && sudo chown -R $USER:$USER /var/run/mysqld", None)

    if not os.path.exists("/etc/apparmor.d/disable/"):
        utils.exec_shell_cmd("sudo ln -s /etc/apparmor.d/usr.sbin.mysqld /etc/apparmor.d/disable/", None)
        utils.exec_shell_cmd("sudo apparmor_parser -R /etc/apparmor.d/usr.sbin.mysqld", None)

    utils.exec_shell_cmd("ulimit -n 65535", None)

    if os.path.exists(MYSQL_BM_ENCRYPTED_DB_TMPFS_PATH):
        utils.exec_shell_cmd(MYSQL_BM_CLEANUP_ENCRYPTED_DB_TMPFS, None)
    if os.path.exists(MYSQL_BM_PLAIN_DB_TMPFS_PATH):
        utils.exec_shell_cmd(MYSQL_BM_CLEANUP_PLAIN_DB_TMPFS, None)

    utils.exec_shell_cmd(f"sudo mkdir -p {MYSQL_BM_PLAIN_DB_TMPFS_PATH} && sudo chown -R $USER:$USER {MYSQL_BM_PLAIN_DB_TMPFS_PATH}")
    init_db_cmd = f"mysqld --initialize-insecure --datadir={MYSQL_BM_PLAIN_DB_TMPFS_PATH}"
    print(f"\n -- Initializing {workload_name.upper()} plain database..\n", init_db_cmd)
    utils.exec_shell_cmd(init_db_cmd, None)

    # Following lines of code to clone 'jkr0103' examples repo and checkout 'mysql' branch
    # must be removed once the examples PR# 28 is merged with examples master.
    print(f"\n -- Cloning 'jkr0103' examples repo and 'mysql' branch..\n")
    os.chdir(GRAMINE_HOME_DIR)
    examples_repo_path = os.path.join(GRAMINE_HOME_DIR, 'examples')
    shutil.rmtree(examples_repo_path)
    utils.exec_shell_cmd("git clone https://github.com/jkr0103/examples.git", None)
    os.chdir(examples_repo_path)
    utils.exec_shell_cmd(f"git checkout mysql", None)

    if os.environ["encryption"] == '1' and 'gramine-sgx' in os.environ["exec_mode"]:
        utils.exec_shell_cmd(f"sudo mkdir -p {MYSQL_BM_ENCRYPTED_DB_TMPFS_PATH} && sudo chown -R $USER:$USER {MYSQL_BM_ENCRYPTED_DB_TMPFS_PATH}")
        mysql_path = os.path.join(examples_repo_path, 'mysql')
        os.chdir(mysql_path)
        print(f"\n -- Generating encryption key..\n")
        enc_key_name = utils.gen_encryption_key()
        enc_key_dump = utils.get_encryption_key_dump(enc_key_name)
        print(f"\n -- Following encryption key dump must be present in manifest template: {enc_key_dump}..\n")
        utils.exec_shell_cmd(f"gramine-sgx-pf-crypt encrypt -w {enc_key_name} -i {MYSQL_BM_PLAIN_DB_TMPFS_PATH} -o {MYSQL_BM_ENCRYPTED_DB_TMPFS_PATH}", None)

    os.chdir(FRAMEWORK_HOME_DIR)

    return True
