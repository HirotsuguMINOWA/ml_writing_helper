"""Thin wrapper of the `ml_writing_helper` CLI.

Choose one of --json / --mode / --conf-maker-web / --conf-maker-cli. Examples:

    ml_writing_helper --json                      # ./ml_writing_helper.json
    ml_writing_helper --mode img_conv --root <this dir> --ext pdf --gray
    ml_writing_helper --mode copy --root <this dir> --src /Users/my_user/Documents/BibTexExported --dst bib
    ml_writing_helper --conf-maker-cli            # create ml_writing_helper.json interactively

Add --watch to keep watching for changes; without it all tasks run once and the command exits.
Run `ml_writing_helper --help` for all options.
"""
import sys

from ml_writing_helper.main import main

if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
