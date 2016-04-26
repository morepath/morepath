"""
This module defines functionality to automatically configure Morepath.

:func:`morepath.scan`, :func:`morepath.autoscan`
are part of the public API.
"""

import sys
import importscan
import importlib
import pkg_resources

from .error import AutoImportError


def scan(package=None, ignore=None, handle_error=None):
    """Scan package for configuration actions (decorators).

    It scans by recursively importing the package and any modules
    in it, including any sub-packages.

    Register any found directives with their app classes.

    :param package: The Python module or package to scan. Optional; if left
      empty case the calling package is scanned.
    :param ignore: A list of packages to ignore. Optional. Defaults to
      ``['.test', '.tests']``. See :func:`importscan.scan` for details.
    :param handle_error: Optional error handling function. See
      :func:`importscan.scan` for details.
    """
    if package is None:
        package = caller_package()
    if ignore is None:
        ignore = ['.test', '.tests']
    importscan.scan(package, ignore, handle_error)


def autoscan(ignore=None):
    """Automatically load Morepath configuration from packages.

    Morepath configuration consists of decorator calls on :class:`App`
    instances, i.e. ``@App.view()`` and ``@App.path()``.

    This function tries to load needed Morepath configuration from all
    packages automatically. This only works if:

     - The package is made available using a ``setup.py`` file.

     - The package or a dependency of the package includes
       ``morepath`` in the ``install_requires`` list of the
       ``setup.py`` file.

     - The ``setup.py`` name is the same as the name of the
       distributed package or module. For example: if the module
       inside the package is named ``myapp`` the package must be named
       ``myapp`` as well (not ``my-app`` or ``MyApp``).

    If the ``setup.py`` name differs from the package name, it's
    possible to specify the module morepath should scan using entry
    points::

        setup(name='some-package',
          ...
          install_requires=[
              'setuptools',
              'morepath'
          ],
          entry_points={
              'morepath': [
                  'scan = somepackage',
              ]
          })

    This function simply recursively imports everything in those packages,
    except for test directories.

    In addition to calling this function you can also import modules
    that use Morepath directives manually, and you can use
    :func:`scan` to automatically import everything in a
    single package.

    Typically called immediately after startup just before the
    application starts serving using WSGI.

    ``autoscan`` always ignores ``.test`` and ``.tests``
    sub-packages -- these are assumed never to contain useful Morepath
    configuration and are not scanned.

    ``autoscan`` can fail with an ``ImportError`` when it tries to
    scan code that imports an optional dependency that is not
    installed. This happens most commonly in test code, which often
    rely on test-only dependencies such as ``pytest`` or ``nose``. If
    those tests are in a ``.test`` or ``.tests`` sub-package they
    are automatically ignored, however.

    If you have a special package with such expected import errors,
    you can exclude them from ``autoscan`` using the ``ignore``
    argument, for instance using ``['special_package']``. You then can
    use :func:`scan` for that package, with a custom
    ``ignore`` argument that excludes the modules that generate import
    errors.

    See also :func:`scan`.

    :param ignore: ignore to ignore some modules
      during scanning. Optional. If ommitted, ignore ``.test`` and
      ``.tests`` packages by default. See :func:`importscan.scan` for
      more details.

    """
    if ignore is None:
        ignore = []
        ignore.extend(['.test', '.tests'])
    for package in morepath_packages():
        importscan.scan(package, ignore)


def morepath_packages():
    """Iterable of modules that depend on morepath. Each such module is
    imported before it is returned.

    If the ``setup.py`` name differs from the name of the distributed
    package or module, the import will fail. See
    :func:`morepath.autoscan` for more information.

    :return: Iterable of modules that depend on Morepath. The modules
      are typically the ``__init__.py`` modules of packages as declared
      by ``setup.py``.

    """
    m = DependencyMap()
    m.load()

    for distribution in m.relevant_dists('morepath'):
        yield import_package(distribution)


def import_package(distribution):
    """
    Takes a pkg_resources distribution and loads the module contained
    in it, if it matches the rules layed out in :func:`morepath.autoscan`.
    """
    try:
        return importlib.import_module(get_module_name(distribution))
    except ImportError:
        raise AutoImportError(distribution.project_name)


class DependencyMap(object):
    """A registry that tracks dependencies between distributions.

    Used by :func:`morepath_packages` to find installed Python distributions
    that depend on Morepath, directly or indirectly.
    """
    def __init__(self):
        self._d = {}
        self._dists = {}

    def load(self):
        """Fill the registry with dependency information.
        """
        for dist in pkg_resources.working_set:
            self._dists[dist.project_name] = dist
            for r in dist.requires():
                self._d.setdefault(
                    dist.project_name, set()).add(r.project_name)

    def depends(self, project_name, on_project_name):
        """Check whether project transitively depends on another.

        A project depends on another project if it directly or
        indirectly requires the other project.

        :param project_name: Python distribution name.
        :param on_project_name: Python distribution name it depends on.
        :return: True if ``project_name`` depends on ``on_project_name``.
        """
        dependent_project_names = self._d.get(project_name, set())
        if on_project_name in dependent_project_names:
            return True
        for n in dependent_project_names:
            if self.depends(n, on_project_name):
                return True
        return False

    def relevant_dists(self, on_project_name):
        """Iterable of distributions that depend on project.

        Dependency is transitive.

        :param on_project_name: Python distribution name
        :return: iterable of Python distribution objects that depend on
          project
        """
        for dist in pkg_resources.working_set:
            if not self.depends(dist.project_name, on_project_name):
                continue
            yield dist


def get_module_name(distribution):
    """Determines the module name to import from the given distribution.

    If an entry point named ``scan`` is found in the group ``morepath``,
    it's value is used. If not, the project_name is used.

    See :func:`morepath.autoscan` for details and an example.
    """
    if hasattr(distribution, 'get_entry_map'):
        entry_points = distribution.get_entry_map('morepath')
    else:
        entry_points = None

    if entry_points and 'scan' in entry_points:
        return entry_points['scan'].module_name
    # use normal setuptools project name.
    # setuptools has the nasty habit to turn _ in package names
    # into -. We turn them back again.
    return distribution.project_name.replace('-', '_')


# taken from pyramid.path

def caller_module(level=2):
    """Give module where calling function is defined.

    :level: levels deep to look up the stack frame
    :return: a Python module
    """
    module_globals = sys._getframe(level).f_globals
    module_name = module_globals.get('__name__') or '__main__'
    module = sys.modules[module_name]
    return module


def caller_package(level=2):
    """Give package where calling function is defined.

    :level: levels deep to look up the stack frame
    :return: a Python module (representing the ``__init__.py`` of a package)
    """
    # caller_module in arglist for tests
    module = caller_module(level + 1)
    f = getattr(module, '__file__', '')
    if ('__init__.py' in f) or ('__init__$py' in f):  # empty at >>>
        # Module is a package
        return module
    # Go up one level to get package
    package_name = module.__name__.rsplit('.', 1)[0]
    return sys.modules[package_name]
