Simple LaTeX Report Template
--------------------------------------------------

This is a simple hello-world starter document for LaTeX in a style suitable
for your assignment report.
It includes:

- Basic outline for a scientific paper
- Bibliography
- Hyperlinks
- Unicode input

You are not required to use this template.
This is only there to help you get started
if you do not already have a LaTeX workflow.

Using the Template
--------------------------------------------------

The basic commands to compile the LaTeX document are:

```bash
lualatex report-template.tex
biber report-template
lualatex report-template.tex
lualatex report-template.tex
```

This will generate `report-template.pdf`.

It may seem strange to run the same command multiple times,
but LaTeX uses the multiple passes to settle things
like bibliography cross-references.
State between runs is saved in the many output files that LaTeX generates
(.aux, .bbl, and so on).

### Makefile

There is also a Makefile in this directory that will run the commands for you.
If you have `make` installed, just run it.

```bash
make
```

You can also run `make clean` to remove generated files.
