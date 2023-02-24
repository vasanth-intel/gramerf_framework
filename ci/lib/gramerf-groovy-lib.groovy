def g_isSklearn = false
def g_sklearnCounter = 0

def waitForNodeState(node_label){
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

def restartNode(node_label){
    node ("$node_label") {
        print "Rebooting $node_label........."
        if (isUnix()) {
            sh "sudo shutdown -r +1"
        } else {
            bat "shutdown /r /f"
        }
    }
    return waitForNodeState(node_label)
}

def getNodeName(){

    if (run_specific_perf_test.contains("ov") || run.contains("ov")){
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
        g_isSklearn = true
        return 'graphene_sklearn'
    }

}

def preActions(){

    // there is a bug in the active choice parameter reference variable which adds comma[,] character at the end
    if(build_gramine.endsWith(","))
    {
        build_gramine = build_gramine.substring(0,build_gramine.length() - 1);
    }
    if(gramine_repo_commit_id.endsWith(","))
    {
        gramine_repo_commit_id = gramine_repo_commit_id.substring(0,gramine_repo_commit_id.length() - 1);
    }
    if(encryption.endsWith(","))
    {
        encryption = encryption.substring(0,encryption.length() - 1).toBoolean();
    }
    if(performance_configuration.endsWith(","))
    {
        performance_configuration = performance_configuration.substring(0,performance_configuration.length() - 1);
    }

}

def run_perf(nodelabel){
    if (g_isSklearn) {
        exec_cmd = ''
        def args = "--ignore=gramine --disable-warnings --perf_config=${perf_config} --build_gramine=${build_gramine} --commit_id=${gramine_repo_commit_id} --exec_mode=${exec_mode}"
        if (!run_specific_perf_test?.trim()){
            exec_cmd = "python3 -m pytest -s -v -m $performance_configuration $args"
        } else {
            exec_cmd = "python3 -m pytest -s -v -k $run_specific_perf_test $args"
        }
        node ("$nodelabel") {
            cleanWs()
            checkout scm
        }
        for(int i=0; i<iterations.toInteger();i++) {
            sleep(time:60,unit:"SECONDS")
            node ("$nodelabel") {
                sh "echo $exec_cmd"
                stash includes: 'logs/*, results/*', name: "sklearn$i"
                g_sklearnCounter = i
            }
            restartNode(nodelabel)
            sleep(time:60,unit:"SECONDS")
        }
    } else {
        def args = "--ignore=gramine --disable-warnings --perf_config=${perf_config} --build_gramine=${build_gramine} --commit_id=${gramine_repo_commit_id} --iterations=${iterations} --exec_mode=${exec_mode}"
        echo "is encryption needed : $encryption"
        if (encryption) {
            args = args + " --encryption=1"
        }
        node ("$nodelabel") {
            cleanWs()
            checkout scm
            if (!run_specific_perf_test?.trim()){
                sh "python3 -m pytest -s -v -m $run $args"
            } else {
                echo " specific performance test $run_specific_perf_test will be executed"
                sh "python3 -m pytest -s -v -k $run_specific_perf_test $args"
            }
            stash includes: 'logs/*, results/*', name: 'perf_results'
        }
    }
}

def download_artifacts(){
    dir('report'){
        if(g_isSklearn){
            for(int i=0; i<g_sklearnCounter;i++) {
                unstash "sklearn$i"
            }
        } else {
            unstash 'perf_results'
            }
        }
    archiveArtifacts artifacts: 'report/*'
}

return this