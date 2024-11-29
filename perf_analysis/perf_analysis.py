import os
import argparse
import pandas as pd
import numpy as np


sgx_deg_list = []


def get_perf_args():
    arg_parser = argparse.ArgumentParser()

    arg_parser.add_argument(
        '--ref_perf_file', '-rf',
        help='Reference perf file against which the perf results should be analyzed.',
        type=str,
        required=True)

    arg_parser.add_argument(
        '--actual_perf_file', '-af',
        help='Actual perf file for which the perf results should be analyzed.',
        type=str,
        required=True)
    
    arg_parser.add_argument(
        '--workload_name', '-w',
        help='Name of the workload for which the performance needs to be analyzed.',
        type=str,
        required=True)

    arg_parser.add_argument(
        '--perf_tolerance', '-tol',
        help='An integer value above which the absolute difference in perf numbers b/w ref and actual perf results will be flagged.',
        type=int,
        required=False,
        default=10)

    args = arg_parser.parse_args()
    return args


def highlight_cells_in_column(column):    
    global sgx_deg_list

    highlight = 'background-color: orange;'
    default = ''

    return [highlight if v in sgx_deg_list else default for v in column]


def compare_dataframes(ref_df, act_df, workload_name, perf_tolerance):
    global sgx_deg_list
    
    col_name = 'SGX-SINGLE-THREAD-DEG' if workload_name.lower() == 'redis' else 'SGX-DEG'

    # Compare values of 'SGX-DEG' column within reference and actual perf files. Subtract and the
    # absolute value of the difference. If the absolute value is greater than the provided performance
    # tolerance value, then capture the corresponding dataframe within a new dataframe.
    tol_dev_df = act_df.where(act_df[col_name].sub(ref_df[col_name]).abs().gt(perf_tolerance), '')

    # Delete all blank rows of the filtered dataframe.
    tol_dev_df = tol_dev_df.replace(r'^\s*$', np.nan, regex=True)
    tol_dev_df.dropna(axis=0, how='any', inplace=True)
    
    sgx_deg_list = tol_dev_df[col_name].tolist()

    formatted_act_df = act_df.style.apply(highlight_cells_in_column, subset=[col_name], axis=0)
        
    return formatted_act_df


def analyze_perf_results(ref_perf_file, act_perf_file, workload_name, perf_tolerance):
    # Remove old perf analysis file.
    out_file = 'Gramine_' + workload_name + '_Perf_Analysis.xlsx'
    if os.path.exists(out_file):
        os.remove(out_file)

    writer = pd.ExcelWriter(out_file, engine='openpyxl')

    if workload_name.lower() == 'redis':
        tpt_ref_df = pd.read_excel(ref_perf_file, index_col=0, usecols="A:I", engine='openpyxl')
        lat_ref_df = pd.read_excel(ref_perf_file, index_col=0, usecols="K:S", engine='openpyxl')
        tpt_act_df = pd.read_excel(act_perf_file, index_col=0, usecols="A:I", engine='openpyxl')
        lat_act_df = pd.read_excel(act_perf_file, index_col=0, usecols="K:S", engine='openpyxl')

        col_list = tpt_ref_df.columns.tolist()
        # We are renaming the column headers for latency dataframes, as they would be read as NATIVE.1,
        # GRAMINE-DIRECT.1, SGX-AVG.1 .. etc within the above read_excel statements for latency dataframes.
        lat_ref_df.columns = col_list
        lat_act_df.columns = col_list
        
        formatted_tpt_df = compare_dataframes(tpt_ref_df, tpt_act_df, workload_name, perf_tolerance)
        formatted_tpt_df.to_excel(writer, sheet_name=workload_name)
        formatted_lat_df = compare_dataframes(lat_ref_df, lat_act_df, workload_name, perf_tolerance)
        formatted_lat_df.to_excel(writer, sheet_name=workload_name, startcol=tpt_act_df.shape[1]+2)
    else:
        ref_df = pd.read_excel(ref_perf_file, index_col=0, usecols="A:I", engine='openpyxl')
        act_df = pd.read_excel(act_perf_file, index_col=0, usecols="A:I", engine='openpyxl')

        formatted_df = compare_dataframes(ref_df, act_df, workload_name, perf_tolerance)
        formatted_df.to_excel(writer)
    
    writer.save()


if __name__ == "__main__":
    args = get_perf_args()
    analyze_perf_results(args.ref_perf_file, args.actual_perf_file, args.workload_name, args.perf_tolerance)
