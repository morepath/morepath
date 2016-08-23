Developing Morepath
===================

Community
---------

Communication is important, so see :doc:`community` for information
on how to get in touch!

Install Morepath for development
--------------------------------

.. highlight:: console

Clone Morepath from github and go to the morepath directory::

  $ git clone git@github.com:morepath/morepath.git
  $ cd morepath

Make sure you have virtualenv_ installed.

.. _virtualenv: https://pypi.python.org/pypi/virtualenv

Create a new virtualenv for Python 3 inside the morepath directory::

  $ virtualenv -p $(which python3) env/py3

Activate the virtualenv::

  $ source env/py3/bin/activate

Install the various dependencies and development tools from
develop_requirements.txt::

  $ pip install -r develop_requirements.txt --src src

If you want to test Morepath also with Python 2.7 you can create a second
virtualenv for it::

  $ virtualenv -p $(which python2.7) env/py27

After activating it with::

  $ source env/py27/bin/activate

you can install the develop requirements as described above.

.. note::

   The following commands work only, if you have the virtualenv activated.

Running the tests
-----------------

You can run the tests using `py.test`_::

  $ py.test morepath

To generate test coverage information as HTML do::

  $ py.test morepath --cov morepath --cov-report html

You can then point your web browser to the ``htmlcov/index.html`` file
in the project directory and click on modules to see detailed coverage
information.

.. _`py.test`: http://pytest.org/latest/

flake8
------

flake8_ is a tool that can do various checks for common Python mistakes
using pyflakes_ and checks for PEP8_ style compliance.

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

  $ sphinx-build -b doctest doc doc/build/doctest

.. note::

   Throughout this documentation, examples are using the Python 3.5 syntax.

.. _Make: https://en.wikipedia.org/wiki/Make_(software)

Building the HTML documentation
-------------------------------

To build the HTML documentation (output in ``doc/build/html``), run::

  $ sphinx-build doc doc/build/html

Developing Reg, Dectate or Importscan
-------------------------------------

If you need to adjust the sources of reg, dectate or importscan and test them
together with morepath, they're available in the src directory.
There you can edit them and test the changes with morepath, which uses them as
dependencies when you install Morepath for developement as described above.

Installing tox locally with with different Python versions
----------------------------------------------------------

If you want to check if Morepath works works with the supported Python versions
and check if it pathes all Travis Ci tests, you can install tox locally.

Tox is also used by Travis Ci on GitHub.

First you should install all Python versions, which you want to test. The
versions which are not installed will be skipped. At least you should install
Python 3.5, which is required by flake8, coverage and doctests, and Python 2.7
for testing Morepath with Python 2.

You can install the Python versions, which are missing in your system with
pyenv_, which can be installed with Homebrew_ on Mac OS X::

  $ brew update
  $ brew install pyenv

or the `pyenv-installer`_ e.g. on Linux::

  $ curl -L https://raw.githubusercontent.com/yyuu/pyenv-installer/master/bin/pyenv-installer | bash

Make sure your bash configuration was updated. If your system uses `~/.bashrc`
instead of `~/.bash_profile` like Debian or Ubuntu, you have to add the
following lines to `~/.bashrc` manually::

  export PATH="~/.pyenv/bin:$PATH"
  eval "$(pyenv init -)"
  eval "$(pyenv virtualenv-init -)"

Then you can install your missing Python versions e.g.::

  $ pyenv install 3.5.2
  $ pyenv install 3.3.6
  $ pyenv install pypy-5.3.1

And activate them globally, the first one will be the default
Python environment::

  $ pyenv global 3.5.2 3.3.6 pypy-5.3.1

Make sure you have recent virtualenv, setuptools and pip installed
systemwide::

  $ sudo pip install -U virtualenv setuptools pip

Now you can install tox::

  $ pip install -U tox

.. _pyenv: https://github.com/yyuu/pyenv

.. _Homebrew: https://github.com/yyuu/pyenv#homebrew-on-mac-os-x

.. _`pyenv-installer`: https://github.com/yyuu/pyenv-installer#pyenv-installer

Tox test environments
---------------------

The following tox test environments are defined for Morepath in tox.ini:

py27
  py.test with Python 2.7

pypy
  py.test with PyPy

py33
  py.test with Python 3.3

py34
  py.test with Python 3.4

py35
  py.test with Python 3.5

pep8
  Flake8 tests in Python 3.5 environment

coverage
  Coverage test for py.test in Python 3.5 environment

docs
  Doctests in Python 3.5 environment

Running tox locally
-------------------

You can run all tox tests with::

  $ tox

You can also specify a test environment to run::

  $ tox -e py35
  $ tox -e pep8
  $ tox -e docs

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
