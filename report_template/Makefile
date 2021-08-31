.PHONY: default clean

default: report-template.pdf

clean:
	git clean -fX .
	rm report-template.pdf

%.pdf: %.tex
	lualatex $*.tex
	biber $*
	lualatex $*.tex
	lualatex $*.tex
