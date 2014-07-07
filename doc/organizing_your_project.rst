Organizing your Project
=======================

Introduction
------------

Morepath does not put any requirements on how your Python code is
organized. You can organize your Python project as you see fit and put
app classes, paths, views, etc, anywhere you like. A single Python
package (or even module) may define a single Morepath app, but could
also define multiple apps. In this Morepath is like Python itself; the
Python language does not restrict you in how you organize functions
and classes.

While this leaves you free to organize your code as you see fit, that
doesn't mean that your code shouldn't be organized. Here are some
guidelines on how you may want to organize things in your own
project. But remember: these are guidelines to break when you see the
need.

Python project
--------------

It is recommended you organize your code in a Python project with a
``setup.py`` where you declare the dependency on Morepath. If you're
unfamiliar with how this works, you can check out `this tutorial`_.

.. _`this tutorial`: http://pythonhosted.org/an_example_pypi_project/setuptools.html

Doing this is good Python practice and makes it easy for you to
install and distribute your project using common tools like pip,
buildout and PyPI. In addition Morepath itself can also load its code
more easily.

Project layout
--------------

Here's a quick overview of the files and directories of Morepath
project that follows the guidelines in this document::

  myproject
      setup.py
      myproject
           __init__.py
          main.py
          model.py
          [collection.py]
          path.py
          view.py

Project setup
-------------

Here is an example of your project's ``setup.py`` with only those
things relevant to Morepath shown and everything else cut out::

  from setuptools import setup, find_packages

  setup(name='myproject',
        packages=find_packages(),
        install_requires=[
           'morepath'
        ],
        entry_points={
           'console_scripts': [
            'myproject-start = myproject.main:main'
            ]
        })

This ``setup.py`` assumes you also have a ``myproject`` subdirectory
in your project directory that is a Python package, i.e. it contains
an ``__init__.py``. This is the directory where you put your code. The
``find_packages()`` call finds it for you.

The ``install_requires`` section declares the dependency on
Morepath. Doing this makes everybody who installs your project
automatically also pull in a release of Morepath and its own
dependencies. In addition, it lets this package be found and
configured when you use :func:`morepath.autosetup`.

Finally there is an ``entry_points`` section that declares a console
script (something you can run on the command-prompt of your operating
system). When you install this project, a ``myproject-start`` script
is automatically generated that you can use to start up the web
server. It calls the ``main()`` function in the ``myproject.main``
module. Let's create this next.

See also the `setuptools documentation`_.

.. _`setuptools documentation`: https://pythonhosted.org/setuptools/

Project naming
--------------

Its possible to name your project differently than you name your
Python package; you could for instance have the name ``ThisProject``
in ``setup.py``, and then have your Python package be still called
``myproject``. We recommend naming the project the same as the Python
package to avoid confusion.

Namespace packages
------------------

Sometimes you have projects that are grouped in some way: they are all
created by the same organization or they are part of the same larger
project. In that case you can use Python namespace packages to make
this relationship clear. Let's say you have a larger project called
``myproject``. The namespace package itself may not contain any code,
so unlike the example everywhere else in this document the
``myproject`` directory is always empty but for a ``__init__.py``.

Different sub-projects could then be called ``myproject.core``,
``myproject.wiki``, etc. Let's examine the files and directories of
``myproject.core``::

  myproject.core
      setup.py
      myproject
          __init__.py
          core
              __init__.py
              main.py
              model.py
              [collection.py]
              path.py
              view.py

The change is the namespace package directory ``myproject`` that contains
a single file, ``__init__.py``, that contains the following code to declare
it is a namespace package::

  __import__('pkg_resources').declare_namespace(__name__)

Inside is the normal package called ``core``.

``setup.py`` is modified too to include a declaration in
``namespace_packages``, and we've changed the entry point::

  setup(name='myproject.core',
        packages=find_packages(),
        namespace_packages=['myproject'],
        install_requires=[
           'morepath'
        ],
        entry_points={
           'console_scripts': [
            'myproject.core-start = myproject.core.main:main'
            ]
        })

See also the `namespace packages documentation`_.

.. _`namespace packages documentation`: http://pythonhosted.org/setuptools/setuptools.html#namespace-packages

Main Module
-----------

The ``main.py`` module is where we define our Morepath app and allow a
way to start it up as a web server. Here's a sketch of ``main.py``::

  import morepath

  class app(morepath.App):
      pass

  def main():
     morepath.autosetup()
     morepath.run(app())

We create an ``app`` class, then have a ``main()`` function that is
going to be called by the ``myproject-start`` entry point we defined
in ``setup.py``. This main function does two things:

* Use :func:`morepath.autosetup()` to set up Morepath, including any
  of your code.

