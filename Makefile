LANGS=de 
SHELL=/bin/sh

SPHINXOPTS    =
SPHINXBUILD   = sphinx-build
PAPER         =

# Internal variables used in sphinx
PAPEROPT_a4     = -D latex_paper_size=a4
PAPEROPT_letter = -D latex_paper_size=letter
ALLSPHINXOPTS   = -d /tmp/_build/doctrees $(PAPEROPT_$(PAPER)) $(SPHINXOPTS) . 

all: clean prepare genversion doc-man tarorig

clean:
	rm -rf build/*
	rm -rf usr/share/man/man1
	rm -rf usr/share/doc
	rm -f doc/*.pyc
	rm -rf doc/_tmp

prepare:
	#if version not set: break
	mkdir -p build/persy_$(VERSION)
	cp -r src/* build/persy_$(VERSION)/


genversion:
	echo $(VERSION) > build/persy_$(VERSION)/usr/share/persy/assets/VERSION

doc-html:
	#build developer documentation and place it in usr/share/doc/persy
	mkdir -p doc/_tmp
	echo $(VERSION) > doc/_tmp/VERSION
	
	#create the folder for the documentation and clean it
	mkdir -p build/persy_$(VERSION)/usr/share/doc/persy
	rm -rf build/persy_$(VERSION)/usr/share/doc/persy/*
	
	cd doc && $(SPHINXBUILD) -a -b html $(ALLSPHINXOPTS) ../build/persy_$(VERSION)/usr/share/doc/persy
	@echo
	@echo "Build finished. The HTML pages are in usr/share/doc"

doc-man:
	# builds(compresses) the manpage(replaces the github urls for the images)
	mkdir -p build/persy_$(VERSION)/usr/share/man/man1
	cat src/README.markdown | pandoc -s -w man  | gzip -c --best > build/persy_$(VERSION)/usr/share/man/man1/persy.1.gz
	@echo
	@echo "Build finished; the manpage is in usr/share/man/man1/persy.1.gz."

language:
	xgettext src/usr/share/persy/lib/*.py -o src/usr/share/persy/locale/messages.pot

build: prepare genversion doc-html doc-man language
	@echo "building..."

tarorig: build
	tar -pcz -C build/persy_$(VERSION) -f build/persy_$(VERSION).orig.tar.gz etc usr Makefile README.markdown

