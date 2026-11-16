SOURCES=$(shell find sources -maxdepth 1 -name '*.ufo') sources/config.yaml
FONTS=$(wildcard fonts/ttf/*.ttf)
PY=venv/bin/python

help:
	@echo "make build     build fonts/ttf and fonts/webfonts from sources (gftools builder + scripts/hint.py)"
	@echo "make verify    check the UFO sources reproduce fonts/ttf (outlines, widths, cmap, GSUB, anchors)"
	@echo "make test      run FontBakery (googlefonts profile) into out/fontbakery"
	@echo "make proof     HTML proofs with gftools gen-html into out/proof"
	@echo "make update    upgrade the Python toolchain and pin requirements.txt"
	@echo "make clean     remove build artefacts"

venv: venv/touchfile

venv/touchfile: requirements.txt
	test -d venv || python3 -m venv venv
	venv/bin/pip install -U pip
	venv/bin/pip install -r requirements.txt
	touch venv/touchfile

build: build.stamp

build.stamp: venv $(SOURCES) scripts/hint.py
	rm -rf fonts
	. venv/bin/activate && gftools builder sources/config.yaml
	$(PY) scripts/hint.py fonts/ttf/*.ttf
	touch build.stamp

verify: venv
	for s in Regular Bold Italic BoldItalic; do \
	  $(PY) scripts/verify_sources.py fonts/ttf/NotoSerifMono-$$s.ttf sources/ArborMono-$$s.ufo || exit 1; done

test: venv build.stamp
	mkdir -p out/fontbakery
	. venv/bin/activate && fontbakery check-googlefonts -l WARN --full-lists --succinct \
	  --html out/fontbakery/fontbakery-report.html \
	  --ghmarkdown out/fontbakery/fontbakery-report.md \
	  $(shell find fonts/ttf -name '*.ttf') || echo '::warning file=sources/config.yaml,title=FontBakery failures::See out/fontbakery'

proof: venv build.stamp
	. venv/bin/activate && gftools gen-html proof $(shell find fonts/ttf -name '*.ttf') -o out/proof

update: venv
	venv/bin/pip install --upgrade $$(grep -v '^#' requirements.txt | grep -v '==')
	venv/bin/pip freeze > requirements.txt

clean:
	rm -rf venv build.stamp out

.PHONY: help venv build verify test proof update clean
