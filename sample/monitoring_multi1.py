from src.core import ChangeHandler

o = ChangeHandler()
o._set_monitor(
    src_dir="fig_src"
    , dst_dir="fig_gen"
    , to_fmt="eps"
)
o._set_monitor(
    src_dir="/Users/hirots-m/Documents/BibTexExported"
    , dst_dir="fig_gen"
    , to_fmt=".bib"
)
o.start_monitors()
