# -*- coding: utf-8 -*-

# target_dir = "app_single/_fig_src"
# _p_dst_dir = "app_single/figs"

###############################################################

import argparse
import os
import platform
import shlex
# import ftplib
import shutil
import sys
import time
import traceback
import unicodedata  # for MacOS NDF
from collections.abc import Callable
from pathlib import Path
from subprocess import STDOUT, check_output
from typing import Final, override
from pdfCropMargins import crop
from PIL import Image
from loguru import logger
from pdf2image import convert_from_path
from watchdog.events import (
    DirMovedEvent,
    FileMovedEvent,
    FileSystemEvent,
    FileSystemEventHandler,
)
from watchdog.observers.api import BaseObserver
from watchdog.observers.polling import PollingObserver
from debtcollector import removals

from src.ml_writing_helper.task_runner.abc_runner import ABCTaskRunner
from src.ml_writing_helper.enum_cls import MethodToFixEPS, StateMonitor
from src.ml_writing_helper.util import Util
from src.ml_writing_helper.task_runner.copy_runner import CopyTask
from src.ml_writing_helper.task_runner.img_conv_runner import ImgConvTaskStruct, SlideAndImgConverter

try:
    from watchdog.observers.fsevents import FSEventsObserver
except Exception:
    FSEventsObserver = None

try:
    from watchdog.observers.inotify import InotifyObserver
except Exception:
    InotifyObserver = None

try:
    from watchdog.observers.kqueue import KqueueObserver
except Exception:
    KqueueObserver = None

try:
    from watchdog.observers.read_directory_changes import WindowsApiObserver
except Exception:
    WindowsApiObserver = None

# wait_sec: int = 1
DEFAULT_OBSERVER_BACKEND: Final[str] = "polling"
MonitorCallback = Callable[[str], None]


def _normalize_observer_backend(observer_backend: str) -> str:
    return observer_backend.strip().lower().replace("-", "_")


def _build_observer(observer_backend: str = DEFAULT_OBSERVER_BACKEND) -> BaseObserver:
    observer_backend = _normalize_observer_backend(observer_backend)
    if observer_backend in ("poll", "polling"):
        return PollingObserver()

    system_name = platform.system()
    if observer_backend in ("native", "auto", "os"):
        if system_name == "Darwin":
            if FSEventsObserver is not None:
                return FSEventsObserver()
            if KqueueObserver is not None:
                return KqueueObserver()
        elif system_name == "Linux":
            if InotifyObserver is not None:
                return InotifyObserver()
        elif system_name == "Windows":
            if WindowsApiObserver is not None:
                return WindowsApiObserver()
    elif observer_backend == "fsevents" and FSEventsObserver is not None:
        return FSEventsObserver()
    elif observer_backend == "kqueue" and KqueueObserver is not None:
        return KqueueObserver()
    elif observer_backend == "inotify" and InotifyObserver is not None:
        return InotifyObserver()
    elif observer_backend in ("windows", "windowsapi") and WindowsApiObserver is not None:
        return WindowsApiObserver()

    supported = ["polling", "native"]
    if FSEventsObserver is not None:
        supported.append("fsevents")
    if KqueueObserver is not None:
        supported.append("kqueue")
    if InotifyObserver is not None:
        supported.append("inotify")
    if WindowsApiObserver is not None:
        supported.append("windowsapi")
    raise ValueError(
        "Unsupported observer backend: %s. Available: %s"
        % (observer_backend, ", ".join(supported))
    )


# import numpy as np
# import matplotlib
# import magic  # python-magic


# from logger_getter import get_logger

# logger = get_logger(__name__)


# --------------------------------
# ログ出力テスト
# --------------------------------
# logger.debug("Hello World!")


