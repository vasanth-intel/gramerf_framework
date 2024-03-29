import os
import time
import subprocess
from common.config_files.constants import *
from common.libs import utils

def init_db(workload_name):
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