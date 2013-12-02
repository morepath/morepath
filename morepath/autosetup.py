import pkg_resources
from pkgutil import walk_packages

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


def morepath_modules():
    namespace_packages = set()
    paths = []
    m = DependencyMap()
    m.load()
    for dist in m.relevant_dists('morepath'):
        if dist.has_metadata('namespace_packages.txt'):
            data = dist.get_metadata('namespace_packages.txt')
            for ns in data.split('\n'):
                namespace_packages.add(ns.strip())
        paths.append(dist.location)

    seen = set()

    for importer, dotted_name, is_pkg in walk_packages(paths,
                                                       onerror=skip_error):
        if not is_pkg:
            continue
        if dotted_name in namespace_packages:
            continue
        if known_prefix(dotted_name, seen):
            continue
        for prefix in prefixes(dotted_name):
            seen.add(prefix)
        m = importer.find_module(dotted_name).load_module(dotted_name)
        # XXX hack to work around bug in walk_packages that will load
        # more than one namespace package
        # XXX performance
        if in_path(m, paths):
           yield m

def prefixes(dottedname):
    parts = dottedname.split('.')
    for i in range(1, len(parts)):
        yield '.'.join(parts[:i])

def known_prefix(dottedname, seen):
    for prefix in prefixes(dottedname):
        if prefix in seen:
            return True
    return False

def in_path(m, paths):
    for path in paths:
        for p in  m.__path__:
            if p.startswith(path):
                return True
    return False

def skip_error(pkg):
    pass

