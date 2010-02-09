#!/bin/bash

# build it
echo -e "Running configure and make"
./configure && make

gpgkey="AF005C40"
version="`cat usr/lib/persy/VERSION`"

echo -e ""
echo -n "Continue releasing persy-${version} ? (y/n): "
read answer
if [ "$answer" != "y" ]; then
    echo "Exit."
    exit 0
fi

# debian .tar.gz
echo -e "Building debian source package..."
debuild -S -sa -k${gpgkey} -i.git -I.git
echo -e "Build finished; Get the debian package at ../persy_${version}.tar.gz"

# publish doc
echo -e "Begin publishing documentation..."
#preparing temp
rm -fr /tmp/_build/html
mkdir -p /tmp/_build/html
mv usr/share/doc/persy/* /tmp/_build/html/
	
#prepare gh-pages and remove existing stuff
git checkout gh-pages
rm -rf *
	
#make the changes
cp -r /tmp/_build/html/* .
git add .
git commit -am "autoupdated documentation"
git push origin gh-pages
	
#switch back to master
git checkout master
mkdir -p  usr/share/doc/persy/ 
mv /tmp/_build/html/* usr/share/doc/persy/ 
echo -e "Documentation publishing finished. The HTML pages are at http://kinkerl.github.com/persy/"

# git tag & push
git tag -f $version
git push origin master --tags

# upload source changes
echo -e "Uploading source changes to ppa"
dput -f  ppa:tmassassin/ppa ../persy_${version}_source.changes

#Released
echo -n "Finaly released persy-$version."

# debian .deb
echo -e ""
echo -n "Building the debian package? (y/n): "
read answer
if [ "$answer" != "y" ]; then
    echo "Exit."
    exit 0
else
    echo -e "Start building debian package..."
    debuild -i.git -I.git
    echo -e "Build finished; Get the debian package at ../persy_${version}_all.deb"
fi

echo -e "Done."
exit 0
