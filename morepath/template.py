"""This module lets you register template engines.

See :class:`morepath.directive.TemplateEngineRegistry`
"""

import os
from .toposort import toposorted, Info
from .error import ConfigError, TopologicalSortError
from .settings import SettingRegistry


class TemplateEngineRegistry(object):
    """A registry of template engines.

    Is used by the :meth:`morepath.App.view`,
    :meth:`morepath.App.json` and :meth:`morepath.App.html` directives
    for template-based rendering.

    :param setting_registry: a :class:`morepath.directive.SettingRegistry`
      instance.

    """
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
        """Register a directory to look for templates.

        Used by the :meth:`morepath.App.template_directory` directive.

        :param key: unique key identifying this directory
        :param directory: absolute path to template directory
        :param before: key to before in template lookup
        :param after: key to sort after in template lookup
        :param configurable: :class:`dectate.Configurable` used that
          registered this template directory. Used for implicit
          sorting by app inheritance.
        """
        self._template_directory_infos.append(
            TemplateDirectoryInfo(key, directory, before, after, configurable))
        self._template_configurable_to_keys.setdefault(
            configurable, []).append(key)

    def register_template_render(self, extension, func):
        """Register way to get a view render function for a file extension.

        Used by the :meth:`morepath.App.template_render` directive. See
        there for more information about parameters.

        :param extension: template extension like ``.pt``
        :param func: function that given loader, name and original_renderer
          constructs a view ``render`` function.
        """
        self._template_renders[extension] = func

    def initialize_template_loader(self, extension, func):
        """Initialize a template loader for an extension.

        Used by the :meth:`morepath.App.template_loader` directive.

        :param extension: template extension like ``.p.t``
        :param func: function that given a list of template directories
          returns a load object that be used to load the template for use.
        """
        self._template_loaders[extension] = func(
            self.sorted_template_directories(), self._setting_registry)

    def sorted_template_directories(self):
        """Get sorted template directories.

        Use explicit ``before`` and ``after`` information but also
        App inheritance to sort template directories in order of template
        lookup.

        :return: a list of template directory paths in the right order
        """
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
        """Get a template render function.

        :param name: filename of the template (with extension, without path),
          such as ``foo.pt``.
        :param original_render: ``render`` function supplied with the view
          directive.
        :return: a ``render`` function that uses the template to render
          the result of a view function.
        """
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


class TemplateDirectoryInfo(Info):
    """Used by :class:`TemplateEngineRegistry` internally.
    """
    def __init__(self, key, directory, before, after, configurable):
        super(TemplateDirectoryInfo, self).__init__(key, before, after)
        self.directory = directory
        self.configurable = configurable
