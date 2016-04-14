import importscan
import dectate
from .fixtures import basic, pkg
import morepath

import pytest
from webtest import TestApp as Client


def test_rescan():
    importscan.scan(basic)
    dectate.commit(basic.app)
    importscan.scan(basic)

    class Sub(basic.app):
        pass

    @Sub.view(model=basic.Model, name='extra')
    def extra(self, request):
        return "extra"

    dectate.commit(Sub)

    c = Client(Sub())

    response = c.get('/1/extra')
    assert response.body == b'extra'

    response = c.get('/1')
    assert response.body == b'The view for model: 1'


def test_scanned_some_error():
    with pytest.raises(ZeroDivisionError):
        importscan.scan(pkg)
