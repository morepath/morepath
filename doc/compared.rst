Comparison with other Web Frameworks
====================================

We hear you ask:

  There are a *million* Python web frameworks out there. How does
  Morepath compare?

If you're already familiar with another web framework, it's useful to
learn how Morepath differ, as it will help you understand it
faster. So we'll try some of that here.

Our abilities to compare Morepath to other web frameworks are limited
by lack of familiarity with them and their aforementioned large
quantity. But we'll try. Feel free to pitch in new comparisons, or
tell us where we get it wrong!

Routing
-------

.. sidebar:: Collect 200 dollars

  Do not directly go to the view. Go to the model first. Only *then*
  go to the view. Do collect 200 dollars. Don't go to `jail
  <https://en.wikipedia.org/wiki/Monopoly_%28game%29>`__.

Morepath is a *routing* web framework, like Django and Flask and a lot
of others. This is a common way to use Pyramid too. This is also
called URL mapping or dispatching. Morepath is to our knowledge,
unique in that the routes don't directly go to *views*, but go through
*models* first.

Morepath's route syntax is very similar to Pyramid's,
i.e. ``/hello/{name}``. Flask is also similar. It's unlike Django's
regular expressions. Morepath works at a higher level than that
deliberately, as that makes it possible to disambiguate similar
routes.

This separation of model and view lookup helps in code organisation,
as it allows you to separate the code that organises the URL space
from the code that implements your actual views.

Linking
-------

Because it routes to models, Morepath allows you to ask for the URL of
a model instance, like this::

  request.link(mymodel)

That is an easier and less brittle way to make links than having to
name your routes explicitly.

Morepath shares the property of model-based links with traversal based
web frameworks like Zope and Grok, and also Pyramid in non-routing
traversal mode. Uniquely among them Morepath *does* route, not
traverse.

View lookup
-----------

Morepath uses a separate view lookup system. The name of the view is
determined from the last step of the path being routed to. With this URL
path for instance::

  /document/edit

the ``/edit`` bit indicates the name of the view to look up for the
document model.

If no view step is supplied, the default view is looked up::

  /document

This is like modern Zope works, and like how the Plone CMS works. It's
also like Grok. It's like Pyramid if it's used with traversal instead
of routing. Overall there's a strong Zope heritage going on, as all
these systems are derived from Zope in one way or another. Morepath is
unique in that it combines *routing* with view lookup.

This decoupling of views from models helps with expressivity, as it
lets you write reusable, generic views, and code organisation as
mentioned before.

WSGI
----

Morepath is a WSGI_-based framework, like Flask or Pyramid. It's
natively WSGI, unlike Django, which also has its own way of doing
middleware.

.. _WSGI: http://wsgi.readthedocs.org/en/latest/

A Morepath app is a standard WSGI app. You can plug it into a WSGI
compliant web server like Apache or Nginx or gunicorn. You can also
combine Morepath with WSGI components, such as for instance the
Fanstatic_ static resource framework.

.. _Fanstatic: http://www.fanstatic.org

Permissions
-----------

Morepath has a permission framework built-in: it knows about
authentication and lets you plug in authenticators, you can protect
views with permissions and plug in code that tells Morepath what
permissions someone has for which models. It's small but powerful in
what it lets you do.

This is unlike most other micro-frameworks like Flask, Bottle,
CherryPy or web.py. It's like Zope, Grok and Pyramid, and has learned
from them, though Morepath's system is more streamlined.

Explicit request
----------------

Some frameworks, like Flask and Bottle, have a magic ``request``
global that you can import. But request isn't really a global, it's a
variable, and in Morepath it's a variable that's passed into view
functions explicitly. This makes Morepath more similar to Pyramid or
Django.

Testability and Global state
----------------------------

Developers that care about writing code try to avoid global state, in
particular mutable global state, as it can make testing harder. If the
framework is required to be in a certain global state before the code
under test can be run, it becomes harder to test that code, as you
need to know first what global state to manipulate.

