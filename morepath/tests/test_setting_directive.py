import morepath
from morepath.error import ConflictError
import pytest
from webtest import TestApp as Client


def setup_module(module):
    morepath.disable_implicit()


def test_app_extends_settings():
    config = morepath.setup()

    alpha = morepath.App(testing_config=config)
    beta = morepath.App(extends=[alpha],
                        testing_config=config)

    @alpha.setting('one', 'foo')
    def get_foo_setting():
        return 'FOO'

    @beta.setting('one', 'bar')
    def get_bar_setting():
        return 'BAR'

    config.commit()

    assert alpha.settings.one.foo == 'FOO'
    with pytest.raises(AttributeError):
        assert alpha.settings.one.bar
    assert beta.settings.one.foo == 'FOO'
    assert beta.settings.one.bar == 'BAR'


def test_app_overrides_settings():
    config = morepath.setup()

    alpha = morepath.App(testing_config=config)
    beta = morepath.App(extends=[alpha],
                        testing_config=config)

    @alpha.setting('one', 'foo')
    def get_foo_setting():
        return 'FOO'

    @beta.setting('one', 'foo')
    def get_bar_setting():
        return 'OVERRIDE'

    config.commit()

    assert alpha.settings.one.foo == 'FOO'
    assert beta.settings.one.foo == 'OVERRIDE'


def test_app_overrides_settings_three():
    config = morepath.setup()

    alpha = morepath.App(testing_config=config)
    beta = morepath.App(extends=[alpha],
                        testing_config=config)
    gamma = morepath.App(extends=[beta], testing_config=config)

    @alpha.setting('one', 'foo')
    def get_foo_setting():
        return 'FOO'

    @beta.setting('one', 'foo')
    def get_bar_setting():
        return 'OVERRIDE'

    config.commit()

    assert gamma.settings.one.foo == 'OVERRIDE'


def test_app_section_settings():
    config = morepath.setup()

    app = morepath.App(testing_config=config)

    @app.setting_section('one')
    def settings():
        return {
            'foo': "FOO",
            'bar': "BAR"
            }

    config.commit()
    assert app.settings.one.foo == 'FOO'
    assert app.settings.one.bar == 'BAR'


def test_app_section_settings_conflict():
    config = morepath.setup()

    app = morepath.App(testing_config=config)

    @app.setting_section('one')
    def settings():
        return {
            'foo': "FOO",
            'bar': "BAR"
            }

    @app.setting('one', 'foo')
    def get_foo():
        return 'another'

    with pytest.raises(ConflictError):
        config.commit()


def test_settings_function():
    morepath.enable_implicit()

    config = morepath.setup()

    app = morepath.App(testing_config=config)

    @app.setting('section', 'name')
    def setting():
        return 'LAH'

    @app.path(path='')
    class Model(object):
        def __init__(self):
            pass

    @app.view(model=Model)
    def default(self, request):
        return morepath.settings().section.name

    config.commit()

    c = Client(app)

    response = c.get('/')
    assert response.body == b'LAH'