class Monitor(FileSystemEventHandler):
    """
    - Part:
        - event receiver : start trigger to convert
        - convert main method
        - convert sub methods
        - check_external_sub_modules: this checkes exists and proposes to install sub modules. e.g.: gs, pdf2eps and so on.
    """

    msg_event_start: str = "-------------------  Start Event  -------------------"
    app_in: tuple[str, ...] = (".jpeg", ".jpg", ".png")
    imagic_fmt_conv_in: tuple[str, ...] = (
        ".png",
        ".jpg",
        ".jpeg",
        ".png",
        ".eps",
        ".svg",
        ".pdf",
    )
    imagic_fmt_conv_out: tuple[str, ...] = (".png", ".jpg", ".jpeg", ".png", ".eps", ".svg")

    _paths_soffice: list[str] = [
        "soffice",
        "/Applications/LibreOffice.app/Contents/MacOS/soffice",
        r"C:\Program Files\LibreOffice\program\soffice.exe"
    ]

    @classmethod
    def _ppaths_soffice(cls) -> tuple[Path, ...]:
        return tuple([Path(x) for x in cls._paths_soffice])

    _ext_pluntuml: tuple[str, ...] = (".pu", ".puml")

    def __init__(
            self,
            log_level_console: str | int | None = None,
            observer_backend: str = DEFAULT_OBSERVER_BACKEND,
    ) -> None:
        """[summary]

        Arguments:
            monitoring_dir {[type]} -- [description]
            _p_dst_dir {str} -- [description]
            export_fmts {list} -- 出力フォーマット。複数指定すると、その全てのフォーマットに出力。

        Keyword Arguments:
            _to_fmt {str} -- [description] (default: {"png"})
        """
        # TODO: startメソッドへmonitoring_dirやoutput_dirを移せ
        # TODO: 各コマンドのPATHのチェック。OSのPATHに登録されている事前提、加えてデフォルトのPATHチェック。それで見つからなければWarningだけだす。
        self._observer: None | BaseObserver = None
        """[注意]
        本プログラムのScriptが存在するPATHをwcdへ移動とする
        """
        # # print("Abs PATH:%s" % __file__)
        # os.chdir(os.path.dirname(os.path.abspath(__file__)))
        # # p=pathlib.Path.parent
        # # p.as_posix()
        # # os.chdir(pathlib.Path.parent.as_posix()) # Change directory into dir of this script
        # #

        # if not output_dir:
        #     output_dir = monitoring_dir
        # cls.target_dir = monitoring_dir
        # cls._p_src = Path(monitoring_dir)
        # # cls._p_dst_dir = output_dir
        # if Path(output_dir).is_absolute():
        #     cls._p_dst_dir = Path(output_dir)
        # else:
        #     cls._p_dst_dir = Path(monitoring_dir).joinpath(output_dir)
        # self._src_pl: Path | None = None
        # self._dst_pl: Path | None = None
        # self._to_fmt: str | None = None
        # self._monitors: dict[tuple[Path, Path], MonitorCallback] = {}
        # self._monitor_fmts: dict[tuple[Path, Path], str] = {}
        self._tasks: list[CopyTask | ABCTaskRunner | ImgConvTaskStruct] = list()
        self._state: StateMonitor = StateMonitor.wait
        self._observer_backend: str = _normalize_observer_backend(observer_backend)
        # self._ppaths_soffice2: list[Path] = self._ppaths_soffice()
        # if log_level_console is not None:
        #     global logger
        #     logger = get_logger(name=__name__, level_console=log_level_console)
        # #
        # # 拡張子チェック
        # #
        # if _to_fmt == "":
        #     cls._to_fmt = cls._p_src.suffix
        # elif _to_fmt[0] != ".":
        #     cls._to_fmt = "." + _to_fmt
        # else:
        #     cls._to_fmt = _to_fmt
        # TODO: 入力フォーマットか否か要チェック

    # @staticmethod
    # def which(name) -> tuple[bool, str]:
    #     """
    #     which command wrapper on python
    #     :param name:
    #     :return:
    #     """
    #     # print(shutil.which('ls'))  # > '/bin/ls'
    #     # print(shutil.which('ssss'))  # > None
    #     res = shutil.which(name)
    #     if res:
    #         return True, res
    #     else:
    #         return False, ""

    @staticmethod
    def util_manage_tmp_path(
            path: Path,
            is_remove_tmp_str: bool = False,
            suffix_new: str | None = None,
    ) -> Path:
        """
        TODO: モジュールtempを使った方が良くないか？
        「共通」したtempファイルpath返却
        :param is_remove_tmp_str: 付記したtmpを示す文字列を削除するか否か
        :param path:
        :param suffix_new: 生成するtmpファイルのsuffix指定
        :return:
        """
        tmp_str = "_tmp"
        if suffix_new is None:
            suffix_new = path.suffix

        if is_remove_tmp_str:
            # tmp取り除く
            return path.with_name(path.stem.replace(tmp_str, "") + suffix_new)
        else:
            # tmp印加
            return path.with_name(path.stem + tmp_str + suffix_new)

    @staticmethod
    def _run_cmd(cmd: str, short_msg: str = "", is_print: bool = True) -> str:
        """
        コマンド(CLI)の実行Helper
        - TODO: Monitorクラスのこのメソッドは将来削除しろ。Converterクラスへ移行済みなので消して良い
        :param cmd:
        :param is_print:
        :return: output of rum
        """
        if is_print:
            logger.info("CMD(%s):%s" % (short_msg, cmd))
        tokens = shlex.split(cmd)
        try:
            output = check_output(tokens, stderr=STDOUT).decode("utf8")
        except Exception as e:
            logger.error(e)
            return "Error occurred"
        if is_print:
            logger.info("Output(%s):%s" % (short_msg, cmd))
        return output
    def show_warning_tool(self) -> None:
        """
        必要なツールの有無の確認？
        :return:
        """
        # TODO: 面倒なんとか最も簡単な方法できないか
        pass

    @classmethod
    def fix_eps(
            cls,
            src_pl: Path,
            method: MethodToFixEPS = MethodToFixEPS.eps_pdf_converter  # Current method
    ) -> Path | None:
        """
        Repair eps corruption
        - epsがlatex上でずれる問題の修正
        - epstopdf,pdf2epsを使うと「画質が落ちる?」
        :param src_pl:
        :return:
        """
        if method == MethodToFixEPS.gs:
            """効果なし？ gs方式"""
            path_cmd_gs = cls.check_ghostscript()
            if path_cmd_gs is None:
                return
            else:
                """
                - URL: https://tex.stackexchange.com/questions/22063/how-to-fix-eps-with-incorrect-bounding-box
                """
                # gs -dNOPAUSE -dBATCH -q -sDEVICE=bbox file.eps
                cmd = "{gs} -dNOPAUSE -dBATCH -q -sDEVICE=bbox {src}".format(
                    gs=path_cmd_gs, src=src_pl
                )
                out_msg = cls._run_cmd(cmd=cmd, short_msg="Repair .eps by Ghost Script")
                if out_msg != "":
                    logger.info(out_msg)  # 生成したbbox情報など呈示
                    return None

        elif method == MethodToFixEPS.eps_pdf_converter:
            """ 効果アリ """
            path_epstopdf = "epstopdf"
            path_pdftops = "pdftops"
            path_epstopdf = shutil.which(path_epstopdf)
            path_pdftops = shutil.which(path_pdftops)
            if (
                    path_epstopdf is None
                    or path_epstopdf == ""
                    or path_pdftops is None
                    or path_pdftops == ""
            ):
                # Failed due to †commands are absent
                logger.error(
                    ".epsファイルを修正しようとしましたが、%s/%sのコマンドにPATHが非存在/通ってません。" % (path_pdftops, path_epstopdf)
                )
                return None

            # Generate tmp
            tmp_pl = cls.util_manage_tmp_path(src_pl)
            tmp_pl = tmp_pl.with_suffix(".pdf")

            # EPS to PDF
            cmd = "{path_epstopdf} -o={tmp} {src}".format(
                path_epstopdf=path_epstopdf,
                # path_pdftops=path_pdftops,
                tmp=tmp_pl,
                src=src_pl,
            )
            out_msg = cls._run_cmd(cmd=cmd, short_msg="Repair1/2(.eps->.pdf):")
            if out_msg != "":
                logger.error(out_msg)
                return None

            cmd = "{path_pdftops} -eps {tmp} {src}".format(
                path_pdftops=path_pdftops, tmp=tmp_pl, src=src_pl
            )
            out_msg = cls._run_cmd(cmd=cmd, short_msg="Repair2/2(.pdf->.eps):")
            # if out_msg != "":
            #     logger.error(out_msg)
            #     return None

            # Remove tmp
            if tmp_pl.exists():
                tmp_pl.unlink()

            # 結果処理
            if out_msg == "":
                logger.info("Succeeded:%s" % src_pl)
                return src_pl
            else:
                logger.error("Failed:%s" % src_pl)
                return None

    def convert_all(
            self,
            src_dir: str | Path,
            dst_dir: str | Path,
            to_fmt: str = ".eps",
            gray: bool = False,
    ) -> None:
        """
        指定したdirの対応拡張子を全て変換する
        :param src_dir:
        :param dst_dir:
        :param to_fmt:
        :param gray:
        :return:
        """
        try:
            src_pl = Path(src_dir)
            del src_dir
            dst_pl = Path(dst_dir)
            del dst_dir
            if not src_pl.exists():
                raise Exception("Dir not Found")
            if not src_pl.is_dir():
                raise Exception("Src is not dir")
            files = src_pl.glob("*")
            for a_file in files:
                print(f"src:{src_pl}, dst:{dst_pl}")
                self.convert(src_file_apath=a_file, dst_dir_apath=dst_pl, to_fmt=to_fmt, gray=gray)
        except Exception as e:
            logger.error(e)

    # @staticmethod
    # def _path_conv(a_path: str | Path) -> Path:
    #     """
    #     入力pathを適切な型変換する
    #     :param a_path:
    #     :return:
    #     """
    #     if isinstance(a_path, str):
    #         src_pl = Path(a_path)  # pathlibのインスタンス
    #     elif isinstance(a_path, Path):
    #         src_pl = a_path
    #     else:
    #         raise Exception(f"srcのpath指定が対応外のタイプ(f{type(a_path)})出す")
    #     return src_pl
    #
    # def convert(
    #         self,
    #         src_file_apath: str | Path,
    #         dst_dir_apath: str | Path,
    #         to_fmt: str = ".png",
    #         is_crop: bool = True,
    #         gray: bool = False,
    # ) -> None:
    #     """
    #     単一ファイル変換
    #     ppt->pdf->cropping
    #     :param src_file_apath:
    #     :param dst_dir_apath: Indicating dir path. NOT file path
    #     :param to_fmt: format type converted
    #     :param is_crop: Whether crop or not
    #     :param gray:
    #     """
    #
    #     try:
    #         # init1
    #         src_pl = Path(src_file_apath)
    #         # dst_pl = self._path_conv(dst_dir_apath)
    #
    #         """ 無視すべき拡張子 """
    #         if (
    #                 src_pl.name.startswith("~")
    #                 or src_pl.name.startswith(".")
    #                 or src_pl.suffix.lower() in (".part", ".tmp")
    #                 or src_pl.stem.endswith("~")
    #         ):
    #             # for bibdesk
    #             logger.info("Ignored: %s" % src_pl.name)
    #             return
    #         if not src_pl.is_absolute():
    #             raise Exception("path_srcは絶対Pathで指定して下さい。src_path:%s" % src_pl)
    #         del src_file_apath
    #         # src_file_apath = None  # 誤って参照しないように
    #
    #         # if isinstance(dst_dir_apath, Path):
    #         #     tmp_dst = dst_dir_apath
    #         # else:
    #         #     tmp_dst = Path(dst_dir_apath)
    #         tmp_dst = Path(dst_dir_apath)
    #
    #         if tmp_dst.is_dir():
    #             dst_pl: Path = tmp_dst.joinpath(src_pl.stem + to_fmt)
    #         else:
    #             dst_pl = tmp_dst
    #         del dst_dir_apath
    #         # dst_dir_apath = None  # Prevent Trouble
    #         # del to_fmt # 消すな. .bibコピー失敗するから. #FIXME: 要修正
    #         # to_fmt = None  # Prevent Trouble
    #         if dst_pl is None:
    #             raise ValueError("Noneであるのはおかしい")
    #         """ チェック """
    #         # to_fmt = cls._validated_fmt(to_fmt=to_fmt, src_pl=src_pl)
    #         if src_pl.suffix is None or src_pl.suffix.lower() == "":
    #             logger.error(
    #                 "Stop conversion because the indicated extension of source was wrong(file:%s)."
    #                 % src_pl.name
    #             )
    #             return
    #         if dst_pl.suffix is None or dst_pl.suffix == "":
    #             logger.error(
    #                 "Stop conversion because the indicated extension of destination was wrong(file:%s)."
    #                 % dst_pl.name
    #             )
    #             return
    #
    #         # preprocee - 前処理で解決
    #         src_pl, dst_pl = Util.preprocess(src_pl=src_pl, dst_pl=dst_pl)
    #         if dst_pl is None:
    #             raise ValueError("Noneであるのはおかしい")
    #         # 下記不要？
    #         if not src_pl.exists() and not dst_pl.suffix == ".bib":
    #             raise Exception("src path(1st-arg:%s)が見つかりません、訂正して下さい" % src_pl.as_posix())
    #         # init2
    #         # # FIXME: Pathしか受け付けないように要修正
    #         # dst_pl = Path(dst_dir_apath)
    #         # if not dst_dir_apath.is_dir():
    #         #     raise Exception("dst_dir_apath(2nd-arg:%s)は、ファイルではなく、フォルダのPATHを指定して下さい" % dst_dir_apath)
    #         # os.chdir(dst_pl.parent)  # important!
    #
    #         # 拡張子毎に振り分け
    #         logger.debug(f"src file ext is {src_pl.suffix}")
    #         if src_pl.suffix.lower() in (".png", ".jpg", ".jpeg", ".ai", ".eps"):
    #             """Image Cropping and Conversion
    #             - [条件] ImageMagicが対応しているFOrmatのみ. Only the format which corresponded to ImageMagick
    #             - files entered in src_folder, converted into dst_pl which cropping. and conv to eps
    #             """
    #             logger.info("Image cropping and Conversion")
    #             # pl_src2 = cls._crop_all_fmt(src_pl, dst_pl.joinpath(src_pl.stem + src_pl.suffix),
    #             #                          to_img_fmt=src_pl.suffix)
    #             # if fmt == ".eps":
    #             #     cls._conv2eps(src_pl=pl_src2, pl_dst_dir=dst_pl.joinpath(src_pl.stem + src_pl.suffix))
    #             # return
    #             # _ = self.mgr_conv_img(src_pl=src_pl, dst_pl=dst_pl, gray=gray)
    #             # _ = self.conv_manipulation_img(src_pl=src_pl, dst_pl=dst_pl, do_trim=is_crop, gray=gray)
    #             # _ = cls._conv_and_crop(src_pl=src_pl, dst_pl=dst_pl)
    #             Converter.conv_manipulation_img(src_pl=src_pl, dst_pl=dst_pl, gray=gray)
    #         elif src_pl.suffix.lower() in ".pdf":
    #             """
    #             .pdfへの変換
    #             """
    #             if dst_pl is None:
    #                 raise ValueError("Noneであるのはおかしい")
    #             dst_pl = Converter.crop_all_fmt(src_pl, dst_pl)
    #             dst_pl = Converter.conv_manipulation_img(
    #                 src_pl, dst_pl, do_trim=True, gray=gray
    #             )  # TODO: 現状ImgMagickの-trimでPDFもcropされている！！
    #             if dst_pl is None:
    #                 raise ValueError("Noneであるのはおかしい")
    #
    #             # FIXME: 下記fixは不要なのでは。
    #             # dst_pl = self.fix_eps(dst_pl)
    #         elif src_pl.suffix.lower() in (".ppt", ".pptx", ".odp") and not src_pl.name.startswith("~"):
    #             """ Slide Conversion """
    #             self.mgr_conv_slide(src_pl, dst_pl, gray=gray)
    #         elif dst_pl.suffix == ".md" and src_pl.name.endswith("_pdc"):
    #             """PANDOCでpdf変換
    #
    #             """
    #             pass
    #             # TODO: PdfにPWを印加できるように。必ずmethod化しろ、この処理は。
    #             # TODO:　変換したpdfをしてPathへ転送
    #         elif dst_pl.suffix == ".md" and src_pl.name.endswith("_mp"):
    #             """Marp-cliを利用したスライドPDFへ
    #             """
    #             pass
    #
    #         elif src_pl.suffix.lower() == ".bib":  # and fmt_if_dst_without_ext == ".bib":
    #             """
    #             .bibファイルのコピー
    #             注意).bib.partが生成されるが、瞬間的に.bibになる。それを捉えて該当フォルダへコピーしている
    #             """
    #             # FIXME: 上記if、条件が重複しているので注
    #             # tmp_src = src_pl  # .with_suffix("")
    #             # tmp_dst = dst_pl.joinpath(src_pl.name)  # .with_suffix(".bib")
    #             # new_path = shutil.copyfile(tmp_src, tmp_dst)
    #             _ = shutil.copy(src_pl, dst_pl)
    #             logger.info("Copied %s to %s" % (src_pl, dst_pl))
    #
    #         elif src_pl.suffix.lower() in self._ext_pluntuml:
    #             """PlantUML
    #             """
    #             logger.debug("Start converting: plantUML")
    #             Converter.plantuml2img(src_pl=src_pl, dst_pl=dst_pl)
    #         elif src_pl.name.endswith("_mermaid") and src_pl.suffix.lower() == ".md" or src_pl.suffix.lower() == ".mmd":
    #             logger.info(f"Mermaid conversion: {src_pl}")
    #             Converter.conv_mermaid_with_crop(
    #                 src_pl=src_pl, dst_pl=dst_pl, gray=gray
    #             )  # , to_fmt=to_fmt)
    #         else:
    #             logger.info("未処理ファイル:%s" % src_pl)
    #
    #         # FIXME: 下記fixは不要なのでは。
    #         # if dst_pl.suffix == ".eps":
    #         #     dst_pl = self.fix_eps(dst_pl)
    #
    #     #
    #     # def conv2pnt(cls, path_src, dir_dst):
    #     #     plib_src = pathlib.Path(path_src)  # pathlibのインスタンス
    #     #     if plib_src.suffix in (".ppt", ".pptx") and not plib_src.name.startswith("~"):
    #     #         path_dst = pathlib.Path(dir_dst) / plib_src.with_suffix(".pdf").name
    #     #         cmd = "/Applications/LibreOffice.app/Contents/MacOS/soffice --headless --convert-to pdf --outdir {out_dir} {path_src}".format(
    #     #             out_dir=out_dir, path_src=path_src)
    #     #         print("[Debug] CMD: ppt2pdf" + cmd)
    #     #         tokens = shlex.split(cmd)
    #     #         subprocess.run(tokens)
    #     except Exception as e:
    #         logger.error(f"{e}@{traceback.format_exc()}")

    @staticmethod
    def check_ghostscript(cmd: str = "gs"):
        res = shutil.which(cmd)
        if res:
            return res
        else:
            msg = """
                Mac: brew isntall ghostscript
                """
            logger.error(msg)

    @staticmethod
    def is_nfd(line: str) -> bool:
        for char in line.strip():
            if unicodedata.combining(char) != 0:
                return True
        return False

    # def start(cls, sleep_time=0.5):
    #     try:
    #         event_handler = cls
    #         observer = Observer()
    #         observer.schedule(event_handler, cls.target_dir, recursive=True)
    #         # event_handler = ChangeHandler()
    #         observer.start()
    #         while True:
    #             try:
    #                 time.sleep(sleep_time)
    #             except KeyboardInterrupt:
    #                 observer.stop()
    #             observer.join()
    #     except Exception as e:
    #         raise Exception("Current path: %s" % pathlib.Path.cwd())

    @staticmethod
    def _get_internal_deal_path(
            path: str | Path,
            pl_cwd: Path = Path.cwd(),
            head_comment: str = "",
    ) -> Path:
        """
        src and base_dst_pl pathの読み込みを代理
        :param path:
        :type path:str | Path
        :return:
        """
        if isinstance(path, str):
            path_pl = Path(path)
        elif isinstance(path, Path):
            path_pl = path
        else:
            raise Exception(
                "%s %s is not type str or Path(pathlib)" % (head_comment, path)
            )
        """convert to absolute path"""
        if not path_pl.is_absolute():
            # if relative path, convert into absolute
            path_pl = pl_cwd.joinpath(path)
        return path_pl

    # def monitor(cls, src_dir, dst_dir
    #             , fmt_if_dst_without_ext="png"
    #             , export_fmts=["png", "eps", "pdf"]
    #             , sleep_time=0.5
    #             ):
    #
    #     cls._src_pl = cls._get_internal_deal_path(src_dir)
    #     cls._dst_pl = cls._get_internal_deal_path(dst_dir)
    #
    #     # 拡張子チェック
    #     cls._to_fmt = cls._validated_fmt(fmt_if_dst_without_ext=fmt_if_dst_without_ext, fname_str_or_pl=cls._src_pl)
    #     try:
    #         event_handler = cls
    #         observer = Observer()
    #         observer.schedule(event_handler, cls._src_pl.as_posix(), recursive=True)
    #         # event_handler = ChangeHandler()
    #         observer.start()
    #         print("[Info] Start monitoring:%s" % cls._src_pl)
    #         while True:
    #             try:
    #                 time.sleep(sleep_time)
    #             except KeyboardInterrupt:
    #                 observer.stop()
    #             observer.join()
    #     except Exception as e:
    #         raise Exception("Current path: %s" % pathlib.Path.cwd())

    def _get_monitor_func(
            self,
            src_pl: Path,
            dst_pl: Path,
            to_fmt_in: str,
            is_crop: bool = True,
            gray: bool = False,
    ) -> MonitorCallback:
        def moniko(path_updated_file: str) -> None:
            self.convert(
                src_file_apath=path_updated_file,
                dst_dir_apath=dst_pl,
                to_fmt=to_fmt_in,
                is_crop=is_crop,
                gray=gray,
            )

        return moniko

    @removals.remove(message="廃止。新しいset_copy,set_conv_imgを使用せよ。古いmethodは起動時にsrcとdstのtimestamp差をチェックしない")
    def set_monitor(
            self,
            src_dir: str | Path,
            dst_dir: str | Path,
            to_fmt: str,
            gray: bool = False,
            is_crop: bool = True,
            mk_dst_dir: bool = True,
    ) -> None:
        """
        Set monitoring path
        :param mk_dst_dir: Make dest dir if not exists
        :param src_dir:
        :param dst_dir:
        :param to_fmt:
        :param gray:
        :param is_crop:
        :return:
        """
        src_pl = self._get_internal_deal_path(path=src_dir)
        dst_pl = self._get_internal_deal_path(path=dst_dir)
        if mk_dst_dir and not dst_pl.exists():
            try:
                dst_pl.mkdir(parents=True, exist_ok=True)
                logger.info(f"Made dir:{dst_pl.as_posix()}")
            except Exception as e:
                logger.error(f"Failed to make dir:{dst_pl.as_posix()}")
                raise e

    def set_copy_task(
            self,
            src_dir: str | Path,
            dst_dir: str | Path,
            src_suffixes: list[str],
            diff_sec: int = 10
    ) -> None:
        ins: CopyTask = CopyTask(
            src_dir_path=src_dir,
            dst_dir_path=dst_dir,
            diff_sec=diff_sec,
            src_suffixes=src_suffixes
        )
        self._tasks.append(ins)
        # to_fmt_in = Util.validated_fmt(to_fmt=to_fmt, src_pl=src_pl)
        # self._monitors[src_pl, dst_pl] = self._get_monitor_func(
        #     src_pl=src_pl,
        #     dst_pl=dst_pl,
        #     to_fmt_in=to_fmt_in,
        #     is_crop=is_crop,
        #     gray=gray,
        # )
        # self._monitor_fmts[src_pl, dst_pl] = to_fmt_in

    def set_img_conv(
            self,
            src_dir: str | Path,
            dst_dir: str | Path,
            to_fmt: str,
            gray: bool = False,
            is_crop: bool = True,
            mk_dst_dir: bool = True,
    ) -> None:
        ins = ImgConvTaskStruct(
            src_dir_path=src_dir,
            dst_dir_path=dst_dir,
            dst_suffix=to_fmt,
            gray=gray,
            is_crop=is_crop,
            mk_dst_dir=mk_dst_dir
        )
        self._tasks.append(ins)

    def stop(self) -> None:
        if self._observer is None:
            return
        self._observer.stop()
        logger.info("Observerを停止した")

    def start_monitors(self, sleep_sec: int | float = 1, observer_backend: str | None = None) -> None:
        """
        Start monitoring change on FS according to set
        : param sleep_sec:
        : return:
        """
        try:
            # ** ObserverをCLIパラで指定可能
            backend = (
                self._observer_backend
                if observer_backend is None
                else _normalize_observer_backend(observer_backend)
            )
            self._observer = _build_observer(backend)
            if self._observer is None:
                raise Exception(f"[bug] ObserverインスタンスがNone")
            for task in self._tasks:
                task.run_all_target_files_in_target_dir()
                self._observer.schedule(task, task.src_dir_path.as_posix(), recursive=True)
            # **
            self._observer.start()
            # print("[Info] Start Monitoring")
            logger.info("Start Monitoring")
            while self._observer.is_alive():
                try:
                    time.sleep(sleep_sec)
                except KeyboardInterrupt:
                    self._observer.stop()
                    break
            self._observer.join()
        except Exception as e:
            raise Exception("Current path: %s" % Path.cwd()) from e
        except Exception as e:
            logger.exception(e)
            raise Exception(e)
            exit(1)

        # try:
        #     event_handler = self
        #
        #
        #     logger.info(f"Using watchdog observer backend: {backend}")
        #     for src_pl, dst_pl in self._monitors.keys():
        #
        #         # Check src path
        #         if not src_pl.exists():
        #             raise Exception("[Error] The path was not exists: %s" % src_pl)
        #         logger.info("Set monitoring Path:%s" % src_pl)
        #
        #         # Check base_dst_pl path
        #         if not dst_pl.exists():
        #             logger.info("右記PATH存在しません、作成しますか?:%s" % dst_pl)
        #
        #             res = ""
        #             while res not in ("y", "n", "Y", "N"):
        #                 res = input("make dir?(y/n)")
        #             if res in ("y", "Y"):
        #                 dst_pl.mkdir(parents=True, exist_ok=True)
        #             else:
        #                 raise Exception("[Error] dst_pathが存在しないので終了しました")
        #         logger.info("Set exporting Path:%s" % dst_pl)
        #
        #         # ! set into scheduling
        #         observer.schedule(event_handler, src_pl.as_posix(), recursive=True)
        #
        #         # ! タイムスタンプ確認: srcがdstより5秒以上新しければコピー
        #         # to_fmt_in = self._monitor_fmts.get((src_pl, dst_pl), "")
        #         # moniko = self._monitors[src_pl, dst_pl]
        #         # for src_file in src_pl.rglob("*"):
        #         #     if not src_file.is_file():
        #         #         continue
        #         #     dst_file = dst_pl / (src_file.stem + to_fmt_in)
        #         #     src_mtime = src_file.stat().st_mtime
        #         #     if not dst_file.exists() or src_mtime - dst_file.stat().st_mtime >= 5:
        #         #         logger.info(f"[Startup] タイムスタンプ差>=5秒: {src_file.name} -> コピー実行")
        #         #         moniko(src_file.as_posix())
        #     # event_handler = ChangeHandler()
        #     observer.start()
        #     # print("[Info] Start Monitoring")
        #     logger.info("Start Monitoring")
        #     while observer.is_alive():
        #         try:
        #             time.sleep(sleep_sec)
        #         except KeyboardInterrupt:
        #             observer.stop()
        #             break
        #     observer.join()
        # except Exception as e:
        #     raise Exception("Current path: %s" % Path.cwd()) from e

    @property
    def state(self) -> StateMonitor:
        """ return monitoring state """
        return self._state


