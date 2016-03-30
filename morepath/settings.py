

class SettingRegistry(object):
    def register_setting(self, section_name, value_name, func):
        section = getattr(self, section_name, None)
        if section is None:
            section = SettingSection()
            setattr(self, section_name, section)
        setattr(section, value_name, func())


class SettingSection(object):
    pass
