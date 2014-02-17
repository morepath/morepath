Building Large Applications
===========================

Introduction
------------

A small web application is relatively easy to understand. It will do
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
example: different organization will each have their own
installation. Or imagine a company with an application that it sells
to its customers: each customer can have its own special deployment.

Different deployments of an application have real differences as every
organization has different requirements. This means that you need to
be able to customize and extend the application to fit the purposes of
each particular deployment. As a result the application will have to
take on framework-like properties. Morepath recognizes that there is a
large gray area between application and framework, and offers support
to build framework-like applications and application-like frameworks.

The document doc:`app_reuse` describes some basic facilities for
application reuse. The document :doc:`organizing_your_project`
describes how a single application project can be organized. This
document sketches out a concrete example of larger application that
consists of multiple sub-projects and sub-apps.

A Code Hosting Site
-------------------

As an example of a large application composed of multiple parts we
will describe how we could build a code hosting site with Morepath
along the lines of Github or Bitbucket. We focus on the paths, not
views.

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

  app = morepath.App()

  @app.path(path='', model=Root)
  def get_root():
     ...

  @app.path(path='{user_name}', model=User)
  def get_user(user_name):
     ...

  @app.path(path='{user_name}/{repository_name}', model=Repository)
  def get_repository(user_name, repository_name):
     ...

We could try to implement settings, issues and wiki as views on
repository, but these are complicated pieces of functionality that
benefit from having sub-URLs (i.e. ``issues/12`` or
``...wiki/mypage``), so we'll model them using paths as well::

  @app.path(path='{user_name}/{repository_name}/settings', model=Settings)
  def get_settings(user_name, repository_name):
     ...

  @app.path(path='{user_name}/{repository_name}/issues', model=Issues)
  def get_issues(user_name, repository_name):
     ...

  @app.path(path='{user_name}/{repository_name}/wiki', model=Wiki)
  def get_wiki(user_name, repository_name):
     ...

Let's also make path to an individual issue,
i.e. ``example.com/faassen/myproject/issues/12``::

  from .model import Issue

  @app.path(path='{user_name}/{repository_name}/issues/{issue_id}', model=Issue)
  def get_issue(user, repository, issue_id):
      ...

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
  tracker or a wiki under the same paths, without having to change a lot
  of code.

We're going to show now how Morepath can solve these problems by
partitioning a larger app into smaller ones, and mounting them. This
is more involved than simply declaring all paths under a single core
app. If you feel more comfortable doing that, by all means do so; you
don't have these problems. But if your application is successful and
grows larger it's likely you will start feeling some of these
problems. Morepath is there to help. We'll now show what changes
you'd make.

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

  core_app = morepath.App()

  issues_app = morepath.App(variables=['issues_id'])

  wiki_app = morepath.App(variables=['wiki_id'])

We will see what the ``variables`` argument is about soon.

We now can group our paths into three. First we have the core app,
which includes the repository and its settings::

  @core_app.path(path='', model=Root)
  def get_root():
     ...

  @core_app.path(path='{user_name}', model=User)
  def get_user(user_name):
     ...

  @core_app.path(path='{user_name}/{repository_name}', model=Repository)
  def get_repository(user_name, repository_name):
     ...

  @core_app.path(path='{user_name}/{repository_name}/settings', model=Settings)
  def get_settings(user_name, repository_name):
     ...

Then we have the paths for our issue tracker::

  @issues_app.path(path='', model=Issues)
  def get_issues(issues_id):
     ...

  @issues_app.path(path='{issue_id}', model=Issue)
  def get_issue(issues_id, issue_id):
      ...

And the paths for our wiki::

  @wiki_app.path(path='', model=Wiki)
  def get_wiki(wiki_id):
     ...

We have drastically simplified the paths in ``issues_app`` and
``wiki_app``; we don't deal with ``user_name`` and ``repository_name``
anymore. Instead we get a ``issues_id`` and ``wiki_id``, but not from
the path. Where does they come from? They are specified by the
``variables`` argument for :class:`morepath.App` that we saw
earlier. We now need to explore the :meth:`AppBase.mount` directive to
see how they are actually obtained.

Mounting apps
------------

