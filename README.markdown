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

If you are not looking at the online version of the documentation, you can find the most recent version at: http://kinkerl.github.com/persy/

Dependencies
============
persy needs the following software at run-time:

 *    git-core
 *    python-pyinotify - to get efficient information about filesystem changes
 *    python-paramiko - ssh library to initialize a remote server
 *    gitk or qgit as a graphical git browser


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
