from __future__ import annotations

import pytest
from webtest import TestApp as Client

import dectate
import morepath
from morepath.converter import Converter
from morepath.error import (
    ConfigError,
    DirectiveReportError,
    LinkError,
    TrajectError,
)


def test_simple_path_one_step() -> None:
    class app(morepath.App):
        pass

    class Model:
        def __init__(self) -> None:
            pass

    @app.path(model=Model, path="simple")
    def get_model() -> Model:
        return Model()

    @app.view(model=Model)
    def default(self: Model, request: morepath.Request) -> str:
        return "View"

    @app.view(model=Model, name="link")
    def link(self: Model, request: morepath.Request) -> str:
        return request.link(self)

    c = Client(app())

    response = c.get("/simple")
    assert response.body == b"View"

    response = c.get("/simple/link")
    assert response.body == b"http://localhost/simple"


def test_simple_path_two_steps() -> None:
    class app(morepath.App):
        pass

    class Model:
        def __init__(self) -> None:
            pass

    @app.path(model=Model, path="one/two")
    def get_model() -> Model:
        return Model()

    @app.view(model=Model)
    def default(self: Model, request: morepath.Request) -> str:
        return "View"

    @app.view(model=Model, name="link")
    def link(self: Model, request: morepath.Request) -> str:
        return request.link(self)

    c = Client(app())

    response = c.get("/one/two")
    assert response.body == b"View"

    response = c.get("/one/two/link")
    assert response.body == b"http://localhost/one/two"


def test_variable_path_one_step() -> None:
    class app(morepath.App):
        pass

    class Model:
        def __init__(self, name: str) -> None:
            self.name = name

    @app.path(model=Model, path="{name}")
    def get_model(name: str) -> Model:
        return Model(name)

    @app.view(model=Model)
    def default(self: Model, request: morepath.Request) -> str:
        return "View: %s" % self.name

    @app.view(model=Model, name="link")
    def link(self: Model, request: morepath.Request) -> str:
        return request.link(self)

    c = Client(app())

    response = c.get("/foo")
    assert response.body == b"View: foo"

    response = c.get("/foo/link")
    assert response.body == b"http://localhost/foo"


def test_variable_path_two_steps() -> None:
    class app(morepath.App):
        pass

    class Model:
        def __init__(self, name: str) -> None:
            self.name = name

    @app.path(model=Model, path="document/{name}")
    def get_model(name: str) -> Model:
        return Model(name)

    @app.view(model=Model)
    def default(self: Model, request: morepath.Request) -> str:
        return "View: %s" % self.name

    @app.view(model=Model, name="link")
    def link(self: Model, request: morepath.Request) -> str:
        return request.link(self)

    c = Client(app())

    response = c.get("/document/foo")
    assert response.body == b"View: foo"

    response = c.get("/document/foo/link")
    assert response.body == b"http://localhost/document/foo"


def test_variable_path_two_variables() -> None:
    class app(morepath.App):
        pass

    class Model:
        def __init__(self, name: str, version: str) -> None:
            self.name = name
            self.version = version

    @app.path(model=Model, path="{name}-{version}")
    def get_model(name: str, version: str) -> Model:
        return Model(name, version)

    @app.view(model=Model)
    def default(self: Model, request: morepath.Request) -> str:
        return f"View: {self.name} {self.version}"

    @app.view(model=Model, name="link")
    def link(self: Model, request: morepath.Request) -> str:
        return request.link(self)

    c = Client(app())

    response = c.get("/foo-one")
    assert response.body == b"View: foo one"

    response = c.get("/foo-one/link")
    assert response.body == b"http://localhost/foo-one"


def test_variable_path_explicit_converter() -> None:
    class app(morepath.App):
        pass

    class Model:
        def __init__(self, id: int) -> None:
            self.id = id

    @app.path(model=Model, path="{id}", converters=dict(id=Converter(int)))
    def get_model(id: int) -> Model:
        return Model(id)

    @app.view(model=Model)
    def default(self: Model, request: morepath.Request) -> str:
        return f"View: {self.id} ({type(self.id)})"

    @app.view(model=Model, name="link")
    def link(self: Model, request: morepath.Request) -> str:
        return request.link(self)

    c = Client(app())

    response = c.get("/1")
    assert response.body in (
        b"View: 1 (<type 'int'>)",
        b"View: 1 (<class 'int'>)",
    )

    response = c.get("/1/link")
    assert response.body == b"http://localhost/1"

    response = c.get("/broken", status=404)


def test_variable_path_implicit_converter() -> None:
    class app(morepath.App):
        pass

    class Model:
        def __init__(self, id: int) -> None:
            self.id = id

    @app.path(model=Model, path="{id}")
    def get_model(id: int = 0) -> Model:
        return Model(id)

    @app.view(model=Model)
    def default(self: Model, request: morepath.Request) -> str:
        return f"View: {self.id} ({type(self.id)})"

    @app.view(model=Model, name="link")
    def link(self: Model, request: morepath.Request) -> str:
        return request.link(self)

    c = Client(app())

    response = c.get("/1")
    assert response.body in (
        b"View: 1 (<type 'int'>)",
        b"View: 1 (<class 'int'>)",
    )

    response = c.get("/1/link")
    assert response.body == b"http://localhost/1"

    response = c.get("/broken", status=404)


def test_variable_path_explicit_trumps_implicit() -> None:
    class app(morepath.App):
        pass

    class Model:
        def __init__(self, id: str | int) -> None:
            self.id = id

    @app.path(model=Model, path="{id}", converters=dict(id=Converter(int)))
    def get_model(id: int | str = "foo") -> Model:
        return Model(id)

    @app.view(model=Model)
    def default(self: Model, request: morepath.Request) -> str:
        return f"View: {self.id} ({type(self.id)})"

    @app.view(model=Model, name="link")
    def link(self: Model, request: morepath.Request) -> str:
        return request.link(self)

    c = Client(app())

    response = c.get("/1")
    assert response.body in (
        b"View: 1 (<type 'int'>)",
        b"View: 1 (<class 'int'>)",
    )

    response = c.get("/1/link")
    assert response.body == b"http://localhost/1"

    response = c.get("/broken", status=404)


def test_url_parameter_explicit_converter() -> None:
    class app(morepath.App):
        pass

    class Model:
        def __init__(self, id: int) -> None:
            self.id = id

    @app.path(model=Model, path="/", converters=dict(id=Converter(int)))
    def get_model(id: int) -> Model:
        return Model(id)

    @app.view(model=Model)
    def default(self: Model, request: morepath.Request) -> str:
        return f"View: {self.id} ({type(self.id)})"

    @app.view(model=Model, name="link")
    def link(self: Model, request: morepath.Request) -> str:
        return request.link(self)

    c = Client(app())

    response = c.get("/?id=1")
    assert response.body in (
        b"View: 1 (<type 'int'>)",
        b"View: 1 (<class 'int'>)",
    )

    response = c.get("/link?id=1")
    assert response.body == b"http://localhost/?id=1"

    response = c.get("/?id=broken", status=400)

    response = c.get("/")
    assert response.body in (
        b"View: None (<type 'NoneType'>)",
        b"View: None (<class 'NoneType'>)",
    )


