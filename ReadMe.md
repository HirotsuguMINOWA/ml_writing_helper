# ML Writing Helper

## Summary

This package is a helper tool for writing documents and papers using Markup Language (ML) such as LaTeX, HTML, or Markdown.



## Function

1. Image insertion support 
   1. This can convert .pptx/.ppt files created by PowerPoint or LibreOffice into image files such as .eps, .pdf, .png and so on.
1. Cropping
   1. This can remove outline white space in the above conversion.
1. Monitoring specific folders and copy if inside files are changed
   1. This can copy files such as .bib file exported from document manager to target folder by detecting their change or export and so on.
1. Grayscale
   1. This can convert to gray scale image.


## Build package

- The below build command will be executed with `pyproject.toml` and Nuitka.

```bash
python -m build --wheel
```

## Setup

### Requirements

Please install the following software before using this package.

1. LibreOffice

## CLI


### Caution for CLI

- CLI run can do one task only per one process.
- If your want to do multi tasks in CLI, you run this app to do each task.
  - If you want to do multi tasks, you had better to use `--json` mode.


### watcher (`watch4ml`)

Choose how to run with one of the following options. They cannot be combined.

| Command                                     | Behavior                                                                                 |
| ------------------------------------------- | ---------------------------------------------------------------------------------------- |
| `watch4ml` (no argument) / `watch4ml --help` | Show the help message                                                                    |
| `watch4ml --json [PATH]`                    | Tasks from the json file. Without PATH, `./ml_writing_helper.json` is used               |
| `watch4ml --json '{...}'`                   | Tasks from a JSON string (see below)                                                     |
| `watch4ml --mode img_conv [params...]`      | Mode `img_conv`: one figure conversion task from CLI parameters                          |
| `watch4ml --mode copy [params...]`          | Mode `copy`: copy tasks from CLI parameters                                              |
| `watch4ml --conf-maker-web [PATH]`          | Create/edit the json file in a web UI (browser). Without PATH, `./ml_writing_helper.json` |
| `watch4ml --conf-maker-cli [PATH]`          | Create/edit the json file interactively in the terminal. Without PATH, `./ml_writing_helper.json` |

- The parameters of `--mode` (`--src`, `--ext`, `--root`, `--log-level`, ...) can be used only with `--mode`. With `--json` or `--conf-maker-*`, write them in the json file instead.
- To run multiple tasks at once (e.g. img_conv and copy), use the json file.

#### Creating the json file (`--conf-maker-web` / `--conf-maker-cli`)

- `--conf-maker-web`: opens a form in the browser. Add tasks, check the preview, then press "保存して監視開始" (save and start watching) or "保存のみ" (save only).
- `--conf-maker-cli`: asks each setting in the terminal. Press Enter to accept the default shown in `[ ]`. Invalid answers (e.g. a folder that does not exist) are asked again. After saving, you can start watching right away.
- If the file already exists, its content is loaded as the initial values and is overwritten when you save.
- If PATH is a folder, `ml_writing_helper.json` is created in it.

#### json instruction

`--json` takes either a json file path or a JSON string:

- If the value starts with `{`, it is parsed as a JSON string and run as the task instruction.
- Otherwise it is treated as a json file path.
- Without a value (`watch4ml --json`), `./ml_writing_helper.json` is used.

Multiple tasks can be defined in one file. Relative paths are resolved from `root`, which is resolved from the json file's directory (for a JSON string, from the current directory).

```json
{
  "root": ".",
  "observer": "polling",
  "sleep_sec": 1.0,
  "log_level": "INFO",
  "tasks": [
    {"type": "img_conv", "src": "fig_src", "dst": "fig_gen", "ext": "pdf", "gray": true, "crop": true},
    {"type": "img_conv", "src": "slides", "dst": "fig_gen", "ext": "eps"},
    {"type": "copy", "src": "~/Documents/BibTexExported", "dst": "bib", "exts": ["bib"], "diff_sec": 10}
  ]
}
```

