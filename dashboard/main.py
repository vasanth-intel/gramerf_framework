import os
import sys
import re
import pandas as pd
import argparse
import yaml
import socket
import psutil
import signal

# workloadlist = ['redis', 'openvino', 'tensorflow', 'tensorflow_encrypted', 'tensorflow_serving']

workload_namelist = {}
workload_namelist['redis'] = 'Redis'
workload_namelist['openvino'] = 'OpenVINO'
workload_namelist['tensorflow'] = 'TensorFlow'
workload_namelist['tensorflow_encrypted'] = 'TensorFlow Encrypted'
workload_namelist['tensorflowserving'] = 'TensorFlow Serving'
workload_namelist['mysql'] = 'MySQL'
workload_namelist['memcached'] = 'Memcached'
workload_namelist['sklearnex'] = 'scikit-learn'
workload_namelist['mariadb'] = 'MariaDB'
workload_namelist['openvinomodelserver'] = 'OpenVINO™ Model Server'
workload_namelist['pytorch'] = 'PyTorch'
workload_namelist['nginx'] = 'NGINX'
workload_namelist['specpower'] = 'SPECpower'

unwamted_cols = ['NATIVE', 'GRAMINE-SGX', 'GRAMINE-SGX-SINGLE-THREAD-NON-EXITLESS', 'GRAMINE-DIRECT',
                 'Unnamed: 9', 'NATIVE.1', 'GRAMINE-SGX-SINGLE-THREAD-NON-EXITLESS.1', 'GRAMINE-DIRECT.1', 'Unnamed: 1', 'ROWS', 'COLUMNS']

dashboard_excl_file = "gramine_perf_data.xlsx"

def is_port_in_use(port: int):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex((socket.gethostname(), port)) == 0

def stop_dashboard_execution():
    if is_port_in_use(8050):
        print("stop the dashboard")
        for proc in psutil.process_iter():
            for conns in proc.connections(kind='inet'):
                if conns.laddr.port == 8050:
                    if proc.pid > 0:
                        print("stop the process : " + str(proc.pid))
                        proc.send_signal(signal.SIGTERM)

def read_yaml_config():
    with open('config/workloads.yaml', 'r') as yaml_file:
        parsed_yaml_file = yaml.safe_load(yaml_file)
    return parsed_yaml_file


def add_workload(workload):
    parsed_yaml_file = read_yaml_config()
    workload_list = parsed_yaml_file["workloads"]
    if not workload in workload_list:
        workload_list.append(workload)
    else:
        print(workload + " is already present in config/workloads.yml")
    with open('config/workloads.yaml', 'w') as yaml_file:
        documents = yaml.safe_dump(parsed_yaml_file, yaml_file)


def get_redis_data(df):
    latency_columns = ['Unnamed: 10', 'NATIVE-AVG.1', 'SGX-SINGLE-THREAD-AVG.1',
                       'DIRECT-AVG.1', 'SGX-SINGLE-THREAD-DEG.1', 'DIRECT-DEG.1']
    rename_latency_columns = {'Unnamed: 10': 'Unnamed: 0',
                              'NATIVE-AVG.1': 'NATIVE-AVG', 'SGX-SINGLE-THREAD-AVG.1': 'SGX-SINGLE-THREAD-AVG',
                              'DIRECT-AVG.1': 'DIRECT-AVG', 'SGX-SINGLE-THREAD-DEG.1': 'SGX-SINGLE-THREAD-DEG', 'DIRECT-DEG.1': 'DIRECT-DEG'}
    rename_columns = {
        'SGX-SINGLE-THREAD-AVG': 'SGX-AVG', 'SGX-SINGLE-THREAD-DEG': 'SGX-DEG'}

    df_latency = df[latency_columns]
    df_latency.rename(columns=rename_latency_columns, inplace=True)
    df = df.drop(columns=latency_columns)
    df = pd.concat([df, df_latency], ignore_index=True)
    df.rename(columns=rename_columns, inplace=True)
    return df


def get_pytorch_data(df_pytorch):
    pytorch_columns = ['Unnamed: 0', 'GRAMINE-SGX_S0_DEG', 'GRAMINE-SGX_S1_DEG']
    df = df_pytorch[pytorch_columns]
    return df

