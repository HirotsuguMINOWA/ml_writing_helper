from core import ChangeHandler

o = ChangeHandler()

# 監視１つ目: pptxをepsら画像へ
o.set_monitor(
    src_dir="sample/fig_src"
    , dst_dir="sample/fig_gen"
    # , fmt_if_dst_without_ext="png"
    , to_fmt=".eps"
)

# 監視２つ目：.bibを所定のpathへコピー
o.set_monitor(
    src_dir="/Users/hirots-m/Documents/BibTexExported"
    , dst_dir="fig_gen"
    , to_fmt=".bib"
)


o.start_monitors()
