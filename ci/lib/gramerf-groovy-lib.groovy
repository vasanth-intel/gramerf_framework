def restartNode(node_label){

    node ("$node_label") {
        print "Rebooting $node_label........."
        if (isUnix()) {
            sh "sudo shutdown -r +1"
        } else {
            bat "shutdown /r /f"
        }
    }

    print "Waiting for the $node_label to reboot........."
    sleep(time:80,unit:"SECONDS")

    def numberOfAttemps = 0
    while (numberOfAttemps < 20) {
        if(Jenkins.instance.getNode(node_label).toComputer().isOnline()){
            print "Node $node_label is rebooted and ready to use"
            return true;
        }
        print "Waiting for the $node_label to reboot........."
        sleep(time:20,unit:"SECONDS")
        numberOfAttemps += 1
    }
    print "Node $node_label is not up running"
    return false
}

def getNodeName(){

    if ( node_name.isEmpty() ) {
        if (run_specific_perf_test.contains("ov") || run.contains("ov") || run_specific_perf_test.contains("ovms_perf") || run.contains("ovms_perf")){
            echo "open vino workload is selected ..."
            return 'graphene_wcity_02'
        } else if (run_specific_perf_test.contains("redis") || run.contains("redis")){
            echo "redis workload is selected ..."
            return 'graphene_perf_redis_taken_out_for_vasanth'
        } else if (run_specific_perf_test.contains("tf_serving") || run.contains("tf_serving")){
            echo "tf_serving workload is selected ..."
            return 'graphene_perf_redis_taken_out_for_vasanth'
        } else if (run_specific_perf_test.contains("tf") || run.contains("tf")){
            echo "tensorflow workload is selected ..."
            return 'graphene_wcity_02'
        } else if (run_specific_perf_test.contains("sklearnex") || run.contains("sklearnex")){
            echo "sklearn workload is selected ..."
            env.isSklearn = true
            return 'graphene_sklearn'
        } else if (run_specific_perf_test.contains("memcached") || run.contains("memcached")){
            echo "memcached workload is selected ..."
            return 'graphene_perf_redis_taken_out_for_vasanth'
        } else if (run_specific_perf_test.contains("pytorch_perf") || run.contains("pytorch_perf")){
            echo "pytorch workload is selected ..."
            return 'graphene_wcity_02'
        } else if (run_specific_perf_test.contains("mysql") || run.contains("mysql") || run_specific_perf_test.contains("mariadb_perf") || run.contains("mariadb_perf")){
            echo "mysql/mariadb workload is selected ..."
            return 'graphene_sklearn'
        } else if (run_specific_perf_test.contains("nginx_perf") || run.contains("nginx_perf")){
            echo "nginx_perf workload is selected ..."
            return 'graphene_sklearn'
        } else if (run_specific_perf_test.contains("specpower_perf") || run.contains("specpower_perf") || run_specific_perf_test.contains("mongodb_perf") || run.contains("mongodb_perf")){
            echo "specpower_perf workload is selected ..."
            return 'graphene_spec'
        }
    } else {
        echo "perf runs will be executed on $node_name"
        return node_name
    }

}

def preActions(){

    // there is a bug in the active choice parameter reference variable which adds comma[,] character at the end
    if(build_gramine.endsWith(","))
    {
        build_gramine = build_gramine.substring(0,build_gramine.length() - 1);
    }
    if(encryption.endsWith(","))
    {
        encryption = encryption.substring(0,encryption.length() - 1).toBoolean();
    }
    if(tmpfs.endsWith(","))
    {
        tmpfs = tmpfs.substring(0,tmpfs.length() - 1).toBoolean();
    }
    if(edmm.endsWith(","))
    {
        edmm = edmm.substring(0,edmm.length() - 1).toBoolean();
    }

}

def run_sklearn_perf(exec_cmd){
    sh "mkdir sklearn_reports"
    for(int i=0; i<iterations.toInteger();i++) {
        sh "$exec_cmd"
        sh "cp -rf logs/ results/ sklearn_reports"
        sleep(time:120,unit:"SECONDS")
    }
}

def get_sklearn_mean_report(){
    sh "echo generating sklearn mean report"
    sh "mkdir -p sklearn_reports/output"
    sh "cp -r sklearn_reports/results/*.xlsx sklearn_reports/output/"
    sh "python3 helper-files/sklearn_utility.py -i ./sklearn_reports/output -o ./sklearn_reports/mean"
    sh "rm -rf sklearn_reports/output"
}

return this