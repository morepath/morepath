from __future__ import annotations

from typing import TYPE_CHECKING, Any

import morepath

from .template_engine import FormatLoader

if TYPE_CHECKING:
    from collections.abc import Mapping

    from webob import Response as BaseResponse

    from morepath.settings import SettingRegistry
    from morepath.types import Render, StrPath


class App(morepath.App):
    pass


@App.path(path="{name}")
class Person:
    def __init__(self, name: str):
        self.name = name


@App.template_directory()
def get_template_directory() -> str:
    return "templates"


@App.template_loader(extension=".format")
def get_template_loader(
    template_directories: list[StrPath], settings: SettingRegistry
) -> FormatLoader:
    return FormatLoader(template_directories)


@App.template_render(extension=".format")
def get_format_render(
    loader: FormatLoader, name: str, original_render: Render
) -> Render:
    template = loader.get(name)

    def render(
        content: Mapping[str, object], request: morepath.Request
    ) -> BaseResponse:
        assert template is not None
        return original_render(template.render(**content), request)

    return render


@App.html(model=Person, template="person.format")
def person_default(self: Person, request: morepath.Request) -> dict[str, Any]:
    return {"name": self.name}


class SubApp(App):
    pass


@SubApp.template_directory(before=get_template_directory)
def get_template_directory_override() -> str:
    return "templates2"
