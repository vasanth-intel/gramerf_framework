#
# Imports
#
from src.libs.Workload import Workload


def run_test(test_config_dict):

    test_obj = Workload(test_config_dict)
    
    # Install and build workload.
    if not test_obj.pre_actions(test_config_dict):
        return False

    return True
