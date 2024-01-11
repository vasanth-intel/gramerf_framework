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


def update_test_name(test_name):
    return re.findall('.*perf_(.*)_.*', test_name)[0]

def update_sklearn_test_name(test_name):
    return re.findall('.*perf_(.*)', test_name)[0]

df = pd.ExcelFile("gramine_perf_data.xlsx")
workload_sheet_name = sorted(df.sheet_names, key=str.lower)
port = 8050
server = Flask(__name__)
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets, server=server)
server = make_server(socket.gethostname(), port, server)

system_details = {}
system_details['Redis'] = html.P(['OS: Ubuntu 20.04.6 LTS', html.Br(), 'Kernel: 6.0.0-060000-generic',
                                 html.Br(), 'CPU(s): 152', html.Br(), 'Thread(s) per core: 2', html.Br(), 'Core(s) per Socket: 38'])
system_details['TensorFlow Serving'] = html.P(['OS: Ubuntu 20.04.6 LTS', html.Br(
), 'Kernel: 6.0.0-060000-generic', html.Br(), 'CPU(s): 152', html.Br(), 'Thread(s) per core: 2', html.Br(), 'Core(s) per Socket: 38'])
system_details['TensorFlow'] = html.P(['OS: Ubuntu 20.04.6 LTS', html.Br(), 'Kernel: 6.0.0-060000-generic', html.Br(
), 'CPU(s): 144', html.Br(), 'Thread(s) per core: 2', html.Br(), 'Core(s) per Socket: 36'])
system_details['OpenVINO'] = html.P(['OS: Ubuntu 20.04.6 LTS', html.Br(), 'Kernel: 6.0.0-060000-generic',
                                    html.Br(), 'CPU(s): 144', html.Br(), 'Thread(s) per core: 2', html.Br(), 'Core(s) per Socket: 36'])
system_details['Memcached'] = html.P(['OS: Ubuntu 20.04.6 LTS', html.Br(), 'Kernel: 6.0.0-060000-generic',
                                     html.Br(), 'CPU(s): 152', html.Br(), 'Thread(s) per core: 2', html.Br(), 'Core(s) per Socket: 38'])
system_details['MySQL'] = html.P(['OS: Ubuntu 20.04.6 LTS', html.Br(), 'Kernel: 6.0.0-060000-generic',
                                 html.Br(), 'CPU(s): 152', html.Br(), 'Thread(s) per core: 2', html.Br(), 'Core(s) per Socket: 38'])
system_details['scikit-learn'] = html.P(['OS: Ubuntu 20.04.6 LTS', html.Br(), 'Kernel: 6.0.0-060000-generic',
                                     html.Br(), 'CPU(s): 152', html.Br(), 'Thread(s) per core: 2', html.Br(), 'Core(s) per Socket: 38'])
system_details['TensorFlow Encrypted'] = html.P(['OS: Ubuntu 20.04.6 LTS', html.Br(), 'Kernel: 6.0.0-060000-generic',
                                                 html.Br(), 'CPU(s): 152', html.Br(), 'Thread(s) per core: 2', html.Br(), 'Core(s) per Socket: 38'])
system_details['MariaDB'] = html.P(['OS: Ubuntu 20.04.6 LTS', html.Br(), 'Kernel: 6.0.0-060000-generic',
                                 html.Br(), 'CPU(s): 152', html.Br(), 'Thread(s) per core: 2', html.Br(), 'Core(s) per Socket: 38'])
system_details['OpenVINO™ Model Server'] = html.P(['OS: Ubuntu 20.04.6 LTS', html.Br(), 'Kernel: 6.0.0-060000-generic',
                                    html.Br(), 'CPU(s): 144', html.Br(), 'Thread(s) per core: 2', html.Br(), 'Core(s) per Socket: 36'])
system_details['PyTorch'] = html.P(['OS: Ubuntu 20.04.6 LTS', html.Br(), 'Kernel: 6.0.0-060000-generic',
                                 html.Br(), 'CPU(s): 152', html.Br(), 'Thread(s) per core: 2', html.Br(), 'Core(s) per Socket: 38'])
system_details['NGINX'] = html.P(['OS: Ubuntu 20.04.6 LTS', html.Br(), 'Kernel: 6.0.0-060000-generic',
                                     html.Br(), 'CPU(s): 152', html.Br(), 'Thread(s) per core: 2', html.Br(), 'Core(s) per Socket: 38'])
