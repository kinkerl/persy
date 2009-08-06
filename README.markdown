Copyright (C) 2009 Dennis Schwertel <s@digitalkultur.net>

persy -- sync tool based on Git
=================================
Since persy builds upon the infrastructure offered by Git, it shares its main
strengths:
* speed: recovering your data is faster that cp -a...
* full revision history
* space-efficient data store, with file compression and textual/binary deltas
* efficient transport protocol to replicate the backup (faster than rsync)

Dependencies
------------
persy needs the following software at run-time:

 *    git-core
 *    python-pyinotify - to get efficient information about filesystem changes
 *    python-paramiko - ssh library to initialize a remote server

Installation
------------
persy can be used just to backup your data or sync your data with multiple 
machines. persy is designed to run by its own on a computer as a revision based
backup application or in an environment with multiple computers and at least 
one server to keep files and folder in sync between them. 


Usage
------------
The normal local workflow is:

     $ persy --config --uname=USERNAME      # username used for the commits
     $ persy --config --mail=MAIL           # useremail used for the commits
     $ persy --init                         # run once to initialize the backup system
     $ persy --config --add_dir=DIR         # DIR is the absolute path to a directory 
                                            # in /home/user (example: /home/username/documents).
                                            # The directory is then integrated in persy
     $ persy                                # starts persy


The normal workflow with a remote Server and an already initialized local repository is:

     $ persy --config --hostname=SERVER     # SERVER = location of the server
     $ persy --config --path=PATH           # PATH = absolute path of the gitrepository on 
                                            # the server (path will be created if it does not exist)
     $ persy --initRemote                   # created a bare git repository on the server in PATH
     $ persy                                # starts persy 


The normal workflow with a already initialized remote Server and no local repository. 
IMPORTANT: the synced directories should be empty before the sync. i had some problems 
with already existing files. you can start a sync and then add new files to the synced directory.

     $ persy --config --uname=USERNAME      # username used for the commits
     $ persy --config --email=MAIL          # useremail used for the commits
     $ persy --config --hostname=SERVER     # SERVER = identifier(ip) of the server
     $ persy --config --path=PATH           # PATH = absolute path of the gitrepository on the 
                                            # server
     $ persy --config --add_dir=DIR         # add the same DIR to persy as on the other machines
     $ persy --syncwithremote               # connects to the remote server and 
                                            # pulls the files from the git repository
     $ persy                                # starts persy

License
------------
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