def _available_observer_backends() -> list[str]:
    backends = ["polling", "native"]
    if FSEventsObserver is not None:
        backends.append("fsevents")
    if KqueueObserver is not None:
        backends.append("kqueue")
    if InotifyObserver is not None:
        backends.append("inotify")
    if WindowsApiObserver is not None:
        backends.append("windowsapi")
    return backends


def _build_cli_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Markuplanguage(.md, .tex) Helper",
        epilog="watchdog observerは既定でpollingです。クラウドストレージの変更追従を優先します。",
    )
    subparsers = parser.add_subparsers(dest="command")

    convert_parser = subparsers.add_parser("convert", help="convert a single file")
    _ = convert_parser.add_argument("src_path", type="str", help="source file path")
    _ = convert_parser.add_argument("dst_dir_apath", help="destination directory or file path")
    _ = convert_parser.add_argument("to_fmt", help="destination format such as png or .png")
    _ = convert_parser.add_argument("--gray", action="store_true", help="convert image to grayscale when supported")
    _ = convert_parser.add_argument("--no-crop", action="store_true", help="disable cropping during conversion")

    monitor_parser = subparsers.add_parser("monitor", help="watch a directory and convert changed files")
    _ = monitor_parser.add_argument("src_dir", help="source directory to monitor")
    _ = monitor_parser.add_argument("dst_dir", help="destination directory")
    _ = monitor_parser.add_argument("to_fmt", help="destination format such as png or .png")
    _ = monitor_parser.add_argument("--gray", action="store_true", help="convert image to grayscale when supported")
    _ = monitor_parser.add_argument("--no-crop", action="store_true", help="disable cropping during conversion")
    _ = monitor_parser.add_argument(
        "--observer",
        default=DEFAULT_OBSERVER_BACKEND,
        choices=_available_observer_backends(),
        help="watchdog observer backend. polling is cloud-storage friendly; native is lighter on local file systems.",
    )
    _ = monitor_parser.add_argument(
        "--sleep-sec",
        type=float,
        default=1.0,
        help="polling interval and main loop sleep time in seconds",
    )
    return parser


