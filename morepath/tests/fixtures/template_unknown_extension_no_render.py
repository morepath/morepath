from __future__ import annotations

from typing import TYPE_CHECKING, Any

import morepath

from .template_engine import FormatLoader

if TYPE_CHECKING:
    from morepath.settings import SettingRegistry
    from morepath.types import StrPath


class App(morepath.App):
    pass


@App.path(path="{name}")
class Person:
    def __init__(self, name: str):
        self.name = name


@App.template_loader(extension=".unknown")
def get_template_loader(
    template_directories: list[StrPath], settings: SettingRegistry
) -> FormatLoader:
    return FormatLoader(template_directories)


@App.template_directory()
def get_template_directory() -> str:
    return "templates"


@App.html(model=Person, template="person.unknown")
def person_default(self: Person, request: morepath.Request) -> dict[str, Any]:
    return {"name": self.name}
