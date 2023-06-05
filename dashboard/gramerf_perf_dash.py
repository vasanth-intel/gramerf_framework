import re
import pandas as pd
import plotly.express as px
import dash
from flask import Flask
from wsgiref.simple_server import make_server
import threading
import socket
from dash import html
from dash import dcc
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc

def update_test_name(test_name):
    return re.findall('.*perf_(.*)_.*', test_name)[0]

df = pd.ExcelFile("gramine_perf_data.xlsx")
port = 8050
server = Flask(__name__)
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets, server=server)
server = make_server(socket.gethostname(), port, server)

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
    df_workload.sort_values(by='Date', inplace=True)
    # df_workload["ww-commit"] = df_workload['commit'] + '-' +df_workload['ww'].astype(str)
    df_workload_throughput = df_workload[df_workload["model"].str.contains(
        "throughput")]

    df_workload_latency = df_workload[df_workload["model"].str.contains(
        "latency")]

    df_workload_throughput.model = df_workload_throughput.model.apply(
        update_test_name)
    df_workload_latency.model = df_workload_latency.model.apply(update_test_name)
    skip_throughput_graph = False
    if df_workload_throughput.empty:
        skip_throughput_graph = True

    if not skip_throughput_graph:
        fig_line_throughput_sgx_deg = px.line(df_workload_throughput, x="commit", y="SGX-DEG", color="model",
                                              labels={
                                                  "SGX-DEG": "Degradation(%)",
                                                  "commit": "Gramine commit"},
                                              title=workload + " throughput perf with Gramine SGX", markers=True)

    skip_latency_graph = False
    if df_workload_latency.empty:
        skip_latency_graph = True

    if not skip_latency_graph:
        fig_line_latency_sgx_deg = px.line(df_workload_latency, x="commit", y="SGX-DEG", color="model",
                                           labels={
                                               "SGX-DEG": "Degradation(%)",
                                               "commit": "Gramine commit"},
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


def start_execution():
    # create a server instance
    # start the server in a separate thread
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.start()

    # start the Dash app in a separate thread
    def start_dash_app():
        app.run_server(debug=True, use_reloader=False)

    dash_thread = threading.Thread(target=start_dash_app)
    dash_thread.start()
    print("started the dashboard")
