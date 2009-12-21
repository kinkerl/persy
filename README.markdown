Copyright (C) 2009 Dennis Schwertel <s@digitalkultur.net>

persy -- sync tool based on Git
=================================
persy is an automated incremental backup tool for your personal files.
it is comparable to dropbox and ubuntuone but with one major difference: 
you dont need a fancy user account in some cloud in the internet. persy manages the sync in a local way: 
all you need is a ssh server (local or remote doesnt matter). i have a old pc here in my local network for example. 

persy is designed to run by its own on a computer as a revision based
backup application or in an environment with multiple computers and at least
one server to keep files and folder in sync between them.

persy tracks changes of local files (you can choose which ones) an stores the changes in a local git repository. 
if you want to enable a remote backup or even a sync, persy can sync and merge the changes with the server over a secure ssh connection. 


You can report BUGS, ask QUESTIONS and DOWNLOAD persy on https://launchpad.net/persy
You can view the SOURCE and the WIKI on http://wiki.github.com/kinkerl/persy

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
After the installaton you will have to do some configuraton depending on your environment, needs and whishes.

Usage
============
How to configure persy and use it

Setup for a local usage
------------
The normal local configuration is:

     $ persy --config --uname=USERNAME      # username used for the commits
     $ persy --config --mail=MAIL           # useremail used for the commits
     $ persy --init                         # run once to initialize the backup system
     $ persy --config --add_dir=DIR         # DIR is the absolute path to a directory 
                                            # in /home/user (example: /home/username/documents).
                                            # The directory is then integrated in persy
     #from now on, you can start persy or/and add it to your autostart:
     $ persy                                # starts persy


Setup for syncing and/or using a remote backup
------------
If you want to sync or backup your files on a remote server, you have to __enable a public key authentication__ 
for the server!!! No extra software on the server is required. The server just needs a ssh server with public 
key authentication and the git-core package.

The normal workflow with a __blank remote Server__ and an __already initialized local repository is__:

     $ persy --config --hostname=SERVER     # SERVER = location of the server
     $ persy --config --path=PATH           # PATH = absolute path of the gitrepository on 
                                            # the server (path will be created if it does not exist)
     $ persy --initRemote                   # created a bare git repository on the server in PATH
     $ persy                                # starts persy 


The normal workflow with a __already initialized remote Server__ and __no local repository__. 
IMPORTANT: the synced directories should be empty before the sync. i had some problems 
with already existing files. you can start a sync and then add new files to the synced directory.

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
     $ persy                                # starts persy

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
