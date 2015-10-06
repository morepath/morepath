import morepath


class App(morepath.App):
    pass


@App.setting_section(section='config')
def get_setting_section_a():
    return {
        'foo': 'FOO'
    }


@App.setting_section(section='config')
def get_setting_section_b():
    return {
        'foo': 'BAR'
    }
