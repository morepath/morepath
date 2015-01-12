import os
from .toposort import toposorted


class TemplateDirectoryInfo(object):
    def __init__(self, key, directory, over, under):
        self.key = key
        self.directory = directory
        if over is not None:
            over = [over]
        else:
            over = []
        if under is not None:
            under = [under]
        else:
            under = []
        self.over = over
        self.under = under

    def before(self):
        return self.over

    def after(self):
        return self.under


class TemplateEngineRegistry(object):
    def __init__(self):
        self.clear()

    def clear(self):
        self._template_loaders = {}
        self._template_renders = {}
        self._template_directory_infos = []

    def register_template_directory_info(self, key,
                                         directory, over, under, app):
        self._template_directory_infos.append(
            TemplateDirectoryInfo(key, directory, over, under))

    def register_template_render(self, extension, func):
        self._template_renders[extension] = func

    def initialize_template_loader(self, extension, func):
        self._template_loaders[extension] = func(
            self.sorted_template_directories(), self.settings)

    def sorted_template_directories(self):
        return [info.directory for info in
                toposorted(self._template_directory_infos)]

    def get_template_render(self, name, original_render):
        _, extension = os.path.splitext(name)
        loader = self._template_loaders.get(extension)
        get_render = self._template_renders.get(extension)
        return get_render(loader, name, original_render)
