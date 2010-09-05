LANGS=de 
SHELL=/bin/sh

PREFIX=/usr
DEST=$(DESTDIR)$(PREFIX)

all: build

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

install_translations:
	install -d $(DEST)/share/persy/locale/de/LC_MESSAGES
	install --mode=644 usr/share/persy/locale/de/LC_MESSAGES/messages.mo $(DEST)/share/persy/locale/de/LC_MESSAGES/messages.mo


clean:
	rm usr/share/persy/assets/VERSION
	rm -rf usr/share/man/man1
	rm -rf usr/share/doc
	rm doc/*.pyc
	rm -rf doc/_tmp

build: genversion doc-man doc-html languagefile