def test_url_parameter_explicit_converter_get_converters() -> None:
    class app(morepath.App):
        pass

    class Model:
        def __init__(self, id: int) -> None:
            self.id = id

    def get_converters() -> dict[str, Converter[int]]:
        return dict(id=Converter(int))

    @app.path(model=Model, path="/", get_converters=get_converters)
    def get_model(id: int) -> Model:
        return Model(id)

    @app.view(model=Model)
    def default(self: Model, request: morepath.Request) -> str:
        return f"View: {self.id} ({type(self.id)})"

    @app.view(model=Model, name="link")
    def link(self: Model, request: morepath.Request) -> str:
        return request.link(self)

    c = Client(app())

    response = c.get("/?id=1")
    assert response.body in (
        b"View: 1 (<type 'int'>)",
        b"View: 1 (<class 'int'>)",
    )

    response = c.get("/link?id=1")
    assert response.body == b"http://localhost/?id=1"

    response = c.get("/?id=broken", status=400)

    response = c.get("/")
    assert response.body in (
        b"View: None (<type 'NoneType'>)",
        b"View: None (<class 'NoneType'>)",
    )


def test_url_parameter_get_converters_overrides_converters() -> None:
    class app(morepath.App):
        pass

    class Model:
        def __init__(self, id: int) -> None:
            self.id = id

    def get_converters() -> dict[str, Converter[int]]:
        return dict(id=Converter(int))

    @app.path(
        model=Model,
        path="/",
        converters={"id": str},
        get_converters=get_converters,
    )
    def get_model(id: int) -> Model:
        return Model(id)

    @app.view(model=Model)
    def default(self: Model, request: morepath.Request) -> str:
        return f"View: {self.id} ({type(self.id)})"

    @app.view(model=Model, name="link")
    def link(self: Model, request: morepath.Request) -> str:
        return request.link(self)

    c = Client(app())

    response = c.get("/?id=1")
    assert response.body in (
        b"View: 1 (<type 'int'>)",
        b"View: 1 (<class 'int'>)",
    )

    response = c.get("/link?id=1")
    assert response.body == b"http://localhost/?id=1"

    response = c.get("/?id=broken", status=400)

    response = c.get("/")
    assert response.body in (
        b"View: None (<type 'NoneType'>)",
        b"View: None (<class 'NoneType'>)",
    )


def test_url_parameter_implicit_converter() -> None:
    class app(morepath.App):
        pass

    class Model:
        def __init__(self, id: int) -> None:
            self.id = id

    @app.path(model=Model, path="/")
    def get_model(id: int = 0) -> Model:
        return Model(id)

    @app.view(model=Model)
    def default(self: Model, request: morepath.Request) -> str:
        return f"View: {self.id} ({type(self.id)})"

    @app.view(model=Model, name="link")
    def link(self: Model, request: morepath.Request) -> str:
        return request.link(self)

    c = Client(app())

    response = c.get("/?id=1")
    assert response.body in (
        b"View: 1 (<type 'int'>)",
        b"View: 1 (<class 'int'>)",
    )

    response = c.get("/link?id=1")
    assert response.body == b"http://localhost/?id=1"

    response = c.get("/?id=broken", status=400)

    response = c.get("/")
    assert response.body in (
        b"View: 0 (<type 'int'>)",
        b"View: 0 (<class 'int'>)",
    )


def test_multiple_url_parameters_stable_order() -> None:
    class App(morepath.App):
        pass

    class Model:
        def __init__(self, a: str, b: str) -> None:
            self.a = a
            self.b = b

    @App.path(model=Model, path="/")
    def get_model(a: str, b: str) -> Model:
        return Model(a, b)

    @App.view(model=Model, name="link")
    def link(self: Model, request: morepath.Request) -> str:
        return request.link(self)

    c = Client(App())

    response = c.get("/link?a=A&b=B")
    assert response.body == b"http://localhost/?a=A&b=B"


def test_url_parameter_explicit_trumps_implicit() -> None:
    class app(morepath.App):
        pass

    class Model:
        def __init__(self, id: int | str) -> None:
            self.id = id

    @app.path(model=Model, path="/", converters=dict(id=Converter(int)))
    def get_model(id: int | str = "foo") -> Model:
        return Model(id)

    @app.view(model=Model)
    def default(self: Model, request: morepath.Request) -> str:
        return f"View: {self.id} ({type(self.id)})"

    @app.view(model=Model, name="link")
    def link(self: Model, request: morepath.Request) -> str:
        return request.link(self)

    c = Client(app())

    response = c.get("/?id=1")
    assert response.body in (
        b"View: 1 (<type 'int'>)",
        b"View: 1 (<class 'int'>)",
    )

    response = c.get("/link?id=1")
    assert response.body == b"http://localhost/?id=1"

    response = c.get("/?id=broken", status=400)

    response = c.get("/")
    assert response.body in (
        b"View: foo (<type 'str'>)",
        b"View: foo (<class 'str'>)",
    )


def test_decode_encode() -> None:
    class app(morepath.App):
        pass

    class Model:
        def __init__(self, id: str) -> None:
            self.id = id

    def my_decode(s: str) -> str:
        return s + "ADD"

    def my_encode(s: str) -> str:
        return s[: -len("ADD")]

    @app.path(
        model=Model,
        path="/",
        converters=dict(id=Converter(my_decode, my_encode)),
    )
    def get_model(id: str) -> Model:
        return Model(id)

    @app.view(model=Model)
    def default(self: Model, request: morepath.Request) -> str:
        return "View: %s" % self.id

    @app.view(model=Model, name="link")
    def link(self: Model, request: morepath.Request) -> str:
        return request.link(self)

    c = Client(app())

    response = c.get("/?id=foo")
    assert response.body == b"View: fooADD"

    response = c.get("/link?id=foo")
    assert response.body == b"http://localhost/?id=foo"


def test_unknown_converter() -> None:
    class app(morepath.App):
        pass

    class Model:
        def __init__(self, d: object) -> None:
            self.d = d

    class Unknown:
        pass

    @app.path(model=Model, path="/")
    def get_model(d: Unknown = Unknown()) -> Model:
        return Model(d)

    @app.view(model=Model)
    def default(self: Model, request: morepath.Request) -> str:
        return "View: %s" % self.d

    @app.view(model=Model, name="link")
    def link(self: Model, request: morepath.Request) -> str:
        return request.link(self)

    with pytest.raises(DirectiveReportError):
        app.commit()


