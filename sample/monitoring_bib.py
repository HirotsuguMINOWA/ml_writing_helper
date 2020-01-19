from src.core import ChangeHandler

ChangeHandler().monitor(
    src_dir="/Users/hirots-m/Documents/BibTexExported"
    , dst_dir="fig_gen"
    , to_fmt=".bib"
)
