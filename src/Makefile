LANGS=de 
SHELL=/bin/sh

PREFIX=/usr
DEST=$(DESTDIR)$(PREFIX)

#Get the version out of the debian changelog
VERSION=`head -n 1 debian/changelog | sed 's/[()]//g' | awk '{print $$2}'`

SPHINXOPTS    =
SPHINXBUILD   = sphinx-build
PAPER         =

# Internal variables used in sphinx
PAPEROPT_a4     = -D latex_paper_size=a4
PAPEROPT_letter = -D latex_paper_size=letter
ALLSPHINXOPTS   = -d /tmp/_build/doctrees $(PAPEROPT_$(PAPER)) $(SPHINXOPTS) .

all: genversion build

genversion:
	@echo "placing VERSION taken from debian/changelog in usr/share/persy/assets/VERSION"
	@echo $(VERSION) > usr/share/persy/assets/VERSION

doc-html:
	#build developer documentation and place it in usr/share/doc/persy
	
	#create the folder for the documentation and clean it
	mkdir -p usr/share/doc/persy
	rm -rf usr/share/doc/persy/*
	
	cd doc && $(SPHINXBUILD) -a -b html $(ALLSPHINXOPTS) ../usr/share/doc/persy
	@echo
	@echo "Build finished. The HTML pages are in usr/share/doc"

doc-latex:
	cd doc && $(SPHINXBUILD) -a -b latex $(ALLSPHINXOPTS) _build/latex
	@echo
	@echo "Build finished; the LaTeX files are in doc/_build/latex."
	@echo "Run \`make all-pdf' or \`make all-ps' in that directory to" \
	      "run these through (pdf)latex."

doc-man:
	# builds(compresses) the manpage(replaces the github urls for the images)
	mkdir -p usr/share/man/man1
	cat README.markdown | sed 's/http:\/\/cloud.github.com\/downloads\/kinkerl\/persy/\/usr\/share\/doc\/persy\/images/g' | pandoc -s -w man  | gzip -c --best > usr/share/man/man1/persy.1.gz
	@echo
	@echo "Build finished; the manpage is in usr/share/man/man1/persy.1.gz."

install: install_translations install_docs
	# install persy
	install -d $(DEST)/bin
	install --mode=755 usr/bin/persy $(DEST)/bin/persy
    
	# install libs
	install -d $(DEST)/share/persy
	install -d $(DEST)/share/persy/lib
	install -d $(DEST)/share/persy/assets
	install -d $(DEST)/share/persy/assets/dist
	install --mode=644 usr/share/persy/lib/*.py $(DEST)/share/persy/lib
	install --mode=644 usr/share/persy/lib/persy.glade $(DEST)/share/persy/lib/persy.glade
	install --mode=644 usr/share/persy/assets/VERSION $(DEST)/share/persy/assets/VERSION
	install --mode=644 usr/share/persy/assets/GPL-2 $(DEST)/share/persy/assets/GPL-2
	install --mode=644 usr/share/persy/assets/*.svg $(DEST)/share/persy/assets
	install --mode=644 usr/share/persy/assets/dist/*.svg $(DEST)/share/persy/assets/dist
	chmod 755 $(DEST)/share/persy/lib/persy.py
	
	# install language:
	install -d $(DEST)/share/persy/locale
	install --mode=644 usr/share/persy/locale/messages.pot $(DEST)/share/persy/locale/messages.pot
	
	# install example config
	install --mode=644 usr/share/persy/example_config $(DEST)/share/persy
	
	# install desktop starter
	install -d $(DEST)/share/applications
	install --mode=644 usr/share/applications/persy.desktop $(DEST)/share/applications/persy.desktop
	
	# install desktop icon
	install -d $(DEST)/share/icons/hicolor/scalable/apps/
	install -d $(DEST)/share/icons/ubuntu-mono-dark/scalable/apps/
	install -d $(DEST)/share/icons/ubuntu-mono-light/scalable/apps/
	install --mode=644 usr/share/icons/hicolor/scalable/apps/*.svg $(DEST)/share/icons/hicolor/scalable/apps
	install --mode=644 usr/share/icons/ubuntu-mono-dark/scalable/apps/*.svg $(DEST)/share/icons/ubuntu-mono-dark/scalable/apps
	install --mode=644 usr/share/icons/ubuntu-mono-light/scalable/apps/*.svg $(DEST)/share/icons/ubuntu-mono-light/scalable/apps
	
	# install bash-completion
	install -d ${DEST}/../etc/bash_completion.d
	install --mode=644 etc/bash_completion.d/persy ${DEST}/../etc/bash_completion.d/persy

remove: remove_docs
	rm $(DEST)/bin/persy
	rm -rf $(DEST)/share/persy
	rm $(DEST)/share/applications/persy.desktop
	rm $(DEST)/share/icons/persy.svg
	rm ${DEST}/../etc/bash_completion.d/persy

install_translations:
	install -d $(DEST)/share/persy/locale/de/LC_MESSAGES
	install --mode=644 usr/share/persy/locale/de/LC_MESSAGES/messages.mo $(DEST)/share/persy/locale/de/LC_MESSAGES/messages.mo

install_docs:
	install -d $(DEST)/share/man/man1
	install --mode=644 usr/share/man/man1/persy.1.gz $(DEST)/share/man/man1/persy.1.gz
	#install -d $(DEST)/share/doc/persy
	#install -d $(DEST)/share/doc/persy/images
	#install -d $(DEST)/share/doc/persy/sources
	#install -d $(DEST)/share/doc/persy/static
	#install --mode=644 usr/share/doc/persy/*.html $(DEST)/share/doc/persy
	#install --mode=644 usr/share/doc/persy/objects.inv $(DEST)/share/doc/persy/objects.inv
	#install --mode=644 usr/share/doc/persy/searchindex.js $(DEST)/share/doc/persy/searchindex.js
	#install --mode=644 usr/share/doc/persy/images/* $(DEST)/share/doc/persy/images
	#install --mode=644 usr/share/doc/persy/sources/*.txt $(DEST)/share/doc/persy/sources
	#install --mode=644 usr/share/doc/persy/static/* $(DEST)/share/doc/persy/static
	
remove_docs:
	rm $(DEST)/share/man/man1/persy.1.gz
	rm -rf $(DEST)/share/doc/persy

languagefile:
	xgettext usr/share/persy/lib/*.py -o usr/share/persy/locale/messages.pot

clean:
	rm usr/share/persy/assets/VERSION
	rm -rf usr/share/man/man1
	rm -rf usr/share/doc
	rm doc/*.pyc
	rm -rf doc/_tmp

build: genversion doc-man doc-html languagefile

