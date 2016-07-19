"""This module defines a registry of settings.

See :class:`morepath.directive.SettingRegistry`
"""


class SettingRegistry(object):
    """Registry of settings.

    Used by the :class:`morepath.App.setting` directive and
    :class:`morepath.App.setting_section` directives.

    Stores sections as attributes, which then have the settings as
    attributes.

    This settings registry is exposed through
    :attr:`morepath.App.settings`.
    """
    def register_setting(self, section_name, setting_name, func):
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


class SettingSection(object):
    """A setting section that contains setting.
    """
    pass
