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

Create a new virtualenv inside the morepath directory::

  $ python -m venv --upgrade-deps .venv

Activate the virtualenv::

  $ source .venv/bin/activate

Install the various dependencies and development tools from
requirements/develop.txt::

  (.venv) $ pip install -Ur requirements/develop.txt --src src

This needs your ssh key installed in github_ to work.

The ``--src src`` option makes sure that the dependent ``reg``,
``dectate`` and ``importscan`` projects are checked out in the ``src``
directory. You can make changes to them during development too.

For upgrading the sources and requirements just run the command again.

.. note::

   The following commands work only if you have the virtualenv activated.

.. _github: https://docs.github.com/en/authentication/connecting-to-github-with-ssh

Install pre-commit hook for Black integration
---------------------------------------------

We're using Black_ for formatting the code and it's recommended to
install the `pre-commit hook`_ for Black integration before committing::

  (.venv) $ pre-commit install

.. _`pre-commit hook`: https://black.readthedocs.io/en/stable/integrations/source_version_control.html

Running the tests
-----------------

You can run the tests using `pytest`_::

  (.venv) $ pytest

To generate test coverage information as HTML do::

  (.venv) $ pytest --cov --cov-report html

You can then point your web browser to the ``htmlcov/index.html`` file
in the project directory and click on modules to see detailed coverage
information.

.. _`pytest`: https://pytest.org

Black
-----

To format the code with the `Black Code Formatter`_ run in the root directory::

  (.venv) $ black .

Black has also integration_ for the most popular editors.

.. _`Black Code Formatter`: https://black.readthedocs.io
.. _integration: https://black.readthedocs.io/en/stable/editor_integration.html

isort
-----

To sort imports with isort_ from the project directory do::

  (.venv) $ isort .

isort uses the settings in ``pyproject.toml``.

.. _isort: https://pycqa.github.io/isort/

flake8
------

flake8_ is a tool that can do various checks for common Python
mistakes using pyflakes_ and checks for PEP8_ style compliance. We
want a codebase where there are no flake8 messages.

To do pyflakes and pep8 checking do::

  (.venv) $ flake8 morepath

.. _flake8: https://pypi.org/project/flake8
.. _pyflakes: https://pypi.org/project/pyflakes
.. _pep8: https://peps.python.org/pep-0008

Type checking
-------------

Morepath uses mypy_ and pyright_ for type checking. Run either checker
from the project directory::

  (.venv) $ mypy
  (.venv) $ pyright

Both checkers use the settings in ``pyproject.toml``.

.. _mypy: https://mypy.readthedocs.io/
.. _pyright: https://microsoft.github.io/pyright/


Running the documentation tests
-------------------------------

The documentation contains code. To check these code snippets, you
can run this code using this command::

  (.venv) $ sphinx-build -b doctest doc doc/build/doctest

Or alternatively if you have ``Make`` installed::

  (.venv) $ cd doc
  (.venv) $ make doctest

Or from the Morepath project directory::

  (.venv) $ make -C doc doctest

Building the HTML documentation
-------------------------------

To build the HTML documentation (output in ``doc/_build/html``), run::

  (.venv) $ sphinx-build doc doc/_build/html

Or alternatively if you have ``Make`` installed::

  (.venv) $ cd doc
  (.venv) $ make html

Or from the Morepath project directory::

  (.venv) $ make -C doc html

Developing Reg, Dectate or Importscan
-------------------------------------

If you need to adjust the sources of Reg, Dectate or Importscan and
test them together with Morepath, they're available in the ``src``
directory. You can edit them and test changes in the Morepath project
directly.

If you want to run the tests for one of them, let's say Reg, do::

  (.venv) $ cd src/reg
  (.venv) $ pytest

Tox
---

With tox you can test Morepath under different Python environments.

We have gh-actions continuous integration installed on Morepath's github
repository and it runs the same tox tests after each checkin.

First you should install all Python versions which you want to
test. The versions which are not installed will be skipped. You should
at least install Python 3.14 which is required by flake8, coverage,
doctests, mypy and pyright.

One tool you can use to install multiple versions of Python is pyenv_.

To find out which test environments are defined for Morepath in tox.ini run::

  (.venv) $ tox -l

You can run all tox tests with::

  (.venv) $ tox

You can also specify a test environment to run e.g.::

  (.venv) $ tox -e py311
  (.venv) $ tox -e lint
  (.venv) $ tox -e docs

To find out which dependencies and which versions
tox installs in the testenv, you can use::

  (.venv) $ tox -e freeze

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