def test_not_all_path_variables_arguments_of_model_factory() -> None:
    class App(morepath.App):
        pass

    class Model:
        def __init__(self, foo: str) -> None:
            self.foo = foo

    class Unknown:
        pass

    @App.path(model=Model, path="/{foo}/{bar}")
    def get_model(foo: str) -> Model:
        return Model(foo)

    with pytest.raises(DirectiveReportError) as e:
        App.commit()
    assert str(e.value).startswith(
        "Variable in path not found in function " "signature: bar"
    )


def test_unknown_explicit_converter() -> None:
    class app(morepath.App):
        pass

    class Model:
        def __init__(self, d: Unknown) -> None:
            self.d = d

    class Unknown:
        pass

    @app.path(model=Model, path="/", converters={"d": Unknown})
    def get_model(d: Unknown) -> Model:
        return Model(d)

    @app.view(model=Model)
    def default(self: Model, request: morepath.Request) -> str:
        return "View: %s" % self.d

    @app.view(model=Model, name="link")
    def link(self: Model, request: morepath.Request) -> str:
        return request.link(self)

    with pytest.raises(DirectiveReportError):
        app.commit()


def test_default_date_converter() -> None:
    class app(morepath.App):
        pass

    class Model:
        def __init__(self, d: date) -> None:
            self.d = d

    from datetime import date

    @app.path(model=Model, path="/")
    def get_model(d: date = date(2011, 1, 1)) -> Model:
        return Model(d)

    @app.view(model=Model)
    def default(self: Model, request: morepath.Request) -> str:
        return "View: %s" % self.d

    @app.view(model=Model, name="link")
    def link(self: Model, request: morepath.Request) -> str:
        return request.link(self)

    c = Client(app())

    response = c.get("/?d=20121110")
    assert response.body == b"View: 2012-11-10"

    response = c.get("/")
    assert response.body == b"View: 2011-01-01"

    response = c.get("/link?d=20121110")
    assert response.body == b"http://localhost/?d=20121110"

    response = c.get("/link")
    assert response.body == b"http://localhost/?d=20110101"

    response = c.get("/?d=broken", status=400)


def test_default_datetime_converter() -> None:
    class app(morepath.App):
        pass

    class Model:
        def __init__(self, d: datetime) -> None:
            self.d = d

    from datetime import datetime

    @app.path(model=Model, path="/")
    def get_model(d: datetime = datetime(2011, 1, 1, 10, 30)) -> Model:
        return Model(d)

    @app.view(model=Model)
    def default(self: Model, request: morepath.Request) -> str:
        return "View: %s" % self.d

    @app.view(model=Model, name="link")
    def link(self: Model, request: morepath.Request) -> str:
        return request.link(self)

    c = Client(app())

    response = c.get("/?d=20121110T144530")
    assert response.body == b"View: 2012-11-10 14:45:30"

    response = c.get("/")
    assert response.body == b"View: 2011-01-01 10:30:00"

    response = c.get("/link?d=20121110T144500")
    assert response.body == b"http://localhost/?d=20121110T144500"

    response = c.get("/link")
    assert response.body == b"http://localhost/?d=20110101T103000"

    c.get("/?d=broken", status=400)


def test_custom_date_converter() -> None:
    class app(morepath.App):
        pass

    class Model:
        def __init__(self, d: date) -> None:
            self.d = d

    from datetime import date
    from time import mktime, strptime

    def date_decode(s: str) -> date:
        return date.fromtimestamp(mktime(strptime(s, "%d-%m-%Y")))

    def date_encode(d: date) -> str:
        return d.strftime("%d-%m-%Y")

    @app.converter(type=date)
    def date_converter() -> Converter[date]:
        return Converter(date_decode, date_encode)

    @app.path(model=Model, path="/")
    def get_model(d: date = date(2011, 1, 1)) -> Model:
        return Model(d)

    @app.view(model=Model)
    def default(self: Model, request: morepath.Request) -> str:
        return "View: %s" % self.d

    @app.view(model=Model, name="link")
    def link(self: Model, request: morepath.Request) -> str:
        return request.link(self)

    c = Client(app())

    response = c.get("/?d=10-11-2012")
    assert response.body == b"View: 2012-11-10"

    response = c.get("/")
    assert response.body == b"View: 2011-01-01"

    response = c.get("/link?d=10-11-2012")
    assert response.body == b"http://localhost/?d=10-11-2012"

    response = c.get("/link")
    assert response.body == b"http://localhost/?d=01-01-2011"

    response = c.get("/?d=broken", status=400)


def test_variable_path_parameter_required_no_default() -> None:
    class app(morepath.App):
        pass

    class Model:
        def __init__(self, id: str) -> None:
            self.id = id

    @app.path(model=Model, path="", required=["id"])
    def get_model(id: str) -> Model:
        return Model(id)

    @app.view(model=Model)
    def default(self: Model, request: morepath.Request) -> str:
        return "View: %s" % self.id

    @app.view(model=Model, name="link")
    def link(self: Model, request: morepath.Request) -> str:
        return request.link(self)

    c = Client(app())

    response = c.get("/?id=a")
    assert response.body == b"View: a"

    response = c.get("/", status=400)


def test_variable_path_parameter_required_with_default() -> None:
    class app(morepath.App):
        pass

    class Model:
        def __init__(self, id: str) -> None:
            self.id = id

    @app.path(model=Model, path="", required=["id"])
    def get_model(id: str = "b") -> Model:
        return Model(id)

    @app.view(model=Model)
    def default(self: Model, request: morepath.Request) -> str:
        return "View: %s" % self.id

    @app.view(model=Model, name="link")
    def link(self: Model, request: morepath.Request) -> str:
        return request.link(self)

    c = Client(app())

    response = c.get("/?id=a")
    assert response.body == b"View: a"

    response = c.get("/", status=400)


def test_type_hints_and_converters() -> None:
    class app(morepath.App):
        pass

    class Model:
        def __init__(self, d: date) -> None:
            self.d = d

    from datetime import date

    @app.path(model=Model, path="", converters=dict(d=date))
    def get_model(d: date) -> Model:
        return Model(d)

    @app.view(model=Model)
    def default(self: Model, request: morepath.Request) -> str:
        return "View: %s" % self.d

    @app.view(model=Model, name="link")
    def link(self: Model, request: morepath.Request) -> str:
        return request.link(self)

    c = Client(app())

    response = c.get("/?d=20140120")
    assert response.body == b"View: 2014-01-20"

    response = c.get("/link?d=20140120")
    assert response.body == b"http://localhost/?d=20140120"


