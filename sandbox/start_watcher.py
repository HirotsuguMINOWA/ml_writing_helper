"""Thin wrapper of the `watch4ml` CLI.

Settings come from ./ml_writing_helper.json (or --json PATH), or from CLI parameters.
With no parameters and no json, a web UI to create the json opens. Equivalent CLI command:

    watch4ml --root <this dir> --ext pdf --gray \
        --copy /Users/my_user/Documents/BibTexExported bib

Run `watch4ml --help` for all options.
"""
import sys

from ml_writing_helper.main import watch

if __name__ == "__main__":
    raise SystemExit(watch(sys.argv[1:]))
