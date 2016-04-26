import morepath
from .fixtures import basic, pkg, self_scan

import pytest
from webtest import TestApp as Client


def test_rescan():
    morepath.scan(basic)

    assert basic.app.commit() == {basic.app}

    morepath.scan(basic)

    class Sub(basic.app):
        pass

    @Sub.view(model=basic.Model, name='extra')
    def extra(self, request):
        return "extra"

    assert Sub.commit() == {Sub}

    c = Client(Sub())

    response = c.get('/1/extra')
    assert response.body == b'extra'

    response = c.get('/1')
    assert response.body == b'The view for model: 1'


def test_scanned_some_error():
    with pytest.raises(ZeroDivisionError):
        morepath.scan(pkg)


def test_caller_package_in_init():
    assert self_scan.get_this_package() == self_scan


def test_self_scanning_package():
    from .fixtures.self_scan.app import App

    # Importing the app as we did above imports the definition only,
    # without any logic.  Querying the app will fail.

    assert App.commit() == {App}
    c = Client(App())
    response = c.get('/', status=404)

    # By performing the scan, we import the module with the application logic:
    self_scan.do_scan()

    # The app needs now to be explicitly recommitted:
    assert App.commit() == {App}

    # Querying the app will now succeed
    c = Client(App())
    response = c.get('/')
    assert response.body == b'The root: ROOT'
