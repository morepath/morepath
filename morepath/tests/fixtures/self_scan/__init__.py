from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from types import ModuleType


def get_this_package() -> ModuleType:
    from morepath.autosetup import caller_package

    return caller_package(1)


def do_scan() -> None:
    import morepath

    morepath.scan()
