"""Example settings python dictionary for Morepath.

It contains also 2 helper functions to create JSON and YAML config files
from this dictionary.
Note: create_yaml_config() does not produce very pretty YAML code.
"""

import json

try:
    import yaml  # noqa
    has_yaml = True
except ImportError:
    has_yaml = False


settings = {
    'chameleon': {
        'debug': True,
    },
    'jinja2': {
        'auto_reload': False,
        'autoescape': True,
        'extensions': [
            'jinja2.ext.autoescape',
            'jinja2.ext.i18n',
        ],
    },
    'jwtauth': {
        'algorithm': 'ES256',
        'leeway': 20,
        'public_key':
            'MIGbMBAGByqGSM49AgEGBSuBBAAjA4GGAAQBWcJwPEAnS/k4kFgUhxNF7J0SQQhZG'
            '+nNgy+/mXwhQ5PZIUmId1a1TjkNXiKzv6DpttBqduHbz/V0EtH+QfWy0B4BhZ5MnT'
            'yDGjcz1DQqKdexebhzobbhSIZjpYd5aU48o9rXp/OnAnrajddpGsJ0bNf4rtMLBqF'
            'YJN6LOslAB7xTBRg=',
    },
    'sqlalchemy': {
        'url': 'sqlite:///morepath.db',
    },
    'transaction': {
        'attempts': 2,
    },
}


def create_json_config():
        stream = file('settings.json', 'w')
        json.dump(settings, stream, sort_keys=True, indent=4,
                  separators=(',', ': '))
        print json.dumps(settings, sort_keys=True, indent=4,
                         separators=(',', ': '))


def create_yaml_config():
    if has_yaml:
        stream = file('settings.yaml', 'w')
        yaml.dump(settings, stream, default_flow_style=False, default_style='',
                  indent=4)
        print yaml.dump(settings, default_flow_style=False, default_style='',
                        indent=4)
    else:
        print "YAML could not be imported. Please install pyyaml first."
