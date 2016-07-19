import morepath
from morepath.tween import TweenRegistry
from morepath.error import TopologicalSortError
import pytest
from webtest import TestApp as Client


def test_tween_sorting_no_tweens():
    reg = TweenRegistry()
    assert reg.sorted_tween_factories() == []


def test_tween_sorting_one_tween():
    reg = TweenRegistry()

    def foo():
        pass

    reg.register_tween_factory(foo, over=None, under=None)
    assert reg.sorted_tween_factories() == [foo]


def test_tween_sorting_two_tweens_under():
    reg = TweenRegistry()

    def top():
        pass

    def bottom():
        pass

    reg.register_tween_factory(top, over=None, under=None)
    reg.register_tween_factory(bottom, over=None, under=top)
    assert reg.sorted_tween_factories() == [top, bottom]


def test_tween_sorting_two_tweens_under_reverse_reg():
    reg = TweenRegistry()

    def top():
        pass

    def bottom():
        pass

    reg.register_tween_factory(bottom, over=None, under=top)
    reg.register_tween_factory(top, over=None, under=None)
    assert reg.sorted_tween_factories() == [top, bottom]


def test_tween_sorting_two_tweens_over():
    reg = TweenRegistry()

    def top():
        pass

    def bottom():
        pass

    reg.register_tween_factory(top, over=bottom, under=None)
    reg.register_tween_factory(bottom, over=None, under=None)
    assert reg.sorted_tween_factories() == [top, bottom]


def test_tween_sorting_two_tweens_over_reverse_reg():
    reg = TweenRegistry()

    def top():
        pass

    def bottom():
        pass

    reg.register_tween_factory(bottom, over=None, under=None)
    reg.register_tween_factory(top, over=bottom, under=None)
    assert reg.sorted_tween_factories() == [top, bottom]


def test_tween_sorting_three():
    reg = TweenRegistry()

    def a():
        pass

    def b():
        pass

    def c():
        pass

    reg.register_tween_factory(a, over=None, under=None)
    reg.register_tween_factory(b, over=None, under=a)
    reg.register_tween_factory(c, over=a, under=None)
    assert reg.sorted_tween_factories() == [c, a, b]


def test_tween_sorting_dag_error():
    reg = TweenRegistry()

    def a():
        pass

    reg.register_tween_factory(a, over=None, under=a)

    with pytest.raises(TopologicalSortError):
        reg.sorted_tween_factories()


def test_tween_sorting_dag_error2():
    reg = TweenRegistry()

    def a():
        pass

    reg.register_tween_factory(a, over=a, under=None)

    with pytest.raises(TopologicalSortError):
        reg.sorted_tween_factories()


def test_tween_sorting_dag_error3():
    reg = TweenRegistry()

    def a():
        pass

    def b():
        pass

    reg.register_tween_factory(a, over=b, under=None)
    reg.register_tween_factory(b, over=a, under=None)

    with pytest.raises(TopologicalSortError):
        reg.sorted_tween_factories()


def test_tween_sorting_dag_error4():
    reg = TweenRegistry()

    def a():
        pass

    def b():
        pass

    def c():
        pass

    reg.register_tween_factory(a, over=b, under=None)
    reg.register_tween_factory(b, over=c, under=None)
    reg.register_tween_factory(c, over=a, under=None)

    with pytest.raises(TopologicalSortError):
        reg.sorted_tween_factories()


def test_tween_directive():
    class app(morepath.App):
        pass

    @app.path(path='')
    class Root(object):
        pass

    @app.view(model=Root)
    def default(self, request):
        return "View"

    @app.tween_factory()
    def get_modify_response_tween(app, handler):
        def plusplustween(request):
            response = handler(request)
            response.headers['Tween-Header'] = 'FOO'
            return response
        return plusplustween

    c = Client(app())

    response = c.get('/')
    assert response.body == b'View'
    assert response.headers['Tween-Header'] == 'FOO'
