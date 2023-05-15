import re
import pandas as pd
import plotly.express as px
import dash

import dash_html_components as html
import dash_core_components as dcc
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

df = pd.ExcelFile('gramine_perf_reports.xlsx')


def update_test_name(test_name):
    return re.findall('.*perf_(.*)_.*', test_name)[0]


app.layout = html.Div([
    html.H1("Gramine Performance Analytics report",
            style={"textAlign": "center"}),

    html.Hr(),

    html.H2("Select workload"),
    html.Div(html.Div([
        dcc.Dropdown(id='workload', clearable=False,
                     value=df.sheet_names[0],
                     options=df.sheet_names),
    ], className="six columns"), className="row",),

    html.Div(id="output-div", children=[]),
    html.Hr(),


])


@app.callback(Output(component_id="output-div", component_property="children"),
              Input(component_id="workload", component_property="value"),
              )
def make_graph(workload):

    df_workload = df.parse(workload)
    # sort the table by ww
    df_workload.sort_values(by='ww', inplace=True)
    # df_workload["ww-commit"] = df_workload['commit'] + '-' +df_workload['ww'].astype(str)
    print(df_workload)
    df_workload_throughput = df_workload[df_workload["test"].str.contains(
        "throughput")]
    print(df_workload_throughput)

    df_workload_latency = df_workload[df_workload["test"].str.contains(
        "latency")]
    print(df_workload_latency)

    df_workload_throughput.test = df_workload_throughput.test.apply(
        update_test_name)
    df_workload_latency.test = df_workload_latency.test.apply(update_test_name)
    skip_throughput_graph = False
    if df_workload_throughput.empty:
        skip_throughput_graph = True

    if not skip_throughput_graph:
        fig_line_throughput_sgx_deg = px.line(df_workload_throughput, x="commit", y="sgx-deg", color="test",
                                              labels={
                                                  "sgx-deg": "Degradation(%)"},
                                              title=workload + " throughput perf with Gramine SGX", markers=True)

    skip_latency_graph = False
    if df_workload_latency.empty:
        skip_latency_graph = True

    if not skip_latency_graph:
        fig_line_latency_sgx_deg = px.line(df_workload_latency, x="commit", y="sgx-deg", color="test",
                                           labels={
                                               "sgx-deg": "Degradation(%)"},
                                           title=workload + " latency perf with Gramine SGX", markers=True)

    graph_list = []

    if not skip_throughput_graph:
        graph_list.append(
            html.Div([dcc.Graph(figure=fig_line_throughput_sgx_deg)]))
    if not skip_latency_graph:
        graph_list.append(
            html.Div([dcc.Graph(figure=fig_line_latency_sgx_deg)]))

    return [
        html.Div(graph_list, className="row"),
    ]


if __name__ == '__main__':
    app.run_server(debug=True, port=8050)
