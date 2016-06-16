Developing Morepath
===================

Community
---------

Communication is important, so see :doc:`community` for information
on how to get in touch!

Install Morepath for development
--------------------------------

.. highlight:: sh

First make sure you have virtualenv_ installed for Python 3.5.

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

  $ /path/to/ve_morepath/bin/python bootstrap.py

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

Running the documentation tests
-------------------------------

The documentation contains code. To check these code snippets, you
can run this code using this command::

  $ bin/sphinxpython bin/sphinx-build -b doctest doc doc/build/doctest

If you have Make_ installed, buildout generates for you a Makefile in
the directory ``doc/build`` that you can use::

  $ (cd doc/build; make doctest)

.. note::

   Throughout this documentation, examples are using the Python 3.5 syntax.

.. _Make: https://en.wikipedia.org/wiki/Make_(software)

Building the HTML documentation
-------------------------------

To build the HTML documentation (output in ``doc/build/html``), run::

  $ bin/sphinxbuilder

Deprecation
-----------

In some cases we have to make changes that break compatibility and
break user code. We mark these in ``CHANGES.txt`` (:doc:`changes`)
using **breaking change**, **deprecated** or **removed**.

These entries should explain the change, and also tell the user what
to do to upgrade their code. Do include an before/after code example
as that makes it much easier, even if it's a simple import change.

We like to keep things moving and reserve the right to introduce
breaking changes. When we do make a breaking change it should be
marked clearly in ``CHANGES.txt`` (:doc:`changes`) with a **Breaking
change** marker.

If it is not a great burden we use deprecations. Morepath in this case
retains the old APIs but issues a deprecation warning. See
:doc:`upgrading` for the notes for end-users concerning this. Here is
the deprecation procedure for developers:

* Add a **Deprecated** entry in ``CHANGES.txt`` that describes what
  to do, as in a **breaking change**.

* Issue a deprecation warning in the code that is deprecated.

* Put a ``**Deprecated**`` entry in the docstring of whatever got
  deprecated with a brief comment on what to do.

* Put an issue labeled ``remove deprecation`` in the tracker for one
  release milestone after the upcoming release that states we should
  remove the deprecation. Create the milestone if needed.

  This way we don't maintain deprecated code and their warnings
  indefinitely -- one release later we remove the backwards
  compatibility code and deprecation warnings.

* Once we go and remove code, we repeat the information on what to do
  in a new *Removed** entry in ``CHANGES.txt``; treat it just like
  **Breaking change** and recycle the text written for the previous
  **Deprecated** entry for the stuff we're now removing.
