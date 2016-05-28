import morepath
from morepath.error import ConflictError
import pytest


def setup_module(module):
    morepath.disable_implicit()


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
