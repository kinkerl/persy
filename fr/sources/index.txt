.. persy documentation master file, created by
   sphinx-quickstart on Sat Feb  6 12:32:16 2010.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Bienvenue sur la documentation de Persy ! 
=========================================
Persy est un outil de sauvegarde incrémentale automatique pour vos fichiers et dossiers personnels. 
Il a également la possibilité de synchroniser vos dossiers sur plusieurs machines. 
Ainsi, il est comparable à dropbox_ ou à ubuntuone_, mais avec une différence majeure :
vous n'avez pas besoin d'ouvrir un compte utilisateur dans un Cloud sur Internet où vous ne saurez pas vraiment où vos données sont stockées et qui peut y avoir accès.

Avec Persy, vous pouvez contrôler le processus à chaque étape et dans chaque machine, mais Persy essaiera de vous éviter autant que possible les détails ennuyeux.
Si vous voulez juste faire une sauvegarde de vos fichiers et conserver quasiment toutes les étapes de votre travail, lancer Persy et indiquez lui les dossiers à préserver dans "à sauvegarder", sur l'onglet Paramètres. 
Si vous voulez sychroniser vos fichiers, vous n'avez besoin que d'un serveur avec ssh et git (dans votre réseau local ou à distance sur Internet, c'est sans importance). 
J'ai un vieux PC ici dans mon réseau local par exemple.
Indiquez à Persy les informations relatives au serveur dont il a besoin, procédez à la configuration, activez la synchronisation à distance et vous pouvez y allez !

Si vous ne consultez pas la version en ligne de la documentation, vous pouvez en trouver la version la plus récente à l'adresse: http://persy.digitalkultur.net

.. note::

   Persy est considéré comme fonctionnellement complet. Je vais corriger les bugs, mais pas ajouter de nouvelles fonctionnalités. Si vous pensez que quelque chose est manquant ou si vous voulez contribuer à Persy, il suffit de m'écrire un message.
   
.. warning::

   Si quelque chose se passe mal, vous pourriez avoir besoin un peu d'expérience avec git. Si vous êtes à l'aise dans la résolution d'un conflit dans git, allez-y et amusez-vous avec Persy ! 

Obtenez Persy
-----------------
Si vous souhaitez obtenir la dernière version de Persy, Consultez la section :ref:`installation`. Vous y trouverez les liens vers les PPA pour Ubuntu, le paquet des sources et peut-être plus !


Contenu
------------------

.. toctree::
   :maxdepth: 2
   
   installation

Indices and tables
------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`


.. _dropbox: https://www.dropbox.com
.. _ubuntuone: https://one.ubuntu.com/
