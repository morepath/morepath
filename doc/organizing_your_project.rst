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

Sounds Like a Lot of Work
-------------------------

You're in luck. If you want to skip this chapter and just get started, you can
use the Morepath cookiecutter template, which follows the guidelines layed out
in this chapter:

`<https://github.com/morepath/morepath-cookiecutter>`_

If you want to find out more about the why and the how, you can always keep
on reading of course.

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
          app.py
          model.py
          [collection.py]
          path.py
          run.py
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
            'myproject-start = myproject.run:run'
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
configured when you use :func:`morepath.autoscan`.

Finally there is an ``entry_points`` section that declares a console
script (something you can run on the command-prompt of your operating
system). When you install this project, a ``myproject-start`` script
is automatically generated that you can use to start up the web
server. It calls the ``run()`` function in the ``myproject.run``
module. Let's create this next.

You now need to install this project. If you want to install this
project for development purposes you can use ``python setup.py
develop``, or ``pip install -e .`` from within a virtualenv.

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
              app.py
              model.py
              [collection.py]
              path.py
              run.py
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
            'myproject.core-start = myproject.core.run:run'
            ]
        })

See also the `namespace packages documentation`_.

.. _`namespace packages documentation`: http://pythonhosted.org/setuptools/setuptools.html#namespace-packages

App Module
-----------

The ``app.py`` module is where we define our Morepath app. Here's a sketch of
``app.py``::

  import morepath

  class App(morepath.App):
      pass

Run Module
----------

.. sidebar:: Why we keep app.py and run.py separate

  Morepath attaches a configuration registry to each application class. This
  can happen twice if we run the run function directly from python (through
  use of ``__main__``). By keeping the application from the run code we can
  be sure that this never happens.

In the ``run.py`` module we define how our application should be served. We
take the ``App`` class defined in ``app.py``, then have a ``run()`` function
that is going to be called by the ``myproject-start`` entry point we defined
in ``setup.py``::

  from .app import App

  def run():
      morepath.autoscan()
      App.commit()
      morepath.run(App())

This run function does the following:

* Use :func:`morepath.autoscan()` to recursively import your own
  package plus any dependencies that are installed.

* Commit the ``App`` class so that its configuration is ready. You can
  omit this step and in this case the configuration is committed when
  Morepath processes the first request. But if you want to see configuration errors
  at startup, use an explicit ``commit``.

* start a WSGI server for the ``App`` instance on port localhost,
  port 5000. This uses the standard library wsgiref WSGI server. Note
  that this should only used for testing purposes, not production! For
  production, use an external WSGI server.

The run module is also a good place to do other general configuration
for the application, such as setting up a database connection.

Upgrading your project to a newer version of Morepath
-----------------------------------------------------

See :doc:`upgrading`.

Debugging scanning problems
---------------------------

If you for some reason get ``404 Not Found`` errors where you expect
some content, something may have gone wrong with scanning the
configuration of your project. Here's a checklist:

* Check whether your project has a ``setup.py`` with an
  ``install_requires`` that depends on ``morepath`` (possibly
  indirectly through another dependency). You need to declare your
  code as a project so that ``autoscan`` can find it.

* Check whether your project is installed in a virtualenv using ``pip
  install -e .`` or in a buildout. Morepath needs to be able to find
  your project in order to scan it.

* Be sure that you have your modules in an actual sub-directory to the
  project with its own ``__init__.py``. Modules in the top-level of a
  project won't be scanned as a package

* Try manually scanning a package and see whether it works then::

    import mysterious_package

    morepath.scan(mysterious_package)

  If this fixes things, the package is somehow not being picked up for
  automatic scanning. Check the package's ``setup.py``.

* Try manually importing the modules before doing a
  :func:`morepath.autoscan` and see whether it works then::

    import mysterious_module

    morepath.autoscan()

  If this fixes things, then your own package is not being picked up
  as a Morepath package for some reason.

* Try moving Morepath directives into the module that also runs
  the application. If this works, your own package is not recognized
  as a proper Morepath package.

Variation: automatic restart
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

During development it can be very helpful to have the WSGI server
restart the Morepath app whenever a file is changed.

Morepath's built in development server does not offer this feature,
but you can accomplish it with `Werkzeug's server`_.

First install the `Werkzeug package`_ into your project. Then modify
your run module to look like this::

  import morepath
  from werkzeug.serving import run_simple
  from .app import App

  def run():
      morepath.autoscan()
      App.commit()
      run_simple('localhost', 8080, App(), use_reloader=True)

Using this runner changes to Python code in your package trigger a
restart of the WSGI server.

.. _`Werkzeug's server`: http://werkzeug.pocoo.org/docs/latest/serving/

.. _`Werkzeug package`: https://pypi.python.org/pypi/Werkzeug

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

Then we modify ``run.py`` to use waitress::

  import waitress

  ...

  def run():
     ...
     waitress.serve(App())

Variation: command-line WSGI servers
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You could also do away with the entry point and instead use
``waitress-serve`` on the command line directly. For this we need to
first create a factory function that returns the fully configured WSGI
app::

  def wsgi_factory():
     morepath.autoscan()
     App.commit()
     return App()

  $ waitress-serve --call myproject.run:wsgi_factory

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

  from .app import App
  from . import model

  @App.path(model=model.Document, path='documents/{id}')
  def get_document(id):
     if id != 'foo':
        return None # not found
     return Document('foo', 'Foo document', 'FOO!')

In the functions decorated by :meth:`App.path` we do whatever
query is necessary to retrieve the model instance from a database, or
return ``None`` if the model cannot be found.

Morepath allows you to scatter ``@App.path`` decorators throughout
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

  from .app import App
  from . import model

  @App.json(model=model.Document)
  def document_default(self, request):
      return {'id': self.id, 'title': self.title, 'content': self.content }

Here we use :meth:`App.view`, :meth:`App.json` and
:meth:`App.html` directives to declare views.

By putting them all in a view module it becomes easy to inspect and
adjust how models are represented, but of course if this becomes large
it's easy to split it into multiple modules.

Directive debugging
-------------------

Morepath's directive issue log messages that can help you debug your
application: see :doc:`logging` for more information.


