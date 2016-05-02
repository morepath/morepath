# -*- coding: utf-8 -*-

import dectate
import morepath
from morepath.converter import Converter
from morepath.error import (
    DirectiveReportError, ConfigError, LinkError, TrajectError)
from morepath.compat import text_type

from webtest import TestApp as Client
import pytest


def setup_module(module):
    morepath.disable_implicit()


def test_simple_path_one_step():
    class app(morepath.App):
        pass

    class Model(object):
        def __init__(self):
            pass

    @app.path(model=Model, path='simple')
    def get_model():
        return Model()

    @app.view(model=Model)
    def default(self, request):
        return "View"

    @app.view(model=Model, name='link')
    def link(self, request):
        return request.link(self)

    c = Client(app())

    response = c.get('/simple')
    assert response.body == b'View'

    response = c.get('/simple/link')
    assert response.body == b'http://localhost/simple'


def test_simple_path_two_steps():
    class app(morepath.App):
        pass

    class Model(object):
        def __init__(self):
            pass

    @app.path(model=Model, path='one/two')
    def get_model():
        return Model()

    @app.view(model=Model)
    def default(self, request):
        return "View"

    @app.view(model=Model, name='link')
    def link(self, request):
        return request.link(self)

    c = Client(app())

    response = c.get('/one/two')
    assert response.body == b'View'

    response = c.get('/one/two/link')
    assert response.body == b'http://localhost/one/two'


def test_variable_path_one_step():
    class app(morepath.App):
        pass

    class Model(object):
        def __init__(self, name):
            self.name = name

    @app.path(model=Model, path='{name}')
    def get_model(name):
        return Model(name)

    @app.view(model=Model)
    def default(self, request):
        return "View: %s" % self.name

    @app.view(model=Model, name='link')
    def link(self, request):
        return request.link(self)

    c = Client(app())

    response = c.get('/foo')
    assert response.body == b'View: foo'

    response = c.get('/foo/link')
    assert response.body == b'http://localhost/foo'


def test_variable_path_two_steps():
    class app(morepath.App):
        pass

    class Model(object):
        def __init__(self, name):
            self.name = name

    @app.path(model=Model, path='document/{name}')
    def get_model(name):
        return Model(name)

    @app.view(model=Model)
    def default(self, request):
        return "View: %s" % self.name

    @app.view(model=Model, name='link')
    def link(self, request):
        return request.link(self)

    c = Client(app())

    response = c.get('/document/foo')
    assert response.body == b'View: foo'

    response = c.get('/document/foo/link')
    assert response.body == b'http://localhost/document/foo'


def test_variable_path_two_variables():
    class app(morepath.App):
        pass

    class Model(object):
        def __init__(self, name, version):
            self.name = name
            self.version = version

    @app.path(model=Model, path='{name}-{version}')
    def get_model(name, version):
        return Model(name, version)

    @app.view(model=Model)
    def default(self, request):
        return "View: %s %s" % (self.name, self.version)

    @app.view(model=Model, name='link')
    def link(self, request):
        return request.link(self)

    c = Client(app())

    response = c.get('/foo-one')
    assert response.body == b'View: foo one'

    response = c.get('/foo-one/link')
    assert response.body == b'http://localhost/foo-one'


def test_variable_path_explicit_converter():
    class app(morepath.App):
        pass

    class Model(object):
        def __init__(self, id):
            self.id = id

    @app.path(model=Model, path='{id}',
              converters=dict(id=Converter(int)))
    def get_model(id):
        return Model(id)

    @app.view(model=Model)
    def default(self, request):
        return "View: %s (%s)" % (self.id, type(self.id))

    @app.view(model=Model, name='link')
    def link(self, request):
        return request.link(self)

    c = Client(app())

    response = c.get('/1')
    assert response.body in \
        (b"View: 1 (<type 'int'>)", b"View: 1 (<class 'int'>)")

    response = c.get('/1/link')
    assert response.body == b'http://localhost/1'

    response = c.get('/broken', status=404)


def test_variable_path_implicit_converter():
    class app(morepath.App):
        pass

    class Model(object):
        def __init__(self, id):
            self.id = id

    @app.path(model=Model, path='{id}')
    def get_model(id=0):
        return Model(id)

    @app.view(model=Model)
    def default(self, request):
        return "View: %s (%s)" % (self.id, type(self.id))

    @app.view(model=Model, name='link')
    def link(self, request):
        return request.link(self)

    c = Client(app())

    response = c.get('/1')
    assert response.body in \
        (b"View: 1 (<type 'int'>)", b"View: 1 (<class 'int'>)")

    response = c.get('/1/link')
    assert response.body == b'http://localhost/1'

    response = c.get('/broken', status=404)


def test_variable_path_explicit_trumps_implicit():
    class app(morepath.App):
        pass

    class Model(object):
        def __init__(self, id):
            self.id = id

    @app.path(model=Model, path='{id}',
              converters=dict(id=Converter(int)))
    def get_model(id='foo'):
        return Model(id)

    @app.view(model=Model)
    def default(self, request):
        return "View: %s (%s)" % (self.id, type(self.id))

    @app.view(model=Model, name='link')
    def link(self, request):
        return request.link(self)

    c = Client(app())

    response = c.get('/1')
    assert response.body in \
        (b"View: 1 (<type 'int'>)", b"View: 1 (<class 'int'>)")

    response = c.get('/1/link')
    assert response.body == b'http://localhost/1'

    response = c.get('/broken', status=404)


