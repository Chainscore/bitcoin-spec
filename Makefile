# Build the Bitcoin Protocol Specification.

SHELL=/bin/bash -eo pipefail

# Experimental; supported values are pdflatex, lualatex, and xelatex.
ENGINE=pdflatex

LATEXMKOPT_pdflatex=
LATEXMKOPT_xelatex=-pdflatex=xelatex -dvi- -ps-
LATEXMKOPT_lualatex=-pdflatex=lualatex -dvi- -ps-

LATEXMK=max_print_line=10000 latexmk $(LATEXMKOPT_$(ENGINE)) -bibtex -pdf -interaction=nonstopmode --halt-on-error --file-line-error -logfilewarnings- -e '$$max_repeat=8'
PDFDIR=out
DOCVERSION ?= Draft 15

.PHONY: all protocol protocol-dark clean

all: protocol protocol-dark

protocol: $(PDFDIR)/protocol.pdf

protocol-dark: $(PDFDIR)/protocol-dark.pdf

$(PDFDIR)/protocol.pdf: protocol.tex macros.tex bitcoin.bib $(wildcard sections/*.tex) $(wildcard assets/*.png)
	printf '\\renewcommand{\\docversion}{%s}\n' "$(DOCVERSION)" > protocol.ver
	mkdir -p aux $(PDFDIR)
	$(LATEXMK) -jobname=protocol -auxdir=aux -outdir=aux $(EXTRAOPT) protocol
	mv -f aux/protocol.pdf $(PDFDIR)/protocol.pdf
	rm -f protocol.ver

$(PDFDIR)/protocol-dark.pdf: protocol.tex macros.tex bitcoin.bib $(wildcard sections/*.tex) $(wildcard assets/*.png)
	printf '\\toggletrue{darkmode}\n\\renewcommand{\\docversion}{%s}\n' "$(DOCVERSION)" > protocol.ver
	mkdir -p aux $(PDFDIR)
	$(LATEXMK) -jobname=protocol-dark -auxdir=aux -outdir=aux $(EXTRAOPT) protocol
	mv -f aux/protocol-dark.pdf $(PDFDIR)/protocol-dark.pdf
	rm -f protocol.ver

clean:
	rm -rf aux protocol.ver $(PDFDIR)
