from src.watcher_pptx2pdf import ChangeHandler
from pathlib import Path

p_src = Path(__file__).resolve().parent.joinpath("fig_src")
p_dest = Path(__file__).resolve().parent.joinpath("fig_tmp")
conv = ChangeHandler(
    monitoring_dir=p_src.as_posix(), output_dir=p_dest.as_posix()
    , dest_ext_no_period="png"
)
conv._conv_slide(
    path_src='fig_src/test.pptx',
    dir_dest=p_dest.as_posix(),
    to_fmt="eps"
)
