Building Large Applications
===========================

Introduction
------------

A small web application is relatively easy to understand. It does
less stuff. That makes the application easier to understand: the UI
(or REST web service) is smaller, and the codebase too.

But sometimes we need larger web applications. Morepath offers a
number of facilities to help you manage the complexity of larger web
applications:

* Morepath lets you build larger applications from multiple smaller
  ones. A CMS may for instance be composed of a document management
  application and a user management application. This is much like how
  you manage complexity in a codebase by decomposing it into smaller
  functions and classes.

* Morepath lets you factor out common, reusable functionality. In
  other words, Morepath helps you build *frameworks*, not just
  end-user applications. For instance, you may have multiple places in
  an application where you need to represent a large result-set in
  smaller batches (with previous/next), and they should share common
  code.

There is also the case of reusable *applications*. Larger applications
are often deployed multiple times. An open source CMS is a good
example: different organizations each have their own installation. Or
imagine a company with an application that it sells to its customers:
each customer can have its own special deployment.

Different deployments of an application have real differences as every
organization has different requirements. This means that you need to
be able to customize and extend the application to fit the purposes of
each particular deployment. As a result the application has to
take on framework-like properties. Morepath recognizes that there is a
large gray area between application and framework, and offers support
to build framework-like applications and application-like frameworks.

The document doc:`app_reuse` describes the basic facilities Morepath
offers for application reuse. The document
:doc:`organizing_your_project` describes how a single application
project can be organized, and we will follow its guidelines in this
document.

This document sketches out an example of a larger application that
consists of multiple sub-projects and sub-apps, and that needs
customization.

A Code Hosting Site
-------------------

Our example large application is a code hosting site along the lines
of Github or Bitbucket. This example is a sketch, not a complete
working application. We focus on the structure of the application as
opposed to the details of the UI.

Let's examine the URL structure of a code hosting site. Our hypothetical
code hosting site lives on ``example.com``::

  example.com

A user (or organization) has a URL directly under the root with the
user name or organization name included::

  example.com/faassen

Under this URL we can find repositories, using the project name
in the URL::

  example.com/faassen/myproject

We can interact with repository settings on this URL::

  example.com/faassen/myproject/settings

We also have a per-repository issue tracker::

  example.com/faassen/myproject/issues

And a per-repository wiki::

  example.com/faassen/myproject/wiki

Simplest approach
-----------------

The simplest approach to make this URL structure work is to implement all
paths in a single application, like this::

  from .model import Root, User, Repository, Settings, Issues, Wiki

  class App(morepath.App):
      pass

  @App.path(path='', model=Root)
  def get_root():
     ...

  @App.path(path='{user_name}', model=User)
  def get_user(user_name):
     ...

  @App.path(path='{user_name}/{repository_name}', model=Repository)
  def get_repository(user_name, repository_name):
     ...

We could try to implement settings, issues and wiki as views on
repository, but these are complicated pieces of functionality that
benefit from having sub-URLs (i.e. ``issues/12`` or
``...wiki/mypage``), so we model them using paths as well::

  @App.path(path='{user_name}/{repository_name}/settings', model=Settings)
  def get_settings(user_name, repository_name):
     ...

  @App.path(path='{user_name}/{repository_name}/issues', model=Issues)
  def get_issues(user_name, repository_name):
     ...

  @App.path(path='{user_name}/{repository_name}/wiki', model=Wiki)
  def get_wiki(user_name, repository_name):
     ...

Let's also make a path to an individual issue,
i.e. ``example.com/faassen/myproject/issues/12``::

  from .model import Issue

  @App.path(path='{user_name}/{repository_name}/issues/{issue_id}', model=Issue)
  def get_issue(user, repository, issue_id):
      ...

Problems
--------

This approach works perfectly well, and it's often the right way to
start, but there are some problems with it:

* The URL patterns in the path are repetitive; for each sub-model
  under the repository we keep having to repeat
  '{user_name}/{repository_name}`.

* We may want to be able to test the wiki or issue tracker during
  development without having to worry about setting up the whole outer
  application.

