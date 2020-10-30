"""
単一ファイルの変換
- eps-black-white
"""

from src.core import ChangeHandler
from pathlib import Path

p = ChangeHandler()
ChangeHandler.conv_img(
    src_pl=Path("fig_sample/test_img.png")
    , dst_pl=Path("_fig_gen/gray-png.eps")
    , do_trim=True
    , gray=True
)

"""jpeg"""
ChangeHandler.conv_img(
    src_pl=Path("fig_sample/test_img.jpg")
    , dst_pl=Path("_fig_gen/gray-jpg.eps")
    , do_trim=True
    , gray=True
)

"""jpeg2"""
ChangeHandler.conv_img(
    src_pl=Path("fig_sample/test_img2.jpg")
    , dst_pl=Path("_fig_gen/gray-jpg2.eps")
    , do_trim=True
    , gray=True
)
