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


def toposorted(infos):
    """Sort infos topologically.

    Info object must have a key attribute, and before and after
    methods that returns a list of keys.
    """
    key_to_info = {}
    depends = {}
    for info in infos:
        key_to_info[info.key] = info
        depends[info.key] = []
    for info in infos:
        for after in info.after():
            after_info = key_to_info[after]
            depends[info.key].append(after_info)
        for before in info.before():
            before_info = key_to_info[before]
            depends[before_info.key].append(info)
    return topological_sort(
        infos, lambda info: depends[info.key])
