"""This module defines a registry of settings.

See :class:`morepath.directive.SettingRegistry`
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Callable


class SettingRegistry:
    """Registry of settings.

    Used by the :class:`morepath.App.setting` directive and
    :class:`morepath.App.setting_section` directives.

    Stores sections as attributes, which then have the settings as
    attributes.

    This settings registry is exposed through
    :attr:`morepath.App.settings`.
    """

    def register_setting(
        self, section_name: str, setting_name: str, func: Callable[[], object]
    ) -> None:
        """Register a setting.

        :param section_name: name of section to register in
        :param setting_name: name of setting
        :param func: function that when called without arguments
          creates the setting value.
        """
        section = getattr(self, section_name, None)
        if section is None:
            section = SettingSection()
            setattr(self, section_name, section)
        setattr(section, setting_name, func())

    if TYPE_CHECKING:
        # NOTE: Let type checkers know about dynamic attributes
        def __getattr__(self, name: str) -> SettingSection:
            raise NotImplementedError


class SettingSection:
    """A setting section that contains setting."""

    if TYPE_CHECKING:
        # NOTE: Let type checkers know about dynamic attributes
        def __getattr__(self, name: str) -> Any:
            raise NotImplementedError

        def __setattr__(self, name: str, value: Any) -> None:
            pass