def test_link_for_none_means_no_parameter() -> None:
    class app(morepath.App):
        pass

    class Model:
        def __init__(self, id: str | None) -> None:
            self.id = id

    @app.path(model=Model, path="")
    def get_model(id: str | None) -> Model:
        return Model(id)

    @app.view(model=Model)
    def default(self: Model, request: morepath.Request) -> str:
        return "View: %s" % self.id

    @app.view(model=Model, name="link")
    def link(self: Model, request: morepath.Request) -> str:
        return request.link(self)

    c = Client(app())

    response = c.get("/")
    assert response.body == b"View: None"

    response = c.get("/link")
    assert response.body == b"http://localhost/"


def test_path_and_url_parameter_converter() -> None:
    class app(morepath.App):
        pass

    class Model:
        def __init__(self, id: int, param: date | None) -> None:
            self.id = id
            self.param = param

    from datetime import date

    @app.path(model=Model, path="/{id}", converters=dict(param=date))
    def get_model(id: int = 0, param: date | None = None) -> Model:
        return Model(id, param)

    @app.view(model=Model)
    def default(self: Model, request: morepath.Request) -> str:
        return f"View: {self.id} {self.param}"

    @app.view(model=Model, name="link")
    def link(self: Model, request: morepath.Request) -> str:
        return request.link(self)

    c = Client(app())

    response = c.get("/1/link")
    assert response.body == b"http://localhost/1"


def test_path_converter_fallback_on_view() -> None:
    class app(morepath.App):
        pass

    class Root:
        pass

    class Model:
        def __init__(self, id: int) -> None:
            self.id = id

    @app.path(model=Root, path="")
    def get_root() -> Root:
        return Root()

    @app.path(model=Model, path="/{id}")
    def get_model(id: int = 0) -> Model:
        return Model(id)

    @app.view(model=Model)
    def default(self: Model, request: morepath.Request) -> str:
        return "Default view for %s" % self.id

    @app.view(model=Root, name="named")
    def named(self: Root, request: morepath.Request) -> str:
        return "Named view on root"

    c = Client(app())

    response = c.get("/1")
    assert response.body == b"Default view for 1"
    response = c.get("/named")
    assert response.body == b"Named view on root"


def test_root_named_link() -> None:
    class app(morepath.App):
        pass

    @app.path(path="")
    class Root:
        pass

    @app.view(model=Root)
    def default(self: Root, request: morepath.Request) -> str:
        return request.link(self, "foo")

    c = Client(app())

    response = c.get("/")
    assert response.body == b"http://localhost/foo"


def test_path_class_and_model_argument() -> None:
    class app(morepath.App):
        pass

    class Foo:
        pass

    @app.path(path="", model=Foo)
    class Root:
        pass

    with pytest.raises(ConfigError):
        app.commit()


def test_path_no_class_and_no_model_argument() -> None:
    class app(morepath.App):
        pass

    @app.path(path="")
    def get_foo() -> None:
        return None

    with pytest.raises(ConfigError):
        app.commit()


def test_url_parameter_list() -> None:
    class app(morepath.App):
        pass

    class Model:
        def __init__(self, item: list[int]) -> None:
            self.item = item

    @app.path(model=Model, path="/", converters={"item": [int]})
    def get_model(item: list[int]) -> Model:
        return Model(item)

    @app.view(model=Model)
    def default(self: Model, request: morepath.Request) -> str:
        return repr(self.item)

    @app.view(model=Model, name="link")
    def link(self: Model, request: morepath.Request) -> str:
        return request.link(self)

    c = Client(app())

    response = c.get("/?item=1&item=2")
    assert response.body == b"[1, 2]"

    response = c.get("/link?item=1&item=2")
    assert response.body == b"http://localhost/?item=1&item=2"

    response = c.get("/link")
    assert response.body == b"http://localhost/"

    response = c.get("/?item=broken&item=1", status=400)

    response = c.get("/")
    assert response.body == b"[]"


def test_url_parameter_list_empty() -> None:
    class app(morepath.App):
        pass

    class Model:
        def __init__(self, item: list[str]) -> None:
            self.item = item

    @app.path(model=Model, path="/", converters={"item": []})
    def get_model(item: list[str]) -> Model:
        return Model(item)

    @app.view(model=Model)
    def default(self: Model, request: morepath.Request) -> str:
        return repr(self.item)

    @app.view(model=Model, name="link")
    def link(self: Model, request: morepath.Request) -> str:
        return request.link(self)

    c = Client(app())

    response = c.get("/?item=a&item=b")
    assert response.body == b"['a', 'b']"

    response = c.get("/link?item=a&item=b")
    assert response.body == b"http://localhost/?item=a&item=b"

    response = c.get("/link")
    assert response.body == b"http://localhost/"

    response = c.get("/")
    assert response.body == b"[]"


def test_url_parameter_list_explicit_converter() -> None:
    class app(morepath.App):
        pass

    class Model:
        def __init__(self, item: list[int]) -> None:
            self.item = item

    @app.path(model=Model, path="/", converters={"item": [Converter(int)]})
    def get_model(item: list[int]) -> Model:
        return Model(item)

    @app.view(model=Model)
    def default(self: Model, request: morepath.Request) -> str:
        return repr(self.item)

    @app.view(model=Model, name="link")
    def link(self: Model, request: morepath.Request) -> str:
        return request.link(self)

    c = Client(app())

    response = c.get("/?item=1&item=2")
    assert response.body == b"[1, 2]"

    response = c.get("/link?item=1&item=2")
    assert response.body == b"http://localhost/?item=1&item=2"

    response = c.get("/link")
    assert response.body == b"http://localhost/"

    response = c.get("/?item=broken&item=1", status=400)

    response = c.get("/")
    assert response.body == b"[]"


def test_url_parameter_list_unknown_explicit_converter() -> None:
    class app(morepath.App):
        pass

    class Unknown:
        pass

    class Model:
        def __init__(self, item: list[Unknown]) -> None:
            self.item = item

    @app.path(model=Model, path="/", converters={"item": [Unknown]})
    def get_model(item: list[Unknown]) -> Model:
        return Model(item)

    with pytest.raises(DirectiveReportError):
        app.commit()


def test_url_parameter_list_but_only_one_allowed() -> None:
    class app(morepath.App):
        pass

    class Model:
        def __init__(self, item: int) -> None:
            self.item = item

    @app.path(model=Model, path="/", converters={"item": int})
    def get_model(item: int) -> Model:
        return Model(item)

    @app.view(model=Model)
    def default(self: Model, request: morepath.Request) -> str:
        return repr(self.item)

    @app.view(model=Model, name="link")
    def link(self: Model, request: morepath.Request) -> str:
        return request.link(self)

    c = Client(app())

    c.get("/?item=1&item=2", status=400)

    c.get("/link?item=1&item=2", status=400)


