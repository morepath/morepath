import morepath


class App(morepath.App):
    pass


@App.setting_section(section="config")
def get_setting_section_a() -> dict[str, str]:
    return {"foo": "FOO"}


@App.setting_section(section="config")
def get_setting_section_b() -> dict[str, str]:
    return {"foo": "BAR"}
