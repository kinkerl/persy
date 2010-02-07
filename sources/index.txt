.. persy documentation master file, created by
   sphinx-quickstart on Sat Feb  6 12:32:16 2010.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to persy's documentation!
=================================
persy is an automated incremental backup tool for your personal files.
it is comparable to dropbox and ubuntuone but with one major difference: 
you dont need a fancy user account in some cloud in the internet. persy manages the synchronization in a personal way: 
all you need is a server with ssh and git (in your local network or remote in the internet doesnt matter). 
i have a old pc here in my local network for example. 

persy is designed to run by its own on a computer as a revision based
backup application or in an environment with multiple computers and at least
one server to keep files and folder in sync between them.

persy tracks changes of local files (you can choose which ones) an stores the changes in a local git repository. 
if you want to enable a remote backup or even a syncronization, persy can syncronize and merge the changes with the server over a secure ssh connection. 


Contents:

.. toctree::
   :maxdepth: 2
   
   persy_gtk
   persy_core
   changelog

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