def test_extra_parameters() -> None:
    class app(morepath.App):
        pass

    class Model:
        def __init__(self, extra_parameters: dict[str, str]) -> None:
            self.extra_parameters = extra_parameters

    @app.path(model=Model, path="/")
    def get_model(extra_parameters: dict[str, str]) -> Model:
        return Model(extra_parameters)

    @app.view(model=Model)
    def default(self: Model, request: morepath.Request) -> str:
        return repr(sorted(self.extra_parameters.items()))

    @app.view(model=Model, name="link")
    def link(self: Model, request: morepath.Request) -> str:
        return request.link(self)

    c = Client(app())

    response = c.get("/?a=A&b=B")
    assert response.body == b"[('a', 'A'), ('b', 'B')]"
    response = c.get("/link?a=A&b=B")
    assert sorted(response.body[len("http://localhost/?") :].split(b"&")) == [
        b"a=A",
        b"b=B",
    ]


def test_extra_parameters_with_get_converters() -> None:
    class app(morepath.App):
        pass

    class Model:
        def __init__(self, extra_parameters: dict[str, int | str]) -> None:
            self.extra_parameters = extra_parameters

    def get_converters() -> dict[str, type[object]]:
        return {
            "a": int,
            "b": str,
        }

    @app.path(model=Model, path="/", get_converters=get_converters)
    def get_model(extra_parameters: dict[str, int | str]) -> Model:
        return Model(extra_parameters)

    @app.view(model=Model)
    def default(self: Model, request: morepath.Request) -> str:
        return repr(sorted(self.extra_parameters.items()))

    @app.view(model=Model, name="link")
    def link(self: Model, request: morepath.Request) -> str:
        return request.link(self)

    c = Client(app())

    response = c.get("/?a=1&b=B")
    assert response.body == b"[('a', 1), ('b', 'B')]"
    response = c.get("/link?a=1&b=B")
    assert sorted(response.body[len("http://localhost/?") :].split(b"&")) == [
        b"a=1",
        b"b=B",
    ]

    c.get("/?a=broken&b=B", status=400)


def test_script_name() -> None:
    class app(morepath.App):
        pass

    class Model:
        def __init__(self) -> None:
            pass

    @app.path(model=Model, path="simple")
    def get_model() -> Model:
        return Model()

    @app.view(model=Model)
    def default(self: Model, request: morepath.Request) -> str:
        return "View"

    @app.view(model=Model, name="link")
    def link(self: Model, request: morepath.Request) -> str:
        return request.link(self)

    c = Client(app())

    response = c.get(
        "/prefix/simple", extra_environ=dict(SCRIPT_NAME="/prefix")
    )
    assert response.body == b"View"

    response = c.get(
        "/prefix/simple/link", extra_environ=dict(SCRIPT_NAME="/prefix")
    )
    assert response.body == b"http://localhost/prefix/simple"


def test_sub_path_different_variable() -> None:
    # See discussion in https://github.com/morepath/morepath/issues/155

    class App(morepath.App):
        pass

    class Foo:
        def __init__(self, id: str) -> None:
            self.id = id

    class Bar:
        def __init__(self, id: str, foo: Foo) -> None:
            self.id = id
            self.foo = foo

    @App.path(model=Foo, path="{id}")
    def get_foo(id: str) -> Foo:
        return Foo(id)

    @App.path(model=Bar, path="{foo_id}/{bar_id}")
    def get_client(foo_id: str, bar_id: str) -> Bar:
        return Bar(bar_id, Foo(foo_id))

    @App.view(model=Foo)
    def default_sbar(self: Foo, request: morepath.Request) -> str:
        return "M: %s" % self.id

    @App.view(model=Bar)
    def default_bar(self: Bar, request: morepath.Request) -> str:
        return f"S: {self.id} {self.foo.id}"

    c = Client(App())

    with pytest.raises(TrajectError) as ex:
        response = c.get("/a")
        assert response.body == b"M: a"

        response = c.get("/a/b")
        assert response.body == b"S: b a"

    assert str(ex.value) == "step {id} and {foo_id} are in conflict"


def test_absorb_path() -> None:
    class app(morepath.App):
        pass

    class Root:
        pass

    class Model:
        def __init__(self, absorb: str) -> None:
            self.absorb = absorb

    @app.path(model=Root, path="")
    def get_root() -> Root:
        return Root()

    @app.path(model=Model, path="foo", absorb=True)
    def get_model(absorb: str) -> Model:
        return Model(absorb)

    @app.view(model=Model)
    def default(self: Model, request: morepath.Request) -> str:
        return "%s" % self.absorb

    @app.view(model=Root)
    def default_root(self: Root, request: morepath.Request) -> str:
        return request.link(Model("a/b"))

    c = Client(app())

    response = c.get("/foo/a")
    assert response.body == b"a"

    response = c.get("/foo")
    assert response.body == b""

    response = c.get("/foo/a/b")
    assert response.body == b"a/b"

    # link to a/b absorb
    response = c.get("/")
    assert response.body == b"http://localhost/foo/a/b"


def test_absorb_path_with_variables() -> None:
    class app(morepath.App):
        pass

    class Root:
        pass

    class Model:
        def __init__(self, id: str, absorb: str) -> None:
            self.id = id
            self.absorb = absorb

    @app.path(model=Root, path="")
    def get_root() -> Root:
        return Root()

    @app.path(model=Model, path="{id}", absorb=True)
    def get_model(id: str, absorb: str) -> Model:
        return Model(id, absorb)

    @app.view(model=Model)
    def default(self: Model, request: morepath.Request) -> str:
        return f"I:{self.id} A:{self.absorb}"

    @app.view(model=Root)
    def default_root(self: Root, request: morepath.Request) -> str:
        return request.link(Model("foo", "a/b"))

    c = Client(app())

    response = c.get("/foo/a")
    assert response.body == b"I:foo A:a"

    response = c.get("/foo")
    assert response.body == b"I:foo A:"

    response = c.get("/foo/a/b")
    assert response.body == b"I:foo A:a/b"

    # link to a/b absorb
    response = c.get("/")
    assert response.body == b"http://localhost/foo/a/b"


def test_absorb_path_explicit_subpath_ignored() -> None:
    class app(morepath.App):
        pass

    class Root:
        pass

    class Model:
        def __init__(self, absorb: str) -> None:
            self.absorb = absorb

    class Another:
        pass

    @app.path(model=Root, path="")
    def get_root() -> Root:
        return Root()

    @app.path(model=Model, path="foo", absorb=True)
    def get_model(absorb: str) -> Model:
        return Model(absorb)

    @app.path(model=Another, path="foo/another")
    def get_another() -> Another:
        return Another()

    @app.view(model=Model)
    def default(self: Model, request: morepath.Request) -> str:
        return "%s" % self.absorb

    @app.view(model=Another)
    def default_another(self: Another, request: morepath.Request) -> str:
        return "Another"

    @app.view(model=Root)
    def default_root(self: Root, request: morepath.Request) -> str:
        return request.link(Another())

    c = Client(app())

    response = c.get("/foo/a")
    assert response.body == b"a"

    response = c.get("/foo/another")
    assert response.body == b"another"

    # link to another still works XXX is this wrong?
    response = c.get("/")
    assert response.body == b"http://localhost/foo/another"


