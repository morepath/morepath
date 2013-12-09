import reg


@reg.generic
def consume(obj, unconsumed):
    """Consume unconsumed to new object starting at obj.

    Returns a boolean meaning that some unconsumed has been consumed,
    an object and the remaining unconsumed stack
    """
    return False, obj, unconsumed


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
def context(model):
    """Get the context dictionary available for a model.
    """
    return {}


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


@reg.generic
def identify(request):
    """Returns an Identity or None if no identity can be found.

    Can also return NO_IDENTITY, but None is converted automatically
    to this.
    """
    raise None


@reg.generic
def remember(request, identity):
    """Get headers to pass to response to remember identity.
    """
    raise NotImplementedError


@reg.generic
def forget(request):
    """Get headers to pass to response to forget identity in response.
    """
    raise NotImplementedError


@reg.generic
def permits(identity, model, permission):
    """Returns True if identity has permission for model.

    identity can be the special NO_IDENTITY singleton; register for
    NoIdentity to handle this case separately.
    """
    raise NotImplementedError


@reg.generic
def user(identity):
    """Gives back a user object for the identity given.

    Returns None if the user is not known to the system.
    """
    raise NotImplementedError
