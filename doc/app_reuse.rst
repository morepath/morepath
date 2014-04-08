App Reuse
=========

Morepath is a microframework with a difference: it's small and easy to
learn like the others, but has special super powers under the hood.

One of those super powers is Reg_, which along with Morepath's
model/view separation makes it easy to write reusable views. But here
we'll talk about another super power: Morepath's application reuse
facilities.

We'll talk about how Morepath lets you isolate applications, extend
and override applications, and compose applications together. Morepath
tries to make these things simple.

.. _Reg: http://blog.startifact.com/posts/reg-now-with-more-generic.html

Application Isolation
---------------------

Morepath lets you create app objects like this:

.. code-block:: python

  app = morepath.App()

These app objects are WSGI applications, but also serve as registries
for application configuration information. This configuration is
specify used decorators. Apps consist of paths and views for models:

.. code-block:: python

  @app.path(model=User, path='users/{username}')
  def get_user(username):
      return query_for_user(username)

  @app.view(model=User)
  def render_user(self, request):
      return "User: %s" % self.username

Here we've exposed the ``User`` model class under the path
``/users/{username}``. When you go to such a URL, the default
(unnamed) view is found. We've provided that too: it just renders
"User: {username}".

What now if we have another app where we want to publish ``User`` in a
different way? No problem, we can just create one:

.. code-block:: python

  other_app = morepath.App()
  @other_app.path(model=User, path='different_path/{username}')
  def get_user(username):
      return different_query_for_user(username)

  @other_app.view(model=User)
  def render_user(self, request):
      return "Differently Displayed User: %s" % self.username

Here we expose ``User`` to the web again, but use a different path and
a different view. If you run ``other_app`` (even in the same runtime), it
functions independently from ``app``.

This app isolation is nothing really special; it's kind of obvious
that this is possible. But that's what we wanted. Let's look at a few
more involved possibilities next.

Application Extension
---------------------

Let's look at our first application ``app`` again. It exposes a single
view for users (the default view). What now if we want to add a new
functionality to this application so that we can edit users as well?

This is simple; we can add a new ``edit`` view to ``app``:

.. code-block:: python

  @app.view(model=User, name='edit')
  def edit_user(self, request):
      return 'Edit user: %s' % self.username

The string we return here is of course useless for a *real* edit view,
but you get the idea.

But what if we have a scenario where there is a core application and
we want to extend it *without modifying it*?

Why would this ever happen, you may ask? Well, it can, especially in
more complex applications and reuse scenarios. Often you have a common
application core and you want to be able to plug into it. Meanwhile,
you want that core application to still function as before when used
(or tested!) by itself. Perhaps there's somebody else who has created
another extension of it.

This architectural principle is called the `Open/Closed Principle`_ in
software engineering, and Morepath makes it really easy to follow
it. What you do is create another app that extends the original:

.. code-block:: python

  extended_app = morepath.App(extends=[app])

And then we can add the view to the extended app:

.. code-block:: python

  @extended_app.view(model=User, name='edit')
  def edit_user(self, request):
      return 'Edit user: %s' % self.username

Now when we publish ``extended_app`` using WSGI, the new ``edit`` view
is there, but when we publish ``app`` it won't be.

Kind of obvious, perhaps. Good. Let's move on.

.. _`Open/Closed Principle`: https://en.wikipedia.org/wiki/Open/closed_principle

Application Overrides
---------------------

Now we get to a more exciting example: overriding applications. What
if instead of adding an extension to a core application you want to
override part of it? For instance, what if we want to change the
default view for ``User``?

Here's how we can do that:

.. code-block:: python

  @extended_app.view(model=User)
  def render_user_differently(self, request):
      return 'Different view for user: %s' % self.username

We've now overridden the default view for ``User`` to a new view that
renders it differently.

You can also do this for what is returned for model paths. We might
for instance want to return a different user object altogether in
our overriding app:

.. code-block:: python

  @extended_app.path(model=OtherUser, path='users/{username}')
  def get_user_differently(username):
      return OtherUser(username)

To make ``OtherUser`` actually be published on the web under
``/users/{username}`` it either needs to be a subclass of ``User``, for
which we've already registered a default view, or we need to register
a new default view for ``OtherUser``.

Overriding apps actually doesn't look much different from how you
build apps in the first place. Hopefully not so obvious that it's
boring. Let's talk about something new.

Nesting Applications
--------------------

Let's talk about application composition: nesting one app in another.

Imagine our user app allows users to have wikis associated with them.
It has paths like ``/users/faassen/wiki`` and ``/users/bob/wiki``.

