"""Thin wrapper of the `watch4ml` CLI.

Settings come from ./ml_writing_helper.json (or --json PATH), or from a mode with CLI parameters.
With no arguments and no json, a web UI to create the json opens. CLI examples:

    watch4ml img_conv --root <this dir> --ext pdf --gray
    watch4ml copy --root <this dir> --src /Users/my_user/Documents/BibTexExported --dst bib

Run `watch4ml --help` for all options.
"""
import sys

from ml_writing_helper.main import watch

if __name__ == "__main__":
    raise SystemExit(watch(sys.argv[1:]))
