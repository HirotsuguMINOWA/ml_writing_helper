from pathlib import Path

from loguru import logger


class Util:
    @staticmethod
    def validated_fmt(to_fmt: str, src_pl: Path) -> str:
        """
        変換用フォーマットのvalue check
        :param to_fmt:
        :param src_pl:
        :return:
        """
        if to_fmt == "":
            return src_pl.suffix
        elif to_fmt[0] != ".":
            return "." + to_fmt
        else:
            return to_fmt

    @staticmethod
    def preprocess(src_pl: Path, dst_pl: Path) -> tuple[Path, Path]:
        """
        各変換前に通すべき前処理。
        :param src_pl:
        :param dst_pl:
        :return:
        """
        try:
            # チェックPATH
            src_pl = src_pl.resolve()
            # check src path
            if not src_pl.is_file():
                msg = f"src_plはfile pathか:{src_pl.as_posix()}"
                raise FileNotFoundError(msg)
            # abs. path
            dst_pl = dst_pl.resolve()
            # 拡張子を持つfileか否かチェック
            if dst_pl.suffix == "":
                msg = f"dst_plはfile pathか:{dst_pl.as_posix()}"
                raise FileNotFoundError(msg)
            if not dst_pl.parent.exists():
                msg = f"dst_plの親PATHが存在しない:{dst_pl.as_posix()}"
                raise FileNotFoundError(msg)
            return src_pl, dst_pl
        except FileNotFoundError as e:
            logger.error(e)
            exit(1)
