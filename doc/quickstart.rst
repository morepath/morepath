Quickstart
==========

Morepath is a micro-framework, and this makes it small and easy to
learn. This quickstart guide should help you get started. We assume
you've already installed Morepath; if not, see the :doc:`installation`
section.

.. _helloworld:

Hello world
-----------

Let's look at a minimal "Hello world!" application in Morepath:

.. literalinclude:: code_examples/hello.py

You can save this as ``hello.py`` and then run it with Python:

.. code-block:: console

  $ python hello.py
  Running <__main__.App object at 0x10f8398d0>
  Listening on http://127.0.0.1:5000
  Press Ctrl-C to stop...

.. sidebar:: Making the server externally accessible

  The default configuration of :func:`morepath.run` uses the
  ``127.0.0.1`` hostname.  This means you can access the web server
  from your own computer, but not from anywhere else. During
  development this is often the best way to go about things.

  But sometimes do want to make the development server accessible from
  the outside world. This can be done by passing an explicit ``host``
  argument of ``0.0.0.0`` to the ``morepath.run()`` function. ::

    morepath.run(App(), host='0.0.0.0')

  Alternatively, you can specify ``0.0.0.0`` on the command line:

  .. code-block:: console

    $ python hello.py --host 0.0.0.0

  Note that the built-in web server is absolutely unsuitable for
  actual deployment. For those cases don't use ``morepath.run()`` at
  all, but instead use an external WSGI server such as waitress_,
  `Apache mod_wsgi`_ or `nginx mod_wsgi`_.

  .. _waitress: http://pylons.readthedocs.org/projects/waitress/en/latest/

  .. _`Apache mod_wsgi`: https://modwsgi.readthedocs.org/en/latest/

  .. _`nginx mod_wsgi`: http://wiki.nginx.org/NgxWSGIModule

If you now go with a web browser to the URL given, you should see
"Hello world!"  as expected. When you want to stop the server, just
press control-C.

Morepath uses port 5000 by default, and it might be the case that
another service is already listening on that port.  If that happens
you can specify a different port on the command line:

.. code-block:: console

  $ python hello.py --port 6000

This application is a bit bigger than you might be used to in other
web micro-frameworks. That's for a reason: Morepath is not geared to
create the most succinct "Hello world!" application but to be
effective for building slightly larger applications, all the way up to
huge ones.

Let's go through the hello world app step by step to gain a better
understanding.

Code Walkthrough
----------------

1. We import ``morepath``.

2. We create a subclass of :class:`morepath.App` named ``App``. This
   class contains our application's configuration: what models and
   views are available.  It can also be instantiated into a WSGI
   application object.

3. We then set up a ``Root`` class. Morepath is model-driven and in
   order to create any views, we first need at least one model, in
   this case the empty ``Root`` class.

   We set up the model as the root of the website (the empty string
   ``''`` indicates the root, but ``'/'`` works too) using the
   :meth:`morepath.App.path` decorator.

4. Now we can create the "Hello world" view. It's just a function that
   takes ``self`` and ``request`` as arguments (we don't need to use
   either in this case), and returns the string ``"Hello
   world!"``. The ``self`` argument is the instance of the ``model``
   class that is being viewed.

   We then need to hook up this view with the
   :meth:`morepath.App.view` decorator.  We say it's associated with
   the ``Root`` model. Since we supply no explicit ``name`` to the
   decorator, the function is the default view for the ``Root`` model
   on ``/``.

5. The ``if __name__ == '__main__'`` section is a way in Python to
   make the code only run if the ``hello.py`` module is started
   directly with Python as discussed above. In a real-world
   application you instead use a setuptools entry point so that a
   startup script for your application is created automatically.

6. We then instantiate the ``App`` class to create a ``WSGI`` app
   using the default web server. Since you create a WSGI app you can
   also plug it into any other WSGI server.

This example presents a compact way to organize your code in a single
module, but for a real project we recommend you read
:doc:`organizing_your_project`. This supports organizing your project
with multiple modules.

Routing
-------

Morepath uses a special routing technique that is different from many
other routing frameworks you may be familiar with. Morepath does not
route to views, but routes to models instead.