Now that we have an independent ``issues_app`` and ``wiki_app``, we want
to be able to mount these under the right URLs under ``core_app``. We
do this using the mount directive::

  @core_app.mount('{user_name}/{repository_name}/issues',
                  app=issues_app)
  def mount_issues(user_name, repository_name):
      return { 'issues_id': get_issues_id(user_name, repository_name) }

Let's look at what this does:

* ``@core_app.mount``: We mount something onto ``core_app``.

* ``app=issues_app``: We are mounting ``issues_app``.

* ``path='{user_name}/{repository_name}/issues'``: We are mounting it
  on that path. All sub-paths in the issues app will be here.

* The ``mount_issues`` function takes the path variables ``user_name``
  and ``repository_name`` as arguments. It then returns a dictionary
  with the mount variables expected by ``issues_app``, in this case
  ``issues_id``. It does this by using ``get_issues_id``, which does
  some kind of database access in order to determine ``issues_id`` for
  ``user_name`` and ``repository_name``.

Mounting the wiki is very similar::

  @core_app.mount('{user_name}/{repository_name}/wiki',
                  app=wiki_app)
  def mount_wiki(user_name, repository_name):
      return { 'wiki_id': get_wiki_id(user_name, repository_name) }

No more path repetition
-----------------------

But we have solved the repetition of paths issue now; the issue
tracker and wiki can consist of many paths, but there is no more need
to repeat '{user_name}/{repository_name}' everywhere.

Testing in isolation
--------------------

To test the issue tracker by itself, we can run it as a separate WSGI app.
To do this we first need to mount it using an ``issues_id``::

  def run_issue_tracker():
      mounted = issues_app.mount(issues_id='foo')
      mounted.run()

Here we mount and run the ``issues_app`` with issue tracker id
``foo``.

XXX implement ``run`` on ``mounted``.

XXX what about a converter for ``issues_id`` to make it an int?

Reusing an app
--------------

We can now reuse the issue tracker app in the sense that we can mount
it in different apps too now; all we need is a way to get
``issues_id``. But what if we want to mount the issue tracker app in a
separate project altogether? To use it now we'd need to import it from
a project that also contains the core app and the wiki app, meaning
that the new project would need to depend on all of this.

To make it truly reusable across projects we should maintain the code
for the issue tracker app in a separate project, and the same for the
wiki app. The core app can then depend on the issue tracker and wiki
projects. Another app that also wants to have an issue tracker can
also depend on the issue tracker app.

To do this we'd split our code into three separate Python projects,
for instance:

* ``myproject.core``

* ``myproject.issues``

* ``myproject.wiki``

Each would be organized as described in
:doc:`organizing_your_code`.

``myproject.core`` would have an ``install_requires`` that depends on
``myproject.issues`` and ``myproject.wiki``. To get ``issues_app`` and
``wiki_app`` in order to mount them in the core, we would simply
import them (for instance in ``myproject.core.main``)::

  from myproject.issues.main import issues_app
  from myproject.wiki.main import wiki_app

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
tracker, letting you free up your brain.

Swapping in a new sub-app
-------------------------

Perhaps a different, better wiki implementation is developed. Let's
call it ``shiny_new_wiki_app``. Swapping in the new sub application
is easy: it's just a matter of changing the mount directive::

  @core_app.mount('{user_name}/{repository_name}/wiki',
                  app=shiny_new_wiki_app)
  def mount_wiki(user_name, repository_name):
      return { 'wiki_id': get_wiki_id(user_name, repository_name) }

Customizing an app
------------------

What if a particular customer wanted *exactly* core app, really, it's
perfect, but then ... wait for it ... they actually need a minor
change. Let's say they want an extra view on ``Repository`` that shows
some important customer-specific metadata. This metadata is retrieved
from a customer-specific extra database. This means we cannot just
modify the core app and add the view there; besides, this new view
isn't useful to any other customers.

XXX example code

Framework apps
--------------




Note that Morepath itself is actually a framework app that your apps
extend automatically. This means you can override parts of it (say,
how links are generated) just like you would override a framework app!
We did our best to make Morepath do the right thing already, but if
not, you *can* customize it.

Organize for Customization
--------------------------



By splitting up the application into separate ones, we've also
organized our code to support various customizations better, like
swapping in a whole new sub-application.



 and we
want to upgrade one customer (but only that customer) to use this
better implementation. To do so we can extend ``core_app`` for this
particular customer only::

  

What if a particular client insists on using a different wiki