Globals can also be a problem when multiple threads try to write the
global at the same time. Web frameworks avoid this by using *thread
locals*. Confusingly enough these locals are *globals*, but they're
isolated from other threads.

Morepath the framework does not require any global state. Of course
Morepath's app *are* module globals, but they're not *used* that way
once Morepath's configuration is loaded and Morepath starts to handle
requests. Morepath's framework code passes the app along as a variable
(or attribute of a variable, such as the request) just like everything
else.

Morepath is built on the Reg generic function library. Implementations
of generic functions can be plugged in separately per Morepath app:
each app is a registry. When you call a generic function Reg needs to
know what registry to use to look it up. You can make this completely
explicit by using a special ``lookup`` argument::

  some_generic_function(doc, 3, lookup=app.lookup())

That's all right in framework code, but doing that all the time is not
very pretty in application code. For convenience, Morepath therefore sets up the
current lookup implicitly as thread local state. Then you can
simply write this::

  some_generic_function(doc, 3)

Flask is quite happy to use global state (with thread locals) to have
a request that you can import. Pyramid is generally careful to avoid
global state, but does use thread local state to get access to the
current registry, similar to what Morepath does.

Summary: Morepath does not require any global state, but for allows
the current lookup to be set up as such for convenience.

Component Architecture
----------------------

Most Python web frameworks don't have a component system. But
successful web applications tend to get more complicated. And then you
may want things from the web framework it cannot do. New APIs may grow
over time, each different. You might end up with a lot of custom
customization facilities, complete with metaclasses and import-time
side-effects. Django has suffered from this, and so did Zope 2.

Microframeworks aim for simplicity so don't suffer so much from this,
but at the cost of some flexibility.

The Zope project made the term "component architecture" (in)famous in
the Python world. Does it sound impressive, suggesting flexibility and
reusability? Or does it sound scary, overengineered,
``RequestProcessorFactoryFactory``-like? At its core it's really a
system to add functionality to objects without having to change their
classes, from the outside, and it helps building generic
functionality.

Part of what made the Zope component architecture scary is that
configuring components together (i.e "this view goes with this model")
was cumbersome and verbose. The Grok web framework provided a way to
make that configuration less cumbersome. Pyramid took a similar
approach but streamlined it. Pyramid also hid complexities of the
component framework behind simple function-based APIs

Morepath went one step further and uses generic functions, based on
the Reg library. These are about as expressive as what you can do with
the Zope Component Architecture underlying Pyramid and Grok and Zope,
but much much simpler to use. The simple function-based APIs *are*
what is pluggable. Morepath is mostly simple functions all the way
down.

No default database
-------------------

Morepath has no default database integration. This is like Flask and
Bottle and Pyramid, but unlike Zope or Django, which have assumptions
about the database baked in (ZODB and Django ORM respectively).

You can plug in your own database, or even have no database at
all. You could use SQLAlchemy, or the ZODB. Morepath lets you treat
anything as models. We're not against writing examples or extensions
that help you do this, though we haven't done so yet. Contribute!

No template language
--------------------

Some micro-frameworks like Flask and Bottle and web.py have template
languages built-in, some, like CherryPy and the Werkzeug toolkit,
don't. Pyramid doesn't have built-in support either, but has standard
plugins for the Chameleon and Mako template languages.

Morepath aims to be a good fit for modern, client-side web
applications written in JavaScript. So we've focused on making it easy
to send anything to the client, especially JSON. If templating is used
for such applications, it's done on the client, in the web browser,
not on the server.

We're planning on letting you plug in server-side template languages
as they're sometimes useful, but we haven't done so yet. Feel free to
contribute!

For now, you can plug in something yourself. CherryPy has a `good document`_
on how to do that with CherryPy, and it'd look very similar with Morepath.

.. _`good document`: http://cherrypy.readthedocs.org/en/latest/progguide/choosingtemplate.html
