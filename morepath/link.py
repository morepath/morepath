from interfaces import ITraject, LinkError

# XXX introduce ILink interface and make it possible to
# completely override link getting strategy based on model

def link(request, model, name, base, lookup):
    # XXX what if path cannot be found?
    # XXX what is the base of base?
    result = '%s/%s' % (link(request, base, '', None, lookup),
                        path(model, base, lookup)) 
    if name != '':
        result += '/' + name
    return result

def get_base(model, lookup):
    return IModelBase.component(model, lookup=self.lookup, default=None)

def path(model, base, lookup):
    if base is None:
        base = get_base(model)
    if base is None:
        raise LinkError(
            "cannot create link to model %r with name %r, "
            "no base can be determined for model" % (model, name))
    traject = ITraject.component(base, lookup=lookup, default=None)
    if traject is None:
        raise LinkError(
            "cannot create link to model %r with name %r, "
            "no path information known for base %r" %
            (model, name, base))
    return traject.get_path(model)

# if model is registered with an app as base, IModelBase is registered
# for that model so it returns the app object
# if model is registered with a get_base, then this is called for that model


