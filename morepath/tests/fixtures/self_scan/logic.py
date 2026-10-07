from __future__ import annotations

from typing import TYPE_CHECKING

from .app import App

if TYPE_CHECKING:
    from morepath.request import Request


@App.path(path="/")
class Root:
    def __init__(self) -> None:
        self.value = "ROOT"


class Model:
    def __init__(self, id: str) -> None:
        self.id = id


@App.view(model=Root)
def root_default(self: Root, request: Request) -> str:
    return f"The root: {self.value}"
