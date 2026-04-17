from pathlib import Path


class Tool:
    def pdfcrop(self, src_pl: Path, dst_pl: Path) -> None:
        """

        :param src_pl:
        :param dst_pl:
        :return:
        """
        pass

    def img_magick(self, src_pl: Path, dst_pl: Path) -> None:
        """

        :param src_pl:
        :param dst_pl:
        :return:
        """
        pass

    def _conv_raw_img(self, src_pl: Path, dst_pl: Path) -> None:
        """
        ラスタ型?(png, jpeg)の画像変換
        :param src_pl:
        :param dst_pl:
        :return:
        """
        pass
