import os
import argparse
import pandas as pd

sklearn_group_cols = ['Unnamed: 0', 'Unnamed: 1', 'ROWS', 'COLUMNS']
sklearn_mean_cols = ["NATIVE", "GRAMINE-SGX",
                     "GRAMINE-DIRECT", "GRAMINE-SGX-DEG", "GRAMINE-DIRECT-DEG"]
output_file_name = ''


def parse_sklearn_perf_data(input_dir):
    global output_file_name
    sklearn_perf_datalist = []
    with os.scandir(input_dir) as entries:
        print(entries)
        owd = os.getcwd()
        os.chdir(input_dir)
        for entry in entries:
            if not output_file_name:
                output_file_name = entry.name
            sklearn_perf_datalist.append(pd.read_excel(entry.name))
        os.chdir(owd)
    return sklearn_perf_datalist


def create_sklearn_perf_report(sklearn_perf_datalist):
    df = pd.DataFrame()

    #merge all the sklearn perf data to one dataframe
    for perf_data in sklearn_perf_datalist:
        df = pd.concat([df, perf_data], ignore_index=True)

    #update perf test name appropriately as values on most of model columns are empty
    for i in df.index:
        if pd.notna(df.iloc[i]['Unnamed: 0']) is False:
            df.at[i, 'Unnamed: 0'] = model_name
        model_name = df.at[i, 'Unnamed: 0']

    #update the model name by merging ROWS and COLUMNS for uniqueness
    df['Unnamed: 0'] = df['Unnamed: 0'] + '_' + \
        df['ROWS'].astype(str) + '_' + df['COLUMNS'].astype(str)
    print(df)
    # df1 = df.loc[(df['Unnamed: 0'] == 'test_sklearnex_perf_skl_config_training_kmeans') & (df['Unnamed: 1'] == 0)]
    # print(df1)
    # df1 = df1[["NATIVE", "GRAMINE-SGX", "GRAMINE-DIRECT", "GRAMINE-SGX-DEG", "GRAMINE-DIRECT-DEG"]].mean()
    # print(df1)

    #group and calculate median for required columns
    df1 = df.groupby(sklearn_group_cols)[sklearn_mean_cols].median()
    print(df1)

    #create the excel
    path = output_dir + '/' + output_file_name
    df1.to_excel(path)


def generate_sklearn_perf_median_report(input_dir, output_dir):
    sklearn_perf_datalist = parse_sklearn_perf_data(input_dir)
    create_sklearn_perf_report(sklearn_perf_datalist)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--indir', type=str,
                        required=True, help='Input directory')
    parser.add_argument('-o', '--outdir', type=str,
                        required=True, help='Output directory')
    args = parser.parse_args()

    if args.outdir:
        output_dir = args.outdir
        if not os.path.exists(output_dir):
            os.mkdir(output_dir)

    if args.indir:
        input_dir = args.indir

    generate_sklearn_perf_median_report(input_dir, output_dir)