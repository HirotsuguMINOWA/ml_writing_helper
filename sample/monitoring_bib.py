from core import ChangeHandler

p = ChangeHandler()
p.set_monitor(
    src_dir="/Users/hirots-m/Documents/BibTexExported"
    , dst_dir="fig_gen"
    , to_fmt=".bib"
)
p.start_monitors()
