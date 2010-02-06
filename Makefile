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
# You can set these variables from the command line.

SPHINXOPTS    =
SPHINXBUILD   = sphinx-build
PAPER         =

# Internal variables.
PAPEROPT_a4     = -D latex_paper_size=a4
PAPEROPT_letter = -D latex_paper_size=letter
ALLSPHINXOPTS   = -d /tmp/_build/doctrees $(PAPEROPT_$(PAPER)) $(SPHINXOPTS) .

GPGKEY=AF005C40

VERSION=`head -n 1 debian/changelog |  sed  's/(/ /' |  sed  's/)/ /' | awk '{print $$2}'`


clean: 
	git clean -f

doc-publish: doc-html
	rm -fr /tmp/_build/html
	mkdir -p /tmp/_build/html
	mv usr/share/doc/persy/* /tmp/_build/html/
	git clean -f
	git checkout gh-pages
	cp -r /tmp/_build/html/* .
	git add .
	git commit -am "autoupdated apidocs"
	git push origin gh-pages
	git checkout master
	mv /tmp/_build/html/* usr/share/doc/persy/ 
	

doc-html: genversion
	#build developer documentation and place it in usr/share/doc
	mkdir -p usr/share/doc
	cd doc && $(SPHINXBUILD) -b html $(ALLSPHINXOPTS) ../usr/share/doc/persy
	@echo
	@echo "Build finished. The HTML pages are in usr/share/doc"

doc-latex: genversion
	cd doc && $(SPHINXBUILD) -b latex $(ALLSPHINXOPTS) _build/latex
	@echo
	@echo "Build finished; the LaTeX files are in doc/_build/latex."
	@echo "Run \`make all-pdf' or \`make all-ps' in that directory to" \
	      "run these through (pdf)latex."

doc-man: genversion
	# builds(compresses) the manpage(replaces the github urls for the images)
	mkdir -p usr/share/man/man1
	cat README.markdown | sed 's/http:\/\/cloud.github.com\/downloads\/kinkerl\/persy/\/usr\/share\/doc\/persy\/images/g' | pandoc -s -w man  | gzip -c --best > usr/share/man/man1/persy.1.gz

doc-images:
	#this is unused at the moment
	# grab the images from the markdown file
	mkdir -p usr/share/doc/persy/images/
	rm -f usr/share/doc/persy/images/*.png 
	sed -n -e 's/\(^.*http\)\([^)]*png\)\()\)/http\2/gp' README.markdown | xargs wget -nc --quiet --directory-prefix=usr/share/doc/persy/images 

language:
	#create the languagefiles
	xgettext usr/lib/persy/*.py -o usr/lib/persy/locale/messages.pot 
	git commit -am "autoupdated languagefiles"

genversion:
	echo $(VERSION) > usr/lib/persy/VERSION

source-package: genversion language doc-man doc-html
	debuild -S -sa -k$(GPGKEY) -i.git -I.git

deb-package: genversion language doc-man doc-html
	debuild -i.git -I.git
	git clean -f
	rm -rf debian/persy

release: source_package
	git tag -f $(VERSION)
	git push origin master --tags
	dput -f  ppa:tmassassin/ppa ../persy_$(VERSION)_source.changes