system_details['SPECpower'] = html.P(['OS: Ubuntu 20.04.6 LTS', html.Br(), 'Kernel: 6.0.0-060000-generic',
                                     html.Br(), 'CPU(s): 128', html.Br(), 'Thread(s) per core: 2', html.Br(), 'Core(s) per Socket: 32'])

workload_details = {}
workload_details['TensorFlow'] = html.P(['TensorFlow: v2.4.0', html.Br(), 'Enclave size: 32GB'])
workload_details['Redis'] = html.P(['Redis: v6.0.5', html.Br(), 'Memtier benchmark: v1.3.0', html.Br(), 'Enclave size: 4GB'])
workload_details['OpenVINO'] = html.P(['OpenVino: v2021.4.2', html.Br(), 'Enclave size: 32GB'])
workload_details['MySQL'] = html.P(['MySQL: v8.0.32-debian (Docker image)', html.Br(), 'Enclave size: 4GB'])
workload_details['Memcached'] = html.P(['Memcached: v1.5.21', html.Br(), 'Memtier benchmark: v1.3.0', html.Br(), 'Enclave size: 4GB'])
workload_details['scikit-learn'] = html.P(['Scikit-Learn: v1.2.0', html.Br(), 'Scikit-learn-intelex: v2023.0.1', html.Br(), 'Enclave size: 64GB'])
workload_details['TensorFlow Serving'] = html.P(['TensorFlow Serving: intel-optimized-tensorflow-serving-avx512-ubuntu20.04', html.Br(), 'Enclave size: 64GB'])
workload_details['TensorFlow Encrypted'] = html.P(['TensorFlow : v2.4.0', html.Br(), 'Enclave size: 32GB'])
workload_details['MariaDB'] = html.P(['MariaDB', html.Br(), 'Enclave size: 2GB'])
workload_details['OpenVINO™ Model Server'] = html.P(['OpenVINO™ Model Server', html.Br(), 'Enclave size: 16GB'])
workload_details['PyTorch'] = html.P(['PyTorch', html.Br(), 'Enclave size: 4GB'])
workload_details['NGINX'] = html.P(['NGINX', html.Br(), 'Enclave size: 512MB'])
workload_details['SPECpower'] = html.P(['SPECpower : 2008-v1.12', html.Br(), 'Enclave size: 64GB'])

app.layout = html.Div([
    html.H1("Gramine Performance Dashboard",
            style={"textAlign": "center"}),

    html.Hr(),

    html.H4("Select workload"),
    html.Div(html.Div([
        dcc.Dropdown(id='workload', clearable=False,
                     value=workload_sheet_name[0],
                     options=workload_sheet_name),
    ], className="six columns"), className="row",),

    html.Hr(),

    html.Div(id="output-div", children=[]),
    html.Hr(),


])


@app.callback(Output(component_id="output-div", component_property="children"),
              Input(component_id="workload", component_property="value"),
              )
