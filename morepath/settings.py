
def register_setting(app, section_name, value_name, func):
    settings = app.settings
    section = getattr(settings, section_name, None)
    if section is None:
        section = SettingSection()
        setattr(settings, section_name, section)
    setattr(section, value_name, func())


class SettingSectionContainer(object):
    pass


class SettingSection(object):
    pass
