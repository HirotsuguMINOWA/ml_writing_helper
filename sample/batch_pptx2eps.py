import shutil

from src.watcher_pptx2pdf import ChangeHandler
from pathlib import Path

p_src = Path(__file__).resolve().parent.joinpath("fig_src")
p_dst = Path(__file__).resolve().parent.joinpath("fig_tmp")

if p_dst.exists():
    shutil.rmtree(p_dst)
    p_dst.mkdir()

conv = ChangeHandler(
    monitoring_dir=p_src.as_posix(), output_dir=p_dst.as_posix()
    , dst_ext_no_period="png"
)
conv.convert(
    path_src='fig_src/test.pptx',
    dir_dst=p_dst.as_posix(),
    to_fmt="eps"
)
