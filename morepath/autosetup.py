import pkg_resources
from pkgutil import walk_packages
from morepath.core import setup


def autoconfig(ignore=None):
    """Automatically load Morepath configuration from packages.

    Morepath configuration consists of decorator calls on :class:`App`
    instances, i.e. ``@app.view()`` and ``@app.path()``.

    This function loads all needed Morepath configuration from all
    packages automatically. These packages do need to be made
    available using a ``setup.py`` file including currect
    ``install_requires`` information so that they can be found using
    setuptools_.

    .. _setuptools: http://pythonhosted.org/setuptools/

    Creates a :class:`Config` object as with :func:`setup`, but before
    returning it scans all packages, looking for those that depend on
    Morepath directly or indirectly. This includes the package that
    calls this function. Those packages are then scanned for
    configuration as with :meth:`Config.scan`.

    You can add manual :meth:`Config.scan` calls yourself on the
    returned :class:`Config` object. Finally you need to call
    :meth:`Config.commit` on the returned :class:`Config` object so
    the configuration is committed.

    Typically called immediately after startup just before the
    application starts serving using WSGI.

    See also :func:`autosetup`.

    :param ignore: Venusian_ style ignore to ignore some modules
      during scanning. Optional.
    :returns: :class:`Config` object.

    .. _Venusian: http://venusian.readthedocs.org

    """
    c = setup()
    for package in morepath_packages():
        c.scan(package, ignore)
    return c


def autosetup(ignore=None):
    """Automatically commit Morepath configuration from packages.

    As with :func:`autoconfig`, but also commits
    configuration. This can be your one-stop function to load all
    Morepath configuration automatically.

    Typically called immediately after startup just before the
    application starts serving using WSGI.

    :param ignore: Venusian_ style ignore to ignore some modules
      during scanning. Optional.
    """
    c = autoconfig(ignore)
    c.commit()


class DependencyMap(object):
    def __init__(self):
        self._d = {}
        self._dists = {}

    def load(self):
        for dist in pkg_resources.working_set:
            self._dists[dist.project_name] = dist
            for r in dist.requires():
                self._d.setdefault(
                    dist.project_name, set()).add(r.project_name)

    def depends(self, project_name, on_project_name):
        dependent_project_names = self._d.get(project_name, set())
        if on_project_name in dependent_project_names:
            return True
        for n in dependent_project_names:
            if self.depends(n, on_project_name):
                return True
        return False

    def relevant_dists(self, on_project_name):
        for dist in pkg_resources.working_set:
            if not self.depends(dist.project_name, on_project_name):
                continue
            yield dist


# XXX support for venusian style ignore?
def morepath_packages():
    namespace_packages = set()
    paths = []
    m = DependencyMap()
    m.load()
    for dist in m.relevant_dists('morepath'):
        if dist.has_metadata('namespace_packages.txt'):
            data = dist.get_metadata('namespace_packages.txt')
            for ns in data.split('\n'):
                ns = ns.strip()
                if ns:
                    namespace_packages.add(ns)
        paths.append(dist.location)

    seen = set()

    for importer, dotted_name, is_pkg in walk_packages(paths):
        if not is_pkg:
            continue
        if dotted_name in namespace_packages:
            continue
        if known_prefix(dotted_name, seen):
            continue
        for prefix in prefixes(dotted_name):
            if prefix not in namespace_packages:
                seen.add(prefix)
        m = importer.find_module(dotted_name).load_module(dotted_name)
        # XXX hack to work around bug in walk_packages that will load
        # more than one namespace package: http://bugs.python.org/issue14787
        # XXX performance
        if in_path(m, paths):
            yield m


def prefixes(dottedname):
    parts = dottedname.split('.')
    yield dottedname
    for i in range(1, len(parts)):
        yield '.'.join(parts[:i])


def known_prefix(dottedname, seen):
    for prefix in prefixes(dottedname):
        if prefix in seen:
            return True
    return False


def in_path(m, paths):
    for path in paths:
        for p in m.__path__:
            if p.startswith(path):
                return True
    return False