| Task key       | Type                | Default         | Description                                                                   |
| -------------- | ------------------- | --------------- | ----------------------------------------------------------------------------- |
| `type`         | `img_conv` / `copy` | required        | Task kind                                                                     |
| `src`, `dst`   | path                | required        | Watched dir / output dir (`dst` is created if missing)                        |
| `ext`          | string              | `pdf`           | `img_conv` only. eps, pdf, png, jpg, jpeg, gif, bmp, tiff                     |
| `gray`, `crop` | bool                | `false`, `true` | `img_conv` only                                                               |
| `exts`         | list                | `["bib"]`       | `copy` only. Extensions to copy                                               |
| `diff_sec`     | int                 | `10`            | `copy` only. Skip when src/dst timestamps differ by this many seconds or less |

- `mode` can be used instead of `type` (same meaning as the CLI mode).
- In `copy` tasks, `ext` can be used instead of `exts` (string or list).

##### JSON string (`--json '{...}'`)

The same format as the json file. A single task can also be written at the top level with `mode` (shorthand):

```bash
# single task (shorthand)
watch4ml --json '{"mode": "copy", "src": "~/Documents/BibTexExported", "dst": "bib", "ext": "bib"}'

# multiple tasks (same format as the json file)
watch4ml --json '{"tasks": [{"mode": "img_conv", "src": "fig_src", "dst": "fig_gen", "ext": "pdf"}, {"mode": "copy", "src": "~/Documents/BibTexExported", "dst": "bib"}]}'
```

Wrap the JSON string in single quotes `'...'` so that the shell passes the double quotes as they are.

#### CLI instruction (`--mode`)

```bash
watch4ml --mode [img_conv|copy] [sub parameters...] [--root [root PATH]]

# fig_src/ -> fig_gen/ as grayscale .pdf
watch4ml --mode img_conv --ext pdf --gray

# copy exported .bib into bib/
watch4ml --mode copy --src ~/Documents/BibTexExported --dst bib
```

##### Common parameters

Available in every mode (e.g. `watch4ml --mode copy --src a --dst b --log-level DEBUG`).

| Option             | Default             | Description                                                                 |
| ------------------ | ------------------- | --------------------------------------------------------------------------- |
| `--observer`       | `polling`           | watchdog backend (`polling` is cloud-storage friendly, `native` is lighter) |
| `--sleep-sec`      | `1.0`               | Main loop sleep time                                                        |
| `--diff-sec`       | `10`                | Skip when src/dst timestamps differ by this many seconds or less            |
| `--log-level`      | `INFO`              | Console log level                                                           |
| `--root root_PATH` | current folder(".") | The base PATH for this app to understand relative PATH                      |

##### Mode: img_conv

This mode converts src path's images (e.g.: .pptx, .png) into dest path with format (e.g.: .eps, .pdf)

| Option      | Default   | Description                                             |
| ----------- | --------- | ------------------------------------------------------- |
| `--src DIR` | `fig_src` | Figure source dir. Once only                            |
| `--dst DIR` | `fig_gen` | Figure output dir (created if missing). Once only       |
| `--ext FMT` | `pdf`     | Output format: eps, pdf, png, jpg, jpeg, gif, bmp, tiff |
| `--gray`    | off       | Convert to grayscale                                    |
| `--no-crop` | off       | Disable cropping                                        |

##### Mode: copy

This mode copies the files of src path into the dest path

| Option      | Default    | Description                                                                                                   |
| ----------- | ---------- | ------------------------------------------------------------------------------------------------------------- |
| `--src SRC` | (required) | Copy changed files from SRC. Repeatable                                                                       |
| `--dst DST` | (required) | Copy changed files to DST. Repeatable: paired with `--src` in order, or a single `--dst` receives all `--src` |
| `--ext EXT` | `bib`      | Extension to copy. Repeatable                                                                                 |

When `--src` and `--dst` are given multiple times, they are matched as follows:

- If both counts are the same, they are paired in the given order (e.g. `--src a --dst x --src b --dst y` copies a→x and b→y).
- If only one `--dst` is given, every `--src` is copied into it.
- Any other combination of counts is an error.

