"""Example settings python dictionary for Morepath.

It contains also a helper function to create a JSON config file
from this dictionary.
"""

import json


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
        stream = open('settings.json', 'w')
        json.dump(settings, stream, sort_keys=True, indent=4,
                  separators=(',', ': '))
        print(json.dumps(settings, sort_keys=True, indent=4,
                         separators=(',', ': ')))
