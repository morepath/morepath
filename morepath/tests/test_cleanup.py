import morepath
import dectate


def setup_module(module):
    morepath.disable_implicit()


def test_cleanup():
    class App(morepath.App):
        pass

    dectate.commit(App)

    # second commit should clean up after the first one, so we
    # expect no conflict errors
    dectate.commit(App)
