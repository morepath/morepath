Design Notes
============

Some of the use cases that influenced Morepath's design are documented
here.

Publish any model
-----------------

It should be possible to publish any model object to the web on a
readable URL. This includes model objects that are retrieved from a
relational database and were created with a ORM.

Allowing individual models to be published on separate URLs avoids the
god object antipattern where all web operations are routed through a
single object. Instead each model, through view objects, can
handle model-specific requests and operations. This encourages a more
modular and reusable application design.

Routing
-------

It should be easy to declare explicit routes to model. A route
consists of a routing pattern with zero or more variables. The
variables are used to identify the model, for instance using a
relational database query.

Having routes makes it easier to reason about the URL structure of an
application. Routes also make it easier to expose models that are
retrieved using a query or are constructed on the fly, without
imposing a specific structure on the models.

Traversal
---------

It should be possible to associate routes with specific models in the
application, not just to the root. This way models with sub-paths to
sub-components can be made available as reusable components; an example
of this could be a container. If the model is published, its
sub-components are then exposed as well.

This allows for increased reuse of not just models but relationships
between models, and lets the developer publish nested structures that
cannot be specified using routing alone.

Linking
-------

If a model is published, it should be possible to automatically
generate a link to a model instance in the form of a URL.

This way there is no need to construct URLs manually, and there is no
need to have to refer to routes explicitly in order to construct URLs.
The system knows which route to use and how to construct the
parameters that go into the route itself, given the model.

This is useful when creating RESTful web services (where hypermedia is
the engine of application state), or to construct rich client-side
applications that get all their URLs from the server from a REST-style
web service.

Model is web-agnostic
---------------------

Model classes should not have to have any web knowledge; no particular
base classes are required, and no methods or attributes need to be
implemented in order to publish instances of that model to the web. In
case of an ORM, the ORM does not need to be reconfigured in order to
publish ORM-mapped classes to the web. Models do not receive any
request object and do not have to generate a response object.

Instead this knowledge is external to the models. Models should be
optimized for programmatic use in general.

View/model separation
-------------------------

View objects are responsible for translating the model to the web and
web operations to operations on the model. Views receive the request
object and generate the response object. This is again to avoid giving
the models knowledge about the web. This is a kind of model/view
separation where the view is the intermediary between the model and
the web.

Isolation between applications
------------------------------

The system allows multiple applications to be published at the same
time. Applications work in isolation from each other by default. For
instance, publishing a model on a URL does not affect another
application, and publishing a view for a model does not make that
view available in the other application.

Sharing between applications
----------------------------

In order to support reusable components, it should be possible to
explicitly break application isolation and make routes to models and
views globally available. Each application will share this information.

[Morepath in fact now allows more controlled sharing; only Morepath
itself is globally shared]

Models can be published once per application
--------------------------------------------

Per application a model can be exposed on a single URL pattern. So,
the same instance could be published once per application, in a URL
structure optimal for each application.

Again this supports applications working in isolation - they may treat
database models differently than other applications do.

Linking to another application
------------------------------

It should be possible to construct URLs to models in the context of
another application, if this application is given explicitly during
link time.

Reusable components
-------------------

It should be possible to define a base class (or interface) for a
model that automatically pulls in (globally registered) views and
sub-paths when you subclass from it. This lets a framework developer
define APIs that an application developer can implement. By doing so,
the application developer automatically gets a whole set of views for
their models.

Declarative
-----------

It should be possible to register the components in a declarative
way. This avoids spaghetti registration code, and also makes it
possible to more easily reason about registrations (for instance to do
overrides or detect conflicts).

Conflicts
---------

If you try to do the same registration multiple times, the system
should fail explicitly, as otherwise this would lead to subtle errors.

Overrides
---------

It should be possible to override one registration with another one.
This should either be an explicit operation, or the result of
overriding in a different registry that has precedence over the
defaults.