##### [Not implement yet] Mode: doc_conv

This mode convert document type(e.g.: markdown) into other type(e.g.:pdf) if src files are changed.


### single file conversion

- `convert4ml src_path dst_dir to_fmt [--gray] [--no-crop]`

## Install

Install requirements
1. LibreOffice
   1. Windows10 or above: `winget install LibreOffice`
   2. MacOS: `brew install --cask libreoffice`
   3. Linux: `sudo apt-get install libreoffice`
   4. Manual install...
2. poppler (used by pdf2image): `brew install poppler` / `sudo apt-get install poppler-utils`
3. this package (pipx recommended):
   1. From a local checkout: `pipx install .` (update: `pipx install --force .`)
   2. From a built wheel: `pipx install dist/ml_writing_helper-<ver>-<tag>.whl`
   3. From GitHub: `pipx install git+https://github.com/HirotsuguMINOWA/ml_writing_helper.git`


## Usage

![usage instruction gif](attachment/usage70.gif)

### Preparation

- Make a rule file for support. 
  - Save this code to ,for example, `start_watcher.py`
1. `python [below code]`
    ```python
    from ml_writing_helper import Monitor
    from pathlib import Path
    manu_path = Path(__file__).resolve().parent # manuscript_path as hiro_watcher
    o=Monitor()

    # Conversion .pptx in fig_src dir TO fig_gen dir.
    o.set_monitor(
     src_dir=manu_path.joinpath("fig_src")
     ,dst_dir=manu_path.joinpath("fig_gen")
     ,to_fmt=".eps" # .png, .pdf and so on.
    )

    # Copy document manager(mendeley/zotero...) exported .bib is copied to manu_path
    o.set_monitor(
      src_dir="/usr/<username>/Documents/BibTexExported"
      ,dst_dir=manu_path
      ,to_fmt=".bib"
    )

    o.start_monitors()
    ```
   
### Usage example from terminal
1. Install this package.
2. `python start_watcher.py`
  
### Usage example from Visual Studio SCode(VSC)
1. Setup
    1. Install PlugIn "CodeRunner(`formulahendry.code-runner`)" to VSC.
2. Settings
   1. Setup path of python interpreter @ `.vscode/settings.json`
      - `.vscode/settings.json`
        ```json
        {
          "code-runner.executorMap": {
            "python": "/Users/YOUR_USER_ID/pyenv/ml_writing_helper/bin/python",
          }
        }
        ```
3. Run a rule file `start_watcher.py`
   1. 'Cmd(Ctrl)+Opt(Alt)+N' to run `start_watcher.py`
   2. Or autorun if combines with `philfontaine.autolaunch`?

# Troubleshooting / Tips

## eps over pdf for LaTeX

- Reason: displays at proper size
- In pdf, `\linewidth` does not fit in the width (multiple columns) correctly, probably because the size of pdf is not correctly obtained.
  - Compared to png, it is easier to use eps or .xbb, because the bounding box is not necessary to specify the size.
  - In IEICE templates, the above size acquisition failure may be the reason why the image is normally output as an image and buried in the text.

## **Cropping(White space remove) failed**

### Cause

1. Invisible frame in the target image

## Slide-to-Img conversion failed

### Cause

1. If you use format `pdf`, change to **`.png`**.
    1. Current version fails to crop pdf files.

## PowerPoint file to image(PDF included) has low quality

1. MacOS: LibreOfficeVanilla is not verified?
    1. This edition was removed the conversion function.
2. is the image quality down when you open that .pttx in LibreOffice?
    1. even if the image quality is not reduced on PowerPoint, the image quality may be reduced when opened in LibreOffice, which could be solved by reworking the document.
    2. a PowerPoint file can be converted to PNG in PowerPoint and then converted to eps in this script.
3. MacOS: LibreOffice application verification not finished?
    1. after installing from Homebrew, if you use LibreOffice without completing the application validation, the image quality will be low.
