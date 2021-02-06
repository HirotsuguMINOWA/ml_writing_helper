"""
Pillowで対応する。不要。
"""
import pathlib
import os
from typing import Tuple

from PIL import Image


class PathWithImg(pathlib.Path):
    """
    - ImageMagic変換用にサイズ指定のため、ソースで画像情報取得可能にする
    - Ref
        - https://stackoverflow.com/questions/29850801/subclass-pathlib-path-fails or zotero
    """
    # def __new__(cls, **kwargs):
    #     path = cls._std_etc()
    #     return super().__new__(cls, path, **kwargs)
    _flavour = pathlib._windows_flavour if os.name == 'nt' else pathlib._posix_flavour

    def __new__(cls, *args):
        return super(PathWithImg, cls).__new__(cls, *args)

    # def __init__(self, *args):
    #     super().__init__() #Path.__init__ does not take any arg (all is done in new)
    #     self._some_instance_ppath_value = self.exists() #Path method

    def __init__(self, *args):
        # super().__init__(arg)
        super().__init__()  # Path.__init__ does not take any arg (all is done in new)
        # self._some_instance_ppath_value = self.exists() #Path method
        # ※ 毎回求めた方がよい、∵ Pathの値変更に追いつけないため。
        # self._dpi = None
        # self._width = None
        # self._height = None
        self._im = None  # Image class of Pillow
        self._dpi = None  # info DPI

    @property
    def im(self) -> Image:
        if self._im is None:
            self._im = Image.open(self.as_posix())
        if self._im:
            return self._im
        else:
            raise Exception("[Bug?] Pillowで画像Loadできないエラー発生¥nさもなくば、Pillowに対応したフォーマットではない？")

    @property
    def dpi1d(self) -> int:
        """
        DPIを返す
        - 無いときは？
        - 縦、横の内、小さい方を返す
        :return:
        """
        # 小さい方のDPIを返す
        if self.dpi[0] > self.dpi[1]:
            return self.dpi[1]
        else:
            return self.dpi[0]

    @property
    def dpi(self) -> Tuple[int, int]:
        if self._dpi is None:
            self._dpi = self.im.info['dpi']  # type: Tuple[int,int]
        if self._dpi is None:
            raise Exception("[Bug?] PillowでDPIを取得できず")
        else:
            return self._dpi

    @property
    def width(self):
        self.im.width

    @property
    def height(self):
        self.im_heiht


if __name__ == '__main__':
    im = PathWithImg("/Users/hirots-m/Documents/PyCharmProjects/ml_writing_helper/sample/fig_sample/test_jpg.jpg")
    if not im.exists():
        raise Exception("ファイルが見つかりません")
    print(im.dpi)
