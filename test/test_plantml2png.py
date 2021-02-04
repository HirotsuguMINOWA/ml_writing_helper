"""
Test to convert files of plantUML in fig_src into .png files.

- plantuml CLI
    - https://plantuml.com/ja/command-line

# 書式
## Output Directory
Back to topEdit using Dokuwiki syntaxEdit using Asciidoc syntaxEdit using Markdown syntax
You can specify an output directory for all images using the -o switch:

java -jar plantuml.jar -o "c:/outputPng" "c:/directory2"

# formatの指定
-teps                          Generate images using EPS format
-testdot                       Test the installation of graphviz
-thtml                         Generate HTML file for class diagram
-tlatex                        Generate images using LaTeX/Tikz format
-tlatex:nopreamble             Generate images using LaTeX/Tikz format without preamble
-tpdf                          Generate images using PDF format
-tpng                          Generate images using PNG format (default)
-tscxml                        Generate SCXML file for state diagram
-tsvg                          Generate images using SVG format
-ttxt                          Generate images with ASCII art
-tutxt                         Generate images with ASCII art using Unicode characters
-tvdx                          Generate images using VDX format
-txmi                          Generate XMI file for class diagram
"""

from test_all_img2eps import AutoTester

a = AutoTester()
# a.start(to_fmt=".eps", target_exts=[".png"])
a.start(to_fmt=".png", target_exts=[".pu", ".puml"])