def test_url_parameter_explicit_converter():
    class app(morepath.App):
        pass

    class Model(object):
        def __init__(self, id):
            self.id = id

    @app.path(model=Model, path='/',
              converters=dict(id=Converter(int)))
    def get_model(id):
        return Model(id)

    @app.view(model=Model)
    def default(self, request):
        return "View: %s (%s)" % (self.id, type(self.id))

    @app.view(model=Model, name='link')
    def link(self, request):
        return request.link(self)

    c = Client(app())

    response = c.get('/?id=1')
    assert response.body in \
        (b"View: 1 (<type 'int'>)", b"View: 1 (<class 'int'>)")

    response = c.get('/link?id=1')
    assert response.body == b'http://localhost/?id=1'

    response = c.get('/?id=broken', status=400)

    response = c.get('/')
    assert response.body in \
        (b"View: None (<type 'NoneType'>)", b"View: None (<class 'NoneType'>)")


def test_url_parameter_explicit_converter_get_converters():
    class app(morepath.App):
        pass

    class Model(object):
        def __init__(self, id):
            self.id = id

    def get_converters():
        return dict(id=Converter(int))

    @app.path(model=Model, path='/', get_converters=get_converters)
    def get_model(id):
        return Model(id)

    @app.view(model=Model)
    def default(self, request):
        return "View: %s (%s)" % (self.id, type(self.id))

    @app.view(model=Model, name='link')
    def link(self, request):
        return request.link(self)

    c = Client(app())

    response = c.get('/?id=1')
    assert response.body in \
        (b"View: 1 (<type 'int'>)", b"View: 1 (<class 'int'>)")

    response = c.get('/link?id=1')
    assert response.body == b'http://localhost/?id=1'

    response = c.get('/?id=broken', status=400)

    response = c.get('/')
    assert response.body in \
        (b"View: None (<type 'NoneType'>)", b"View: None (<class 'NoneType'>)")


def test_url_parameter_get_converters_overrides_converters():
    class app(morepath.App):
        pass

    class Model(object):
        def __init__(self, id):
            self.id = id

    def get_converters():
        return dict(id=Converter(int))

    @app.path(model=Model, path='/', converters={id: type(u"")},
              get_converters=get_converters)
    def get_model(id):
        return Model(id)

    @app.view(model=Model)
    def default(self, request):
        return "View: %s (%s)" % (self.id, type(self.id))

    @app.view(model=Model, name='link')
    def link(self, request):
        return request.link(self)

    c = Client(app())

    response = c.get('/?id=1')
    assert response.body in \
        (b"View: 1 (<type 'int'>)", b"View: 1 (<class 'int'>)")

    response = c.get('/link?id=1')
    assert response.body == b'http://localhost/?id=1'

    response = c.get('/?id=broken', status=400)

    response = c.get('/')
    assert response.body in \
        (b"View: None (<type 'NoneType'>)", b"View: None (<class 'NoneType'>)")


def test_url_parameter_implicit_converter():
    class app(morepath.App):
        pass

    class Model(object):
        def __init__(self, id):
            self.id = id

    @app.path(model=Model, path='/')
    def get_model(id=0):
        return Model(id)

    @app.view(model=Model)
    def default(self, request):
        return "View: %s (%s)" % (self.id, type(self.id))

    @app.view(model=Model, name='link')
    def link(self, request):
        return request.link(self)

    c = Client(app())

    response = c.get('/?id=1')
    assert response.body in \
        (b"View: 1 (<type 'int'>)", b"View: 1 (<class 'int'>)")

    response = c.get('/link?id=1')
    assert response.body == b'http://localhost/?id=1'

    response = c.get('/?id=broken', status=400)

    response = c.get('/')
    assert response.body in \
        (b"View: 0 (<type 'int'>)", b"View: 0 (<class 'int'>)")


def test_url_parameter_explicit_trumps_implicit():
    class app(morepath.App):
        pass

    class Model(object):
        def __init__(self, id):
            self.id = id

    @app.path(model=Model, path='/',
              converters=dict(id=Converter(int)))
    def get_model(id='foo'):
        return Model(id)

    @app.view(model=Model)
    def default(self, request):
        return "View: %s (%s)" % (self.id, type(self.id))

    @app.view(model=Model, name='link')
    def link(self, request):
        return request.link(self)

    c = Client(app())

    response = c.get('/?id=1')
    assert response.body in \
        (b"View: 1 (<type 'int'>)", b"View: 1 (<class 'int'>)")

    response = c.get('/link?id=1')
    assert response.body == b'http://localhost/?id=1'

    response = c.get('/?id=broken', status=400)

    response = c.get('/')
    assert response.body in \
        (b"View: foo (<type 'str'>)", b"View: foo (<class 'str'>)")


def test_decode_encode():
    class app(morepath.App):
        pass

    class Model(object):
        def __init__(self, id):
            self.id = id

    def my_decode(s):
        return s + 'ADD'

    def my_encode(s):
        return s[:-len('ADD')]

    @app.path(model=Model, path='/',
              converters=dict(id=Converter(my_decode, my_encode)))
    def get_model(id):
        return Model(id)

    @app.view(model=Model)
    def default(self, request):
        return "View: %s" % self.id

    @app.view(model=Model, name='link')
    def link(self, request):
        return request.link(self)

    c = Client(app())

    response = c.get('/?id=foo')
    assert response.body == b"View: fooADD"

    response = c.get('/link?id=foo')
    assert response.body == b'http://localhost/?id=foo'


