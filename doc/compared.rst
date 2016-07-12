Comparison with other Web Frameworks
====================================

We hear you ask:

  There are a *million* Python web frameworks out there. How does
  Morepath compare?

.. sidebar:: Pyramid Design Chocies

  This document is a bit like the `Design Defense Document
  <http://docs.pylonsproject.org/projects/pyramid/en/latest/designdefense.html>`__
  of the Pyramid web framework. The Pyramid document makes for a very
  interesting read if you're interested in web framework design. More
  web frameworks should do that.

If you're already familiar with another web framework, it's useful to
learn how Morepath is the same and how it is different, as that helps
you understand it more quickly. So we go into some of this here.

Our ability to compare Morepath to other web frameworks is limited by
our familiarity with them, and also by their aforementioned large
quantity. But we'll try. Feel free to pitch in new comparisons, or
tell us where we get it wrong!

You may also want to read the :doc:`design` document.

Overview
--------

Morepath aims to be foundational. All web applications are
different. Some are simple. Some, like CMSes, are like frameworks
themselves. It's likely that some of you will need to build your own
frameworky things on top of Morepath. Morepath offers various
facilities to help you there: you can define reusable base
applications and it even allows you to extend Morepath with new
directives. Morepath isn't there to be hidden away under another
framework though - these extensions still look like Morepath. The
orientation towards being foundational makes Morepath more like
Pyramid, or perhaps Flask, than like Django.

Morepath aims to have a small core. It isn't full stack; it's a
microframework. It should be easy to pick up. This makes it similar to
other microframeworks like Flask or CherryPy, but different from
Django and Zope, which offer a lot of features.

Morepath is opinionated. There is only one way to do routing and one
way to do configuration. This makes it like a lot of web frameworks,
but unlike Pyramid, which takes more of a toolkit approach where a lot
of choices are made available.

Morepath is a routing framework, but it's model-centric. Models have
URLs. This makes it like a URL traversal framework like Zope or Grok,
and also like Pyramid when traversal is in use. It makes it unlike
other routing frameworks like Django or Flask, which have less
awareness of models.

Paradoxically enough one thing Morepath is opinionated about is
*flexibility*, as that's part of its mission to be a good foundation.
That's what its configuration system (Dectate_) and generic function
system (Reg_) are all about. Want to change behavior? You can override
everything. You can introduce new registries and new directives. Even
core behavior of Morepath can be changed by overriding its generic
functions. This makes Morepath like Zope, and especially like Pyramid,
but less like Django or Flask.

.. _Dectate: http://dectate.readthedocs.org

.. _Reg: http://reg.readthedocs.org

Routing
-------

.. sidebar:: Collect 200 dollars

  Do not directly go to the view. Go to the model first. Only *then*
  go to the view. Do collect 200 dollars. Don't go to `jail
  <https://en.wikipedia.org/wiki/Monopoly_%28game%29>`__.

Morepath is a *routing* web framework, like Django and Flask and a lot
of others. This is a common way to use Pyramid too (the other is
traversal). This is also called URL mapping or dispatching. Morepath
is to our knowledge, unique in that the routes don't directly go to
*views*, but go through *models* first.

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
name your routes explicitly. Morepath pushes link generation quite
far: it can construct links with paths and URL parameters
automatically.

Morepath shares the property of model-based links with traversal based
web frameworks like Zope and Grok, and also Pyramid in non-routing
traversal mode. Uniquely among them Morepath *does* route, not
traverse.

For more: :doc:`paths_and_linking`.

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

For more: :doc:`views`.

WSGI
----

Morepath is a WSGI_-based framework, like Flask or Pyramid. It's
natively WSGI, unlike Django, which while WSGI is supported also has
its own way of doing middleware.

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

For more you can check out `this blog entry
<http://blog.startifact.com/posts/morepath-security.html>`__. (It will
be integrated in this documentation later).

Explicit request
----------------

Some frameworks, like Flask and Bottle, have a magic ``request``
global that you can import. But request isn't really a global, it's a
variable, and in Morepath it's a variable that's passed into view
functions explicitly. This makes Morepath more similar to Pyramid or
Django.

Testability and Global state
----------------------------

Developers that care about writing testable code try to avoid global
state, in particular mutable global state, as it can make testing
harder. If the framework is required to be in a certain global state
before the code under test can be run, it becomes harder to test that
code, as you need to know first what global state to manipulate.

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
each app has a separate reg registry. When you call a generic function
Reg needs to know what registry to use to look it up. You can make
this completely explicit by using a special ``lookup`` argument::

  some_generic_function(doc, 3, lookup=app.lookup)

That's all right in framework code, but doing that all the time is not
very pretty in application code. For convenience, Morepath therefore
sets up the current lookup implicitly as thread local state. Then you
can simply write this::

  some_generic_function(doc, 3)

Flask is quite happy to use global state (with thread locals) to have
a request that you can import. Pyramid is generally careful to avoid
global state, but does allow using thread local state to get access to
the current registry in some cases.

Summary: Morepath does not require any global state, but allows the
current lookup to be set up as such for convenience.

No default database
-------------------

