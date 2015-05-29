Tweens
======

Introduction
------------

Tweens are a light-weight framework component that sits between the
web server and the app. It's very similar to a WSGI middleware, except
that a tween has access to the Morepath API and is therefore less
low-level.

Tweens can be used to implement transaction handling, logging, error
handling and the like.

signature of a handler
----------------------

Morepath has an internal `publish` function that takes a single
:class:`morepath.Request` argument, and returns a
:class:`morepath.Response` as a result::

  def publish(request):
      ...
      return response

Tweens have the same signature.

We call such functions *handlers*.

Under and over
--------------

Given a handler, we can create a factory that creates a tween that
wraps around it::

  def make_tween(app, handler):
      def my_tween(request):
          print "Enter"
          response = handler(request)
          print "Exit"
          return response
      return my_tween

We say that *my_tween* is *over* the ``handler`` argument, and
conversely that ``handler`` is *under* ``my_tween``.

The application constructs a chain of tween over tween, ultimately
reaching the request handler. Request come in in the outermost tween
and descend down the chain into the underlying tweens, and finally
into the Morepath `publish` handler itself.

What can a tween do?
--------------------

A tween can:

* amend or replace the request before it goes in to the handler under it.

* amend or replace the response before it goes back out to the handler
  over it.

* inspect the request and completely take over response generation for
  some requests.

* catch and handle exceptions raised by the handler under it.

* do things before and after the request is handled: this can be
  logging, or commit or abort a database transaction.

Creating a tween factory
------------------------

To have a tween, we need to add a tween factory to the app. The tween
factory is a function that given a handler constructs a tween. You can
register a tween factory using the :meth:`App.tween_factory`
directive::

  @App.tween_factory()
  def make_tween(app, handler):
      def my_tween(request):
          print "Enter"
          response = handler(request)
          print "Exit"
          return response
      return my_tween

The tween chain is now:

.. code-block:: none

  my_tween -> publish

It can be useful to control the order of the tween chain. You can do this
by passing ``under`` or ``over`` to `tween_factory`::

  @App.tween_factory(over=make_tween)
  def make_another_tween(app, handler):
      def another_tween(request):
          print "Another"
          return handler(request)
      return another_tween

The tween chain is now:

.. code-block:: none

  another_tween -> my_tween -> publish

If instead you used ``under``::

  @App.tween_factory(under=make_tween)
  def make_another_tween(app, handler):
      def another_tween(request):
          print "Another"
          return handler(request)
      return another_tween

Then the tween chain is:

.. code-block:: none

  my_tween -> another_tween -> publish

Tweens and settings
-------------------

A tween factory may need access to some application settings in order
to construct its tweens. A logging tween for instance needs access to
a setting that indicates the path of the logfile.

The tween factory gets two arguments: the app and the handler. You can
then access the app's settings using ``app.registry.settings``. See
also the :doc:`settings` section.

Tweens and apps
---------------

You can register different tween factories in different Morepath
apps. A tween factory only has an effect when the app under which it
is registered is being run directly as a WSGI app. A tween factory has
no effect if its app is mounted under another app. Only the tweens of
the outer app are in effect at that point, and they are *also* in
effect for any apps mounted into it.

This means that if you install a logging tween in an app, and you run
this app with a WSGI server, the logging takes place for that app and
any other app that may be mounted into it, directly or indirectly.

more.transaction
----------------

If you need to integrate SQLAlchemy or the ZODB into Morepath,
Morepath offers a special app you can extend that includes a
transaction tween that interfaces with the transaction_ package. The
`morepath_sqlalchemy`_ demo project gives an example of what that
looks like with SQLAlchemy.

.. _transaction: https://pypi.python.org/pypi/transaction

.. _morepath_sqlalchemy: https://github.com/morepath/morepath_sqlalchemy