* We may want to reuse the wiki application elsewhere, or in multiple
  places in the same larger application. But ``user_name`` and
  ``repository_name`` are now hardcoded in the way to get any sub-path
  into the wiki.

* We could have different teams developing the core app and the wiki
  (and issue tracker, etc). It would be nice to partition the code so
  that the wiki developers don't need to look at the core app code and
  vice versa.

* You may want the abilitity to swap in new implementations of a issue
  tracker or a wiki under the same paths, without having to change a
  lot of code.

We're going to show how Morepath can solve these problems by
partitioning a larger app into smaller ones, and mounting them.

The code to accomplish this is more involved than simply declaring all
paths under a single core app as we did before. If you feel more
comfortable doing that, by all means do so; you don't have these
problems. But if your application is successful and grows larger you
may encounter these problems, and these features are then there to
help.

Multiple sub-apps
-----------------

Let's split up the larger app into multiple sub apps. How many
sub-apps do we need? We could go and partition things up into many
sub-applications, but that risks getting lost in another kind of
complexity. So let's start with three application:

* core app, everything up to repository, and including settings.

* issue tracker app.

* wiki sub app.

In code::

  class CoreApp(morepath.App):
      pass

  class IssuesApp(morepath.App):
      def __init__(self, issues_id):
          self.issues_id = issues_id

  class WikiApp(morepath.App):
      def __init__(self, wiki_id):
          self.wiki_id = wiki_id

Note that ``IssuesApp`` and ``WikiApp`` expect arguments to be
initialized; we'll learn more about this later.

We now can group our paths into three. First we have the core app,
which includes the repository and its settings::

  @CoreApp.path(path='', model=Root)
  def get_root():
     ...

  @CoreApp.path(path='{user_name}', model=User)
  def get_user(user_name):
     ...

  @CoreApp.path(path='{user_name}/{repository_name}', model=Repository)
  def get_repository(user_name, repository_name):
     ...

  @CoreApp.path(path='{user_name}/{repository_name}/settings', model=Settings)
  def get_settings(user_name, repository_name):
     ...

Then we have the paths for our issue tracker::

  @IssuesApp.path(path='', model=Issues)
  def get_issues():
     ...

  @IssuesApp.path(path='{issue_id}', model=Issue)
  def get_issue(issue_id):
      ...

And the paths for our wiki::

  @WikiApp.path(path='', model=Wiki)
  def get_wiki():
     ...

We have drastically simplified the paths in ``IssuesApp`` and
``WikiApp``; we don't deal with ``user_name`` and ``repository_name``
anymore.

Mounting apps
-------------

Now that we have an independent ``IssuesApp`` and ``WikiApp``, we
want to be able to mount these under the right URLs under
``CoreApp``. We do this using the mount directive::

  def variables(app):
      repository = get_repository_for_wiki_id(app.wiki_id)
      return dict(
            repository_name=repository.name,
            user_name=repository.user.name)

  @CoreApp.mount(path='{user_name}/{repository_name}/issues',
                 app=IssuesApp, variables=variables)
  def mount_issues(user_name, repository_name):
      return IssuesApp(issues_id=get_issues_id(user_name, repository_name))

Let's look at what this does:

* ``@CoreApp.mount``: We mount something onto ``CoreApp``.

* ``path='{user_name}/{repository_name}/issues'``: We are mounting it
  on that path. All sub-paths in the issue tracker app will fall under
  it.

* ``app=IssuesApp``: We are mounting ``IssuesApp``.

* The ``mount_issues`` function takes the path variables ``user_name``
  and ``repository_name`` as arguments. It then returns an instance of
  the ``IssuesApp``. To create one we need to convert the
  ``user_name`` and ``repository_name`` into an issues id. We do this
  by looking it up in some kind of database.

* The ``variables`` function needs to do the inverse: given a
  ``WikiApp`` instance it needs to translate this back into a
  ``repository_name`` and ``user_name``. This allows Morepath to link
  to a mounted ``WikiApp``.

