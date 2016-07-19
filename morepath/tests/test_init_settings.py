import pytest

import morepath
from morepath.error import ConflictError
from morepath.tests.fixtures.config import settings as settings_file


def test_init_settings():

    settings_dict = {
        'foo': {
            'enable_foo': True,
            'engine': 'ADVANCED'
        },
        'bar': {
            'space': 'huge',
            'security': False
        }
    }

    class App(morepath.App):
        pass

    App.init_settings(settings_dict)
    morepath.commit(App)

    app = App()

    assert app.settings.foo.enable_foo is True
    assert app.settings.foo.engine == 'ADVANCED'
    assert app.settings.bar.space == 'huge'
    assert app.settings.bar.security is False


def test_app_extends_settings():
    class Alpha(morepath.App):
        pass

    class Beta(Alpha):
        pass

    Alpha.init_settings({
        'foo': {
            'enable_foo': True,
            'engine': 'ADVANCED'
        },
    })

    Beta.init_settings({
        'bar': {
            'space': 'huge',
            'security': False
        }
    })

    morepath.commit(Alpha, Beta)

    alpha_inst = Alpha()
    settings = alpha_inst.settings

    assert settings.foo.engine == 'ADVANCED'
    with pytest.raises(AttributeError):
        settings.bar.space

    beta_inst = Beta()
    settings = beta_inst.settings

    assert settings.foo.engine == 'ADVANCED'
    assert settings.bar.space == 'huge'


def test_app_overrides_settings():
    class Alpha(morepath.App):
        pass

    class Beta(Alpha):
        pass

    Alpha.init_settings({
        'foo': {
            'enable_foo': True,
            'engine': 'ADVANCED'
        },
        'bar': {
            'space': 'huge',
            'security': False
        }
    })

    Beta.init_settings({
        'bar': {
            'space': 'tiny',
            'security': True
        }
    })

    morepath.commit(Alpha, Beta)

    alpha_inst = Alpha()
    settings = alpha_inst.settings

    assert settings.foo.engine == 'ADVANCED'
    assert settings.bar.space == 'huge'

    beta_inst = Beta()
    settings = beta_inst.settings

    assert settings.foo.engine == 'ADVANCED'
    assert settings.bar.space == 'tiny'


def test_section_settings_conflict():

    settings = {
        'foo': {
            'enable_foo': True,
            'engine': 'ADVANCED'
        },
        'bar': {
            'space': 'huge',
            'security': False
        }
    }

    class App(morepath.App):
        pass

    App.init_settings(settings)

    @App.setting('foo', 'engine')
    def get_foo_setting():
        return 'STANDARD'

    with pytest.raises(ConflictError):
        morepath.commit(App)


def test_extentions_settings():

    settings_dict = settings_file.settings

    class App(morepath.App):
        pass

    App.init_settings(settings_dict)
    morepath.commit(App)

    app = App()

    assert app.settings.chameleon.debug is True
    assert app.settings.jinja2.auto_reload is False
    assert app.settings.jinja2.autoescape is True
    assert app.settings.jinja2.extensions == [
        'jinja2.ext.autoescape',
        'jinja2.ext.i18n'
    ]
    assert app.settings.jwtauth.algorithm == 'ES256'
    assert app.settings.jwtauth.leeway == 20
    assert app.settings.jwtauth.public_key == \
        'MIGbMBAGByqGSM49AgEGBSuBBAAjA4GGAAQBWcJwPEAnS/k4kFgUhxNF7J0SQQhZG'\
        '+nNgy+/mXwhQ5PZIUmId1a1TjkNXiKzv6DpttBqduHbz/V0EtH+QfWy0B4BhZ5MnT'\
        'yDGjcz1DQqKdexebhzobbhSIZjpYd5aU48o9rXp/OnAnrajddpGsJ0bNf4rtMLBqF'\
        'YJN6LOslAB7xTBRg='
    assert app.settings.sqlalchemy.url == 'sqlite:///morepath.db'
    assert app.settings.transaction.attempts == 2
