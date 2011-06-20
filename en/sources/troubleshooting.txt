Troubleshooting
===============================

When something is odd or just not working, please take your time to write a bug at launchpad_ to make persy better!

More informations and quick help
-----------------------------------

If you just want a more detailed output of the stuff persy does, start persy with the ``--verbose`` command line argument.
This can give valueable information about whats happening.

.. code-block:: bash
  :linenos:

   persy --verbose

When something with the synchronization is not working, you can test your settings and environment with 4 quick tests on the synchronization tab on the settings menu. 
A green dog is ok, orange is an error state. If an error does occure, the error message is displayed as a notification. 
The corresponding action to a test MAY fix a problem. Nothing bad will happen so you can always give it a try.


Advanced and manual troubleshooting
------------------------------------

To really check whats happening OR do some manual stuff with the git repository, use the a development/debugging Option ``--setenv`` (only for advanced users, notice the dot in the beginning). 

.. code-block:: bash
  :linenos:

   . persy --setenv

This sets the environment variables (``GIT_DIR``, ``GIT_WORK_TREE``) of the parent shell in a way that all git commands execute in the parent shell are operating on the persy git repository. 
Take a look at the help message when using this option.
This is useful if you want to start your own git viewer or want to mess with your data. 


.. _launchpad: https://launchpad.net/persy

Working with large repositories
------------------------------------

Persy can handle large repositorys quite well. The only problem is the initial pull from or push to a remote repository. This may take a very long time, depending on the size of your files. It might help to use a manual pull from a remote location. It is expected to be more stable this way. Please take a look at the "Manual pull from a remote repository" paragraph if you want to perform this. 

Manual pull from a remote repository
-------------------------------------

To get a local checkout / backup from a remote repository you have start a terminal and switch into a "persy" environment. After you did this, you can make the git pull:

.. code-block:: bash
  :linenos:

   . persy --setenv
   git pull origin master

This may take a long time depending on the size of your repostiory and can be usefull when the repository is to big to pull with persy or you dont have a graphical interface. 

