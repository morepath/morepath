import morepath


def setup_module(module):
    morepath.disable_implicit()


def test_cleanup():
    config = morepath.setup()

    class app(morepath.App):
        testing_config = config

    config.commit()

    # second commit should clean up after the first one, so we
    # expect no conflict errors
    config.commit()


def test_configurables():
    config = morepath.setup()

    class app(morepath.App):
        testing_config = config

    assert config.configurables[0] is morepath.App.registry
    assert config.configurables[1] is app.registry
    assert len(config.configurables) == 2