def test_unknown_converter():
    class app(morepath.App):
        pass

    class Model(object):
        def __init__(self, d):
            self.d = d

    class Unknown(object):
        pass

    @app.path(model=Model, path='/')
    def get_model(d=Unknown()):
        return Model(d)

    @app.view(model=Model)
    def default(self, request):
        return "View: %s" % self.d

    @app.view(model=Model, name='link')
    def link(self, request):
        return request.link(self)

    with pytest.raises(DirectiveReportError):
        app.commit()


def test_unknown_explicit_converter():
    class app(morepath.App):
        pass

    class Model(object):
        def __init__(self, d):
            self.d = d

    class Unknown(object):
        pass

    @app.path(model=Model, path='/', converters={'d': Unknown})
    def get_model(d):
        return Model(d)

    @app.view(model=Model)
    def default(self, request):
        return "View: %s" % self.d

    @app.view(model=Model, name='link')
    def link(self, request):
        return request.link(self)

    with pytest.raises(DirectiveReportError):
        app.commit()


def test_default_date_converter():
    class app(morepath.App):
        pass

    class Model(object):
        def __init__(self, d):
            self.d = d

    from datetime import date

    @app.path(model=Model, path='/')
    def get_model(d=date(2011, 1, 1)):
        return Model(d)

    @app.view(model=Model)
    def default(self, request):
        return "View: %s" % self.d

    @app.view(model=Model, name='link')
    def link(self, request):
        return request.link(self)

    c = Client(app())

    response = c.get('/?d=20121110')
    assert response.body == b"View: 2012-11-10"

    response = c.get('/')
    assert response.body == b"View: 2011-01-01"

    response = c.get('/link?d=20121110')
    assert response.body == b'http://localhost/?d=20121110'

    response = c.get('/link')
    assert response.body == b'http://localhost/?d=20110101'

    response = c.get('/?d=broken', status=400)


def test_default_datetime_converter():
    class app(morepath.App):
        pass

    class Model(object):
        def __init__(self, d):
            self.d = d

    from datetime import datetime

    @app.path(model=Model, path='/')
    def get_model(d=datetime(2011, 1, 1, 10, 30)):
        return Model(d)

    @app.view(model=Model)
    def default(self, request):
        return "View: %s" % self.d

    @app.view(model=Model, name='link')
    def link(self, request):
        return request.link(self)

    c = Client(app())

    response = c.get('/?d=20121110T144530')
    assert response.body == b"View: 2012-11-10 14:45:30"

    response = c.get('/')
    assert response.body == b"View: 2011-01-01 10:30:00"

    response = c.get('/link?d=20121110T144500')
    assert response.body == b'http://localhost/?d=20121110T144500'

    response = c.get('/link')
    assert response.body == b'http://localhost/?d=20110101T103000'

    c.get('/?d=broken', status=400)


def test_custom_date_converter():
    class app(morepath.App):
        pass

    class Model(object):
        def __init__(self, d):
            self.d = d

    from datetime import date
    from time import strptime, mktime

    def date_decode(s):
        return date.fromtimestamp(mktime(strptime(s, '%d-%m-%Y')))

    def date_encode(d):
        return d.strftime('%d-%m-%Y')

    @app.converter(type=date)
    def date_converter():
        return Converter(date_decode, date_encode)

    @app.path(model=Model, path='/')
    def get_model(d=date(2011, 1, 1)):
        return Model(d)

    @app.view(model=Model)
    def default(self, request):
        return "View: %s" % self.d

    @app.view(model=Model, name='link')
    def link(self, request):
        return request.link(self)

    c = Client(app())

    response = c.get('/?d=10-11-2012')
    assert response.body == b"View: 2012-11-10"

    response = c.get('/')
    assert response.body == b"View: 2011-01-01"

    response = c.get('/link?d=10-11-2012')
    assert response.body == b'http://localhost/?d=10-11-2012'

    response = c.get('/link')
    assert response.body == b'http://localhost/?d=01-01-2011'

    response = c.get('/?d=broken', status=400)


def test_variable_path_parameter_required_no_default():
    class app(morepath.App):
        pass

    class Model(object):
        def __init__(self, id):
            self.id = id

    @app.path(model=Model, path='', required=['id'])
    def get_model(id):
        return Model(id)

    @app.view(model=Model)
    def default(self, request):
        return "View: %s" % self.id

    @app.view(model=Model, name='link')
    def link(self, request):
        return request.link(self)

    c = Client(app())

    response = c.get('/?id=a')
    assert response.body == b"View: a"

    response = c.get('/', status=400)


def test_variable_path_parameter_required_with_default():
    class app(morepath.App):
        pass

    class Model(object):
        def __init__(self, id):
            self.id = id

    @app.path(model=Model, path='', required=['id'])
    def get_model(id='b'):
        return Model(id)

    @app.view(model=Model)
    def default(self, request):
        return "View: %s" % self.id

    @app.view(model=Model, name='link')
    def link(self, request):
        return request.link(self)

    c = Client(app())

    response = c.get('/?id=a')
    assert response.body == b"View: a"

    response = c.get('/', status=400)


