import yaml
import ruamel.yaml


def load_task_info(task_info_path):
    with open(task_info_path) as task_info_file:
        task_info = yaml.safe_load(task_info_file)
    return task_info


def save_task_info(task_info, task_info_path):
    try:
        parsed_task_info = {
            "task": {}
        }
        parsed_task_info["task"]["id"] = task_info["task_id"]
        parsed_task_info["task"]["type"] = task_info["task_type"]
        parsed_task_info["task"]["start_time"] = task_info["task_start_time"]

        ruamel_yaml = ruamel.yaml.YAML()
        ruamel_yaml.preserve_quotes = True
        with open(task_info_path, "w") as settings_file:
            ruamel_yaml.dump(parsed_task_info, settings_file)
        return True
    except:
        return False
