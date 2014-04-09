Developing Morepath
===================

Install Morepath for development
--------------------------------

.. highlight:: sh

First make sure you have virtualenv_ installed for Python 2.7.

.. _virtualenv: https://pypi.python.org/pypi/virtualenv

Now create a new virtualenv somewhere for Morepath development::

  $ virtualenv /path/to/ve_morepath

You should also be able to recycle an existing virtualenv, but this
guarantees a clean one. Note that we skip activating the environment
here, as this is just needed to initially bootstrap the Morepath
buildout.

Clone Morepath from github and go to the morepath directory::

  $ git clone git@github.com:morepath/morepath.git
  $ cd morepath

Now we need to run bootstrap.py to set up buildout, using the Python from the
virtualenv we've created before::

  $ python /path/to/ve_morepath/bin/python/bootstrap.py

This installs buildout, which can now set up the rest of the development
environment::

  $ bin/buildout

This downloads and installs various dependencies and tools. The
commands you run in ``bin`` are all restricted to the virtualenv you
set up before. There is therefore no need to refer to the virtualenv
once you have the development environment going.

Running the tests
-----------------

You can run the tests using `py.test`_. Buildout has installed it for
you in the ``bin`` subdirectory of your project::

  $ bin/py.test morepath

To generate test coverage information as HTML do::

  $ bin/py.test morepath --cov morepath --cov-report html

You can then point your web browser to the ``htmlcov/index.html`` file
in the project directory and click on modules to see detailed coverage
information.

.. _`py.test`: http://pytest.org/latest/

flake8
------

The buildout also installs flake8_, which is a tool that
can do various checks for common Python mistakes using pyflakes_ and
checks for PEP8_ style compliance.

To do pyflakes and pep8 checking do::

  $ bin/flake8 morepath

.. _flake8: https://pypi.python.org/pypi/flake8

.. _pyflakes: https://pypi.python.org/pypi/pyflakes

.. _pep8: http://www.python.org/dev/peps/pep-0008/

radon
-----

The buildout installs radon_. This is a tool that can check various
measures of code complexity.

To check for `cyclomatic complexity`_ (excluding the tests)::

  $ bin/radon cc morepath -e "morepath/tests*"

To filter for anything not ranked ``A``::

  $ bin/radon cc morepath --min B -e "morepath/tests*"

And to see the maintainability index::

  $ bin/radon mi morepath -e "morepath/tests*"

.. _radon: https://radon.readthedocs.org/en/latest/commandline.html

.. _`cyclomatic complexity`: https://en.wikipedia.org/wiki/Cyclomatic_complexity