Mounting the wiki is very similar::

  def variables(app):
      return dict(user_name=get_username_for_wiki_id(app.id))

  @CoreApp.mount(path='{user_name}/{repository_name}/wiki',
                  app=WikiApp, variables=variables)
  def mount_wiki(user_name, repository_name):
      return WikiApp(get_wiki_id(user_name, repository_name))

No more path repetition
-----------------------

We have solved the repetition of paths issue now; the issue tracker
and wiki handle many paths, but there is no more need to repeat
'{user_name}/{repository_name}' everywhere.

Testing in isolation
--------------------

To test the issue tracker by itself, we can run it as a separate WSGI
app::

  def run_issue_tracker():
      mounted = IssuesApp(4)
      morepath.run(mounted)

Here we mount and run the ``issues_app`` with issue tracker id
``4``.

You can hook the ``run_issue_tracker`` function up to a script by
using an entry point in ``setup.py`` as we've seen in
:doc:`organizing_your_project`.

You can also mount applications this way in automated tests and then
use WebTest_ or some other WSGI testing library, as explained in
:doc:`testing`.

.. _WebTest: http://webtest.readthedocs.org/

Reusing an app
--------------

We can now reuse the issue tracker app in the sense that we can mount
it in different apps; all we need is a way to get ``issues_id``. What
then if we have another Python project and we wanted to reuse the
issue tracker in it as well? In that case it may start sense to start
maintaining the issue tracker it in a separate Python project of its
own.

We could for instance split our code into three separate Python
projects, for instance:

* ``myproject.core``

* ``myproject.issues``

* ``myproject.wiki``

Each would be organized as described in
:doc:`organizing_your_project`.

``myproject.core`` could have an ``install_requires`` in its
``setup.py`` that depends on ``myproject.issues`` and
``myproject.wiki``. To get ``IssuesApp`` and ``WikiApp`` in order to
mount them in the core, we would simply import them (for instance in
``myproject.core.app``)::

  from myproject.issues.app import IssuesApp
  from myproject.wiki.app import WikiApp

In some scenarios you may want to turn this around: the ``IssuesApp``
and ``WikiApp`` know they should be mounted in ``CoreApp``, but the
``CoreApp`` wants to remain innocent of this. In that case, you would
have ``myproject.issues`` and ``myproject.wiki`` both depend on
``myproject.core``, whereas ``myproject.core`` depends on nothing. The
wiki and issues projects then mount themselves into the core app.

Different teams
---------------

Now that we have separate projects for the core, issue tracker and
wiki, it becomes possible for a team to focus on the wiki without
having to worry about core or the issue tracker and vice versa.

This may in fact be of benefit even when you alone are working on all
three projects! When developing software it is important to free up
your brain so you only have to worry about one detail at the time:
this an important reason why we decomposition logic into functions and
classes. By decomposing the project into three independent ones, you
can temporarily forget about the core when you're working on the issue
tracker, allowing you to focus on the problems at hand.

Swapping in a new sub-app
-------------------------

Perhaps a different, better wiki implementation is developed. Let's
call it ``ShinyNewWikiApp``. Swapping in the new sub application is
easy: it's just a matter of changing the mount directive::

  @CoreApp.mount(path='{user_name}/{repository_name}/wiki',
                 app=ShinyNewWikiApp, variables=variables)
  def mount_wiki(user_name, repository_name):
      return ShinyNewWikiApp(get_wiki_id(user_name, repository_name))

Customizing an app
------------------

Let's change gears and talk about customization now.

Imagine a scenario where a particular customer wants *exactly* core
app. Really, it's perfect, exactly what they need, no change needed,
but then ... wait for it ... they actually do need a minor tweak.

Let's say they want an extra view on ``Repository`` that shows some
important customer-specific metadata. This metadata is retrieved from
a customer-specific extra database, so we cannot just add it to core
app. Besides, this new view isn't useful to other customers.