def test_absorb_path_root() -> None:
    class app(morepath.App):
        pass

    class Model:
        def __init__(self, absorb: str) -> None:
            self.absorb = absorb

    @app.path(model=Model, path="", absorb=True)
    def get_model(absorb: str) -> Model:
        return Model(absorb)

    @app.view(model=Model)
    def default(self: Model, request: morepath.Request) -> str:
        return f"A:{self.absorb} L:{request.link(self)}"

    c = Client(app())

    response = c.get("/a")
    assert response.body == b"A:a L:http://localhost/a"

    response = c.get("/")
    assert response.body == b"A: L:http://localhost/"

    response = c.get("/a/b")
    assert response.body == b"A:a/b L:http://localhost/a/b"


def test_path_explicit_variables() -> None:
    class App(morepath.App):
        pass

    class Model:
        def __init__(self, id: str) -> None:
            self.store_id = id

    @App.path(
        model=Model, path="models/{id}", variables=lambda m: {"id": m.store_id}
    )
    def get_model(id: str) -> Model:
        return Model(id)

    @App.view(model=Model)
    def default(self: Model, request: morepath.Request) -> str:
        return request.link(self)

    c = Client(App())

    response = c.get("/models/1")
    assert response.body == b"http://localhost/models/1"


def test_path_explicit_variables_app_arg() -> None:
    class App(morepath.App):
        pass

    class Model:
        def __init__(self, id: str) -> None:
            self.store_id = id

    def my_variables(app: App, m: Model) -> dict[str, str]:
        assert isinstance(app, App)
        return {"id": m.store_id}

    @App.path(model=Model, path="models/{id}", variables=my_variables)
    def get_model(id: str) -> Model:
        return Model(id)

    @App.view(model=Model)
    def default(self: Model, request: morepath.Request) -> str:
        return request.link(self)

    c = Client(App())

    response = c.get("/models/1")
    assert response.body == b"http://localhost/models/1"


def test_error_when_path_variable_is_none() -> None:
    class App(morepath.App):
        pass

    class Model:
        def __init__(self, id: str) -> None:
            self.store_id = id

    @App.path(model=Model, path="models/{id}", variables=lambda m: {"id": None})
    def get_model(id: str) -> Model:
        return Model(id)

    @App.view(model=Model)
    def default(self: Model, request: morepath.Request) -> str:
        return request.link(self)

    c = Client(App())

    with pytest.raises(LinkError):
        c.get("/models/1")


def test_error_when_path_variable_is_missing() -> None:
    class App(morepath.App):
        pass

    class Model:
        def __init__(self, id: str) -> None:
            self.store_id = id

    @App.path(model=Model, path="models/{id}", variables=lambda m: {})
    def get_model(id: str) -> Model:
        return Model(id)

    @App.view(model=Model)
    def default(self: Model, request: morepath.Request) -> str:
        return request.link(self)

    c = Client(App())

    with pytest.raises(KeyError):
        c.get("/models/1")


def test_error_when_path_variables_isnt_dict() -> None:
    class App(morepath.App):
        pass

    class Model:
        def __init__(self, id: str) -> None:
            self.store_id = id

    @App.path(model=Model, path="models/{id}", variables=lambda m: "nondict")  # type: ignore
    def get_model(id: str) -> Model:
        return Model(id)

    @App.view(model=Model)
    def default(self: Model, request: morepath.Request) -> str:
        return request.link(self)

    c = Client(App())

    with pytest.raises(LinkError):
        c.get("/models/1")


def test_resolve_path_method_on_request_same_app() -> None:
    class App(morepath.App):
        pass

    class Model:
        def __init__(self) -> None:
            pass

    @App.path(model=Model, path="simple")
    def get_model() -> Model:
        return Model()

    @App.view(model=Model)
    def default(self: Model, request: morepath.Request) -> str:
        return str(isinstance(request.resolve_path("simple"), Model))

    @App.view(model=Model, name="extra")
    def extra(self: Model, request: morepath.Request) -> str:
        return str(request.resolve_path("nonexistent") is None)

    @App.view(model=Model, name="appnone")
    def appnone(self: Model, request: morepath.Request) -> object:
        return request.resolve_path("simple", app=None)  # type: ignore

    c = Client(App())

    response = c.get("/simple")
    assert response.body == b"True"
    response = c.get("/simple/extra")
    assert response.body == b"True"
    with pytest.raises(LinkError):
        c.get("/simple/appnone")


def test_resolve_path_method_on_request_different_app() -> None:
    class App(morepath.App):
        pass

    class Model:
        def __init__(self) -> None:
            pass

    @App.path(model=Model, path="simple")
    def get_model() -> Model:
        return Model()

    @App.view(model=Model)
    def default(self: Model, request: morepath.Request) -> str:
        child = request.app.child("sub")
        assert child is not None
        obj = request.resolve_path("p", app=child)
        return str(isinstance(obj, SubModel))

    class Sub(morepath.App):
        pass

    class SubModel:
        pass

    @Sub.path(model=SubModel, path="p")
    def get_sub_model() -> SubModel:
        return SubModel()

    @App.mount(path="sub", app=Sub)
    def mount_sub() -> Sub:
        return Sub()

    c = Client(App())

    response = c.get("/simple")
    assert response.body == b"True"


def test_resolve_path_with_dots_in_url() -> None:
    class app(morepath.App):
        pass

    class Root:
        def __init__(self, absorb: str) -> None:
            self.absorb = absorb

    @app.path(model=Root, path="root", absorb=True)
    def get_root(absorb: str) -> Root:
        return Root(absorb)

    @app.view(model=Root)
    def default(self: Root, request: morepath.Request) -> str:
        return "%s" % self.absorb

    c = Client(app())

    response = c.get("/root/x/../child")
    assert response.body == b"child"

    response = c.get("/root/x/%2E%2E/child")
    assert response.body == b"child"

    response = c.get("/root/%2E%2E/%2E%2E/root")
    assert response.body == b""

    response = c.get("/root/%2E%2E/%2E%2E/root")
    assert response.body == b""

    response = c.get("/root/%2E%2E/%2E%2E/test", expect_errors=True)
    assert response.status_code == 404


def test_quoting_link_generation() -> None:
    class App(morepath.App):
        pass

    class Model:
        def __init__(self) -> None:
            pass

    @App.path(model=Model, path="sim?ple")
    def get_model() -> Model:
        return Model()

    @App.view(model=Model)
    def default(self: Model, request: morepath.Request) -> str:
        return "View"

    @App.view(model=Model, name="link")
    def link(self: Model, request: morepath.Request) -> str:
        return request.link(self)

    c = Client(App())

    response = c.get("/sim%3Fple")
    assert response.body == b"View"

    response = c.get("/sim%3Fple/link")
    assert response.body == b"http://localhost/sim%3Fple"


