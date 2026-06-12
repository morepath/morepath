from __future__ import annotations

from typing import TYPE_CHECKING

from webtest import TestApp as Client

from morepath import App, render_json

if TYPE_CHECKING:
    from webob import Response as BaseResponse

    from morepath import Request
    from morepath.types import Tween


def test_request_reset() -> None:
    # In order to  verify the behaviour of Request.reset  we issue the
    # same request three times:
    #
    # 1. The server responds successfully (generate_error = False)
    #
    # 2. The server responds with an error (generate_error = True) and
    # returns the request as it was when the exception was thrown
    # (reset_request = False).
    #
    # 3. The server responds with an error (generate_error = True) and
    # returns the request as it was when it was received
    # (reset_request = True).

    generate_error = False
    reset_request = False

    class RootApp(App):
        pass

    @RootApp.tween_factory()
    def report_error(app: RootApp, handler: Tween) -> Tween:
        def tween(request: Request) -> BaseResponse:
            try:
                response = handler(request)
                response.headers["Tween-Header"] = "FOO"
                return response
            except RuntimeError:
                if reset_request:
                    request.reset()
                response = render_json(
                    {
                        "app": repr(type(request.app)),
                        "unconsumed": request.unconsumed,
                    },
                    request,
                )
                response.status_code = 500
                return response

        return tween

    class MountedApp(App):
        pass

    @MountedApp.path(path="catalog")
    class Catalog:
        pass

    @MountedApp.view(model=Catalog, name="text")
    def view_catalog(self: Catalog, request: Request) -> str:
        if generate_error:
            raise RuntimeError("Error!")
        return "The catalog"

    RootApp.mount(app=MountedApp, path="mount")(MountedApp)

    c = Client(RootApp())

    response = c.get("/mount/catalog/text")
    assert response.text == "The catalog"
    assert response.headers["Tween-Header"] == "FOO"

    generate_error = True
    response = c.get("/mount/catalog/text", status=500)
    assert response.json == {"app": repr(MountedApp), "unconsumed": ["text"]}

    reset_request = True
    response = c.get("/mount/catalog/text", status=500)
    assert response.json == {
        "app": repr(RootApp),
        "unconsumed": ["text", "catalog", "mount"],
    }
