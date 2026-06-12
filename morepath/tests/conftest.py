from __future__ import annotations

from typing import TYPE_CHECKING, Any, NoReturn

import pytest

if TYPE_CHECKING:
    from collections.abc import Iterable


@pytest.fixture
def mockserver(monkeypatch: pytest.MonkeyPatch) -> MockServer:
    """Make the server in wsgiref receive Ctrl-C as soon as it starts serving.

    The fixture object provides these methods:
        * set_argv(list): set the command-line arguments seen by morepath.run
        * run(*args, **kw): run morepath.run and return the exit code

    """
    import sys
    from wsgiref.simple_server import WSGIServer

    def mock_serve_forever(self: WSGIServer) -> NoReturn:
        raise KeyboardInterrupt

    monkeypatch.setattr(WSGIServer, "serve_forever", mock_serve_forever)
    argv = ["script-name"]
    monkeypatch.setattr(sys, "argv", argv)
    return MockServer(argv)


class MockServer:
    def __init__(self, argv: list[str]) -> None:
        self.argv = argv

    def set_argv(self, argv: Iterable[str]) -> None:
        """Set the command-line arguments seen by morepath.run."""
        self.argv.extend(argv)

    def run(self, *args: Any, **kw: Any) -> str | int | None:
        """Wrapper around morepath.run to catch SystemExit.

        :return: the exit code."""
        import morepath

        with pytest.raises(SystemExit) as ex:
            morepath.run(*args, **kw)

        return ex.value.code
