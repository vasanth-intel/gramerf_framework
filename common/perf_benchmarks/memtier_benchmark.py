

def construct_client_exec_cmd(tcd, exec_mode = 'native'):
    client_ssh_cmd = None

    client_name = tcd['client_username'] + "@" + tcd['client_ip']
    benchmark_exec_mode = 'native'
    if exec_mode == 'gramine-direct':
        benchmark_exec_mode = 'gramine_direct'
    elif exec_mode == 'gramine-sgx':
        benchmark_exec_mode = 'gramine_sgx'
    elif exec_mode == 'gramine-sgx-exitless':
        benchmark_exec_mode = 'gramine_sgx_exitless'

    benchmark_exec_cmd = f"cd {tcd['client_scripts_path']} && ./start_benchmark.sh {benchmark_exec_mode} {tcd['test_name']} {tcd['data_size']} {tcd['rw_ratio']} {tcd['iterations']}"
    if tcd['workload_name'] == 'Memcached':
        benchmark_exec_cmd += " --protocol=memcache_binary --hide-histogram"
    
    client_ssh_cmd = f"sshpass -e ssh {client_name} '{benchmark_exec_cmd}'"

    print("\n-- Client command name = \n", client_ssh_cmd)

    return client_ssh_cmd