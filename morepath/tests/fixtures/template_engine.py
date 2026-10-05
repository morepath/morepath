from __future__ import annotations

import os
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from morepath.types import StrPath


class FormatTemplate:
    def __init__(self, text: str):
        self.text = text

    def render(self, **kw: object) -> str:
        return self.text.format(**kw)


class FormatLoader:
    def __init__(self, template_directories: list[StrPath]):
        self.template_directories = template_directories

    def get(self, name: str) -> FormatTemplate | None:
        for template_directory in self.template_directories:
            path = os.path.join(template_directory, name)
            if not os.path.exists(path):
                continue
            with open(path) as f:
                return FormatTemplate(f.read())
        return None
