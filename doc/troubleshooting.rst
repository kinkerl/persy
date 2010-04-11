Troubleshooting
===============================

When something is odd or just not working, please take your time to write a bug at launchpad_ to make persy better!

more informations and quick help
-----------------------------------

If you just want a more detailed output of the stuff persy does, start persy with the ``--verbose`` command line argument.
This can give valueable information about whats happening.

.. code-block:: bash
  :linenos:

   persy --verbose

When something with the synchronization is not working, you can test your settings and environment with 4 quick tests on the synchronization tab on the settings menu. 
A green dog is ok, orange is an error state. If an error does occure, the error message is displayed as a notification. 
The corresponding action to a test MAY fix a problem. Nothing bad will happen so you can always give it a try.


advanced and manual troubleshooting
------------------------------------

To really check whats happening OR do some manual stuff with the git repository, use the a development/debugging Option ``--setenv`` (only for advanced users, notice the dot in the beginning). 

.. code-block:: bash
  :linenos:

   . persy --setenv

This sets the environment variables (``GIT_DIR``, ``GIT_WORK_TREE``) of the parent shell in a way that all git commands execute in the parent shell are operating on the persy git repository. 
Take a look at the help message when using this option.
This is useful if you want to start your own git viewer or want to mess with your data. 


.. _launchpad: https://launchpad.net/persy
