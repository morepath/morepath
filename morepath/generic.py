import reg


@reg.generic
def consumer(obj):
    """A consumer consumes steps in a stack to find an object.
    """
    raise NotImplementedError


@reg.generic
def app(obj):
    """Get the application that this object is associated with.
    """
    raise NotImplementedError


@reg.generic
def base(model):
    """Get the base that this model is associated with.
    """
    raise NotImplementedError


@reg.generic
def lookup(obj):
    """Get the lookup that this object is associated with.
    """
    raise NotImplementedError


@reg.generic
def path(model):
    """Get the path for a model in its own application.
    """
    raise NotImplementedError


@reg.generic
def link(request, model):
    """Create a link (URL) to a model, including any mounted applications.
    """
    raise NotImplementedError


@reg.generic
def traject(obj):
    """Get traject for obj.
    """
    raise NotImplementedError


@reg.generic
def view(request, model):
    """Get the view that represents the model in the context of a request.

    This view is a representation of the model that be rendered to
    a response. It may also return a Response directly. If a string is
    returned, the string is converted to a Response with the string as
    the response body.
    """
    raise NotImplementedError


@reg.generic
def response(request, model):
    """Get a Response for the model in the context of the request.
    """
    raise NotImplementedError