.. sidebar:: Why route to models?

  Why does Morepath route to models? It allows for some nice
  features. The most concrete feature is automatic hyperlink
  generation - we'll go into more detail about this later.

  A more abstract feature is that Morepath through model-driven design
  allows for greater code reuse: this is the basis for Morepath's
  super-powers. We'll show a few of these special things you can do
  with Morepath later.

  Finally Morepath's model-oriented nature makes it a more natural fit
  for REST_ applications. This is useful when you need to create a web
  service or the foundation to a rich client-side application.

  .. _REST: https://en.wikipedia.org/wiki/Representational_state_transfer

Models
~~~~~~

A model is any Python object that represents the content of your
application: say a document, or a user, an address, and so on. A model
may be a plain in-memory Python object or be backed by a database
using an ORM such as SQLAlchemy_, or some NoSQL database such as the
ZODB_. This is entirely up to you; Morepath does not put special
requirements on models.

.. _SQLAlchemy: http://www.sqlalchemy.org/

.. _ZODB: http://www.zodb.org/en/latest/

Above we've exposed a ``Root`` model to the root route ``/``, which is
rather boring. To make things more interesting, let's imagine we have
an application to manage users. Here's our ``User`` class:

.. testcode::

  class User(object):
      def __init__(self, username, fullname, email):
          self.username = username
          self.fullname = fullname
          self.email = email

We also create a simple users database:

.. testcode::

  users = {}
  def add_user(user):
      users[user.username] = user

  faassen = User('faassen', 'Martijn Faassen', 'faassen@startifact.com')
  bob = User('bob', 'Bob Bobsled', 'bob@example.com')
  add_user(faassen)
  add_user(bob)

Publishing models
~~~~~~~~~~~~~~~~~

.. testcode::
  :hide:

  import morepath
  class App(morepath.App):
      pass

.. sidebar:: Custom variables function

  The default behavior is for Morepath to retrieve the variables by
  name using ``getattr`` from the model objects. This only works if
  those variables exist on the model under that name. If not, you can
  supply a custom ``variables`` function that given the model returns
  a dictionary with all the variables in it. Here's how::

    @App.path(model=User, path='/users/{username}',
              variables=lambda model: dict(username=model.username))
    def get_user(username):
        return users.get(username)

  Of course this ``variables`` is not necessary as it has the same
  behavior as the default, but you can do whatever you want in the
  variables function in order to get the username.

  Getting ``variables`` right is important for link generation.

We want our application to have URLs that look like this::

  /users/faassen

  /users/bob

Here's the code to expose our users database to such a URL:

.. testcode::

  @App.path(model=User, path='/users/{username}')
  def get_user(username):
      return users.get(username)

The ``get_user`` function gets a user model from the users database by
using the dictionary ``get`` method. If the user doesn't exist, it
returns ``None``. We could've fitted a SQLAlchemy query in here
instead.

Now let's look at the decorator. The ``model`` argument has the class
of the model that we're putting on the web. The ``path`` argument has
the URL path under which it should appear.

The path can have variables in it which are between curly braces
(``{`` and ``}``). These variables become arguments to the function
being decorated. Any arguments the function has that are not in the
path are interpreted as URL parameters.

What if the user doesn't exist? We want the end-user to see a 404
error.  Morepath does this automatically for you when you return
``None`` for a model, which is what ``get_user`` does when the model
cannot be found.

Now we've published the model to the web but we can't view it yet.

.. sidebar:: converters

  A common use case is for path variables to be a database id. These
  are often integers only. If a non-integer is seen in the path we
  know it doesn't match. You can specify a path variable contains an
  integer using the integer converter. For instance::

    @App.path(model=Post, path='posts/{post_id}', converters=dict(post_id=int))
    def get_post(post_id):
        return query_post(post_id)

  You can do this more succinctly too by using a default parameter for
  ``post_id`` that is an int, for instance::

    @App.path(model=Post, path='posts/{post_id}')
    def get_post(post_id=0):
        return query_post(post_id)

For more on this, see :doc:`paths_and_linking`.

Views
~~~~~

In order to actually see a web page for a user model, we need to
create a view for it:

.. testcode::

  @App.view(model=User)
  def user_info(self, request):
      return "User's full name is: %s" % self.fullname

The view is a function decorated by :meth:`morepath.App.view` (or
related decorators such as :meth:`morepath.App.json` and
:meth:`morepath.App.html`) that gets two arguments: ``self``,
which is the model that this view is working for, so in this case an
instance of ``User``, and ``request`` which is the current
request. ``request`` is a :class:`morepath.request.Request` object (a
subclass of :class:`webob.request.BaseRequest`).