def test_quoting_link_generation_umlaut() -> None:
    class App(morepath.App):
        pass

    class Model:
        def __init__(self) -> None:
            pass

    @App.path(model=Model, path="simëple")
    def get_model() -> Model:
        return Model()

    @App.view(model=Model)
    def default(self: Model, request: morepath.Request) -> str:
        return "View"

    @App.view(model=Model, name="link")
    def link(self: Model, request: morepath.Request) -> str:
        return request.link(self)

    c = Client(App())

    response = c.get("/sim%C3%ABple")
    assert response.body == b"View"

    response = c.get("/sim%C3%ABple/link")
    assert response.body == b"http://localhost/sim%C3%ABple"


def test_quoting_link_generation_tilde() -> None:
    # tilde is an unreserved character according to
    # https://www.ietf.org/rfc/rfc3986.txt but urllib.quote
    # quotes it anyway. We test whether our workaround using
    # the safe parameter works

    class App(morepath.App):
        pass

    class Model:
        def __init__(self) -> None:
            pass

    @App.path(model=Model, path="sim~ple")
    def get_model() -> Model:
        return Model()

    @App.view(model=Model)
    def default(self: Model, request: morepath.Request) -> str:
        return "View"

    @App.view(model=Model, name="link")
    def link(self: Model, request: morepath.Request) -> str:
        return request.link(self)

    c = Client(App())

    response = c.get("/sim~ple")
    assert response.body == b"View"

    response = c.get("/sim~ple/link")
    assert response.body == b"http://localhost/sim~ple"


def test_parameter_quoting() -> None:
    class App(morepath.App):
        pass

    class Model:
        def __init__(self, s: str | None) -> None:
            self.s = s

    @App.path(model=Model, path="")
    def get_model(s: str | None) -> Model:
        return Model(s)

    @App.view(model=Model)
    def default(self: Model, request: morepath.Request) -> str:
        return "View: %s" % self.s

    @App.view(model=Model, name="link")
    def link(self: Model, request: morepath.Request) -> str:
        return request.link(self)

    c = Client(App())

    response = c.get("/?s=sim%C3%ABple")
    assert response.body == "View: simëple".encode()

    response = c.get("/link?s=sim%C3%ABple")
    assert response.body == b"http://localhost/?s=sim%C3%ABple"


def test_parameter_quoting_tilde() -> None:
    class App(morepath.App):
        pass

    class Model:
        def __init__(self, s: str | None) -> None:
            self.s = s

    @App.path(model=Model, path="")
    def get_model(s: str | None) -> Model:
        return Model(s)

    @App.view(model=Model)
    def default(self: Model, request: morepath.Request) -> str:
        return "View: %s" % self.s

    @App.view(model=Model, name="link")
    def link(self: Model, request: morepath.Request) -> str:
        return request.link(self)

    c = Client(App())

    response = c.get("/?s=sim~ple")
    assert response.body == b"View: sim~ple"

    response = c.get("/link?s=sim~ple")
    assert response.body == b"http://localhost/?s=sim~ple"


def test_class_link_without_variables() -> None:
    class App(morepath.App):
        pass

    class Model:
        pass

    @App.path(model=Model, path="/foo")
    def get_model() -> Model:
        return Model()

    @App.view(model=Model)
    def link(self: Model, request: morepath.Request) -> str:
        return request.class_link(Model)

    c = Client(App())

    response = c.get("/foo")
    assert response.body == b"http://localhost/foo"


def test_class_link_no_app() -> None:
    class App(morepath.App):
        pass

    class Model:
        pass

    @App.path(model=Model, path="/foo")
    def get_model() -> Model:
        return Model()

    @App.view(model=Model)
    def link(self: Model, request: morepath.Request) -> str:
        return request.class_link(Model, app=None)  # type: ignore

    c = Client(App())

    with pytest.raises(LinkError):
        c.get("/foo")


def test_class_link_with_variables() -> None:
    class App(morepath.App):
        pass

    class Model:
        pass

    @App.path(model=Model, path="/foo/{x}")
    def get_model(x: str) -> Model:
        return Model()

    @App.view(model=Model)
    def link(self: Model, request: morepath.Request) -> str:
        return request.class_link(Model, variables={"x": "X"})

    c = Client(App())

    response = c.get("/foo/3")
    assert response.body == b"http://localhost/foo/X"


def test_class_link_with_missing_variables() -> None:
    class App(morepath.App):
        pass

    class Model:
        pass

    @App.path(model=Model, path="/foo/{x}")
    def get_model(x: str) -> Model:
        return Model()

    @App.view(model=Model)
    def link(self: Model, request: morepath.Request) -> str:
        return request.class_link(Model, variables={})

    c = Client(App())

    with pytest.raises(KeyError):
        c.get("/foo/3")


def test_class_link_with_extra_variable() -> None:
    class App(morepath.App):
        pass

    class Model:
        pass

    @App.path(model=Model, path="/foo/{x}")
    def get_model(x: str) -> Model:
        return Model()

    @App.view(model=Model)
    def link(self: Model, request: morepath.Request) -> str:
        return request.class_link(Model, variables={"x": "X", "y": "Y"})

    c = Client(App())

    response = c.get("/foo/3")
    assert response.body == b"http://localhost/foo/X"


def test_class_link_with_url_parameter_variable() -> None:
    class App(morepath.App):
        pass

    class Model:
        pass

    @App.path(model=Model, path="/foo/{x}")
    def get_model(x: str, y: str) -> Model:
        return Model()

    @App.view(model=Model)
    def link(self: Model, request: morepath.Request) -> str:
        return request.class_link(Model, variables={"x": "X", "y": "Y"})

    c = Client(App())

    response = c.get("/foo/3")
    assert response.body == b"http://localhost/foo/X?y=Y"


def test_class_link_with_subclass() -> None:
    class App(morepath.App):
        pass

    class Model:
        pass

    class Sub(Model):
        pass

    @App.path(model=Model, path="/foo/{x}")
    def get_model(x: str) -> Model:
        return Model()

    @App.view(model=Model)
    def link(self: Model, request: morepath.Request) -> str:
        return request.class_link(Sub, variables={"x": "X"})

    c = Client(App())

    response = c.get("/foo/3")
    assert response.body == b"http://localhost/foo/X"