def test_type_hints_and_converters():
    class app(morepath.App):
        pass

    class Model(object):
        def __init__(self, d):
            self.d = d

    from datetime import date

    @app.path(model=Model, path='', converters=dict(d=date))
    def get_model(d):
        return Model(d)

    @app.view(model=Model)
    def default(self, request):
        return "View: %s" % self.d

    @app.view(model=Model, name='link')
    def link(self, request):
        return request.link(self)

    c = Client(app())

    response = c.get('/?d=20140120')
    assert response.body == b"View: 2014-01-20"

    response = c.get('/link?d=20140120')
    assert response.body == b'http://localhost/?d=20140120'


def test_link_for_none_means_no_parameter():
    class app(morepath.App):
        pass

    class Model(object):
        def __init__(self, id):
            self.id = id

    @app.path(model=Model, path='')
    def get_model(id):
        return Model(id)

    @app.view(model=Model)
    def default(self, request):
        return "View: %s" % self.id

    @app.view(model=Model, name='link')
    def link(self, request):
        return request.link(self)

    c = Client(app())

    response = c.get('/')
    assert response.body == b"View: None"

    response = c.get('/link')
    assert response.body == b'http://localhost/'


def test_path_and_url_parameter_converter():
    class app(morepath.App):
        pass

    class Model(object):
        def __init__(self, id, param):
            self.id = id
            self.param = param

    from datetime import date

    @app.path(model=Model, path='/{id}', converters=dict(param=date))
    def get_model(id=0, param=None):
        return Model(id, param)

    @app.view(model=Model)
    def default(self, request):
        return "View: %s %s" % (self.id, self.param)

    @app.view(model=Model, name='link')
    def link(self, request):
        return request.link(self)

    c = Client(app())

    response = c.get('/1/link')
    assert response.body == b'http://localhost/1'


def test_path_converter_fallback_on_view():
    class app(morepath.App):
        pass

    class Root(object):
        pass

    class Model(object):
        def __init__(self, id):
            self.id = id

    @app.path(model=Root, path='')
    def get_root():
        return Root()

    @app.path(model=Model, path='/{id}')
    def get_model(id=0):
        return Model(id)

    @app.view(model=Model)
    def default(self, request):
        return "Default view for %s" % self.id

    @app.view(model=Root, name='named')
    def named(self, request):
        return "Named view on root"

    c = Client(app())

    response = c.get('/1')
    assert response.body == b'Default view for 1'
    response = c.get('/named')
    assert response.body == b'Named view on root'


def test_root_named_link():
    class app(morepath.App):
        pass

    @app.path(path='')
    class Root(object):
        pass

    @app.view(model=Root)
    def default(self, request):
        return request.link(self, 'foo')

    c = Client(app())

    response = c.get('/')
    assert response.body == b'http://localhost/foo'


def test_path_class_and_model_argument():
    class app(morepath.App):
        pass

    class Foo(object):
        pass

    @app.path(path='', model=Foo)
    class Root(object):
        pass

    with pytest.raises(ConfigError):
        app.commit()


def test_path_no_class_and_no_model_argument():
    class app(morepath.App):
        pass

    @app.path(path='')
    def get_foo():
        return None

    with pytest.raises(ConfigError):
        app.commit()


def test_url_parameter_list():
    class app(morepath.App):
        pass

    class Model(object):
        def __init__(self, item):
            self.item = item

    @app.path(model=Model, path='/', converters={'item': [int]})
    def get_model(item):
        return Model(item)

    @app.view(model=Model)
    def default(self, request):
        return repr(self.item)

    @app.view(model=Model, name='link')
    def link(self, request):
        return request.link(self)

    c = Client(app())

    response = c.get('/?item=1&item=2')
    assert response.body == b"[1, 2]"

    response = c.get('/link?item=1&item=2')
    assert response.body == b'http://localhost/?item=1&item=2'

    response = c.get('/link')
    assert response.body == b'http://localhost/'

    response = c.get('/?item=broken&item=1', status=400)

    response = c.get('/')
    assert response.body == b"[]"


def test_url_parameter_list_empty():
    class app(morepath.App):
        pass

    class Model(object):
        def __init__(self, item):
            self.item = item

    @app.path(model=Model, path='/', converters={'item': []})
    def get_model(item):
        return Model(item)

    @app.view(model=Model)
    def default(self, request):
        return repr(self.item)

    @app.view(model=Model, name='link')
    def link(self, request):
        return request.link(self)

    c = Client(app())

    response = c.get('/?item=a&item=b')
    assert response.body in (b"[u'a', u'b']", b"['a', 'b']")

    response = c.get('/link?item=a&item=b')
    assert response.body == b'http://localhost/?item=a&item=b'

    response = c.get('/link')
    assert response.body == b'http://localhost/'

    response = c.get('/')
    assert response.body == b"[]"


def test_url_parameter_list_explicit_converter():
    class app(morepath.App):
        pass

    class Model(object):
        def __init__(self, item):
            self.item = item

    @app.path(model=Model, path='/', converters={'item': [Converter(int)]})
    def get_model(item):
        return Model(item)

    @app.view(model=Model)
    def default(self, request):
        return repr(self.item)

    @app.view(model=Model, name='link')
    def link(self, request):
        return request.link(self)

    c = Client(app())

    response = c.get('/?item=1&item=2')
    assert response.body == b"[1, 2]"

    response = c.get('/link?item=1&item=2')
    assert response.body == b'http://localhost/?item=1&item=2'

    response = c.get('/link')
    assert response.body == b'http://localhost/'

    response = c.get('/?item=broken&item=1', status=400)

    response = c.get('/')
    assert response.body == b"[]"