def _parse_cli_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = _build_cli_parser()
    args_in = list(sys.argv[1:] if argv is None else argv)
    if args_in and args_in[0] not in ("convert", "monitor", "-h", "--help"):
        args_in = ["convert", *args_in]
    args = parser.parse_args(args_in)
    if args.command is None:
        parser.print_help()
        raise SystemExit(1)
    return args


def _run_convert_cli(args: argparse.Namespace) -> int:
    src_pl = Path(args.src_path)
    if not src_pl.is_absolute():
        src_pl = Path.cwd().joinpath(src_pl)
    logger.debug("fname_str_or_pl:%s" % src_pl)
    monitor_ins = Monitor()
    monitor_ins.convert(
        src_file_apath=src_pl.as_posix(),
        dst_dir_apath=args.dst_dir_apath,
        to_fmt=args.to_fmt,
        is_crop=not args.no_crop,
        gray=args.gray,
    )
    logger.debug("END-END-END")
    return 0


def _run_monitor_cli(args: argparse.Namespace) -> int:
    monitor_ins = Monitor(observer_backend=args.observer)
    monitor_ins.set_monitor(
        src_dir=args.src_dir,
        dst_dir=args.dst_dir,
        to_fmt=args.to_fmt,
        is_crop=not args.no_crop,
        gray=args.gray,
        mk_dst_dir=True,
    )
    monitor_ins.start_monitors(
        sleep_sec=args.sleep_sec,
        observer_backend=args.observer,
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    args = _parse_cli_args(argv=argv)
    if args.command == "monitor":
        return _run_monitor_cli(args)
    return _run_convert_cli(args)


def monitor(argv: list[str] | None = None) -> int:
    args_in = list(sys.argv[1:] if argv is None else argv)
    if not args_in or args_in[0] != "monitor":
        args_in = ["monitor", *args_in]
    return main(args_in)


def convert(argv: list[str] | None = None) -> int:
    logger.debug("sys.argv:%s" % sys.argv)
    return main(argv)


if __name__ == "__main__":
    raise SystemExit(main())
