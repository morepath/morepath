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
