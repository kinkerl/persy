#!/bin/sh
# Copyright (c) 2010 Dennis Schwertel
#
# AUTHOR:
# Dennis Schwertel <s@digitalkultur.net>
#
# This file is part of persy
#
# persy is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published
# by the Free Software Foundation; either version 2 of the License, or (at
# your option) any later version.
#
# persy is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with persy; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

GPGKEY=AF005C40

PREFIX=/usr
DEST=$(DESTDIR)$(PREFIX)

clean: 
	git clean -f

doc:
	# builds(compresses) the manpage(replaces the github urls for the images)
	mkdir -p usr/share/man/man1
	cat README.markdown | sed 's/http:\/\/cloud.github.com\/downloads\/kinkerl\/persy/\/usr\/share\/doc\/persy\/images/g' | pandoc -s -w man  | gzip -c --best > usr/share/man/man1/persy.1.gz

	# creates a html doc (replaces the github urls for the images)
	mkdir -p usr/share/doc/persy
	cat README.markdown | sed 's/http:\/\/cloud.github.com\/downloads\/kinkerl\/persy/file:\/\/\/usr\/share\/doc\/persy\/images/g' | pandoc --toc -c default.css -o usr/share/doc/persy/index.html

	# grab the images from the markdown file
	rm usr/share/doc/persy/images/*.png 
	sed -n -e 's/\(^.*http\)\([^)]*png\)\()\)/http\2/gp' README.markdown | xargs wget -nc --quiet --directory-prefix=usr/share/doc/persy/images 

language:
	#create the languagefiles
	xgettext usr/lib/persy/*.py -o usr/lib/persy/locale/messages.pot 

genversion:
	echo $(VERSION) > usr/lib/persy/VERSION

source_package: genversion language doc
	debuild -S -sa -k$(GPGKEY) -i.git -I.git

deb_package: genversion language doc
	debuild -i.git -I.git

release: source_package
	git tag -f $(VERSION)
	git push origin master --tags
	dput -f  ppa:tmassassin/ppa ../persy_$(VERSION)_source.changes

# install: language genversion doc
install: language genversion
	# install application
	install -d $(DEST)/bin
	install usr/bin/persy $(DEST)/bin

	# install lib
	install -d $(DEST)/lib/persy
	install -d $(DEST)/lib/persy/assets
	install -d $(DEST)/lib/persy/assets/dist
	install --mode=644 usr/lib/persy/*.py $(DEST)/lib/persy
	install --mode=644 usr/lib/persy/persy.glade $(DEST)/lib/persy
	install --mode=644 usr/lib/persy/VERSION $(DEST)/lib/persy
	install --mode=644 usr/lib/persy/assets/*.svg $(DEST)/lib/persy/assets
	install --mode=644 usr/lib/persy/assets/dist/*.svg $(DEST)/lib/persy/assets/dist
	chmod 755 $(DEST)/lib/persy/persy.py

	# install example config
	install --mode=644 usr/lib/persy/example_config $(DEST)/lib/persy

	# install language
	install -d $(DEST)/lib/persy/locale
	install --mode=644 usr/lib/persy/locale/messages.pot $(DEST)/lib/persy/locale/messages.pot

	# install manpage/doc

	# install desktop starter
	install -d $(DEST)/share/applications
	install --mode=644 usr/share/applications/persy.desktop $(DEST)/share/applications

	# install desktop icon
	install -d $(DEST)/share/icons
	install --mode=644 usr/share/icons/persy.svg $(DEST)/share/icons

	# install bash-completion
	install -d /etc/bash_completion.d
	install --mode=644 etc/bash_completion.d/persy /etc/bash_completion.d

