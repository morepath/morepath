from .error import TopologicalSortError


def topological_sort(l, get_depends):
    result = []
    marked = set()
    temporary_marked = set()

    def visit(n):
        if n in marked:
            return
        if n in temporary_marked:
            raise TopologicalSortError("Not a DAG")
        temporary_marked.add(n)
        for m in get_depends(n):
            visit(m)
        marked.add(n)
        result.append(n)
    for n in l:
        visit(n)
    return result


class Info(object):
    """Toposorted info helper.

    Base class that helps with toposorted. ``before`` and ``after``
    can be lists of keys, or a single key, or ``None``.
    """
    def __init__(self, key, before, after):
        self.key = key
        self.before = _convert_before_after(before)
        self.after = _convert_before_after(after)


def _convert_before_after(l):
    if isinstance(l, (list, tuple)):
        return list(l)
    elif l is None:
        return []
    else:
        return [l]


def toposorted(infos):
    """Sort infos topologically.

    Info object must have a key attribute, and before and after
    attributes that returns a list of keys.
    """
    key_to_info = {}
    depends = {}
    for info in infos:
        key_to_info[info.key] = info
        depends[info.key] = []
    for info in infos:
        for after in info.after:
            after_info = key_to_info[after]
            depends[info.key].append(after_info)
        for before in info.before:
            before_info = key_to_info[before]
            depends[before_info.key].append(info)
    return topological_sort(
        infos, lambda info: depends[info.key])
