"""Thin wrapper of the `watch4ml` CLI.

Choose one of --json / --mode / --conf-maker-web / --conf-maker-cli. Examples:

    watch4ml --json                      # ./ml_writing_helper.json
    watch4ml --mode img_conv --root <this dir> --ext pdf --gray
    watch4ml --mode copy --root <this dir> --src /Users/my_user/Documents/BibTexExported --dst bib
    watch4ml --conf-maker-cli            # create ml_writing_helper.json interactively

Run `watch4ml --help` for all options.
"""
import sys

from ml_writing_helper.main import watch

if __name__ == "__main__":
    raise SystemExit(watch(sys.argv[1:]))
