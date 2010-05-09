.. persy documentation master file, created by
   sphinx-quickstart on Sat Feb  6 12:32:16 2010.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to persy's documentation!
=================================
persy is an automated incremental backup tool for your personal files and folders.
It also has the ability to synchronize your folders over multiple machines.
So, it is comparable to dropbox_ and ubuntuone_ but with one major difference: 
you dont need a user account in a cloud in the internet where you dont really know where your stuff is and who may have access to it. 

With persy, you control every step and station in the process but persy tries to keep most of the annoying things out of the way.
If you just want to backup your files and save nearly every step you do, run persy and add your folders to persy in the "backup" settings tab. 
If you want to sychronize your files, all you need is a server with ssh and git (in your local network or remote in the internet doesnt matter). 
I have a old pc here in my local network for example. Give persy the server data it needs, follow the configuration, enable remote synchronization and there you go!

If you are not looking at the online version of the documentation, you can find the most recent version at: http://persy.digitalkultur.net

Get persy
-----------------

If you want to get the latest version of persy, take a look at the :ref:`installation`-section!
There you will find links to the ppa for Ubunu, the source package and maybe more!


Contents
------------------

.. toctree::
   :maxdepth: 2
   
   installation
   usage
   troubleshooting
   developer
   trivia
   changes

Indices and tables
------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`


.. _dropbox: https://www.dropbox.com
.. _ubuntuone: https://one.ubuntu.com/
