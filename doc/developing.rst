Developing Morepath
===================

Community
---------

Communication is important, so see :doc:`community` for information
on how to get in touch!

Install Morepath for development
--------------------------------

.. highlight:: console

Clone Morepath from github::

  $ git clone git@github.com:morepath/morepath.git

If this doesn't work and you get an error 'Permission denied (publickey)',
you need to upload your ssh public key to github_.

Then go to the morepath directory::

  $ cd morepath

Make sure you have virtualenv_ installed.

Create a new virtualenv for Python 3 inside the morepath directory::

  $ virtualenv -p python3 env/py3

Activate the virtualenv::

  $ source env/py3/bin/activate

Make sure you have recent setuptools and pip installed::

  $ pip install -U setuptools pip

Install the various dependencies and development tools from
requirements/develop.txt::

  $ pip install -Ur requirements/develop.txt --src src

This needs your ssh key installed in github_ to work.

The ``--src src`` option makes sure that the dependent ``reg``,
``dectate`` and ``importscan`` projects are checked out in the ``src``
directory. You can make changes to them during development too.

For upgrading the sources and requirements just run the command again.

If you want to test Morepath with Python 2.7 as well you can create a
second virtualenv for it::

  $ virtualenv -p python2.7 env/py27

You can then activate it::

  $ source env/py27/bin/activate

Then uprade setuptools and pip and install the develop requirements as
described above.

.. note::

   The following commands work only if you have the virtualenv activated.

.. _github: https://help.github.com/articles/generating-an-ssh-key

.. _virtualenv: https://pypi.python.org/pypi/virtualenv

Running the tests
-----------------

You can run the tests using `py.test`_::

  $ py.test

To generate test coverage information as HTML do::

  $ py.test --cov --cov-report html

You can then point your web browser to the ``htmlcov/index.html`` file
in the project directory and click on modules to see detailed coverage
information.

.. _`py.test`: http://pytest.org/latest/

flake8
------

flake8_ is a tool that can do various checks for common Python
mistakes using pyflakes_ and checks for PEP8_ style compliance. We
want a codebase where there are no flake8 messages.

To do pyflakes and pep8 checking do::

  $ flake8 morepath

.. _flake8: https://pypi.python.org/pypi/flake8

.. _pyflakes: https://pypi.python.org/pypi/pyflakes

.. _pep8: http://www.python.org/dev/peps/pep-0008/

radon
-----

radon_ is a tool that can check various measures of code complexity.

To check for `cyclomatic complexity`_ (excluding the tests)::

  $ radon cc morepath -e "morepath/tests*"

To filter for anything not ranked ``A``::

  $ radon cc morepath --min B -e "morepath/tests*"

And to see the maintainability index::

  $ radon mi morepath -e "morepath/tests*"

.. _radon: https://radon.readthedocs.org/en/latest/commandline.html

.. _`cyclomatic complexity`: https://en.wikipedia.org/wiki/Cyclomatic_complexity

Running the documentation tests
-------------------------------

The documentation contains code. To check these code snippets, you
can run this code using this command::

  (py3) $ sphinx-build -b doctest doc doc/build/doctest

Or alternatively if you have ``Make`` installed::

  (py3) $ cd doc
  (py3) $ make doctest

Or from the Morepath project directory::

  (py3) $ make -C doc doctest

Since the sample code in the documentation is maintained in Python 3
syntax, we do not support running the doctests with Python 2.7.

Building the HTML documentation
-------------------------------

To build the HTML documentation (output in ``doc/build/html``), run::

  $ sphinx-build doc doc/build/html

Or alternatively if you have ``Make`` installed::

  $ cd doc
  $ make html

Or from the Morepath project directory::

  $ make -C doc html

Developing Reg, Dectate or Importscan
-------------------------------------

If you need to adjust the sources of Reg, Dectate or Importscan and
test them together with Morepath, they're available in the ``src``
directory. You can edit them and test changes in the Morepath project
directly.

If you want to run the tests for one of them, let's say Reg, do::

  $ cd src/reg
  $ py.test

Tox
---

With tox you can test Morepath under different Python environments.

We have Travis continuous integration installed on Morepath's github
repository and it runs the same tox tests after each checkin.

First you should install all Python versions which you want to
test. The versions which are not installed will be skipped. You should
at least install Python 3.5 which is required by flake8, coverage and
doctests and Python 2.7 for testing Morepath with Python 2.

One tool you can use to install multiple versions of Python is pyenv_.

To find out which test environments are defined for Morepath in tox.ini run::

  $ tox -l

You can run all tox tests with::

  $ tox

You can also specify a test environment to run e.g.::

  $ tox -e py35
  $ tox -e pep8
  $ tox -e docs

To find out which dependencies and which versions
tox installs in the testenv, you can use::

  $ tox -e freeze

.. _pyenv: https://github.com/yyuu/pyenv

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