One approach might be to implement a wiki application within the user
application we already have, along these lines:

.. code-block:: python

  @app.path(model=Wiki, path='users/{username}/wiki')
  def get_wiki(username):
      return wiki_for_user(username)

  @app.view(model=Wiki)
  def wiki_default_view(request, model):
      return "Default view for wiki"

(this is massively simplified of course. we'd also have a ``Page``
model that's exposed on a sub-path under the wiki, with its own views,
etc)

But this feels bad. Why?

* Why would we implement a wiki as part of our user app? Our wiki
  application should really be an app by itself, that we can use
  byitself and also test by itself.

* There's the issue of the username: it appears in all paths that go
  to wiki-related models (the wiki itself, any wiki pages). But why
  should we have to care about the username of a user when we are
  thinking about wikis?

* It would also be nice if we can use the wiki app in other contexts
  as well, instead of only letting it be associated with users. What
  about associating a wiki app with a project instead, like you can do
  in github?

A separate app for wikis seems obvious. So let's do it. Here's the
wiki app by itself:

.. code-block:: python

  wiki_app = morepath.App()

  @wiki_app.path(model=Wiki, path='{wiki_id}')
  def get_wiki(wiki_id):
      return query_wiki(wiki_id)

  @wiki_app.view(model=Wiki)
  def wiki_default_view(self, request):
      return "Default view for wiki"

This is an app that exposes wikis on URLs using ``wiki_id``, like
``/my_wiki``, ``/another_wiki``.

But that won't work if we want to associate wikis with users. What if
we want the paths we had before, like ``/users/faassen/wiki``?

Morepath has a solution. We can *mount* the wiki app in the user app,
like this:

.. code-block:: python

  @app.mount(app=wiki_app, path='users/{username}/wiki')
  def mount_wiki(username):
      return {
         'wiki_id': get_wiki_id_for_username(username)
      }

We do need to adjust the wiki app a bit as right now it expects
``wiki_id`` to be in its paths, and the wiki id won't show up when
mounted. We need to do two things: tell the wiki app that we expect
the ``wiki_id`` variable::

  wiki_app = morepath.App(variables=['wiki_id'])

And we need to register the model so that its path is empty:

.. code-block:: python

  @wiki_app.path(model=Wiki, path='')
  def get_wiki(wiki_id):
      return query_wiki(wiki_id)

But where does ``wiki_id`` come from now if not from the path? We
already have it: it was determined when the app was mounted, and comes
from the dictionary that we return from ``mount_wiki()``.

What if we want to use ``wiki_app`` by itself, as a WSGI app? That can
be useful, also for testing purposes. It needs this ``wiki_id``
parameter now. We can construct this WSGI app from ``wiki_app`` by
mounting it explicitly:

.. code-block:: python

  wsgi_app = wiki_app.mounted(wiki_id=5)

This is a WSGI app that we can run by itself that uses ``wiki_id``.

Linking to other mounted apps
-----------------------------

When we have one app mounted inside another, we want a way to make links
between them.

You can use :attr:`morepath.Request.parent` to link to an object in an
app's parent app::

  request.parent.link(obj)

If there is no parent application, this raises a
:exc:`morepath.error.LinkError`.

You can use :meth:`morepath.Request.child` to link to an object in a
mounted child application::

  request.child(child_app).link(obj)

If the ``child_app`` is not mounted here, this will also raise a
:exc:`morepath.error.LinkError`.

This won't work though in the case of ``wiki_app`` of the previous
example, as it mounted inside ``app`` using the ``username``. Here's
how we supply it to get the appropriate ``wiki_app``::

  request.child(wiki_app, username='foo').link(obj)

You can compose ``parent`` and ``child`` together in order to get to
anywhere in the mounted app graph; getting to a sibling app for
instance looks like this::

  app.parent.child(sibling_app)

Besides using ``.link`` you can also use ``.view`` this way.

Application Reuse
-----------------

Many web frameworks have mechanisms for overriding specific behavior
and to support reusable applications. These tend to have been
developed in an ad-hoc fashion as new needs arose.

Morepath instead has a *general* mechanism for supporting app
extension and reuse. You use the same principles and APIs you already
use to create new applications. Any normal Morepath app can without
extra effort be reused. Anything registered in a Morepath app can be
overridden. This is because Morepath builds on a powerful general
configuration system.

Further reading
---------------

To see an extended example of how you can structure larger
applications to support reuse, see :doc:`building_large_applications`.

