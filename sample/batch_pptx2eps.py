import shutil

from core import ChangeHandler
from pathlib import Path

p_src = Path(__file__).resolve().parent.joinpath("fig_src")
p_dst = Path(__file__).resolve().parent.joinpath("fig_gen")

print("SRC:%s" % p_src)
if p_dst.exists():
    shutil.rmtree(p_dst)
    p_dst.mkdir()

conv = ChangeHandler()

conv.convert(
    src_file_apath=p_src.joinpath("test_ppt.pptx"),
    dst_dir_apath=p_dst.as_posix(),
    to_fmt="eps"
)
