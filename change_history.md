# Change History

## 2026-10-15(v0.10.0)

### Changed: the two commands were merged into `ml_writing_helper`

- `convert4ml` and `watch4ml` were removed and replaced by the single command `ml_writing_helper`
  - `[project.scripts]` is now `ml_writing_helper = "ml_writing_helper.main:main"`
- The former `watch4ml` behavior is the default: `ml_writing_helper --json / --mode / --conf-maker-web / --conf-maker-cli`
  - `--monitor` branches the behavior as before: with it the command keeps watching, without it all tasks run once and exit
  - `ml_writing_helper` with no argument shows the help message (exit code 0)
- The former `convert4ml` behavior is the `convert` subcommand
  - `ml_writing_helper convert src_path dst_dir to_fmt [--gray] [--no-crop]`
  - The subcommand name can be omitted (`ml_writing_helper fig_src/fig1.pptx fig_gen pdf`), so old command lines keep working
- Kept for backward compatibility
  - The legacy `monitor` subcommand (watch one folder; it keeps watching without `--monitor`)
  - A leading `watch` token is accepted and ignored (`ml_writing_helper watch --mode img_conv` == `ml_writing_helper --mode img_conv`)
  - `main.watch()` / `main.convert()` / `main.monitor()` still exist but are deprecated (DeprecationWarning); use `main.main()`

### Upgrade

- Reinstall so that the old commands are removed: `pipx install --force .`
- Replace `watch4ml` with `ml_writing_helper`, and `convert4ml X Y Z` with `ml_writing_helper convert X Y Z` in your scripts

### Files added/changed

- Changed: `pyproject.toml` (`[project.scripts]`), `main.py` (one top-level parser, `_add_watch_args()`, `_parse_cli_args()`, `main()` dispatch)
- Changed: `config.py` (error messages), `sandbox/start_watcher.py`, `ReadMe.md`, `test/test_monitor_option.py`

## 2026-10-15(v0.9.0)

### Added: `--monitor` option (run once or keep watching)

- Without `--monitor`, `watch4ml` now runs all tasks once (converts / copies the files that need it) and exits
- With `--monitor`, `watch4ml` keeps running and processes files whenever they change (stop with Ctrl+C)
- How to specify
  - CLI: `watch4ml --mode doc_conv --src docs --dst out --monitor`
  - json: top-level `"monitor": true` (bool, default `false`). A non-bool value is reported as a config error
  - Watching continues if either `--monitor` or `"monitor": true` is given
- `--monitor` can be combined with any of `--json`, `--mode`, `--conf-maker-web`, `--conf-maker-cli` (an exception to the rule that `--json` cannot be combined with other CLI parameters). `watch4ml --monitor` alone is an error because no launcher is given
- `--conf-maker-web`: added a "monitor" checkbox to the global settings, and renamed the button "保存して監視開始" to "保存して実行" (save and run)
- `--conf-maker-cli`: added a question for `monitor`, and changed the final question to "この設定で実行しますか" (run with this config?)

### Breaking change

- The default behavior of `watch4ml` changed from "keep watching" to "run once and exit". To keep watching as before, add `--monitor` or write `"monitor": true` in the json file
- Unchanged: calling `Monitor().start_monitors()` from Python (e.g. `start_watcher.py`) and the legacy `monitor` subcommand still keep watching

### Files added/changed

- Added: `test/test_monitor_option.py`
- Changed: `main.py` (`--monitor` option, new `Monitor.run_once()`, `monitor` argument of `Monitor.start_monitors()`)
- Changed: `config.py` (`monitor` in json and `WatchConfig.monitor`), `webui.py`, `conf_maker_cli.py`
- Changed: `ReadMe.md` (section "Run once or keep watching (`--monitor`)")

## 2026-10-15(v0.8.0)

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
