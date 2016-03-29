History of Morepath
===================

For more recent changes, see :doc:`changes`.

Morepath was written by Martijn Faassen (me writing this document).

The genesis of Morepath is complex and involves a number of projects.

Web Framework Inspirations
--------------------------

Morepath was inspired by Zope, in particular its component
architecture; a reimagined version of this is available in Reg, a core
dependency of Morepath.

An additional inspiration was the Grok web framework I helped create,
which was based on Zope 3 technologies, and Pyramid, a reimagined
version of Zope 3, created by Chris McDonough.

Pyramid in particular has been the source of a lot of ideas, including
bits of implementation.

Once the core of Morepath had been created I found there had been
quite a bit of parallel evolution with Flask. Flask served as a later
inspiration in its capabilities and documentation. Morepath also used
Werkzeug (basis for Flask) for a while to implement its request and
response objects, but eventually I found WebOb the better fit for
Morepath and switched to that.

Configuration system
--------------------

In 2006 I co-founded the Grok web framework. The fundamental
configuration mechanism this project uses was distilled into the
Martian library:

https://pypi.python.org/pypi/martian

Martian was reformulated by Chris McDonough (founder of the Pyramid
project) into Venusian, a simpler, decorator based approach:

https://pypi.python.org/pypi/venusian

Morepath originally used Venusian as a foundation to its configuration
system. I like the way Venusian separates decorators from their
execution, but Venusian also makes setup more difficult to reason
about for users than simply registering the decorator with the configuration
system during import-time.

Morepath's configuration system had grown over time and had grown a
few hacks here and there. Removing Venusian was not simple as a
result, plus I had a long-standing issue where I wanted to document
the configuration system properly.

So in 2016 I extracted Morepath's configuration system into its own
reusable project, called `dectate`_. I also extensively refactored it
and removed the Venusian dependency. Morepath now uses Dectate as a
clean and well-documented configuration system.

.. _dectate: http://dectate.readthedocs.org

Routing system
--------------

In 2009 I wrote a library called Traject:

https://pypi.python.org/pypi/traject

I was familiar with Zope traversal. Zope traversal matches a URL with
an object by parsing the URL and going through an object graph step by
step to find the matching object. This works well for objects stored
in an object database, as they're already in such a graph. I tried to
make this work properly with a relational database exposed through an
ORM, but noticed that I had to adjust the object mapping too much just
to please the traversal system.

This led me to a routing system, so expose the relational database
objects to a URL. But I didn't want to give up some nice properties of
traversal, in particular that for any object that you can traverse to
you can also generate a URL. I also wanted to maintain a separation
between models and views. This led to the creation of Traject.

I used Traject successfully in a number of projects (based on Grok). I
also ported Traject to JavaScript as part of the Obviel client-side
framework. While Traject is fairly web-framework independent, to my
knowledge Traject hasn't found much adoption elsewhere.

Morepath contains a further evolution of the Traject concept (though
not the Traject library directly).

Reg
---

In early 2010 I started the iface project with Thomas Lotze. In 2012 I
started the Crom project. Finally I combined them into the Comparch
project in 2013. I then renamed Comparch to Reg, and finally
`converted Reg to a generic function implementation`_.

.. _`converted Reg to a generic function implementation`: http://blog.startifact.com/posts/reg-now-with-more-generic.html

See `Reg's history section`_ for more information on its history. The
Reg project provides the fundamental registries that Morepath builds
on.

.. _`Reg's history section`: http://reg.readthedocs.org/en/latest/history.html

Publisher
---------

In 2010 I wrote a system called Dawnlight:

https://bitbucket.org/faassen/dawnlight

It was the core of an object publishing system with a system to find a
model and a view for that model, based on a path. It used some
concepts I'd learned while implementing Traject (a URL path can be
seen as a stack that's being consumed), and it was intended to be easy
to plug in Traject. I didn't use Dawnlight myself, but it was adopted
by the developers of the Cromlech web framework (Souheil Chelfouh and
Alex Garel):

http://pypi.dolmen-project.org/pypi/cromlech.dawnlight

Morepath contains a reformulation of the Dawnlight system,
particularly in its publisher module.

Combining it all
----------------

In 2013 I started to work with CONTACT Software. They encouraged me to
rethink these various topics. This led me to combine these lines of
development into Morepath: Reg registries, decorator-based
configuration using Venusian, and traject-style publication of models
and resources.

Spinning a Web Framework
------------------------

In the fall of 2013 I gave a keynote speech at PyCon DE about the creative
processes behind Morepath, called "Spinning a Web Framework":

.. raw:: html

  <iframe id="ytplayer" type="text/html" width="640" height="390"
    src="http://www.youtube.com/embed/9A5T9C2OBB4?autoplay=0&origin=http://morepath.readthedocs.org"
    frameborder="0"></iframe>
