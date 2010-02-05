% persy help

Name
============
persy - syncronization based on Git

Description
============
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

Since persy builds upon the infrastructure offered by Git, it shares its main
strengths:

 *    speed: recovering your data is faster that cp -a...
 *    full revision history
 *    space-efficient data store, with file compression and textual/binary deltas
 *    efficient transport protocol to replicate the backup (faster than rsync)

Dependencies
============
persy needs the following software at run-time:

 *    git-core
 *    python-pyinotify - to get efficient information about filesystem changes
 *    python-paramiko - ssh library to initialize a remote server
 *    gitk or qgit as a graphical git browser

Installation
============
If you can, install the deb package. It will take care of "all" problems. 
After the installaton you will have to do some configuraton depending on your environment, needs and whishes

Usage
============
How to configure persy and use it

Setup for a local usage (settings menu)
------------
For a quick start, just run persy

     $ persy                               
Now you have to add directories to persy. You can do this in the settings menu into the "backup" tab (take a look at the screenshot).

![see illustration](http://cloud.github.com/downloads/kinkerl/persy/persy_settings_quickstart.png)

The watched directories and files can be in absolute format (starts with / ) or relative to the userhome. 

After you added the directories (and maybe lookt at the other configuration options too) you might want to actually start persy.
just rightclick on the status icon and check the "start/stop persy" checkbox.


![see illustration](http://cloud.github.com/downloads/kinkerl/persy/start_persy.png)


Setup for a local usage (command line)
------------
You can also do this configuration in the commandline. This is recommended for experienced users only and is not necessary if you configured persy with the settings menu.

     $ persy --config --uname=USERNAME      # username used
     $ persy --config --mail=MAIL           # useremail used
     $ persy --config --add_dir=DIR         # DIR is the path to a directory in /home/user 
                                            # (example: /home/username/documents).
                                            # The directory is then integrated in persy.
                                            # From now on, you can start persy or/and 
                                            # add it to your autostart:
     $ persy --start                        # starts persy
You can configure your desktop environment to execute persy at login.

Setup for syncing and/or using a remote backup
------------
If you want to sync or backup your files on a remote server, you have to __enable a public key authentication__ for the server ([more information](http://sial.org/howto/openssh/publickey-auth/)). No extra persy serversoftware is required as you can see in this illustration:

![see illustration](http://cloud.github.com/downloads/kinkerl/persy/sync.png)

The server just needs a ssh server with public key authentication and the git-core package.

You only have to configure the client computer with persy installed!
The normal workflow with a __blank remote Server__ and an __already initialized local repository is__:

     $ persy --config --hostname=SERVER     # SERVER = location of the server
     $ persy --config --path=PATH           # PATH = absolute path of the gitrepository on 
                                            # the server (path will be created if it does not exist)
     $ persy --initRemote                   # created a bare git repository on the server in PATH
     $ persy --start                        # starts persy 

The normal workflow with a __already initialized remote Server__ and __no local repository__. 

IMPORTANT: the synced directories should be empty before the sync. i had some problems with already existing files. you can start a sync and then add new files to the synced directory.

     $ persy --config --uname=USERNAME      # username used for the commits
     $ persy --config --mail=MAIL           # useremail used for the commits
     $ persy --config --hostname=SERVER     # SERVER = identifier(ip) of the server
     $ persy --config --path=PATH           # PATH = absolute path of the gitrepository on the 
                                            # server
     $ persy --config --add_dir=DIR         # add the same DIR to persy as on the other machines
     $ persy --syncwithremote               # connects to the remote server and 
                                            # pulls the files from the git repository
                                            # depending on the size of your existing repository
                                            # this can take a long(!) time
     $ persy --start                        # starts persy

Advanced Usage
==========
You can use persy without a centralized server to which every clients connects and performes the synchronization (like in the illustration image above).
You can also run persy without a second computer at all and synchronize with other parts(repositories) on the filesystem.
Right now, this is not the intended use and i  will not cover this in the cli or the upcomming gui. 
You can however configure this in the git configuration for persy ~/.persy/git/config and i try to take care of the internal implementation.
If you have questions regarding esoteric setups, feel free to mail me.

Commandline Options
-----------
please look at the help generated by persy (the command is: persy --help) for more information about options

A development Option is --setenv.
This sets the environment variables (GIT_DIR, GIT_WORK_TREE) of the parent shell in a way that all git commands execute in the parent shell are operating on the persy git repository.
Take a look at the help message when using this option.


See also
===========
You can report BUGS, ask QUESTIONS and DOWNLOAD persy on [launchpad](https://launchpad.net/persy)
You can view the SOURCE and DEVELOPMENT on [github](http://wiki.github.com/kinkerl/persy)

Author
============
Copyright (C) 2009, 2010 Dennis Schwertel <s@digitalkultur.net>

License
============
persy is free software: you can redistribute it and/or modify it
under the terms of the GNU General Public License as published by the Free
Software Foundation, either version 2 of the License, or (at your option) any
later version.

persy is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
General Public License for more details.

You should have received a copy of the GNU General Public License
along with persy; if not, write to the Free Software
Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
