from common.config_files.constants import *
import baremetal_benchmarking.workloads as baremetal_workloads
import docker_benchmarking.workloads as container_workloads


class Workload(object):
    """
    Base class for all workloads. Generic actions are taken here.
    All workload specific actions would be implemented in the respective
    derived workload class.
    """
    def __init__(self,
                 test_config_dict):
        self.name = test_config_dict['workload_name']
        self.command = None
        if (os.environ["perf_config"] == "container") and ("MySql" in test_config_dict['workload_name'] or "MariaDB" in test_config_dict['workload_name']):
            workload_script = "InMemoryDBWorkload"
        else:
            workload_script = test_config_dict['workload_name'] + "Workload"
        
        if os.environ["perf_config"] == "container":
            self.workload_class = getattr(globals()["container_workloads"], workload_script)
        else:
            self.workload_class = getattr(globals()["baremetal_workloads"], workload_script)
        print(self.workload_class)
        self.workload_obj = self.workload_class(test_config_dict)

    def pre_actions(self, test_config_dict):
        """
        Performs pre-actions for the workload.
        :param test_config_dict: Test config data
        :return:
        """
        self.workload_obj.pre_actions(test_config_dict)

    # setup_workload - implement in a subclass if needed
    def get_workload_home_dir(self):
        return self.workload_obj.get_workload_home_dir()

    # setup_workload - implement in a subclass if needed
    def setup_workload(self, test_config_dict):
        return self.workload_obj.setup_workload(test_config_dict)

    # execute_workload - implement in a subclass if needed
    def execute_workload(self, test_config_dict, e_mode, test_dict):
        self.workload_obj.execute_workload(test_config_dict, e_mode, test_dict)

    # update_test_results_in_global_dict - implement in a subclass if needed
    def update_test_results_in_global_dict(self, test_config_dict, test_dict):
        self.workload_obj.update_test_results_in_global_dict(test_config_dict, test_dict)

    # process_results - implement in a subclass if needed
    def process_results(self, test_config_dict):
        self.workload_obj.process_results(test_config_dict)
