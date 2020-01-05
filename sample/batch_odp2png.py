from ml_writing_helper.__init__ import ChangeHandler
from pathlib import Path

p_src = Path(__file__).resolve().parent.joinpath("fig_src")
p_dst = Path(__file__).resolve().parent.joinpath("fig_tmp")
conv = ChangeHandler(
    monitoring_dir=p_src.as_posix(), output_dir=p_dst.as_posix()
    , dst_ext_no_period=""
)
conv.convert(
    path_src=p_src.joinpath("test.odp"),
    dir_dst=p_dst.as_posix(),
    to_fmt="png"
)
