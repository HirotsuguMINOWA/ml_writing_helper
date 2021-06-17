"""
単一ファイルの変換
- eps-black-white
"""

from src.main import Monitor
from pathlib import Path

p = Monitor()
Monitor.conv_manipulation_img(
    src_pl=Path("fig_sample/test_img.png")
    , dst_pl=Path("_fig_gen/gray-png.eps")
    , do_trim=True
    , gray=True
)

"""jpeg"""
Monitor.conv_manipulation_img(
    src_pl=Path("fig_sample/test_img.jpg")
    , dst_pl=Path("_fig_gen/gray-jpg.eps")
    , do_trim=True
    , gray=True
)

"""jpeg2"""
Monitor.conv_manipulation_img(
    src_pl=Path("fig_sample/test_img2.jpg")
    , dst_pl=Path("_fig_gen/gray-jpg2.eps")
    , do_trim=True
    , gray=True
)
