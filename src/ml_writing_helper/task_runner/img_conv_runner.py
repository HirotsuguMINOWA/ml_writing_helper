"""
画像を.epsなど形式変換する処理
"""

import shutil
from typing import Final, override
from pathlib import Path

from loguru import logger
from typed_classproperties import cached_classproperty

from ml_writing_helper.enum_cls import TaskType
from ml_writing_helper.task_runner.abc_runner import ABCTaskRunner
from ml_writing_helper.util import Util
from ml_writing_helper.converter.slide_img_converter import SlideAndImgConverter, ImgConvInputType, ImgConvOutputType


# 出力がepsの場合、監視folderにpngなど画像ファイルが書き込まれたらepsへ変換するコードをかけ
class ImgConvTaskStruct(ABCTaskRunner):

    # @cached_classproperty
    # def target_src_suffixes(cls) -> Sequence[str]:
    #     return [".pptx", ".ppt", ".png", ".jpeg", ".jpg", ".gif"]
    def __repr__(self):
        return f'{self.__class__.__name__}(src_dir_path:{self._src_dir_path}, dst_dir_path={self._dest_dir_path}, src_suffixes={self._src_suffixes}, dst_suffixes={self._src_suffixes})'

    def __init__(
            self,
            src_dir_path: str | Path,
            dst_dir_path: str | Path,
            dst_suffix: str,  # TODO: [優先度:大] dst_extへ要変更。問題は、to_fmtが広範囲に使われているため合わせて変更が必要
            diff_sec: int = 10,
            gray: bool = False,
            is_crop: bool = True,
            mk_dst_dir: bool = True
    ):
        super().__init__(
            src_dir_path=src_dir_path,
            dst_dir_path=dst_dir_path,
            diff_sec=diff_sec,
            dst_suffixes=tuple([dst_suffix]),
            src_suffixes=[str(x) for x in tuple(ImgConvInputType)],  # [".pptx", ".ppt", ".png", ".jpeg", ".jpg", ".gif"],
        )
        self._dst_suffix: Final[ImgConvOutputType] = ImgConvOutputType(dst_suffix)
        self._gray: Final[bool] = gray
        self._is_crop: Final[bool] = is_crop
        self._mk_dst_dir: Final[bool] = mk_dst_dir

    @cached_classproperty
    def task_type(cls) -> TaskType:
        return TaskType.img_conv

    def convert(
            self,
            src_file_apath: str | Path,
            # dst_dir_apath: str | Path,
            dst_suffix: str = "png",
            is_crop: bool = True,
            gray: bool = False,
    ) -> None:
        """
        単一ファイル変換
        ppt->pdf->cropping
        :param src_file_apath:
        # :param dst_dir_apath: Indicating dir path. NOT file path
        :param dst_suffix: format type converted
        :param is_crop: Whether crop or not
        :param gray:
        """

        try:
            # init1
            src_pl = Path(src_file_apath)
            # dst_pl = self._path_conv(dst_dir_apath)

            """ 無視すべき拡張子 """
            if (
                    src_pl.name.startswith("~")
                    or src_pl.name.startswith(".")
                    or src_pl.suffix.lower() in (".part", ".tmp")
                    or src_pl.stem.endswith("~")
            ):
                # for bibdesk
                logger.info("Ignored: %s" % src_pl.name)
                return
            if not src_pl.is_absolute():
                raise Exception("path_srcは絶対Pathで指定して下さい。src_path:%s" % src_pl)
            del src_file_apath
            # src_file_apath = None  # 誤って参照しないように

            # if isinstance(dst_dir_apath, Path):
            #     tmp_dst = dst_dir_apath
            # else:
            #     tmp_dst = Path(dst_dir_apath)
            # tmp_dst = Path(dst_dir_apath)

            # if tmp_dst.is_dir():
            #     dst_pl: Path = tmp_dst.joinpath(src_pl.stem + dst_suffix)
            # else:
            #     dst_pl = tmp_dst
            dst_pl = self.dst_file_path(update_file_path=src_pl)
            # del dst_dir_apath
            # dst_dir_apath = None  # Prevent Trouble
            # del to_fmt # 消すな. .bibコピー失敗するから. #FIXME: 要修正
            # to_fmt = None  # Prevent Trouble
            if __debug__ and dst_pl is None:  # pyright: ignore[reportUnnecessaryComparison]
                raise ValueError("Noneであるのはおかしい")
            """ チェック """
            # to_fmt = cls._validated_fmt(to_fmt=to_fmt, src_pl=src_pl)
            if src_pl.suffix is None or src_pl.suffix.lower() == "":
                logger.error(
                    "Stop conversion because the indicated extension of source was wrong(file:%s)."
                    % src_pl.name
                )
                return
            if dst_pl.suffix is None or dst_pl.suffix == "":
                logger.error(
                    "Stop conversion because the indicated extension of destination was wrong(file:%s)."
                    % dst_pl.name
                )
                return

            # preprocee - 前処理で解決
            src_pl, dst_pl = Util.preprocess(src_pl=src_pl, dst_pl=dst_pl)
            if dst_pl is None:
                raise ValueError("Noneであるのはおかしい")
            # 下記不要？
            if not src_pl.exists() and not dst_pl.suffix == ".bib":
                raise Exception("src path(1st-arg:%s)が見つかりません、訂正して下さい" % src_pl.as_posix())
            # init2
            # # FIXME: Pathしか受け付けないように要修正
            # dst_pl = Path(dst_dir_apath)
            # if not dst_dir_apath.is_dir():
            #     raise Exception("dst_dir_apath(2nd-arg:%s)は、ファイルではなく、フォルダのPATHを指定して下さい" % dst_dir_apath)
            # os.chdir(dst_pl.parent)  # important!

            # 拡張子毎に振り分け
            logger.debug(f"src file ext is {src_pl.suffix}")
            if src_pl.suffix.lower() in (".png", ".jpg", ".jpeg", ".ai", ".eps"):
                """Image Cropping and Conversion
                - [条件] ImageMagicが対応しているFOrmatのみ. Only the format which corresponded to ImageMagick
                - files entered in src_folder, converted into dst_pl which cropping. and conv to eps
                """
                logger.info("Image cropping and Conversion")
                # pl_src2 = cls._crop_all_fmt(src_pl, dst_pl.joinpath(src_pl.stem + src_pl.suffix),
                #                          to_img_fmt=src_pl.suffix)
                # if fmt == ".eps":
                #     cls._conv2eps(src_pl=pl_src2, pl_dst_dir=dst_pl.joinpath(src_pl.stem + src_pl.suffix))
                # return
                # _ = self.mgr_conv_img(src_pl=src_pl, dst_pl=dst_pl, gray=gray)
                # _ = self.conv_manipulation_img(src_pl=src_pl, dst_pl=dst_pl, do_trim=is_crop, gray=gray)
                # _ = cls._conv_and_crop(src_pl=src_pl, dst_pl=dst_pl)
                SlideAndImgConverter.conv_manipulation_img(src_pl=src_pl, dst_pl=dst_pl, gray=gray)
            elif src_pl.suffix.lower() in ".pdf":
                """
                .pdfへの変換
                """
                if dst_pl is None:
                    raise ValueError("Noneであるのはおかしい")
                dst_pl = SlideAndImgConverter.crop_all_fmt(src_pl, dst_pl)
                dst_pl = SlideAndImgConverter.conv_manipulation_img(
                    src_pl, dst_pl, do_trim=True, gray=gray
                )  # TODO: 現状ImgMagickの-trimでPDFもcropされている！！
                if dst_pl is None:
                    raise ValueError("Noneであるのはおかしい")

                # FIXME: 下記fixは不要なのでは。
                # dst_pl = self.fix_eps(dst_pl)
            elif src_pl.suffix.lower() in (".ppt", ".pptx", ".odp") and not src_pl.name.startswith("~"):
                """ Slide Conversion """
                SlideAndImgConverter.mgr_conv_slide(src_pl, dst_pl, gray=gray)
            elif dst_pl.suffix == ".md" and src_pl.name.endswith("_pdc"):
                """PANDOCでpdf変換

                """
                pass
                # TODO: PdfにPWを印加できるように。必ずmethod化しろ、この処理は。
                # TODO:　変換したpdfをしてPathへ転送
            elif dst_pl.suffix == ".md" and src_pl.name.endswith("_mp"):
                """Marp-cliを利用したスライドPDFへ
                """
                pass

            elif src_pl.suffix.lower() == ".bib":  # and fmt_if_dst_without_ext == ".bib":
                """
                .bibファイルのコピー
                注意).bib.partが生成されるが、瞬間的に.bibになる。それを捉えて該当フォルダへコピーしている
                """
                # FIXME: 上記if、条件が重複しているので注
                # tmp_src = src_pl  # .with_suffix("")
                # tmp_dst = dst_pl.joinpath(src_pl.name)  # .with_suffix(".bib")
                # new_path = shutil.copyfile(tmp_src, tmp_dst)
                _ = shutil.copy(src_pl, dst_pl)
                logger.info("Copied %s to %s" % (src_pl, dst_pl))

            elif src_pl.suffix.lower() in SlideAndImgConverter._ext_pluntuml:
                """PlantUML
                """
                logger.debug("Start converting: plantUML")
                SlideAndImgConverter.plantuml2img(src_pl=src_pl, dst_pl=dst_pl)
            elif src_pl.name.endswith("_mermaid") and src_pl.suffix.lower() == ".md" or src_pl.suffix.lower() == ".mmd":
                logger.info(f"Mermaid conversion: {src_pl}")
                SlideAndImgConverter.conv_mermaid_with_crop(
                    src_pl=src_pl, dst_pl=dst_pl, gray=gray
                )  # , to_fmt=to_fmt)
            else:
                logger.info("未処理ファイル:%s" % src_pl)

            # FIXME: 下記fixは不要なのでは。
            # if dst_pl.suffix == ".eps":
            #     dst_pl = self.fix_eps(dst_pl)

        #
        # def conv2pnt(cls, path_src, dir_dst):
        #     plib_src = pathlib.Path(path_src)  # pathlibのインスタンス
        #     if plib_src.suffix in (".ppt", ".pptx") and not plib_src.name.startswith("~"):
        #         path_dst = pathlib.Path(dir_dst) / plib_src.with_suffix(".pdf").name
        #         cmd = "/Applications/LibreOffice.app/Contents/MacOS/soffice --headless --convert-to pdf --outdir {out_dir} {path_src}".format(
        #             out_dir=out_dir, path_src=path_src)
        #         print("[Debug] CMD: ppt2pdf" + cmd)
        #         tokens = shlex.split(cmd)
        #         subprocess.run(tokens)
        except Exception as e:
            logger.exception(e)

    @override
    def _run_internal(self, update_file_path: Path) -> None:
        self.convert(
            src_file_apath=update_file_path,  # pathlib.Path,
            # dst_dir_apath=self.dest_file_path(update_file_path=update_file_path).parent,  # TODO: 二度手間
            dst_suffix=self._dst_suffix,
            gray=self._gray,
            is_crop=self._is_crop,
            # mk_dst_dir=True,
        )

    @override
    def dst_file_path(self, update_file_path: Path) -> Path:
        return self._dest_dir_path.joinpath(f"{update_file_path.stem}.{self._dst_suffix}")

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ImgConvTaskStruct):
            return NotImplemented
        return (
                self.task_type == other.task_type
                and self._dest_dir_path == other._dest_dir_path
                and self._dst_suffix == other._dst_suffix
                and self._gray == other._gray
                and self._is_crop == other._is_crop
                and self._mk_dst_dir == other._mk_dst_dir
        )

    def __hash__(self) -> int:
        return hash(
            (
                self.task_type,
                self._dest_dir_path,
                self._dst_suffix,
                self._gray,
                self._is_crop,
                self._mk_dst_dir,
            )
        )
