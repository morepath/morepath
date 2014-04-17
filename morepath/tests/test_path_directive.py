import morepath
from morepath import setup
from morepath.converter import Converter
from morepath.error import DirectiveReportError, ConfigError

from webtest import TestApp as Client
import pytest


def setup_module(module):
    morepath.disable_implicit()


def test_simple_path_one_step():
    config = setup()
    app = morepath.App(testing_config=config)

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

    config.commit()

    c = Client(app)

    response = c.get('/simple')
    assert response.body == b'View'

    response = c.get('/simple/link')
    assert response.body == b'/simple'


def test_simple_path_two_steps():
    config = setup()
    app = morepath.App(testing_config=config)

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

    config.commit()

    c = Client(app)

    response = c.get('/one/two')
    assert response.body == b'View'

    response = c.get('/one/two/link')
    assert response.body == b'/one/two'


def test_variable_path_one_step():
    config = setup()
    app = morepath.App(testing_config=config)

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

    config.commit()

    c = Client(app)

    response = c.get('/foo')
    assert response.body == b'View: foo'

    response = c.get('/foo/link')
    assert response.body == b'/foo'


def test_variable_path_two_steps():
    config = setup()
    app = morepath.App(testing_config=config)

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

    config.commit()

    c = Client(app)

    response = c.get('/document/foo')
    assert response.body == b'View: foo'

    response = c.get('/document/foo/link')
    assert response.body == b'/document/foo'


def test_variable_path_two_variables():
    config = setup()
    app = morepath.App(testing_config=config)

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

    config.commit()

    c = Client(app)

    response = c.get('/foo-one')
    assert response.body == b'View: foo one'

    response = c.get('/foo-one/link')
    assert response.body == b'/foo-one'


def test_variable_path_explicit_converter():
    config = setup()
    app = morepath.App(testing_config=config)

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

    config.commit()

    c = Client(app)

    response = c.get('/1')
    assert response.body in \
        (b"View: 1 (<type 'int'>)", b"View: 1 (<class 'int'>)")

    response = c.get('/1/link')
    assert response.body == b'/1'

    response = c.get('/broken', status=404)


def test_variable_path_implicit_converter():
    config = setup()
    app = morepath.App(testing_config=config)

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

    config.commit()

    c = Client(app)

    response = c.get('/1')
    assert response.body in \
        (b"View: 1 (<type 'int'>)", b"View: 1 (<class 'int'>)")

    response = c.get('/1/link')
    assert response.body == b'/1'

    response = c.get('/broken', status=404)


def test_variable_path_explicit_trumps_implicit():
    config = setup()
    app = morepath.App(testing_config=config)

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

    config.commit()

    c = Client(app)

    response = c.get('/1')
    assert response.body in \
        (b"View: 1 (<type 'int'>)", b"View: 1 (<class 'int'>)")

    response = c.get('/1/link')
    assert response.body == b'/1'

    response = c.get('/broken', status=404)


def test_url_parameter_explicit_converter():
    config = setup()
    app = morepath.App(testing_config=config)

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

    config.commit()

    c = Client(app)

    response = c.get('/?id=1')
    assert response.body in \
        (b"View: 1 (<type 'int'>)", b"View: 1 (<class 'int'>)")

    response = c.get('/link?id=1')
    assert response.body == b'/?id=1'

    response = c.get('/?id=broken', status=400)

    response = c.get('/')
    assert response.body in \
        (b"View: None (<type 'NoneType'>)", b"View: None (<class 'NoneType'>)")


def test_url_parameter_explicit_converter_get_converters():
    config = setup()
    app = morepath.App(testing_config=config)

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

    config.commit()

    c = Client(app)

    response = c.get('/?id=1')
    assert response.body in \
        (b"View: 1 (<type 'int'>)", b"View: 1 (<class 'int'>)")

    response = c.get('/link?id=1')
    assert response.body == b'/?id=1'

    response = c.get('/?id=broken', status=400)

    response = c.get('/')
    assert response.body in \
        (b"View: None (<type 'NoneType'>)", b"View: None (<class 'NoneType'>)")


def test_url_parameter_get_converters_overrides_converters():
    config = setup()
    app = morepath.App(testing_config=config)

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

    config.commit()

    c = Client(app)

    response = c.get('/?id=1')
    assert response.body in \
        (b"View: 1 (<type 'int'>)", b"View: 1 (<class 'int'>)")

    response = c.get('/link?id=1')
    assert response.body == b'/?id=1'

    response = c.get('/?id=broken', status=400)

    response = c.get('/')
    assert response.body in \
        (b"View: None (<type 'NoneType'>)", b"View: None (<class 'NoneType'>)")


