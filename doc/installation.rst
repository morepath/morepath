Installation
============

Quick and Dirty Installation
----------------------------

To get started with Morepath right away, first create a Python 3.5
virtualenv_::

  $ virtualenv morepath_env
  $ source morepath_env/bin/activate

Now install Morepath into it::

  $ pip install morepath

You can now use the virtual env's Python to run any code that uses
Morepath::

  $ python quickstart.py

See :doc:`quickstart` for information on how to get started with
Morepath itself, including an example of ``quickstart.py``.

.. _virtualenv: http://www.virtualenv.org/

.. _cookiecutter:

Creating a Morepath Project Using Cookiecutter
----------------------------------------------

Morepath provides an official cookiecutter template. Cookiecutter is a tool
that creates projects through project templates. Morepath's template comes
with a very simple application, either in RESTful or traditional HTML flavor.

Follow the instructions on Morepath's cookiecutter template repository to
get started:

`<https://github.com/morepath/morepath-cookiecutter>`_

This is a great way to get started with Morepath as a beginner or to start
a new project as a seasoned Morepath user.

Creating a Morepath Project Manually
------------------------------------

When you develop a web application it's a good idea to use standard
Python project organization practices. :doc:`organizing_your_project`
has some recommendations on how to do this with Morepath. Relevant in
particular is the contents of ``setup.py``, which depends on Morepath
and also sets up an entry point to start the web server.

Once you have a project you can use tools like pip_ or
buildout_. We'll briefly describe how to use both.

.. _pip: http://www.pip-installer.org/

.. _buildout: http://www.buildout.org/

pip
~~~


With pip and a virtualenv called ``morepath_env``, you can do this in
your project's root directory::

  $ pip install --editable .

You can now run the application like this (if you called the console
script ``myproject-start``)::

  $ myproject-start

buildout
~~~~~~~~

Buildout is more involved than pip, but can also do a lot more for you
automatically and repeatedly.

Create a ``buildout.cfg`` file containing this::

  [buildout]
  develop = .
  parts = scripts devpython
  versions = versions

  [versions]
  venusian = 1.0a8
  morepath = 0.1
  reg = 0.6

  [scripts]
  recipe = zc.recipe.egg:scripts
  eggs = myproject
         pytest

  [devpython]
  recipe = zc.recipe.egg
  interpreter = devpython
  eggs = myproject
         flake8

This describes how to install our project for development. Change
``myproject`` to the name your project has in ``setup.py``.

Place a buildout `bootstrap.py`_ in your project's root directory.

.. _`bootstrap.py`: http://downloads.buildout.org/2/bootstrap.py

The first time you create or check out a project you need to bootstrap
the buildout. You can do this using the ``bootstrap.py`` script. Do
this from a virtualenv::

  $ /path/to/morepath_env/bin/python bootstrap.py

You only need to do this once. After that you can run::

  $ bin/buildout

each time you want to redo the installation after you change the
buildout config. It's safe to run this when nothing has really changed
too.

Once you've run buildout, you can start your application. If it's
named ``myproject-start`` in the entry point in ``setup.py``, you can
run it like this::

  $ bin/myproject-start

.. sidebar:: ``bin`` directory

  Everything in ``bin`` will run in the virtualenv you've used to
  bootstrap your project automatically (or in a subset thereof).

What's going on with buildout?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

What's going on? What else did that ``buildout.cfg`` do for us?

The ``develop`` line tells which directories to look in for Python
projects (with a ``setup.py``).  In this case only the local project
directory ``.`` is one. But if you also have the checkout of another
project that you depend on (maybe a development version of Morepath
itself), you can add that directory to the ``develop`` section.

.. sidebar:: mr.developer

  If you are going to develop such a multi-project codebase you should
  consider the buildout extension `mr.developer`_ which can help you
  automate this.

  .. _`mr.developer`: https://pypi.python.org/pypi/mr.developer

``parts`` tells buildout what to configure; they are described in
the ``[scripts]`` and ``[devpython]`` sections later.

The line ``versions=versions`` tells buildout to lock down version
numbers according to the ``[versions]``
section.

.. sidebar:: show-picked-versions

  You can add a line ``show-picked-versions = true`` to the
  ``[buildout]`` section. When you now run ``bin/buildout`` this dumps
  all versions of libraries you use directly or indirectly that you
  haven't locked down to an explicit version to the console. You can
  then lock them down in the ``[versions]`` section.

  Locking down versions is useful if you want to make sure everybody
  has the same versions of the libraries in development.

The ``[scripts]`` section installs your web application as a script in
the ``bin`` subdirectory of your project, according to the
``console_scripts`` entry point in your project's ``setup.py``. If
it's called ``myproject-start``, then you can start it like this::

  bin/myproject-start

This will start a HTTP server for your project.

The buildout also has installed `pytest`_ so you can run your
project's tests automatically::

  bin/py.test myproject

(if your Python package is in ``myproject``)

..  _pytest: http://pytest.org/

.. sidebar:: Test dependencies

  If you want to add some extra dependencies just for testing, you can
  do this in your project's ``setup.py`` by adding::

    extras_require = dict(
      test=['pytest >= 2.5',
            'pytest-cov'],
    ),

  This makes sure we have a ``pytest`` version 2.5 or later, and we
  install the ``pytest-cov`` code coverage extension.

  You can then modify the ``[scripts]`` section in ``buildout.cfg`` to
  use the extra ``test`` requirements::

    [scripts]
    recipe = zc.recipe.egg:scripts
    eggs = myproject [test]
           pytest

Now as to some optional extras. The ``[devpython]`` section installs a
Python interpreter which can import exactly what your project can
import. It assumes your project is called ``myproject`` in its
``setup.py``; change the name to match your project. You can start it
using::

  $ bin/devpython

You'll get the usual Python console ``>>>``. This is useful for
testing your project's imports and API manually.

It also installs the flake8_ tool which runs pep 8 checks and pyflakes
automatically. You can run it against your project by writing::

  $ bin/flake8 myproject

where ``myproject`` is your project's source code directory.

.. _flake8: https://pypi.python.org/pypi/flake8

Depending on Morepath development versions
------------------------------------------

If you like being on the cutting edge and want to depend on the latest
Morepath and Reg development versions always, we recommend you use
buildout with the mr.developer extension for your project. You can see
how in `this buildout.cfg`_.

.. _`this buildout.cfg`: https://github.com/morepath/morepath_hello/blob/master/buildout.cfg

You can also install these using pip (in a virtualenv). Here's how::

  $ pip install git+git://github.com/morepath/reg.git@master

  $ pip install git+git://github.com/morepath/morepath.git@master
