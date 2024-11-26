# ML Writing Helper

## Summary

This package is a helper tool for writing documents and papers using Markup Language (ML) such as LaTeX, HTML, or Markdown.



## Function

1. Image insersion support 
   1. This can convert .pptx/.ppt files created by PowerPoint or LibreOffice into image files such as .eps, .pdf, .png and so on.
1. Cropping
   1. This can remove outline white space in the above conversion.
1. Monitoring specific folders and copy if inside files are changed
   1. This can copy files such as .bib file exported from document manager to target folder by detecting their change or export and so on.
1. Grayscale
   1. This can convert to gray scale image.


## Setup

### Requirements

Please install the following software before using this package.

1. LibreOffice

## CLI(Not Implemented yet)

- ~~Format: `convert4ml src_path dst_dir to_fmt is_crop`~~

### watcher

- ~~Format: `mlhelper.watch`~~

## Usage

### Install

Install requirements
1. LibreOffice
   1. Windows10 or above: `winget install LibreOffice`
   2. MacOS: `brew install --cask libreoffice`
   3. Linux: `sudo apt-get install libreoffice`
   4. Manual install...
2. this package:
   1. `pip install -U git+https://github.com/HirotsuguMINOWA/ml_writing_helper.git`

### Run at terminal

1. `python [below code]`
    ```python
    from ml_writing_helper.main import Monitor
    from pathlib import Path
    manu_path = Path(__file__).resolve().parent # manuscript_path as hiro_watcher
    o=Monitor()

    o.set_monitor(
     src_dir=manu_path.joinpath("fig_src")
     ,dst_dir=manu_path.joinpath("fig_gen")
     ,to_fmt=".eps"
    )

    o.set_monitor(
      src_dir="/usr/<username>/Documents/BibTexExported"
      ,dst_dir=manu_path
      ,to_fmt=".bib"
    )

    o.start_monitors()
    ```

### Use on VSCode

1. Step 1 Setup
    1. Install PlugIn "CodeRunner(`formulahendry.code-runner`)"
2. Step 2 Settings
    1. Setup path of python interpreter @ `.vscode/settings.json`
      ```.vscode/settings.json
      {
        "code-runner.executorMap": {
          "python": "/Users/YOUR_USER_ID/pyenv/ml_writing_helper/bin/python",
        },
      }
      ```
- Autorun if combines with `philfontaine.autolaunch`?

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