def test_url_parameter_implicit_converter():
    config = setup()
    app = morepath.App(testing_config=config)

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

    config.commit()

    c = Client(app)

    response = c.get('/?id=1')
    assert response.body in \
        (b"View: 1 (<type 'int'>)", b"View: 1 (<class 'int'>)")

    response = c.get('/link?id=1')
    assert response.body == b'/?id=1'

    response = c.get('/?id=broken', status=400)

    response = c.get('/')
    assert response.body in \
        (b"View: 0 (<type 'int'>)", b"View: 0 (<class 'int'>)")


def test_url_parameter_explicit_trumps_implicit():
    config = setup()
    app = morepath.App(testing_config=config)

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

    config.commit()

    c = Client(app)

    response = c.get('/?id=1')
    assert response.body in \
        (b"View: 1 (<type 'int'>)", b"View: 1 (<class 'int'>)")

    response = c.get('/link?id=1')
    assert response.body == b'/?id=1'

    response = c.get('/?id=broken', status=400)

    response = c.get('/')
    assert response.body in \
        (b"View: foo (<type 'str'>)", b"View: foo (<class 'str'>)")


def test_decode_encode():
    config = setup()
    app = morepath.App(testing_config=config)

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

    config.commit()

    c = Client(app)

    response = c.get('/?id=foo')
    assert response.body == b"View: fooADD"

    response = c.get('/link?id=foo')
    assert response.body == b'/?id=foo'


def test_unknown_converter():
    config = setup()
    app = morepath.App(testing_config=config)

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
        config.commit()


def test_unknown_explicit_converter():
    config = setup()
    app = morepath.App(testing_config=config)

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
        config.commit()


def test_default_date_converter():
    config = setup()
    app = morepath.App(testing_config=config)

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

    config.commit()

    c = Client(app)

    response = c.get('/?d=20121110')
    assert response.body == b"View: 2012-11-10"

    response = c.get('/')
    assert response.body == b"View: 2011-01-01"

    response = c.get('/link?d=20121110')
    assert response.body == b'/?d=20121110'

    response = c.get('/link')
    assert response.body == b'/?d=20110101'

    response = c.get('/?d=broken', status=400)


def test_default_datetime_converter():
    config = setup()
    app = morepath.App(testing_config=config)

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

    config.commit()

    c = Client(app)

    response = c.get('/?d=20121110T144530')
    assert response.body == b"View: 2012-11-10 14:45:30"

    response = c.get('/')
    assert response.body == b"View: 2011-01-01 10:30:00"

    response = c.get('/link?d=20121110T144500')
    assert response.body == b'/?d=20121110T144500'

    response = c.get('/link')
    assert response.body == b'/?d=20110101T103000'

    response = c.get('/?d=broken', status=400)


def test_custom_date_converter():
    config = setup()
    app = morepath.App(testing_config=config)

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

    config.commit()

    c = Client(app)

    response = c.get('/?d=10-11-2012')
    assert response.body == b"View: 2012-11-10"

    response = c.get('/')
    assert response.body == b"View: 2011-01-01"

    response = c.get('/link?d=10-11-2012')
    assert response.body == b'/?d=10-11-2012'

    response = c.get('/link')
    assert response.body == b'/?d=01-01-2011'

    response = c.get('/?d=broken', status=400)


def test_variable_path_parameter_required_no_default():
    config = setup()
    app = morepath.App(testing_config=config)

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

    config.commit()

    c = Client(app)

    response = c.get('/?id=a')
    assert response.body == b"View: a"

    response = c.get('/', status=400)


def test_variable_path_parameter_required_with_default():
    config = setup()
    app = morepath.App(testing_config=config)

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

    config.commit()

    c = Client(app)

    response = c.get('/?id=a')
    assert response.body == b"View: a"

    response = c.get('/', status=400)


def test_type_hints_and_converters():
    config = setup()
    app = morepath.App(testing_config=config)

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

    config.commit()

    c = Client(app)

    response = c.get('/?d=20140120')
    assert response.body == b"View: 2014-01-20"

    response = c.get('/link?d=20140120')
    assert response.body == b'/?d=20140120'