* start a WSGI server for the ``app`` instance on port localhost,
  port 5000. This uses the standard library wsgiref WSGI server. Note
  that this should only used for testing purposes, not production! For
  production, use an external WSGI server.

The main module is also a good place to do other general configuration
for the application, such as setting up a database connection.

Variation: no or multiple entry points
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Not all packages have an entry point to start it up: a framework app
that isn't intended to be run directly may not define one. Some
packages may define multiple apps and multiple entry points.

Variation: waitress
~~~~~~~~~~~~~~~~~~~

Instead of using Morepath's simple built-in WSGI server you can use
another WSGI server. The built-in WSGI server is only meant for
testing, so we strongly recommend doing so in production. Here's how
you'd use Waitress_. First we adjust ``setup.py`` so we also require
waitress::

  ...
        install_requires=[
           'morepath',
           'waitress'
        ],
  ...

Then we modify ``main.py`` to use waitress::

  import waitress

  ...

  def main():
     ...
     waitress.serve(app())

Variation: command-line WSGI servers
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You could also do away with the entry point and instead use
``waitress-serve`` on the command line directly. For this we need to
first create a factory function that returns the fully configured WSGI
app::

  def wsgi_factory():
     morepath.autosetup()
     return app()

  $ waitress-serve --call myproject.main:wsgi_factory

This uses waitress's ``--call`` functionality to invoke a WSGI factory
instead of a WSGI function. If you want to use a WSGI function
directly we have to create one using the ``wsgi_factory`` function we
just defined. To avoid circular dependencies you should do it in a
separate module that is only used for this purpose, say ``wsgi.py``::

  prepared_app = wsgi_factory()

You can then do::

  $ waitress-serve myproject.wsgi:prepared_app

You can also use gunicorn_ this way::

  $ gunicorn -w 4 myproject.wsgi:prepared_app

.. _Waitress: http://docs.pylonsproject.org/projects/waitress/en/latest/

.. _Gunicorn: http://gunicorn.org

Model module
------------

The ``model.py`` module is where we define the models relevant to the
web application. They may integrate with some kind of database system,
for instance the SQLAlchemy_ ORM. Note that your model code is
completely independent from Morepath and there is no reason to import
anything Morepath related into this module. Here is an example
``model.py`` that just uses plain Python classes::

  class Document(object):
      def __init__(self, id, title, content):
          self.id = id
          self.title = title
          self.content = content

.. _SQLAlchemy: http://sqlalchemy.org

Variation: models elsewhere
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Sometimes you don't want to include model definitions in the same
codebase that also implements a web application, as you would like to
reuse them outside of the web context without any dependencies on
Morepath. Your model classes are independent from Morepath, so this is
easy to do: just put them in a separate project and depend on it from
your web project.

You can also have a project that reuses models defined by another
Morepath project. Each Morepath app is isolated from the others by
default, so you could remix its models into a whole new web
application.

Variation: collection module
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

An application tends to contain two kinds of models:

* content object models, i.e. a Document. If you use an ORM like
  SQLAlchemy these would typically be backed by a table.

* collection models, i.e. a collection of documents. This typically
  let you browse content models, search/filter for them, and let you
  add or remove them.

Since collection models tend to not be backed by a database directly
but are often application-specific classes, it can make sense to
maintain them in a separate ``collection.py`` module. This module,
like ``model.py`` also does not have any dependencies on Morepath.

Path module
-----------

Now that we have models, we need to publish them on the web. First we need
to define their paths. We do this in a ``path.py`` module::

  from myproject.main import app
  from myproject import model

  @app.path(model=model.Document, path='documents/{id}')
  def get_document(id):
     if id != 'foo':
        return None # not found
     return Document('foo', 'Foo document', 'FOO!')

In the functions decorated by :meth:`App.path` we do whatever
query is necessary to retrieve the model instance from a database, or
return ``None`` if the model cannot be found.

Morepath allows you to scatter ``@app.path`` decorators throughout
your codebase, but by putting them all together in a single module it
becomes really easy to inspect and adjust the URL structure of your
application, and to see exactly what is done to query or construct the
model instances. Once it becomes really big you can always split a
single path module into multiple ones, though at that point you may
want to consider splitting off a separate project with its own
application instead.

View module
-----------

We have models and they're published on a path. Now we need to represent
them as actual web resources. We do this in the ``view.py`` module::

  from myproject.main import app
  from myproject import model

  @app.json(model=model.Document)
  def document_default(self, request):
      return {'id': self.id, 'title': self.title, 'content': self.content }

Here we use :meth:`App.view`, :meth:`App.json` and
:meth:`App.html` directives to declare views.

By putting them all in a view module it becomes easy to inspect and
adjust how models are represented, but of course if this becomes large
it's easy to split it into multiple modules.
