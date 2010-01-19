% persy development help

Publishing the Package
============
How to publish a new package in small and easy steps:

Build the documentation
-------------------------
execute the MakeDoc script in the source 

Build the source Package
-------------------------
     debuild -S -sa -k$GPGKEY -i.git -I.git
$GPGKEY must be set


Push to Launchpad
-------------------------
     dput -f  ppa:tmassassin/ppa persy_<VERSION>_source.changes 

