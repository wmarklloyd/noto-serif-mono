SOURCES=$(shell find sources -maxdepth 1 -name '*.ufo') sources/config.yaml
FONTS=$(wildcard fonts/ttf/*.ttf)
PY=venv/bin/python
FONTSPECTOR?=fontspector

help:
	@echo "make build     build fonts/ttf and fonts/webfonts from sources (gftools builder + scripts/hint.py)"
	@echo "make verify    check the UFO sources reproduce fonts/ttf (outlines, widths, cmap, GSUB, anchors)"
	@echo "make test      run fontspector (googlefonts profile) into out/fontspector"
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

build.stamp: venv $(SOURCES) scripts/hint.py scripts/make_hint_controls.py
	rm -rf fonts
	. venv/bin/activate && gftools builder sources/config.yaml
	$(PY) scripts/make_hint_controls.py fonts/ttf/*.ttf
	$(PY) scripts/hint.py fonts/ttf/*.ttf
	touch build.stamp

verify: venv
	for s in Regular Bold Italic BoldItalic; do \
	  $(PY) scripts/verify_sources.py fonts/ttf/NotoSerifMono-$$s.ttf sources/NotoSerifMono-$$s.ufo || exit 1; done

# fontspector is a Rust tool, not on PyPI with the rest of the toolchain:
# `cargo install --locked fontspector`, or set FONTSPECTOR to a release binary.
# The fonts are checked from a copy in out/fontspector/notoserifmono/, the directory
# they will have in google/fonts (ofl/notoserifmono), which dirname_matches_nameid_1 checks.
test: build.stamp
	rm -rf out/fontspector && mkdir -p out/fontspector/notoserifmono
	cp fonts/ttf/*.ttf out/fontspector/notoserifmono/
	$(FONTSPECTOR) -p googlefonts -l warn --full-lists --succinct \
	  --html out/fontspector/fontspector-report.html \
	  --ghmarkdown out/fontspector/fontspector-report.md \
	  out/fontspector/notoserifmono/*.ttf || echo '::warning file=sources/config.yaml,title=fontspector failures::See out/fontspector'

proof: venv build.stamp
	. venv/bin/activate && gftools gen-html proof $(shell find fonts/ttf -name '*.ttf') -o out/proof

update: venv
	venv/bin/pip install --upgrade $$(grep -v '^#' requirements.txt | grep -v '==')
	venv/bin/pip freeze > requirements.txt

clean:
	rm -rf venv build.stamp out

.PHONY: help venv build verify test proof update clean
