import os
import re
import pandas as pd
import xlsxwriter
import argparse
import yaml

# workloadlist = ['redis', 'openvino', 'tensorflow', 'tensorflow_encrypted', 'tensorflow_serving']

unwamted_cols = ['NATIVE', 'GRAMINE-SGX', 'GRAMINE-SGX-SINGLE-THREAD-NON-EXITLESS', 'GRAMINE-DIRECT',
                 'Unnamed: 9', 'NATIVE.1', 'GRAMINE-SGX-SINGLE-THREAD-NON-EXITLESS.1', 'GRAMINE-DIRECT.1']

dashboard_excl_file = "gramine_perf_data.xlsx"

def read_yaml_config():
    with open('config/workloads.yaml', 'r') as yaml_file:
        parsed_yaml_file = yaml.safe_load(yaml_file)
        print(parsed_yaml_file)
    return parsed_yaml_file

def add_workload(workload):
    parsed_yaml_file = read_yaml_config()
    workload_list = parsed_yaml_file["workloads"]
    if not workload in workload_list:
        workload_list.append(workload)
    else:
        print(workload + " is already present in config/workloads.yml")
    print(workload_list)
    with open('config/workloads.yaml', 'w') as yaml_file:
        documents = yaml.safe_dump(parsed_yaml_file, yaml_file)

def get_redis_data(filename, date, commit_id):    
    latency_columns = ['Unnamed: 10', 'NATIVE-AVG.1', 'SGX-SINGLE-THREAD-AVG.1', 'DIRECT-AVG.1', 'SGX-SINGLE-THREAD-DEG.1', 'DIRECT-DEG.1']
    
    df_redis = pd.read_excel(filename, usecols=lambda x: x not in unwamted_cols)
    df_latency = df_redis[latency_columns]

    df_latency.rename(columns={'Unnamed: 10': 'model',
          'NATIVE-AVG.1': 'NATIVE-AVG', 'SGX-SINGLE-THREAD-AVG.1': 'SGX-SINGLE-THREAD-AVG', 'DIRECT-AVG.1':'DIRECT-AVG', 'SGX-SINGLE-THREAD-DEG.1':'SGX-SINGLE-THREAD-DEG', 'DIRECT-DEG.1':'DIRECT-DEG'}, inplace=True)
    print(df_latency)
    df_redis = df_redis.drop(columns=latency_columns)
    df_redis.rename(columns={'Unnamed: 0':'model'}, inplace=True)
    print(df_redis)
    df_redis = pd.concat([df_redis, df_latency], ignore_index=True)

    df_redis['Date'] = date
    df_redis['Date'] = pd.to_datetime(df_redis.Date, format='%Y-%m-%d').dt.date

    df_redis['commit'] = commit_id
    return df_redis

def get_perf_data(filename, date, commit_id):
    df = pd.read_excel(filename, usecols=lambda x: x not in unwamted_cols)
    df.rename(columns={'Unnamed: 0':'model'}, inplace=True)
    df['Date'] = date
    df['Date'] = pd.to_datetime(df.Date, format='%Y-%m-%d').dt.date
    df['commit'] = commit_id
    return df

def drop_duplicates(path):
    df = pd.read_excel(path, sheet_name=None)
    with pd.ExcelWriter(path,datetime_format='m/d/yyyy') as writer:
        for workload in df:
            df[workload].drop_duplicates(inplace=True)
            df[workload].to_excel(writer, sheet_name=workload, index=False)

def read_excel(filename, perf_df, workloadlist):
    print(filename)
    commit_id = re.search(r'.*_([^.]+)', filename)[1]
    date = re.search("([0-9]{4}\-[0-9]{2}\-[0-9]{2})", filename)
    result = False
    for i in workloadlist:
        workload_identifier = i + "_perf"
        if workload_identifier in filename:
            result = True
            if i == "redis":
                perf_df[i].append(get_redis_data(filename, date.group(1), commit_id))
            else:
                perf_df[i].append(get_perf_data(filename, date.group(1), commit_id))
    if not result:
        print("unknown file :" + filename)

def write_excel(path, perf_df_from_excl):
    if os.path.isfile(path):
        with pd.ExcelWriter(path, mode="a", engine="openpyxl", if_sheet_exists="overlay", datetime_format='m/d/yyyy') as writer:
            for workload in perf_df_from_excl:
                print(workload)
                workload_merge_df = pd.DataFrame()
                for workload_perf_data in perf_df_from_excl[workload]:
                    workload_merge_df = pd.concat([workload_merge_df, workload_perf_data], ignore_index=True)
                if workload_merge_df.empty:
                    continue
                if workload in writer.sheets:
                    workload_merge_df.to_excel(writer, sheet_name=workload, startrow=writer.sheets[workload].max_row, index=False, header=False)
                else:
                    workload_merge_df.to_excel(writer, sheet_name=workload, index=False)
    else:
        with pd.ExcelWriter(path,datetime_format='m/d/yyyy') as writer:
            for workload in perf_df_from_excl:
                print(workload)
                workload_merge_df = pd.DataFrame()
                for workload_perf_data in perf_df_from_excl[workload]:
                    workload_merge_df = pd.concat([workload_merge_df, workload_perf_data], ignore_index=True)
                if workload_merge_df.empty:
                    continue
                workload_merge_df.to_excel(writer, sheet_name=workload, index=False)
    drop_duplicates(path)

def update_dashboard_input_file(input_dir, output_dir):
    workloadlist = read_yaml_config()['workloads']
    with os.scandir(input_dir) as entries:
        owd = os.getcwd()
        os.chdir(input_dir)
        perf_df_from_excl =  new_dict = {workload: [] for workload in workloadlist}
        for entry in entries:
            read_excel(entry.name, perf_df_from_excl, workloadlist)
        os.chdir(owd)
        print(perf_df_from_excl)    
    path = output_dir + '/' + dashboard_excl_file
    write_excel(path, perf_df_from_excl)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-a', '--add_workload', type=str, help='ex: --add_workload mysql')
    parser.add_argument('-i', '--input', type=str, required=True, help='Input directory')
    parser.add_argument('-o', '--output', type=str, required=True, help='Output directory')
    parser.add_argument('-r', '--replace', action="store_true", help='Delete file content before writing to it')
    args = parser.parse_args()

    if args.add_workload :
        add_workload(args.add_workload)

    if args.input :
        input_dir = args.input

    if args.output :
        output_dir = args.output
        if not os.path.exists(output_dir):
            os.mkdir(output_dir)

    if args.replace :
        if os.path.isfile(output_dir + '/' + dashboard_excl_file):
            os.remove(output_dir + '/' + dashboard_excl_file)

    update_dashboard_input_file(input_dir, output_dir)
    









    
