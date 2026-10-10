"""Thin wrapper of the `watch4ml` CLI.

All settings are given as CLI parameters. Equivalent command:

    watch4ml --root <this dir> --ext pdf --gray \
        --copy /Users/my_user/Documents/BibTexExported bib

Run `watch4ml --help` for all options.
"""
import sys

from ml_writing_helper.main import watch

if __name__ == "__main__":
    raise SystemExit(watch(sys.argv[1:]))