def make_graph(workload):

    df_workload = df.parse(workload)
    df_workload["datecommit"] = df_workload["Date"].astype(
        str) + ' ' + df_workload["commit"].astype(str)
    # sort the table by ww
    df_workload.sort_values(by='Date', inplace=True)

    # df_workload["ww-commit"] = df_workload['commit'] + '-' +df_workload['ww'].astype(str)
    df_workload_throughput = df_workload[df_workload["model"].str.contains(
        "throughput")]
    df_workload_latency = df_workload[df_workload["model"].str.contains(
        "latency")]

    if workload == "SPECpower":
        df_workload_throughput.model = df_workload_throughput.model.apply(update_sklearn_test_name)
    else:
        df_workload_throughput.model = df_workload_throughput.model.apply(update_test_name)
        df_workload_latency.model = df_workload_latency.model.apply(update_test_name)

    skip_throughput_graph = False
    if df_workload_throughput.empty:
        skip_throughput_graph = True

    if workload == "PyTorch":
        y_coordinate = ["GRAMINE-SGX_S0_DEG", "GRAMINE-SGX_S1_DEG"]
    else:
        y_coordinate = "SGX-DEG"

    if not skip_throughput_graph:
        fig_line_throughput_sgx_deg = px.line(df_workload_throughput, x="datecommit", y=y_coordinate, color="model",
                                              labels={
                                                  "SGX-DEG": "Degradation(%)"
                                              },
                                              hover_data={
                                                  'datecommit': False,
                                                  'commit': True
                                              },
                                              markers=True)
        if '2023-05-22' in set(df_workload_throughput['Date'].astype(str)):
            fig_line_throughput_sgx_deg.add_vrect(x0="0", x1="2023-05-22 ad39399", annotation_text="Green section represents perf data collection on Ubuntu18.04 distro", 
                                              annotation_position="top left", fillcolor="green", opacity=0.25, line_width=0, annotation_font_color="blue",
                                              annotation=dict(font_size=20, font_family="Times New Roman"))
        elif '2023-05-14' in set(df_workload_throughput['Date'].astype(str)):
            fig_line_throughput_sgx_deg.add_vrect(x0="0", x1="2023-05-14 9ead920", annotation_text="Green section represents perf data collection on Ubuntu18.04 distro", 
                                              annotation_position="top left", fillcolor="green", opacity=0.25, line_width=0, annotation_font_color="blue",
                                              annotation=dict(font_size=20, font_family="Times New Roman"))
        fig_line_throughput_sgx_deg.update_layout(title_text=workload + " throughput perf data using Gramine SGX", title_x=0.45, 
                                                  xaxis_title='Weekly Perf Run on latest Gramine Commit(YYYY-MM-DD commitID)<br>gramine commit history <a href="https://github.com/gramineproject/gramine/commits/master">link</a>',
                                                  yaxis_title="Degradation in % (Gramine SGX vs Linux Native)")


    skip_latency_graph = False
    if df_workload_latency.empty:
        skip_latency_graph = True

    if not skip_latency_graph:
        fig_line_latency_sgx_deg = px.line(df_workload_latency, x="datecommit", y=y_coordinate, color="model",
                                           labels={
                                               "SGX-DEG": "Degradation(%)"
                                           },
                                           hover_data={
                                               'datecommit': False,
                                               'commit': True
                                           },
                                           markers=True)
        if '2023-05-22' in set(df_workload_latency['Date'].astype(str)):
            fig_line_latency_sgx_deg.add_vrect(x0="0", x1="2023-05-22 ad39399", annotation_text="Green section represents perf data collection on Ubuntu18.04 distro", 
                                              annotation_position="top left", fillcolor="green", opacity=0.25, line_width=0, annotation_font_color="blue",
                                              annotation=dict(font_size=20, font_family="Times New Roman"))
        elif '2023-05-14' in set(df_workload_latency['Date'].astype(str)):
            fig_line_latency_sgx_deg.add_vrect(x0="0", x1="2023-05-14 9ead920", annotation_text="Green section represents perf data collection on Ubuntu18.04 distro", 
                                              annotation_position="top left", fillcolor="green", opacity=0.25, line_width=0, annotation_font_color="blue",
                                              annotation=dict(font_size=20, font_family="Times New Roman"))
        fig_line_latency_sgx_deg.update_layout(title_text=workload + " latency perf data using Gramine SGX", title_x=0.45, xaxis_title='Weekly Perf Run on latest Gramine Commit(YYYY-MM-DD commitID)<br>gramine commit history <a href="https://github.com/gramineproject/gramine/commits/master">link</a>',
                                               yaxis_title="Degradation in % (Gramine SGX vs Linux Native)")

    graph_list = []

    graph_list.append(html.Div(id="system_workload_info", children=[
        html.Div([
            html.Div([
                html.H4("System Details"),
                system_details[workload]
            ], className="six columns"),
            html.Div([
                html.H4("Workload Details"),
                workload_details[workload]
            ], className="six columns"),
        ], className="row"),
    ]))
    
    graph_list.append(html.Hr())

    if workload == "scikit-learn":
        df_workload.model = df_workload.model.apply(update_sklearn_test_name)
        fig_line_sklearn_latency_sgx_deg = px.line(df_workload, x="datecommit", y="SGX-DEG", color="model",
                                           labels={
                                               "SGX-DEG": "Degradation(%)"
                                           },
                                           hover_data={
                                               'datecommit': False,
                                               'commit': True
                                           },
                                           markers=True)
        fig_line_sklearn_latency_sgx_deg.update_layout(title_text=workload + " latency perf data using Gramine SGX", title_x=0.45, xaxis_title='Weekly Perf Run on latest Gramine Commit(YYYY-MM-DD commitID)<br>gramine commit history <a href="https://github.com/gramineproject/gramine/commits/master">link</a>', yaxis_title="Degradation in % (Gramine SGX vs Linux Native)")
        graph_list.append(
            html.Div([dcc.Graph(figure=fig_line_sklearn_latency_sgx_deg)]))

    if not skip_throughput_graph:
        graph_list.append(
            html.Div([dcc.Graph(figure=fig_line_throughput_sgx_deg)]))
        graph_list.append(html.Hr())
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