def test_url_parameter_list_unknown_explicit_converter():
    class app(morepath.App):
        pass

    class Model(object):
        def __init__(self, item):
            self.item = item

    class Unknown(object):
        pass

    @app.path(model=Model, path='/', converters={'item': [Unknown]})
    def get_model(item):
        return Model(item)

    with pytest.raises(DirectiveReportError):
        app.commit()


def test_url_parameter_list_but_only_one_allowed():
    class app(morepath.App):
        pass

    class Model(object):
        def __init__(self, item):
            self.item = item

    @app.path(model=Model, path='/', converters={'item': int})
    def get_model(item):
        return Model(item)

    @app.view(model=Model)
    def default(self, request):
        return repr(self.item)

    @app.view(model=Model, name='link')
    def link(self, request):
        return request.link(self)

    c = Client(app())

    c.get('/?item=1&item=2', status=400)

    c.get('/link?item=1&item=2', status=400)


def test_extra_parameters():
    class app(morepath.App):
        pass

    class Model(object):
        def __init__(self, extra_parameters):
            self.extra_parameters = extra_parameters

    @app.path(model=Model, path='/')
    def get_model(extra_parameters):
        return Model(extra_parameters)

    @app.view(model=Model)
    def default(self, request):
        return repr(sorted(self.extra_parameters.items()))

    @app.view(model=Model, name='link')
    def link(self, request):
        return request.link(self)

    c = Client(app())

    response = c.get('/?a=A&b=B')
    assert response.body in \
        (b"[(u'a', u'A'), (u'b', u'B')]", b"[('a', 'A'), ('b', 'B')]")
    response = c.get('/link?a=A&b=B')
    assert sorted(response.body[len('http://localhost/?'):].split(b"&")) == [
        b'a=A', b'b=B']


def test_extra_parameters_with_get_converters():
    class app(morepath.App):
        pass

    class Model(object):
        def __init__(self, extra_parameters):
            self.extra_parameters = extra_parameters

    def get_converters():
        return {
            'a': int,
            'b': type(u""),
        }

    @app.path(model=Model, path='/', get_converters=get_converters)
    def get_model(extra_parameters):
        return Model(extra_parameters)

    @app.view(model=Model)
    def default(self, request):
        return repr(sorted(self.extra_parameters.items()))

    @app.view(model=Model, name='link')
    def link(self, request):
        return request.link(self)

    c = Client(app())

    response = c.get('/?a=1&b=B')
    assert response.body in \
        (b"[(u'a', 1), (u'b', u'B')]", b"[('a', 1), ('b', 'B')]")
    response = c.get('/link?a=1&b=B')
    assert sorted(response.body[len('http://localhost/?'):].split(b"&")) == [
        b'a=1', b'b=B']

    c.get('/?a=broken&b=B', status=400)


def test_script_name():
    class app(morepath.App):
        pass

    class Model(object):
        def __init__(self):
            pass

    @app.path(model=Model, path='simple')
    def get_model():
        return Model()

    @app.view(model=Model)
    def default(self, request):
        return "View"

    @app.view(model=Model, name='link')
    def link(self, request):
        return request.link(self)

    c = Client(app())

    response = c.get('/prefix/simple',
                     extra_environ=dict(SCRIPT_NAME='/prefix'))
    assert response.body == b'View'

    response = c.get('/prefix/simple/link',
                     extra_environ=dict(SCRIPT_NAME='/prefix'))
    assert response.body == b'http://localhost/prefix/simple'


def test_sub_path_different_variable():
    # See discussion in https://github.com/morepath/morepath/issues/155

    class App(morepath.App):
        pass

    class Master(object):
        def __init__(self, id):
            self.id = id

    class Slave(object):
        def __init__(self, id, master):
            self.id = id
            self.master = master

    @App.path(model=Master, path='{id}')
    def get_master(id):
        return Master(id)

    @App.path(model=Slave, path='{master_id}/{slave_id}')
    def get_slave(master_id, slave_id):
        return Slave(slave_id, Master(master_id))

    @App.view(model=Master)
    def default_master(self, request):
        return "M: %s" % self.id

    @App.view(model=Slave)
    def default_slave(self, request):
        return "S: %s %s" % (self.id, self.master.id)

    c = Client(App())

    with pytest.raises(TrajectError) as ex:
        response = c.get('/a')
        assert response.body == b'M: a'

        response = c.get('/a/b')
        assert response.body == b'S: b a'

    assert str(ex.value) == 'step {id} and {master_id} are in conflict'


def test_absorb_path():
    class app(morepath.App):
        pass

    class Root(object):
        pass

    class Model(object):
        def __init__(self, absorb):
            self.absorb = absorb

    @app.path(model=Root, path='')
    def get_root():
        return Root()

    @app.path(model=Model, path='foo', absorb=True)
    def get_model(absorb):
        return Model(absorb)

    @app.view(model=Model)
    def default(self, request):
        return "%s" % self.absorb

    @app.view(model=Root)
    def default_root(self, request):
        return request.link(Model('a/b'))

    c = Client(app())

    response = c.get('/foo/a')
    assert response.body == b'a'

    response = c.get('/foo')
    assert response.body == b''

    response = c.get('/foo/a/b')
    assert response.body == b'a/b'

    # link to a/b absorb
    response = c.get('/')
    assert response.body == b'http://localhost/foo/a/b'


