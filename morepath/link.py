from interfaces import ITraject, IModelBase, IRoot, IPath, LinkError

# XXX introduce ILink interface and make it possible to
# completely override link getting strategy based on model

def link(request, model, name, base, lookup):
    result = []
    if name:
        result.append(name)
    while True:
        path = IPath.adapt(request, model, lookup=request.lookup)
        if path:
            result.append(path)
        model = IModelBase.adapt(model, lookup=request.lookup, default=None)
        if model is None:
            break
    result.reverse()
    return '/'.join(result)

def path(request, model):
    return IPath.adapt(request, model, lookup=request.lookup)

def get_base(model, lookup):
    return IModelBase.adapt(model, lookup=lookup, default=None)