What we need to do is create a new customer specific core app in a
separate project that is exactly like the original core app by
extending it, but with the one extra view added. Let's call the
project ``important_customer.core``. ``important_customer.core`` has
an ``install_requires`` in its ``setup.py`` that depends on
``myproject.core`` and also the customer database (which we call
``customerdatabase`` in this example).

Now we can import ``CoreApp`` in ``important_customer.core``'s
``app.py`` module, and extend it::

  from myproject.core.app import CoreApp

  class CustomerApp(CoreApp):
      pass

At this point ``CustomerApp`` and ``CoreApp`` have identical
behavior. We can now make our customization and add a new JSON view to
``Repository``::

  from myproject.core.model import Repository
  # customer specific database
  from customerdatabase import query_metadata

  @CustomerApp.json(model=Repository, name='customer_metadata')
  def repository_customer_metadata(self, request):
      metadata = query_metadata(self.id) # use repository id to find it
      return {
        'special_marketing_info': medata.marketing_info,
        'internal_description': metadata.description
      }

You can now run ``CustomerApp`` and get the core app with exactly the one
tweak the customer wanted: a view with the extra metadata. The
``important_customer.core`` project depends on ``customerdatabase``,
but ``myproject.core`` remains unchanged.

We've made exactly the tweak necessary without having to modify our
original project. The original project continues to work the same way
it always did.

Swapping in, for one customer
-----------------------------

Morepath lets you extend *any* directive, not just the ``view``
directive. It also lets you *override* things in the applications you
extend. Let's say the important customer wants *exactly* the original
wiki, with just one tiny teeny little tweak. Other customers should
still continue to use the original wiki.

We'd tweak the wiki just as we would tweak the core app. We end up
with a ``TweakedWikiApp``::

  from myproject.wiki.app import WikiApp

  class TweakedWikiApp(WikiApp):
       pass

  # some kind of tweak
  @TweakedWikiApp.json(model=WikiPage, name='extra_info')
  def page_extra_info(self, request):
      ...

We want a new version of ``CoreApp`` just for this customer that
mounts ``TweakedWikiApp`` instead of ``WikiApp``::

  class ImportantCustomerApp(CoreApp):
      pass

  @ImportantCustomerApp.mount(path='{user_name}/{repository_name}/wiki',
                              app=TweakedWikiApp, variables=variables)
  def mount_wiki(user_name, repository_name):
      return TweakedWikiApp(get_wiki_id(user_name, repository_name))

The ``mount`` directive above overrides the one in the ``CoreApp``
that we're extending, because it uses the same ``path`` but mounts
``TweakedWikiApp`` instead.

Framework apps
--------------

A ``morepath.App`` subclass does not need to be a full working web
application. Instead it can be a framework with only those paths and
views that we intend to be reusable.

We could for instance have a base class ``Metadata`` and define some
views for it in the framework app. If we then have an application that
inherits from the framework app, any ``Metadata`` model we expose to
the web using the ``path`` directive automatically gets its views
supplied by the framework.

For instance::

  class Framework(morepath.App):
      pass

  class Metadata(object):
      def __init__(self, d):
          self.d = d # metadata dictionary

      def get_metadata(self):
          return self.d

  @Framework.json(model=Metadata, name='metadata')
  def metadata_view(self, request):
      return self.get_metadata()

We want to use this framework in our own application::

  class App(Framework):
      pass

Let's have a model that subclasses from ``Metadata``::

  class Document(Metadata):
      ...

Let's put the model on a path::

  @App.path(path='documents/{id}', model=Document)
  def get_document(id):
      ...

Since ``App`` extends ``Framework``, all documents published this way
have a ``metadata`` view automatically. Apps that don't extend
``Framework`` won't have this behavior, of course.

As we mentioned before, there is a gray area between application and
framework; applications tend to gain attributes of a framework, and
larger frameworks start to look more like applications. Don't worry
too much about which is which, but enjoy the creative possibilities!

Note that Morepath itself is designed as an application
(:class:`morepath.App`) that your apps extend. This means you can
override parts of it just like you would override a framework app! We
did our best to make Morepath do the right thing already, but if not,
you *can* customize it.
