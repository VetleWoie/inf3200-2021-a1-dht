.PHONY: default dvi clean

default: kv-store-assignment.pdf ../README.md ../README.html

clean:
	git clean -fX .

%.pdf: %.md $(wildcard *.bib) $(wildcard *.csl)
	pandoc --citeproc $< -o $@

README_OPTS := --standalone --toc --citeproc
README_OPTS += --shift-heading-level-by=1 --to gfm
README_OPTS += --webtex="https://latex.codecogs.com/svg.latex?"
README_OPTS += --resource-path assignment-text/ --from markdown+rebase_relative_paths

../README.md: kv-store-assignment.md $(wildcard *.bib) $(wildcard *.csl)
	cd .. && pandoc $(README_OPTS) assignment-text/$< -o README.md

# LaTeX math in a GitHub README? Best to stick to display math, no inline
#
# GitHub disables JavaScript when rendering a README, for security reasons.
# This means that MathJax and other JavaScript-based math renderers won't work.
#
# Pandoc's --webtex option uses a web service to render math as an image.
# This is fine for display-math formulas, but the images don't fit well into
# flows of text. (SVGs fit better than PNGs, but still not seamlessly.)
#
# For inline math, try to approximate it with Unicode math characters
# and Markdown formatting, e.g. O(\log_2 n) ->  O(log~2~ _n_).
#
# Don't forget about Pandoc's subscript and superscript features.
# https://pandoc.org/MANUAL.html#superscripts-and-subscripts
#
# Unicode-table.com is a good place to look up Unicode math symbols.
# https://unicode-table.com/en/sets/mathematical-signs/
#
# The sciweavers.org URL below is an alternative to
# Pandoc's default converter at codecogs.com
# (which happened to be down the day I was trying to figure this out).
# As of August 2021, sciweavers seems to have a problem with their transfer
# encoding, causing the browser to interpret the PNG data as text
# and then complain about the resulting UTF-8 errors.
# This causes Chrome to render some of the images as an iframe of garbage text.
#
# # Default webtex
# README_OPTS += --webtex
#
# # Render SVG instead of default PNG
# README_OPTS += --webtex="https://latex.codecogs.com/svg.latex?"
#
# # Use alternate rendering service (beware of transfer encoding errors)
# README_OPTS += --webtex="http://www.sciweavers.org/tex2img.php?bc=White&fc=Black&im=png&fs=12&ff=arev&edit=0&eq="

%.html: %.md
	pandoc --from gfm $< -o $@
