Dépannage
===============================

Si vous observer quelque chose de bizarre, ou simplement qui ne fonctionne pas, prenez s'il vous plaît le temps de rapporter un bug sur launchpad_ pour permettre d'améliorer Persy !

Plus d'informations et aide rapide
-----------------------------------

Si vous souhaitez disposer d'informations détaillées sur ce que fait Persy, lancez le en ligne de commande avec l'option ``--verbose``.
Cela peut vous permettre des informations intéressance sur ce qui arrive.

.. code-block:: bash
  :linenos:

   persy --verbose

Quand quelque chose ne fonctionne pas avec la synchronisation, vous pouvez tester vos paramètres et votre environnement avec 4 tests rapides disponible sur l'onglet synchronisation du menu de configuration.
Un chien vert indique que tout va bien, un chien orange indique un problème. Si une erreur est survenue, le message d'erreur est affiché en tant que notification.
L'action qui correspond à un test PEUT résoudre le problème. Comme rien de grave ne peut se produire, vous pouvez toujours essayer.


Dépannage avancée et manuel
------------------------------------

Pour vérifier vraiment ce qui se passe OU gérer manuellement certaine affires avec le dépôt git, vous pouvez utiliser l'option du mode développement/débogage ``--setenv`` (réservé uniquement aux utilisateurs avancés, notez le point au début de la ligne de commande).

.. code-block:: bash
  :linenos:

   . persy --setenv

Ceci définit les variables d'environnement (``GIT_DIR``, ``GIT_WORK_TREE``) du shell parent de façon à ce que toutes les commandes git exécutées dans le shell parent concernent le dépôt git de Persy. 
Lisez les messages d'aide lorsque vous utilisez cette option. 
Ceci est utile si vous voulez utiliser votre propre visionneuse git ou manipuler vos données.

.. _launchpad: https://launchpad.net/persy

Travailler avec de grands dépôts 
------------------------------------

Persy peut gérer correctement de grands dépôts. Le seul problème est la synchronisation initiale à partir ou depuis un dépôt distant. Selon la taille de vos fichiers, cela peut prendre très longtemps. Il pourrait être plus efficace d'utiliser un autre moyen pour initialiser la synchronisation à partir, ou vers un dépôt distant. Le fonctionnement devrait être plus stable de cette façon. Merci de lire le paragraphe "Initialiser manuellement depuis un dépôt distant" si vous envisagez de faire cela.

Initialiser manuellement depuis un dépôt distant
--------------------------------------------------

Pour obtenir localement une extraction à partir d'un dépôt distant, vous devez lancer un terminal et passer dans l'environnement de Persy. Après avoir fait cela, vous pouvez récupérer votre copie locale par un git pull :

.. code-block:: bash
  :linenos:

   . persy --setenv
   git pull origin master

Cela peut prendre longtemps selon la taille de votre dépôt et peut être utile lorsqu'il est trop gros pour être descendu avec Persy; ou si vous ne disposez pas d'une interface graphique.