def test_absorb_path_with_variables():
    class app(morepath.App):
        pass

    class Root(object):
        pass

    class Model(object):
        def __init__(self, id, absorb):
            self.id = id
            self.absorb = absorb

    @app.path(model=Root, path='')
    def get_root():
        return Root()

    @app.path(model=Model, path='{id}', absorb=True)
    def get_model(id, absorb):
        return Model(id, absorb)

    @app.view(model=Model)
    def default(self, request):
        return "I:%s A:%s" % (self.id, self.absorb)

    @app.view(model=Root)
    def default_root(self, request):
        return request.link(Model('foo', 'a/b'))

    c = Client(app())

    response = c.get('/foo/a')
    assert response.body == b'I:foo A:a'

    response = c.get('/foo')
    assert response.body == b'I:foo A:'

    response = c.get('/foo/a/b')
    assert response.body == b'I:foo A:a/b'

    # link to a/b absorb
    response = c.get('/')
    assert response.body == b'http://localhost/foo/a/b'


def test_absorb_path_explicit_subpath_ignored():
    class app(morepath.App):
        pass

    class Root(object):
        pass

    class Model(object):
        def __init__(self, absorb):
            self.absorb = absorb

    class Another(object):
        pass

    @app.path(model=Root, path='')
    def get_root():
        return Root()

    @app.path(model=Model, path='foo', absorb=True)
    def get_model(absorb):
        return Model(absorb)

    @app.path(model=Another, path='foo/another')
    def get_another():
        return Another()

    @app.view(model=Model)
    def default(self, request):
        return "%s" % self.absorb

    @app.view(model=Another)
    def default_another(self, request):
        return "Another"

    @app.view(model=Root)
    def default_root(self, request):
        return request.link(Another())

    c = Client(app())

    response = c.get('/foo/a')
    assert response.body == b'a'

    response = c.get('/foo/another')
    assert response.body == b'another'

    # link to another still works XXX is this wrong?
    response = c.get('/')
    assert response.body == b'http://localhost/foo/another'


def test_absorb_path_root():
    class app(morepath.App):
        pass

    class Model(object):
        def __init__(self, absorb):
            self.absorb = absorb

    @app.path(model=Model, path='', absorb=True)
    def get_model(absorb):
        return Model(absorb)

    @app.view(model=Model)
    def default(self, request):
        return "A:%s L:%s" % (self.absorb, request.link(self))

    c = Client(app())

    response = c.get('/a')
    assert response.body == b'A:a L:http://localhost/a'

    response = c.get('/')
    assert response.body == b'A: L:http://localhost/'

    response = c.get('/a/b')
    assert response.body == b'A:a/b L:http://localhost/a/b'


def test_error_when_path_variable_is_none():
    class App(morepath.App):
        pass

    class Model(object):
        def __init__(self, id):
            self.store_id = id

    @App.path(model=Model, path='models/{id}',
              variables=lambda m: {'id': None})
    def get_model(id):
        return Model(id)

    @App.view(model=Model)
    def default(self, request):
        return request.link(self)

    c = Client(App())

    with pytest.raises(LinkError):
        c.get('/models/1')


def test_error_when_path_variable_is_missing():
    class App(morepath.App):
        pass

    class Model(object):
        def __init__(self, id):
            self.store_id = id

    @App.path(model=Model, path='models/{id}',
              variables=lambda m: {})
    def get_model(id):
        return Model(id)

    @App.view(model=Model)
    def default(self, request):
        return request.link(self)

    c = Client(App())

    with pytest.raises(KeyError):
        c.get('/models/1')


def test_error_when_path_variables_isnt_dict():
    class App(morepath.App):
        pass

    class Model(object):
        def __init__(self, id):
            self.store_id = id

    @App.path(model=Model, path='models/{id}',
              variables=lambda m: 'nondict')
    def get_model(id):
        return Model(id)

    @App.view(model=Model)
    def default(self, request):
        return request.link(self)

    c = Client(App())

    with pytest.raises(LinkError):
        c.get('/models/1')


def test_resolve_path_method_on_request_same_app():
    class App(morepath.App):
        pass

    class Model(object):
        def __init__(self):
            pass

    @App.path(model=Model, path='simple')
    def get_model():
        return Model()

    @App.view(model=Model)
    def default(self, request):
        return text_type(isinstance(request.resolve_path('simple'), Model))

    @App.view(model=Model, name='extra')
    def extra(self, request):
        return text_type(request.resolve_path('nonexistent') is None)

    @App.view(model=Model, name='appnone')
    def appnone(self, request):
        return request.resolve_path('simple', app=None)

    c = Client(App())

    response = c.get('/simple')
    assert response.body == b'True'
    response = c.get('/simple/extra')
    assert response.body == b'True'
    with pytest.raises(LinkError):
        c.get('/simple/appnone')