Morepath has no default database integration. This is like Flask and
Bottle and Pyramid, but unlike Zope or Django, which have assumptions
about the database baked in (ZODB and Django ORM respectively).

You can plug in your own database, or even have no database at
all. You could use SQLAlchemy, or the ZODB. Morepath lets you treat
anything as models. We're not against writing examples or extensions
that help you do this, though we haven't done so yet. Contribute!

Pluggable template languages
-----------------------------

Some micro-frameworks like Flask and Bottle and web.py have template
languages built-in, some, like CherryPy and the Werkzeug toolkit,
don't. Pyramid doesn't have built-in support either, but has standard
plugins for the Chameleon and Mako template languages.

Morepath allows you to plug in server templates. You can plug in
Jinja2_ through `more.jinja2`_ and plug in Chameleon_ through
`more.chameleon`_.

.. _Jinja2: http://jinja.pocoo.org/

.. _Chameleon: https://chameleon.readthedocs.org

.. _`more.jinja2`: https://pypi.python.org/pypi/more.jinja2

.. _`more.chameleon`: https://pypi.python.org/pypi/more.chameleon

You don't have to use a server template language though: Morepath aims
to be a good fit for modern, client-side web applications written in
JavaScript. We've made it easy to send anything to the client,
especially JSON. If templating is used for such applications, it's
done on the client, in the web browser, not on the server.

Code configuration
------------------

Most Python web frameworks don't have an explicit code configuration
system. With "code configuration" I mean expressing things like "this
function handles this route", "this view works for this model", and
"this is the authentication system for this app". It also includes
extension and overrides, such as "here is an additional route", "use
this function to handle this route instead of what the core said".

If a web framework doesn't deal with code configuration explicitly, an
implicit code configuration tends to grow. There is one way to set up
routes, another way to declare models, another way to do generic
views, yet another way to configure the permission system, and so
on. Each system works differently and uses a different API. Config
files, metaclasses and import-time side effects may all be involved.

On top of this, if the framework wants to allow reuse, extension and
overrides the APIs tends to grow even more distinct with specialised
use cases, or yet more new APIs are grown.

Django is an example where configuration gained lots of knobs and
buttons; another example is the original Zope.

Microframeworks aim for simplicity so don't suffer from this so much,
though probably at the cost of some flexibility. You can still observe
this kind of evolution in Flask's pluggable views subsystem, though,
for instance.

To deal with this problem in an explicit way the Zope project
pioneered a component configuration mechanism. By having a universal
mechanism in which code is configured, the configuration API becomes
general and allows extension and override in a general manner as
well. Zope uses XML files for this.

The Grok project tried to put a friendlier face on the rather verbose
configuration system of Zope. Pyramid refined Grok's approach further.
It offers a range of options for configuration: explicit calls in
Python code, decorators, and an extension that uses Zope-style XML.

In order to do its decorator based configuration, the Pyramid project
created the Venusian_ python library. This is in turn a reimagined
version of the Martian_ python library created by the Grok
project. Venusian was used by the Morepath project originally, and
even though it is gone it still helped inspire Morepath's
configuration system.

Morepath uses a new, general configuration system called Dectate_ that
is based around decorators attached to application objects. These
application objects can extend other ones. Dectate supports a range
sophisticated extension and override use cases in a general way.

.. _Venusian: http://pypi.python.org/pypi/venusian

.. _Martian: http://pypi.python.org/pypi/martian

.. _Dectate: http://dectate.readthedocs.org

Components and Generic functions
--------------------------------

The Zope project made the term "zope component architecture" (ZCA)
(in)famous in the Python world. Does it sound impressive, suggesting
flexibility and reusability? Or does it sound scary, overengineered,
``RequestProcessorFactoryFactory``-like? Are you intimidated by it? We
can't blame you.

At its core the ZCA is really a system to add functionality to objects
from the outside, without having to change their classes. It helps
when you need to build extensible applications and reusable generic
functionality. Under the hood, it's just a fancy registry that knows
about inheritance. Its a really powerful system to help build more
complicated applications and frameworks. It's used by Zope, Grok and
Pyramid.

Morepath uses something else: a library called Reg_. This is a new,
reimagined, streamlined implementation of the idea of the ZCA.

.. _Reg: http://reg.readthedocs.org

The underlying registration APIs of the ZCA is rather involved, with
quite a few special cases. Reg has a simpler, more general
registration API that is flexible enough to fulfill a range of use
cases.

Finally what makes the Zope component architecture rather involved to
use is its reliance on *interfaces*. An interface is a special kind of
object introduced by the Zope component architecture that is used to
describe the API of objects. It's like an abstract base class.

If you want to look up things in a ZCA component registry the ZCA
requires you to look up an interface. This requires you to *write*
interfaces for everything you want to be able to look up. The
interface-based way to do lookups also looks rather odd to the average
Python developer: it's not considered to be very Pythonic. To mitigate
the last problem Pyramid creates simple function-based APIs on top of
the underlying interfaces.

Morepath by using Reg does away with interfaces altogether -- instead
it uses generic functions. The simple function-based APIs *are* what
is pluggable; there is no need to deal with interfaces anymore, but
the system retains the power. Morepath is simple functions all the way
down.