def get_perf_data(filename, date, commit_id, workload):
    df = pd.read_excel(filename, usecols=lambda x: x not in unwamted_cols)
    if workload == "redis" or workload == "memcached":
        df = get_redis_data(df)
    if workload == "sklearnex":
        df = df.drop(columns=['GRAMINE-DIRECT-DEG'])
        df.rename(columns={'GRAMINE-SGX-DEG': 'SGX-DEG'}, inplace=True)
    if workload == 'pytorch':
        df = get_pytorch_data(df)
    df.rename(columns={'Unnamed: 0': 'model'}, inplace=True)
    df['Date'] = date
    df['Date'] = pd.to_datetime(df.Date, format='%Y-%m-%d').dt.date
    df['commit'] = commit_id
    return df


def drop_duplicates(path):
    df = pd.read_excel(path, sheet_name=None)
    with pd.ExcelWriter(path, datetime_format='m/d/yyyy') as writer:
        for workload in df:
            df[workload].drop_duplicates(inplace=True)
            df[workload].to_excel(writer, sheet_name=workload, index=False)


def read_excel(filename, perf_df, workloadlist):
    print("parsing file : " + filename)
    commit_id = re.search(r'.*_([^.]+)', filename)[1]
    date = re.search("([0-9]{4}\-[0-9]{2}\-[0-9]{2})", filename)
    result = False
    for workload in workloadlist:
        workload_identifier = workload + "_perf"
        if workload_identifier in filename:
            result = True
            perf_df[workload].append(get_perf_data(
                    filename, date.group(1), commit_id, workload))
    if not result:
        print("unknown file :" + filename)


def write_excel(path, perf_df_from_excl):
    if os.path.isfile(path):
        with pd.ExcelWriter(path, mode="a", engine="openpyxl", if_sheet_exists="overlay", datetime_format='m/d/yyyy') as writer:
            for workload in perf_df_from_excl:
                print("writing " + workload + " perf data...")
                workload_merge_df = pd.DataFrame()
                for workload_perf_data in perf_df_from_excl[workload]:
                    workload_merge_df = pd.concat(
                        [workload_merge_df, workload_perf_data], ignore_index=True)
                if workload_merge_df.empty:
                    continue
                if workload_namelist[workload] in writer.sheets:
                    workload_merge_df.to_excel(
                        writer, sheet_name=workload_namelist[workload], startrow=writer.sheets[workload_namelist[workload]].max_row, index=False, header=False)
                else:
                    workload_merge_df.to_excel(
                        writer, sheet_name=workload_namelist[workload], index=False)
    else:
        with pd.ExcelWriter(path, datetime_format='m/d/yyyy') as writer:
            for workload in perf_df_from_excl:
                print("writing " + workload + " perf data...")
                workload_merge_df = pd.DataFrame()
                for workload_perf_data in perf_df_from_excl[workload]:
                    workload_merge_df = pd.concat(
                        [workload_merge_df, workload_perf_data], ignore_index=True)
                if workload_merge_df.empty:
                    continue
                workload_merge_df.to_excel(
                    writer, sheet_name=workload_namelist[workload], index=False)
    drop_duplicates(path)

def update_dashboard_input_file(input_dir, output_dir, replace):
    workloadlist = read_yaml_config()['workloads']
    with os.scandir(input_dir) as entries:
        owd = os.getcwd()
        os.chdir(input_dir)
        perf_df_from_excl = new_dict = {workload: []
                                        for workload in workloadlist}
        for entry in entries:
            read_excel(entry.name, perf_df_from_excl, workloadlist)
        os.chdir(owd)
    path = output_dir + '/' + dashboard_excl_file

    # kill dashboard
    stop_dashboard_execution()

    if replace:
        if os.path.isfile(output_dir + '/' + dashboard_excl_file):
            os.remove(output_dir + '/' + dashboard_excl_file)

    write_excel(path, perf_df_from_excl)
    #start dashboard
    import gramerf_perf_dash
    gramerf_perf_dash.start_execution()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--restart', action="store_true",
                        help='restart Dashboard service'),
    parser.add_argument('-a', '--add_workload', type=str,
                        help='ex: --add_workload mysql')
    parser.add_argument('-i', '--input', type=str,
                        required=not '--restart' in sys.argv, help='Input directory')
    parser.add_argument('-o', '--output', type=str,
                        required=not '--restart' in sys.argv, help='Output directory')
    parser.add_argument('-r', '--replace', action="store_true",
                        help='Delete old dashboard data')
    args = parser.parse_args()

    if args.restart:
        stop_dashboard_execution()
        import gramerf_perf_dash
        gramerf_perf_dash.start_execution()
        exit()

    if args.add_workload:
        add_workload(args.add_workload)

    if args.input:
        input_dir = args.input

    if args.output:
        output_dir = args.output
        if not os.path.exists(output_dir):
            os.mkdir(output_dir)

    update_dashboard_input_file(input_dir, output_dir, args.replace)
