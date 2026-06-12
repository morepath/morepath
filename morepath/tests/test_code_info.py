from __future__ import annotations

import morepath


def test_code_info() -> None:
    class App(morepath.App):
        pass

    @App.path(path="")
    class Model:
        def __init__(self) -> None:
            pass

    @App.view(model=Model)
    def default(self: Model, request: object) -> str:
        return "View"

    App.commit()
    app = App()

    r = morepath.Request.blank("/", method="GET", app=app)
    app.publish(r)
    assert r.path_code_info is not None
    assert r.path_code_info.sourceline == '@App.path(path="")'
    assert r.view_code_info is not None
    assert r.view_code_info.sourceline == "@App.view(model=Model)"


def test_code_info_no_path() -> None:
    class App(morepath.App):
        pass

    App.commit()
    app = App()

    r = morepath.Request.blank("/", method="GET", app=app)
    app.publish(r)
    assert r.path_code_info is None
    assert r.view_code_info is not None
