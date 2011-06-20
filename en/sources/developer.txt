Developer Documentation
=================================
This is an overview what you might want to know if you want to hack and contribute to persy.

Contributing
---------------------------------
If you want to contribute in anyway, please go to github_ or launchpad_.


persy-dev Package
________________________________

If you want to Test your code or release it, you might want to take a look at the persy-dev package.
It can be found at github (http://github.com/kinkerl/persy-dev) and stores all the files which are not a direct part of the persy application (this includes artwork).


Dependencies
--------------------------------

At runtime you need the following packages (these names are taken from ubuntu and might differ on other distributions):

 *   git-core - git!
 *   gitk or qgit - graphical git browser
 *   xterm - used for log
 *   librsvg2-common - important for svg graphics
 *   python-gtk2 - the gui framework
 *   python-glade2 - creates the gui
 *   python-notify - notifications
 *   python-pyinotify - to get efficient information about filesystem changes
 *   python-paramiko - ssh library to initialize a remote server
 *   python-configobj - configlib

For some actions in the Makefile you also need:

 *   python-sphinx - build the documentation
 *   pandoc - build the manpage

.. _github: http://github.com/kinkerl/persy
.. _launchpad: https://launchpad.net/persy


Writing Documentation
--------------------------

The documentation is split into several independent packages depending on the language it is written in(persy-doc-fr, persy-doc-en). It consists of some files written in REST_-Markup and is rendered to an HTML version with Sphinx_. 



Building a new HTML Documentation
__________________________________

.. note::
   Sphinx must be installed for this action. On Ubuntu, it is part of the python-sphinx package.

First, you have to change in the project root of the documentation This is should be the parent directory of "/doc".  You can run 

.. code-block:: bash
  :linenos:

   make

This will render the documentation found in /doc and place the result in /build. You can use your favorite browser to view the result. 



.. _Sphinx: http://sphinx.pocoo.org/
.. _REST: http://en.wikipedia.org/wiki/ReStructuredText


Create a release of persy
--------------------------

This is straigt forward. Go in the project root folder and run the following command:

.. code-block:: bash
  :linenos:

   VERSION="x.x.x" make tarorig

This will create a release-quality version of persy in /build/persy_x.x.x/ and an additional tarball in /build used for distribution and further packaging.