def test_link_for_none_means_no_parameter():
    config = setup()
    app = morepath.App(testing_config=config)

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

    config.commit()

    c = Client(app)

    response = c.get('/')
    assert response.body == b"View: None"

    response = c.get('/link')
    assert response.body == b'/'


def test_path_and_url_parameter_converter():
    config = setup()
    app = morepath.App(testing_config=config)

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

    config.commit()

    c = Client(app)

    response = c.get('/1/link')
    assert response.body == b'/1'


def test_root_named_link():
    config = setup()
    app = morepath.App(testing_config=config)

    @app.path(path='')
    class Root(object):
        pass

    @app.view(model=Root)
    def default(self, request):
        return request.link(self, 'foo')

    config.commit()

    c = Client(app)

    response = c.get('/')
    assert response.body == b'/foo'


def test_path_class_and_model_argument():
    config = setup()
    app = morepath.App(testing_config=config)

    class Foo(object):
        pass

    @app.path(path='', model=Foo)
    class Root(object):
        pass

    with pytest.raises(ConfigError):
        config.commit()


def test_path_no_class_and_no_model_argument():
    config = setup()
    app = morepath.App(testing_config=config)

    @app.path(path='')
    def get_foo():
        return None

    with pytest.raises(ConfigError):
        config.commit()


def test_url_parameter_list():
    config = setup()
    app = morepath.App(testing_config=config)

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

    config.commit()

    c = Client(app)

    response = c.get('/?item=1&item=2')
    assert response.body == b"[1, 2]"

    response = c.get('/link?item=1&item=2')
    assert response.body == b'/?item=1&item=2'

    response = c.get('/link')
    assert response.body == b'/'

    response = c.get('/?item=broken&item=1', status=400)

    response = c.get('/')
    assert response.body == b"[]"


def test_url_parameter_list_empty():
    config = setup()
    app = morepath.App(testing_config=config)

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

    config.commit()

    c = Client(app)

    response = c.get('/?item=a&item=b')
    assert response.body in (b"[u'a', u'b']", b"['a', 'b']")

    response = c.get('/link?item=a&item=b')
    assert response.body == b'/?item=a&item=b'

    response = c.get('/link')
    assert response.body == b'/'

    response = c.get('/')
    assert response.body == b"[]"


def test_url_parameter_list_explicit_converter():
    config = setup()
    app = morepath.App(testing_config=config)

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

    config.commit()

    c = Client(app)

    response = c.get('/?item=1&item=2')
    assert response.body == b"[1, 2]"

    response = c.get('/link?item=1&item=2')
    assert response.body == b'/?item=1&item=2'

    response = c.get('/link')
    assert response.body == b'/'

    response = c.get('/?item=broken&item=1', status=400)

    response = c.get('/')
    assert response.body == b"[]"


def test_url_parameter_list_unknown_explicit_converter():
    config = setup()
    app = morepath.App(testing_config=config)

    class Model(object):
        def __init__(self, item):
            self.item = item

    class Unknown(object):
        pass

    @app.path(model=Model, path='/', converters={'item': [Unknown]})
    def get_model(item):
        return Model(item)

    with pytest.raises(DirectiveReportError):
        config.commit()


def test_url_parameter_list_but_only_one_allowed():
    config = setup()
    app = morepath.App(testing_config=config)

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

    config.commit()

    c = Client(app)

    c.get('/?item=1&item=2', status=400)

    c.get('/link?item=1&item=2', status=400)


def test_extra_parameters():
    config = setup()
    app = morepath.App(testing_config=config)

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

    config.commit()

    c = Client(app)

    response = c.get('/?a=A&b=B')
    assert response.body in \
        (b"[(u'a', u'A'), (u'b', u'B')]", b"[('a', 'A'), ('b', 'B')]")
    response = c.get('/link?a=A&b=B')
    assert sorted(response.body[2:].split(b"&")) == [b'a=A', b'b=B']


def test_extra_parameters_with_get_converters():
    config = setup()
    app = morepath.App(testing_config=config)

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

    config.commit()

    c = Client(app)

    response = c.get('/?a=1&b=B')
    assert response.body in \
        (b"[(u'a', 1), (u'b', u'B')]", b"[('a', 1), ('b', 'B')]")
    response = c.get('/link?a=1&b=B')
    assert sorted(response.body[2:].split(b"&")) == [b'a=1', b'b=B']