Now the URLs listed above such as ``/users/faassen`` will work.

What if we want to provide an alternative view for the user, such as
an ``edit`` view which allows us to edit it? We need to give it a
name:

.. testcode::

  @App.view(model=User, name='edit')
  def edit_user(self, request):
      return "An editing UI goes here"

Now we have functionality on URLs like ``/users/faassen/edit`` and
``/users/bob/edit``.

For more on this, see :doc:`views`.

Linking to models
~~~~~~~~~~~~~~~~~

.. testcode::
  :hide:

  request = App().request({'PATH_INFO': '/', 'wsgi.url_scheme': 'http', 'HTTP_HOST': 'example.com'})

Morepath is great at creating links to models: it can do it for you
automatically. Previously we've defined an instance of ``User`` called
``bob``. What now if we want to link to the default view of ``bob``?
We simply do this:

  >>> request.link(bob)
  'http://example.com/users/bob'

What if we want to see Bob's edit view? We do this:

  >>> request.link(bob, 'edit')
  'http://example.com/users/bob/edit'

Using :meth:`morepath.Request.link` everywhere for link generation is
easy. You only need models and remember which view names are
available, that's it. If you ever have to change the path of your
model, you won't need to adjust any linking code.

For more on this, see :doc:`paths_and_linking`.

.. sidebar:: Link generation compared

  If you're familiar with routing frameworks where links are generated
  to views (such as Flask or Django) link generation is more
  involved. You need to give each route a name, and then refer back to
  this route name when you want to generate a link. You also need to
  supply the variables that go into the route. With Morepath, you
  don't need a route name, and if the default way of getting variables
  from a model is not correct, you only need to explain once how to
  create the variables for a route, with the ``variables`` argument to
  ``@App.path``.

  In addition, Morepath links are completely generic: you can pass in
  anything linkable. This means that writing a generic view that uses
  links becomes easier -- there is no dependency on particular named
  URL paths anymore.


JSON and HTML views
~~~~~~~~~~~~~~~~~~~

``@App.view`` is rather bare-bones. You usually know more about what
you want to return than that. If you want to return JSON, you can use
the shortcut ``@App.json`` instead to declare your view::

  @App.json(model=User, name='info')
  def user_json_info(self, request):
      return {'username': self.username,
              'fullname': self.fullname,
              'email': self.email}

This automatically serializes what is returned from the function JSON,
and sets the content-type header to ``application/json``.

If we want to return HTML, we can use ``@App.html``::

  @App.html(model=User)
  def user_info(self, request):
      return "<p>User's full name is: %s</p>" % self.fullname

This automatically sets the content type to ``text/html``. It doesn't
do any HTML escaping though, so the use of ``%`` above is unsafe! We
recommend the use of a HTML template language in that case.

Request object
--------------

The first argument for a view function is the request object. We'll
give a quick overview of what's possible here, but consult the
WebOb API documentation for more information.

* ``request.GET`` contains any URL parameters (``?key=value``). See
  :attr:`webob.request.BaseRequest.GET`.

* ``request.POST`` contains any HTTP form data that was submitted. See
  :attr:`webob.request.BaseRequest.POST`.

* ``request.method`` gets the HTTP method (``GET``, ``POST``, etc). See
  :attr:`webob.request.BaseRequest.method`.

* ``request.cookies`` contains the cookies. See
  :attr:`webob.request.BaseRequest.cookies`. ``response.set_cookie`` can be
  used to set cookies. See :meth:`webob.response.Response.set_cookie`.

Redirects
---------

To redirect to another URL, use :func:`morepath.redirect`. For example::

  @App.view(model=User, name='extra')
  def redirecting(self, request):
      return morepath.redirect(request.link(self, 'other'))

HTTP Errors
-----------

To trigger an HTTP error response you can raise various WebOb HTTP
exceptions (:mod:`webob.exc`). For instance::

  from webob.exc import HTTPNotAcceptable

  @App.view(model=User, name='extra')
  def erroring(self, request):
      raise HTTPNotAcceptable()

But note that Morepath already raises a lot of these errors for you
automatically just by having your structure your code the Morepath
way.
