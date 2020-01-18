from src.core import ChangeHandler
ChangeHandler().monitor(
    src_dir="fig_src"
    , dst_dir="fig_gen"
    , to_fmt="eps"
)
