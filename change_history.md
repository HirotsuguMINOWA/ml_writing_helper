# Change History

## 2026-10-15 0.8.0

### Added: Mode `doc_conv` (document conversion)

Incorporated the conversion functionality from md2pdf.py so that Markdown / HTML files in a watch folder can be automatically converted to PDF, HTML, and DOCX.

- How to launch
  - CLI: `watch4ml --mode doc_conv --src docs --dst docs_out --ext pdf --ext html`
  - json: `{"type": "doc_conv", "src": "docs", "dst": "docs_out", "ext": ["pdf", "html"]}`
  - Configurations can also be created via `--conf-maker-web` (button "＋ Add document conversion task") and `--conf-maker-cli` (mode `doc_conv`)
- CLI parameters: `--src` (default `.`), `--dst` (default same as `--src`), `--ext` (pdf / html / docx, multiple allowed), `--engine`, `--pattern` (default `*.md`, multiple allowed), `--header` (multiple allowed)
- json fields: `src`, `dst`, `ext`, `engine`, `pattern`, `header`, `marp_header`, `copy_exts`, `diff_sec`
- Behavior
  - Subfolders under src are also included, and the folder structure of src is reproduced in dst
  - With `engine: auto`, the conversion method is selected per file
    - Marp (frontmatter contains `marp: true`) → marp
    - Slidev → slidev
    - Contains mermaid / plantuml blocks → the diagrams are rendered with playwright (headless Chromium) and the output is saved as PDF
    - Otherwise → pandoc (lualatex)
    - HTML output is browser-facing HTML with marked.js / mermaid.js / highlight.js / KaTeX included
  - `.html` input (`--pattern "*.html"`) is converted to PDF via Chrome's headless print, and to DOCX via pandoc
  - At startup, conversion runs only if src is newer than the output by more than `diff_sec` seconds; while watching, conversion runs whenever src is newer than the output
  - If dst is located inside src, files inside dst are not converted. Hidden files/folders and `node_modules` are excluded
  - If required tools are missing, a warning is issued and conversion is attempted with pandoc as far as possible

### Changes from md2pdf.py

- Removed the hardcoded pandoc path (`/opt/homebrew/bin/pandoc`) and the bundled marp binary; the tools are now looked up on PATH (if marp / slidev is not available, `npx` is used)
- The Japanese TeX header (luatexja) is now kept in the code. The Hiragino font specification is now applied only on macOS
- playwright has become an optional dependency (`pip install "ml_writing_helper[doc]"`). Automatic installation via pip has been removed. If Chromium is not present, `playwright install chromium` is run automatically the first time it is needed
- Output formats were reduced to three: pdf / html / docx (`html_pdf` / `html_docx` were removed)
- HTML output for Marp files is now done with marp
- While watching, a single save no longer triggers the conversion twice (no conversion if the output is newer than src)

### Files added/changed

- Added: `src/ml_writing_helper/converter/doc_converter.py` (conversion processing)
- Added: `src/ml_writing_helper/task_runner/doc_conv_runner.py` (watch task `DocConvTask`)
- Added: `test/test_doc_conv.py`
- Changed: `config.py`, `main.py`, `webui.py`, `conf_maker_cli.py`, `enum_cls.py` (`TaskType.doc_conv`)
- Changed: `pyproject.toml` (added `doc` to optional-dependencies)
- Changed: `ReadMe.md` (description of Mode: doc_conv and the required tools)
