import yaml
import ruamel.yaml


def load_params(settings_path):
    with open(settings_path) as settings_file:
        settings = yaml.safe_load(settings_file)
    return settings


def save_params(settings, settings_path):
    try:
        ruamel_yaml = ruamel.yaml.YAML()
        ruamel_yaml.preserve_quotes = True
        with open(settings_path, "w") as settings_file:
            ruamel_yaml.dump(settings, settings_file)
        return True
    except:
        return False