def test_resolve_path_method_on_request_different_app():
    class App(morepath.App):
        pass

    class Model(object):
        def __init__(self):
            pass

    @App.path(model=Model, path='simple')
    def get_model():
        return Model()

    @App.view(model=Model)
    def default(self, request):
        obj = request.resolve_path('p', app=request.app.child('sub'))
        return text_type(isinstance(obj, SubModel))

    class Sub(morepath.App):
        pass

    class SubModel(object):
        pass

    @Sub.path(model=SubModel, path='p')
    def get_sub_model():
        return SubModel()

    @App.mount(path='sub', app=Sub)
    def mount_sub():
        return Sub()

    c = Client(App())

    response = c.get('/simple')
    assert response.body == b'True'


def test_resolve_path_with_dots_in_url():
    class app(morepath.App):
        pass

    class Root(object):
        def __init__(self, absorb):
            self.absorb = absorb

    @app.path(model=Root, path='root', absorb=True)
    def get_root(absorb):
        return Root(absorb)

    @app.view(model=Root)
    def default(self, request):
        return "%s" % self.absorb

    c = Client(app())

    response = c.get('/root/x/../child')
    assert response.body == b'child'

    response = c.get('/root/x/%2E%2E/child')
    assert response.body == b'child'

    response = c.get('/root/%2E%2E/%2E%2E/root')
    assert response.body == b''

    response = c.get('/root/%2E%2E/%2E%2E/root')
    assert response.body == b''

    response = c.get('/root/%2E%2E/%2E%2E/test', expect_errors=True)
    assert response.status_code == 404


def test_quoting_link_generation():
    class App(morepath.App):
        pass

    class Model(object):
        def __init__(self):
            pass

    @App.path(model=Model, path='sim?ple')
    def get_model():
        return Model()

    @App.view(model=Model)
    def default(self, request):
        return "View"

    @App.view(model=Model, name='link')
    def link(self, request):
        return request.link(self)

    c = Client(App())

    response = c.get('/sim%3Fple')
    assert response.body == b'View'

    response = c.get('/sim%3Fple/link')
    assert response.body == b'http://localhost/sim%3Fple'


def test_quoting_link_generation_umlaut():
    class App(morepath.App):
        pass

    class Model(object):
        def __init__(self):
            pass

    @App.path(model=Model, path=u'simëple')
    def get_model():
        return Model()

    @App.view(model=Model)
    def default(self, request):
        return "View"

    @App.view(model=Model, name='link')
    def link(self, request):
        return request.link(self)

    c = Client(App())

    response = c.get('/sim%C3%ABple')
    assert response.body == b'View'

    response = c.get('/sim%C3%ABple/link')
    assert response.body == b'http://localhost/sim%C3%ABple'


def test_quoting_link_generation_tilde():
    # tilde is an unreserved character according to
    # https://www.ietf.org/rfc/rfc3986.txt but urllib.quote
    # quotes it anyway. We test whether our workaround using
    # the safe parameter works

    class App(morepath.App):
        pass

    class Model(object):
        def __init__(self):
            pass

    @App.path(model=Model, path='sim~ple')
    def get_model():
        return Model()

    @App.view(model=Model)
    def default(self, request):
        return "View"

    @App.view(model=Model, name='link')
    def link(self, request):
        return request.link(self)

    c = Client(App())

    response = c.get('/sim~ple')
    assert response.body == b'View'

    response = c.get('/sim~ple/link')
    assert response.body == b'http://localhost/sim~ple'


def test_parameter_quoting():
    class App(morepath.App):
        pass

    class Model(object):
        def __init__(self, s):
            self.s = s

    @App.path(model=Model, path='')
    def get_model(s):
        return Model(s)

    @App.view(model=Model)
    def default(self, request):
        return u"View: %s" % self.s

    @App.view(model=Model, name='link')
    def link(self, request):
        return request.link(self)

    c = Client(App())

    response = c.get('/?s=sim%C3%ABple')
    assert response.body == u"View: simëple".encode('utf-8')

    response = c.get('/link?s=sim%C3%ABple')
    assert response.body == b'http://localhost/?s=sim%C3%ABple'


def test_parameter_quoting_tilde():
    class App(morepath.App):
        pass

    class Model(object):
        def __init__(self, s):
            self.s = s

    @App.path(model=Model, path='')
    def get_model(s):
        return Model(s)

    @App.view(model=Model)
    def default(self, request):
        return u"View: %s" % self.s

    @App.view(model=Model, name='link')
    def link(self, request):
        return request.link(self)

    c = Client(App())

    response = c.get('/?s=sim~ple')
    assert response.body == u"View: sim~ple".encode('utf-8')

    response = c.get('/link?s=sim~ple')
    assert response.body == b'http://localhost/?s=sim~ple'


def test_class_link_without_variables():
    class App(morepath.App):
        pass

    class Model(object):
        pass

    @App.path(model=Model, path='/foo')
    def get_model():
        return Model()

    @App.view(model=Model)
    def link(self, request):
        return request.class_link(Model)

    c = Client(App())

    response = c.get('/foo')
    assert response.body == b"http://localhost/foo"


def test_class_link_no_app():
    class App(morepath.App):
        pass

    class Model(object):
        pass

    @App.path(model=Model, path='/foo')
    def get_model():
        return Model()

    @App.view(model=Model)
    def link(self, request):
        return request.class_link(Model, app=None)

    c = Client(App())

    with pytest.raises(LinkError):
        c.get('/foo')


def test_class_link_with_variables():
    class App(morepath.App):
        pass

    class Model(object):
        pass

    @App.path(model=Model, path='/foo/{x}')
    def get_model(x):
        return Model()

    @App.view(model=Model)
    def link(self, request):
        return request.class_link(Model, variables={'x': 'X'})

    c = Client(App())

    response = c.get('/foo/3')
    assert response.body == b"http://localhost/foo/X"