def test_absorb_class_path() -> None:
    class App(morepath.App):
        pass

    class Root:
        pass

    class Model:
        def __init__(self, absorb: str) -> None:
            self.absorb = absorb

    @App.path(model=Root, path="")
    def get_root() -> Root:
        return Root()

    @App.path(model=Model, path="foo", absorb=True)
    def get_model(absorb: str) -> Model:
        return Model(absorb)

    @App.view(model=Model)
    def default(self: Model, request: morepath.Request) -> str:
        return "%s" % self.absorb

    @App.view(model=Root)
    def default_root(self: Root, request: morepath.Request) -> str:
        return request.class_link(Model, variables={"absorb": "a/b"})

    c = Client(App())

    # link to a/b absorb
    response = c.get("/")
    assert response.body == b"http://localhost/foo/a/b"


def test_absorb_class_path_with_variables() -> None:
    class App(morepath.App):
        pass

    class Root:
        pass

    class Model:
        def __init__(self, id: str, absorb: str) -> None:
            self.id = id
            self.absorb = absorb

    @App.path(model=Root, path="")
    def get_root() -> Root:
        return Root()

    @App.path(model=Model, path="{id}", absorb=True)
    def get_model(id: str, absorb: str) -> Model:
        return Model(id, absorb)

    @App.view(model=Model)
    def default(self: Model, request: morepath.Request) -> str:
        return f"I:{self.id} A:{self.absorb}"

    @App.view(model=Root)
    def default_root(self: Root, request: morepath.Request) -> str:
        return request.class_link(Model, variables=dict(id="foo", absorb="a/b"))

    c = Client(App())

    # link to a/b absorb
    response = c.get("/")
    assert response.body == b"http://localhost/foo/a/b"


def test_class_link_extra_parameters() -> None:
    class App(morepath.App):
        pass

    class Model:
        def __init__(self, extra_parameters: dict[str, str]) -> None:
            self.extra_parameters = extra_parameters

    @App.path(model=Model, path="/")
    def get_model(extra_parameters: dict[str, str]) -> Model:
        return Model(extra_parameters)

    @App.view(model=Model)
    def default(self: Model, request: morepath.Request) -> str:
        return repr(sorted(self.extra_parameters.items()))

    @App.view(model=Model, name="link")
    def link(self: Model, request: morepath.Request) -> str:
        return request.class_link(
            Model, variables={"extra_parameters": {"a": "A", "b": "B"}}
        )

    c = Client(App())

    response = c.get("/link?a=A&b=B")
    assert sorted(response.body[len("http://localhost/?") :].split(b"&")) == [
        b"a=A",
        b"b=B",
    ]


def test_path_on_model_class() -> None:
    class App(morepath.App):
        pass

    @App.path("/")
    class Model:
        def __init__(self) -> None:
            pass

    @App.path("/login")
    class Login:
        pass

    @App.view(model=Model)
    def model_view(self: Model, request: morepath.Request) -> str:
        return "Model"

    @App.view(model=Login)
    def login_view(self: Login, request: morepath.Request) -> str:
        return "Login"

    c = Client(App())

    response = c.get("/")
    assert response.body == b"Model"
    response = c.get("/login")
    assert response.body == b"Login"


def test_path_without_model() -> None:
    class App(morepath.App):
        pass

    @App.path("/")
    def get_path() -> None:
        pass

    with pytest.raises(dectate.DirectiveReportError):
        App.commit()


def test_two_path_on_same_model_should_conflict() -> None:
    class App(morepath.App):
        pass

    @App.path("/login")
    @App.path("/")
    class Login:
        pass

    with pytest.raises(dectate.ConflictError):
        App.commit()


def test_path_on_same_model_explicit_and_class_should_conflict() -> None:
    class App(morepath.App):
        pass

    @App.path("/")
    class Login:
        pass

    @App.path("/login", model=Login)
    def get_path() -> Login:
        return Login()

    with pytest.raises(dectate.ConflictError):
        App.commit()


def test_nonexisting_path_too_long_unconsumed() -> None:
    class App(morepath.App):
        pass

    class Model:
        def __init__(self) -> None:
            pass

    @App.path(model=Model, path="simple")
    def get_model() -> Model:
        return Model()

    @App.view(model=Model)
    def default(self: Model, request: morepath.Request) -> str:
        return "View"

    c = Client(App())

    c.get("/foo/bar/baz", status=404)


def test_collection_and_item() -> None:
    class App(morepath.App):
        pass

    class Collection:
        def __init__(self) -> None:
            self.items: dict[str, Item] = {}

    class Item:
        def __init__(self, id: str) -> None:
            self.id = id

    collection = Collection()
    collection.items["a"] = Item("a")
    collection.items["b"] = Item("b")

    @App.path(model=Collection, path="/")
    def get_collection() -> Collection:
        return collection

    @App.path(model=Item, path="/{id}")
    def get_item(id: str) -> Item | None:
        return collection.items.get(id)

    @App.view(model=Collection)
    def default_collection(self: str, request: morepath.Request) -> str:
        return "Collection"

    @App.view(model=Item)
    def default(self: Item, request: morepath.Request) -> str:
        return "View: %s" % self.id

    c = Client(App())

    r = c.get("/c", status=404)
    assert r.body != b"Collection"

    r = c.get("/a")
    assert r.body == b"View: a"


def test_view_for_missing() -> None:
    class App(morepath.App):
        pass

    class Item:
        def __init__(self, id: str) -> None:
            self.id = id

    @App.path(model=Item, path="/{id}")
    def get_item(id: str) -> Item | None:
        if id == "found":
            return Item(id)
        return None

    @App.view(model=Item, name="edit")
    def default(self: Item, request: morepath.Request) -> str:
        return "View: %s" % self.id

    c = Client(App())

    c.get("/notfound/+edit", status=404)

    c.get("/notfound/edit", status=404)


def test_absorb_error() -> None:
    class App(morepath.App):
        pass

    @App.path("/")
    class Root:
        pass

    @App.view(model=Root)
    def view_root(self: Root, request: morepath.Request) -> str:
        return "root"

    class File:
        def __init__(self, absorb: str) -> None:
            self.absorb = absorb

    @App.path("/files", model=File, absorb=True)
    def get_file(absorb: str) -> File | None:
        if absorb == "foo":
            return File("foo")
        return None

    @App.view(model=File)
    def view_file(self: File, request: morepath.Request) -> str:
        return request.path

    App.commit()

    client = Client(App())
    assert client.get("/").text == "root"
    assert client.get("/files/foo").text == "/files/foo"
    client.get("/files/bar", status=404)


def test_named_view_on_root() -> None:
    class App(morepath.App):
        pass

    @App.path(path="/")
    class Root:
        pass

    @App.view(model=Root, name="named")
    def named(self: Root, request: morepath.Request) -> str:
        return "Named view on root"

    @App.view(model=Root)
    def default(self: Root, request: morepath.Request) -> str:
        return "Default view on root"

    c = Client(App())

    response = c.get("/named")
    assert response.body == b"Named view on root"

    response = c.get("/+named")
    assert response.body == b"Named view on root"

    response = c.get("/")
    assert response.body == b"Default view on root"
