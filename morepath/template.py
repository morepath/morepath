import os
from .toposort import toposorted, Info
from .error import ConfigError, TopologicalSortError
from .settings import SettingRegistry


class TemplateDirectoryInfo(Info):
    def __init__(self, key, directory, before, after, configurable):
        super(TemplateDirectoryInfo, self).__init__(key, before, after)
        self.directory = directory
        self.configurable = configurable


class TemplateEngineRegistry(object):
    factory_arguments = {
        'setting_registry': SettingRegistry
    }

    def __init__(self, setting_registry):
        self._setting_registry = setting_registry
        self._template_loaders = {}
        self._template_renders = {}
        self._template_directory_infos = []
        self._template_configurable_to_keys = {}

    def register_template_directory_info(self, key,
                                         directory, before, after,
                                         configurable):
        self._template_directory_infos.append(
            TemplateDirectoryInfo(key, directory, before, after, configurable))
        self._template_configurable_to_keys.setdefault(
            configurable, []).append(key)

    def register_template_render(self, extension, func):
        self._template_renders[extension] = func

    def initialize_template_loader(self, extension, func):
        self._template_loaders[extension] = func(
            self.sorted_template_directories(), self._setting_registry)

    def sorted_template_directories(self):
        # make sure that template directories defined in subclasses
        # override those in base classes
        for info in self._template_directory_infos:
            extra_before = []
            for base in info.configurable.extends:
                extra_before.extend(
                    self._template_configurable_to_keys.get(base, []))
            info.before.extend(extra_before)
        try:
            return [info.directory for info in
                    toposorted(self._template_directory_infos)]
        except TopologicalSortError:
            raise ConfigError(
                "Cannot sort template directories as dependency graph has "
                "cycles. Could be because explicit dependencies conflict with "
                "application inheritance.")

    def get_template_render(self, name, original_render):
        _, extension = os.path.splitext(name)
        loader = self._template_loaders.get(extension)
        if loader is None:
            raise ConfigError(
                "No template_loader configured for extension: %s" % extension)
        get_render = self._template_renders.get(extension)
        if get_render is None:
            raise ConfigError(
                "No template_render configured for extension: %s" % extension)
        return get_render(loader, name, original_render)