def test_class_link_with_missing_variables():
    class App(morepath.App):
        pass

    class Model(object):
        pass

    @App.path(model=Model, path='/foo/{x}')
    def get_model(x):
        return Model()

    @App.view(model=Model)
    def link(self, request):
        return request.class_link(Model, variables={})

    c = Client(App())

    with pytest.raises(KeyError):
        c.get('/foo/3')


def test_class_link_with_extra_variable():
    class App(morepath.App):
        pass

    class Model(object):
        pass

    @App.path(model=Model, path='/foo/{x}')
    def get_model(x):
        return Model()

    @App.view(model=Model)
    def link(self, request):
        return request.class_link(Model, variables={'x': 'X', 'y': 'Y'})

    c = Client(App())

    response = c.get('/foo/3')
    assert response.body == b"http://localhost/foo/X"


def test_class_link_with_url_parameter_variable():
    class App(morepath.App):
        pass

    class Model(object):
        pass

    @App.path(model=Model, path='/foo/{x}')
    def get_model(x, y):
        return Model()

    @App.view(model=Model)
    def link(self, request):
        return request.class_link(Model, variables={'x': 'X', 'y': 'Y'})

    c = Client(App())

    response = c.get('/foo/3')
    assert response.body == b"http://localhost/foo/X?y=Y"


def test_class_link_with_subclass():
    class App(morepath.App):
        pass

    class Model(object):
        pass

    class Sub(Model):
        pass

    @App.path(model=Model, path='/foo/{x}')
    def get_model(x):
        return Model()

    @App.view(model=Model)
    def link(self, request):
        return request.class_link(Sub, variables={'x': 'X'})

    c = Client(App())

    response = c.get('/foo/3')
    assert response.body == b"http://localhost/foo/X"


def test_absorb_class_path():
    class App(morepath.App):
        pass

    class Root(object):
        pass

    class Model(object):
        def __init__(self, absorb):
            self.absorb = absorb

    @App.path(model=Root, path='')
    def get_root():
        return Root()

    @App.path(model=Model, path='foo', absorb=True)
    def get_model(absorb):
        return Model(absorb)

    @App.view(model=Model)
    def default(self, request):
        return "%s" % self.absorb

    @App.view(model=Root)
    def default_root(self, request):
        return request.class_link(Model, variables={'absorb': 'a/b'})

    c = Client(App())

    # link to a/b absorb
    response = c.get('/')
    assert response.body == b'http://localhost/foo/a/b'


def test_absorb_class_path_with_variables():
    class App(morepath.App):
        pass

    class Root(object):
        pass

    class Model(object):
        def __init__(self, id, absorb):
            self.id = id
            self.absorb = absorb

    @App.path(model=Root, path='')
    def get_root():
        return Root()

    @App.path(model=Model, path='{id}', absorb=True)
    def get_model(id, absorb):
        return Model(id, absorb)

    @App.view(model=Model)
    def default(self, request):
        return "I:%s A:%s" % (self.id, self.absorb)

    @App.view(model=Root)
    def default_root(self, request):
        return request.class_link(Model,
                                  variables=dict(id='foo', absorb='a/b'))

    c = Client(App())

    # link to a/b absorb
    response = c.get('/')
    assert response.body == b'http://localhost/foo/a/b'


def test_class_link_extra_parameters():
    class App(morepath.App):
        pass

    class Model(object):
        def __init__(self, extra_parameters):
            self.extra_parameters = extra_parameters

    @App.path(model=Model, path='/')
    def get_model(extra_parameters):
        return Model(extra_parameters)

    @App.view(model=Model)
    def default(self, request):
        return repr(sorted(self.extra_parameters.items()))

    @App.view(model=Model, name='link')
    def link(self, request):
        return request.class_link(
            Model,
            variables={'extra_parameters': {'a': 'A', 'b': 'B'}})

    c = Client(App())

    response = c.get('/link?a=A&b=B')
    assert sorted(response.body[len('http://localhost/?'):].split(b"&")) == [
        b'a=A', b'b=B']


def test_path_on_model_class():
    class App(morepath.App):
        pass

    @App.path('/')
    class Model(object):
        def __init__(self):
            pass

    @App.path('/login')
    class Login(object):
        pass

    @App.view(model=Model)
    def model_view(self, request):
        return "Model"

    @App.view(model=Login)
    def login_view(self, request):
        return "Login"

    c = Client(App())

    response = c.get('/')
    assert response.body == b'Model'
    response = c.get('/login')
    assert response.body == b'Login'


def test_path_without_model():
    class App(morepath.App):
        pass

    @App.path('/')
    def get_path():
        pass

    with pytest.raises(dectate.DirectiveReportError):
        App.commit()


def test_two_path_on_same_model_should_conflict():
    class App(morepath.App):
        pass

    @App.path('/login')
    @App.path('/')
    class Login(object):
        pass

    with pytest.raises(dectate.ConflictError):
        App.commit()


def test_path_on_same_model_explicit_and_class_should_conflict():
    class App(morepath.App):
        pass

    @App.path('/')
    class Login(object):
        pass

    @App.path('/login', model=Login)
    def get_path():
        return Login()

    with pytest.raises(dectate.ConflictError):
        App.commit()
