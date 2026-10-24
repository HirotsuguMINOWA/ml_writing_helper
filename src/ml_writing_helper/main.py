# -*- coding: utf-8 -*-

# target_dir = "app_single/_fig_src"
# _p_dst_dir = "app_single/figs"

###############################################################

import argparse
import platform
import shlex
import shutil
import sys
import time
import unicodedata  # for MacOS NDF
from collections.abc import Callable, Sequence
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

from ml_writing_helper.task_runner.abc_runner import ABCTaskRunner
from ml_writing_helper.enum_cls import MethodToFixEPS, StateMonitor
from ml_writing_helper.task_runner.copy_runner import CopyTask
from ml_writing_helper.task_runner.img_conv_runner import ImgConvTaskStruct
from ml_writing_helper.task_runner.doc_conv_runner import DocConvTask
from ml_writing_helper.converter.doc_converter import (
    DEFAULT_DOC_ENGINE,
    DOC_ENGINES,
    DOC_OUTPUT_FORMATS,
    normalize_input_patterns,
)
from ml_writing_helper.task_runner.scorm_runner import ScormTask
from ml_writing_helper.config import (
    CONFIG_FILENAME,
    DEFAULT_COPY_EXTS,
    DEFAULT_SCORM_PATTERNS,
    DEFAULT_DIFF_SEC,
    DEFAULT_LOG_LEVEL,
    DEFAULT_OBSERVER,
    DEFAULT_SLEEP_SEC,
    LOG_LEVELS,
    OUTPUT_FORMATS,
    ConfigError,
    CopyTaskConfig,
    DocConvTaskConfig,
    ImgConvTaskConfig,
    ScormTaskConfig,
    TaskConfig,
    WatchConfig,
    format_config_error,
    load_config,
    load_config_arg,
    resolve_path,
    strip_dot,
)

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
DEFAULT_OBSERVER_BACKEND: Final[str] = DEFAULT_OBSERVER
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
        self._tasks: list[CopyTask | ABCTaskRunner | ImgConvTaskStruct | DocConvTask | ScormTask] = list()
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

    # def convert_all(
    #         self,
    #         src_dir: str | Path,
    #         dst_dir: str | Path,
    #         to_fmt: str = ".eps",
    #         gray: bool = False,
    # ) -> None:
    #     """
    #     指定したdirの対応拡張子を全て変換する
    #     :param src_dir:
    #     :param dst_dir:
    #     :param to_fmt:
    #     :param gray:
    #     :return:
    #     """
    #     try:
    #         src_pl = Path(src_dir)
    #         del src_dir
    #         dst_pl = Path(dst_dir)
    #         del dst_dir
    #         if not src_pl.exists():
    #             raise Exception("Dir not Found")
    #         if not src_pl.is_dir():
    #             raise Exception("Src is not dir")
    #         files = src_pl.glob("*")
    #         for a_file in files:
    #             print(f"src:{src_pl}, dst:{dst_pl}")
    #             self.convert(src_file_apath=a_file, dst_dir_apath=dst_pl, to_fmt=to_fmt, gray=gray)
    #     except Exception as e:
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

    # def _get_monitor_func(
    #         self,
    #         src_pl: Path,
    #         dst_pl: Path,
    #         to_fmt_in: str,
    #         is_crop: bool = True,
    #         gray: bool = False,
    # ) -> MonitorCallback:
    #     def moniko(path_updated_file: str) -> None:
    #         self.convert(
    #             src_file_apath=path_updated_file,
    #             dst_dir_apath=dst_pl,
    #             to_fmt=to_fmt_in,
    #             is_crop=is_crop,
    #             gray=gray,
    #         )
    #
    #     return moniko

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
        dst_pl = self._get_internal_deal_path(path=dst_dir)
        if mk_dst_dir and not dst_pl.exists():
            dst_pl.mkdir(parents=True, exist_ok=True)
            logger.info(f"Made dir:{dst_pl.as_posix()}")
        ins = ImgConvTaskStruct(
            src_dir_path=src_dir,
            dst_dir_path=dst_dir,
            dst_suffix=to_fmt,
            gray=gray,
            is_crop=is_crop,
            mk_dst_dir=mk_dst_dir
        )
        self._tasks.append(ins)

    def set_doc_conv(
            self,
            src_dir: str | Path,
            dst_dir: str | Path | None = None,
            formats: Sequence[str] = ("pdf",),
            engine: str = DEFAULT_DOC_ENGINE,
            patterns: Sequence[str] | None = None,
            headers: Sequence[str | Path] = (),
            marp_headers: Sequence[str | Path] = (),
            copy_exts: Sequence[str] = (),
            diff_sec: int = 10,
    ) -> None:
        """Markdown/HTML を PDF/HTML/DOCX へ変換するタスク。dst_dir 省略時は src_dir へ出力する。"""
        src_pl = self._get_internal_deal_path(path=src_dir)
        dst_pl = src_pl if dst_dir is None else self._get_internal_deal_path(path=dst_dir)
        dst_pl.mkdir(parents=True, exist_ok=True)
        self._tasks.append(
            DocConvTask(
                src_dir_path=src_pl,
                dst_dir_path=dst_pl,
                output_formats=formats,
                engine=engine,
                input_patterns=patterns,
                header_files=headers,
                marp_header_files=marp_headers,
                copy_exts=copy_exts,
                diff_sec=diff_sec,
            )
        )

    def set_scorm(
            self,
            src: str | Path,
            dst: str | Path | None = None,
            patterns: Sequence[str] = DEFAULT_SCORM_PATTERNS,
            diff_sec: int = 10,
    ) -> None:
        """Markdown の小テストを SCORM 1.2 の ZIP へ変換するタスク。src はファイルかフォルダ。dst 省略時は src のフォルダへ出力する。"""
        src_pl = self._get_internal_deal_path(path=src)
        if dst is None:
            dst_pl = src_pl.parent if src_pl.is_file() else src_pl
        else:
            dst_pl = self._get_internal_deal_path(path=dst)
        (dst_pl.parent if dst_pl.suffix.lower() == ".zip" else dst_pl).mkdir(parents=True, exist_ok=True)
        self._tasks.append(ScormTask(src_path=src_pl, dst_path=dst_pl, patterns=patterns, diff_sec=diff_sec))

    def stop(self) -> None:
        if self._observer is None:
            return
        self._observer.stop()
        logger.info("Observerを停止した")

    def run_once(self) -> None:
        """設定した全タスクを一度だけ実行する（監視はしない）"""
        for task in self._tasks:
            task.run_all_target_files_in_target_dir()
        logger.info("All tasks finished")

    def start_monitors(
            self,
            sleep_sec: int | float = 1,
            observer_backend: str | None = None,
            monitor: bool = True,
    ) -> None:
        """
        Start monitoring change on FS according to set
        : param sleep_sec:
        : param monitor: False なら一通り処理したら監視せずに戻る
        : return:
        """
        if not monitor:
            self.run_once()
            return
        try:
            # ** ObserverをCLIパラで指定可能
            backend = (
                self._observer_backend
                if observer_backend is None
                else _normalize_observer_backend(observer_backend)
            )
            self._observer = _build_observer(backend)
            if self._observer is None: # pyright: ignore[reportUnnecessaryComparison]
                raise Exception("[bug] ObserverインスタンスがNone")
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
            logger.exception(e)
            raise Exception("Current path: %s" % Path.cwd()) from e

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


PROG_NAME: Final[str] = "ml_writing_helper"
# legacy subcommands (the former convert4ml / monitor). Hidden from --help; use --mode instead
CLI_COMMANDS: Final[tuple[str, ...]] = ("convert", "monitor")
# `watch` used to be a subcommand (watch4ml); it is now the default behavior. see _parse_cli_args
LEGACY_WATCH_COMMAND: Final[str] = "watch"
WATCH_MODES: Final[tuple[str, ...]] = ("img_conv", "copy", "doc_conv", "scorm")
# `ml_writing_helper` entry options: exactly one of them selects what to do (dest names)
WATCH_LAUNCHERS: Final[tuple[str, ...]] = ("json", "mode", "conf_maker_web", "conf_maker_cli")
DEFAULT_MONITOR_HINT: Final[str] = "without --monitor, all tasks run once and the command exits"
# options usable only with --mode (dest names)
WATCH_MODE_OPTIONS: Final[tuple[str, ...]] = (
    "src", "dst", "ext", "gray", "no_crop", "engine", "pattern", "header",
    "root", "observer", "sleep_sec", "diff_sec", "log_level",
)
WATCH_EPILOG: Final[str] = f"""examples:
  {PROG_NAME} --mode img_conv --ext pdf --gray          # convert once and exit
  {PROG_NAME} --mode img_conv --ext pdf --monitor       # keep watching for changes
  {PROG_NAME} --mode copy --src ~/Documents/BibTexExported --dst bib
  {PROG_NAME} --mode doc_conv --src docs --dst docs_out --ext pdf --ext html
  {PROG_NAME} --mode scorm --src quiz.md --dst quiz_scorm12.zip
  {PROG_NAME} --mode scorm --src quiz --dst scorm_out --monitor   # rebuild when a quiz .md changes
  {PROG_NAME} --json                       # use ./{CONFIG_FILENAME}
  {PROG_NAME} --json my_tasks.json
  {PROG_NAME} --json '{{"mode": "copy", "src": "a", "dst": "b"}}'
  {PROG_NAME} --conf-maker-web             # create ./{CONFIG_FILENAME} in a web UI
  {PROG_NAME} --conf-maker-cli             # create ./{CONFIG_FILENAME} interactively in the terminal

watchdog observerは既定でpollingです。クラウドストレージの変更追従を優先します。
"""


def _add_common_conv_args(parser: argparse.ArgumentParser) -> None:
    _ = parser.add_argument("--gray", action="store_true", help="convert image to grayscale when supported")
    _ = parser.add_argument("--no-crop", action="store_true", help="disable cropping during conversion")


def _add_common_monitor_args(parser: argparse.ArgumentParser | argparse._ArgumentGroup) -> None:
    # defaults are None so that `watch` can tell whether an option was given. see _apply_monitor_defaults
    _ = parser.add_argument(
        "--observer",
        choices=_available_observer_backends(),
        help=f"watchdog observer backend (default: {DEFAULT_OBSERVER_BACKEND}). "
             "polling is cloud-storage friendly; native is lighter on local file systems.",
    )
    _ = parser.add_argument(
        "--sleep-sec",
        type=float,
        help=f"main loop sleep time in seconds (default: {DEFAULT_SLEEP_SEC})",
    )
    _ = parser.add_argument(
        "--diff-sec",
        type=int,
        help=f"skip a file if src and dst timestamps differ by this many seconds or less (default: {DEFAULT_DIFF_SEC})",
    )
    _ = parser.add_argument(
        "--log-level",
        choices=LOG_LEVELS,
        type=str.upper,
        help=f"console log level (default: {DEFAULT_LOG_LEVEL})",
    )


def _add_watch_args(parser: argparse.ArgumentParser) -> None:
    """Add the main options of `ml_writing_helper` (the former `watch4ml`) to its top level parser."""
    parser.set_defaults(print_watch_help=parser.print_help)

    launch = parser.add_argument_group("how to run (choose one)")
    _ = launch.add_argument(
        "--json",
        nargs="?",
        const=CONFIG_FILENAME,
        metavar="PATH_OR_JSON",
        help=f"run tasks from a json file, or from a JSON string starting with '{{' (default: ./{CONFIG_FILENAME})",
    )
    _ = launch.add_argument(
        "--mode",
        choices=WATCH_MODES,
        help="run one kind of task from CLI parameters below",
    )
    _ = launch.add_argument(
        "--conf-maker-web",
        nargs="?",
        const=CONFIG_FILENAME,
        metavar="PATH",
        help=f"create/edit the json file in a web UI (default: ./{CONFIG_FILENAME})",
    )
    _ = launch.add_argument(
        "--conf-maker-cli",
        nargs="?",
        const=CONFIG_FILENAME,
        metavar="PATH",
        help=f"create/edit the json file interactively in the terminal (default: ./{CONFIG_FILENAME})",
    )
    _ = launch.add_argument(
        "--monitor",
        action="store_true",
        help="keep running and process files when they change (json: \"monitor\": true). "
             f"Usable with all of the above; {DEFAULT_MONITOR_HINT}",
    )

    task = parser.add_argument_group(
        "--mode parameters",
        "img_conv: --src/--dst/--ext once each, --gray, --no-crop. "
        "copy: --src/--dst/--ext repeatable (--src and --dst required). "
        "doc_conv: --src/--dst once each, --ext/--pattern/--header repeatable, --engine. "
        "scorm: --src (Markdown quiz file or dir)/--dst once each, --pattern repeatable",
    )
    _ = task.add_argument(
        "--src", action="append", metavar="DIR",
        help="source dir to watch (img_conv default: fig_src, doc_conv/scorm default: current dir). "
             "scorm: a Markdown quiz file is also accepted",
    )
    _ = task.add_argument(
        "--dst", action="append", metavar="DIR",
        help="output dir, created if missing (img_conv default: fig_gen, doc_conv/scorm default: same as --src). "
             "copy: paired with --src in order, or a single --dst receives all --src. "
             "scorm: a .zip path is also accepted when --src is a file",
    )
    _ = task.add_argument(
        "--ext", action="append", type=strip_dot, metavar="EXT",
        help=f"img_conv: output format {'/'.join(OUTPUT_FORMATS)} (default: pdf). "
             "copy: extension to copy (default: bib). "
             f"doc_conv: output format {'/'.join(DOC_OUTPUT_FORMATS)}, repeatable (default: pdf)",
    )
    _ = task.add_argument("--gray", action="store_true", help="img_conv: convert to grayscale")
    _ = task.add_argument("--no-crop", action="store_true", help="img_conv: disable cropping")
    _ = task.add_argument(
        "--engine", choices=DOC_ENGINES,
        help=f"doc_conv: conversion engine (default: {DEFAULT_DOC_ENGINE}; "
             "auto uses marp/slidev by frontmatter and playwright for mermaid/plantuml)",
    )
    _ = task.add_argument(
        "--pattern", action="append", metavar="GLOB",
        help='doc_conv/scorm: file names to convert, repeatable (default: "*.md"). e.g. "*_marp.md", "*.html"',
    )
    _ = task.add_argument(
        "--header", action="append", metavar="TEX",
        help="doc_conv: TeX header file passed to pandoc for PDF, repeatable",
    )

    common = parser.add_argument_group("--mode common parameters")
    _add_common_monitor_args(common)
    _ = common.add_argument(
        "--root",
        metavar="DIR",
        help="base dir to resolve relative paths (default: current dir)",
    )


def _build_cli_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=PROG_NAME,
        description=(
            "Markuplanguage(.md, .tex) Helper: convert figures / copy files / convert documents / build SCORM 1.2 quizzes. "
            "Choose one of --json, --mode, --conf-maker-web, --conf-maker-cli. "
            "Add --monitor to keep watching for changes; otherwise all tasks run once and the command exits. "
            "With no argument, this help is shown."
        ),
        epilog=WATCH_EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    _add_watch_args(parser)
    parser.set_defaults(command=None)
    return parser


def _build_legacy_parser() -> argparse.ArgumentParser:
    """Parser of the legacy subcommands `convert` / `monitor`. They are kept working but not shown in --help."""
    parser = argparse.ArgumentParser(prog=PROG_NAME)
    subparsers = parser.add_subparsers(dest="command", required=True)

    convert_parser = subparsers.add_parser(
        "convert", prog=f"{PROG_NAME} convert", help="convert a single file and exit (the former convert4ml)"
    )
    _ = convert_parser.add_argument("src_path", type=str, help="source file path")
    _ = convert_parser.add_argument("dst_dir_apath", help="destination directory")
    _ = convert_parser.add_argument("to_fmt", help="destination format such as png or .png")
    _add_common_conv_args(convert_parser)

    monitor_parser = subparsers.add_parser(
        "monitor", prog=f"{PROG_NAME} monitor",
        help="watch one directory and convert changed files (keeps watching without --monitor)",
    )
    _ = monitor_parser.add_argument("src_dir", help="source directory to monitor")
    _ = monitor_parser.add_argument("dst_dir", help="destination directory")
    _ = monitor_parser.add_argument("to_fmt", help="destination format such as png or .png")
    _add_common_conv_args(monitor_parser)
    _add_common_monitor_args(monitor_parser)
    return parser


def _parse_cli_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse argv of `ml_writing_helper`. ``command`` is None when the main (watch) options are used."""
    args_in = list(sys.argv[1:] if argv is None else argv)
    if args_in and args_in[0] == LEGACY_WATCH_COMMAND:
        # `watch4ml watch ...` / `watch4ml ...`: the former subcommand is now the default behavior
        args_in = args_in[1:]
    elif args_in and not args_in[0].startswith("-"):
        if args_in[0] not in CLI_COMMANDS:
            # `ml_writing_helper fig.pptx fig_gen pdf` works like the former convert4ml
            args_in = ["convert", *args_in]
        return _build_legacy_parser().parse_args(args_in)
    return _build_cli_parser().parse_args(args_in)


def _set_log_level(level: str) -> None:
    logger.remove()
    _ = logger.add(sys.stderr, level=level)


def _apply_monitor_defaults(args: argparse.Namespace) -> None:
    if args.observer is None:
        args.observer = DEFAULT_OBSERVER_BACKEND
    if args.sleep_sec is None:
        args.sleep_sec = DEFAULT_SLEEP_SEC
    if args.diff_sec is None:
        args.diff_sec = DEFAULT_DIFF_SEC
    if args.log_level is None:
        args.log_level = DEFAULT_LOG_LEVEL


def _run_convert_cli(args: argparse.Namespace) -> int:
    src_pl = resolve_path(args.src_path, Path.cwd())
    logger.debug("fname_str_or_pl:%s" % src_pl)
    dst_dir = resolve_path(args.dst_dir_apath, Path.cwd())
    dst_dir.mkdir(parents=True, exist_ok=True)
    task = ImgConvTaskStruct(
        src_dir_path=src_pl.parent,
        dst_dir_path=dst_dir,
        dst_suffix=strip_dot(args.to_fmt),
        gray=args.gray,
        is_crop=not args.no_crop,
    )
    task.convert(src_file_apath=src_pl, gray=args.gray, is_crop=not args.no_crop)
    return 0


def _run_monitor_cli(args: argparse.Namespace) -> int:
    _apply_monitor_defaults(args)
    _set_log_level(args.log_level)
    monitor_ins = Monitor(observer_backend=args.observer)
    monitor_ins.set_img_conv(
        src_dir=resolve_path(args.src_dir, Path.cwd()),
        dst_dir=resolve_path(args.dst_dir, Path.cwd()),
        to_fmt=strip_dot(args.to_fmt),
        is_crop=not args.no_crop,
        gray=args.gray,
        mk_dst_dir=True,
    )
    monitor_ins.start_monitors(sleep_sec=args.sleep_sec)
    return 0


def _opt(dest: str) -> str:
    return "--" + dest.replace("_", "-")


_PARAM_ERROR: Final[str] = "パラメータに誤りがあります"


def _watch_config_from_cli(args: argparse.Namespace) -> WatchConfig:
    """Build WatchConfig from `--mode` CLI options. Raises ConfigError."""
    _apply_monitor_defaults(args)
    root = resolve_path(args.root or ".", Path.cwd())
    if not root.is_dir():
        raise ConfigError([f"--root のフォルダが見つかりません\n指定値: \"{args.root}\"\n探した場所: {root}"], title=_PARAM_ERROR)
    srcs: list[str] = args.src or []
    dsts: list[str] = args.dst or []
    exts: list[str] = args.ext or []
    errors: list[str] = []
    tasks: list[TaskConfig] = []

    doc_only = ("engine", "header")
    if args.mode != "doc_conv":
        errors.extend(f"{_opt(flag)} は --mode doc_conv でだけ使えます" for flag in doc_only if getattr(args, flag))
    if args.mode not in ("doc_conv", "scorm") and args.pattern:
        errors.append("--pattern は --mode doc_conv / scorm でだけ使えます")
    if args.mode != "img_conv":
        errors.extend(f"{_opt(flag)} は --mode img_conv でだけ使えます" for flag in ("gray", "no_crop") if getattr(args, flag))

    if args.mode == "doc_conv":
        tasks.append(_doc_conv_config_from_cli(args, root, srcs, dsts, exts, errors))
    elif args.mode == "scorm":
        tasks.append(_scorm_config_from_cli(args, root, srcs, dsts, exts, errors))
    elif args.mode == "img_conv":
        for name, values in (("--src", srcs), ("--dst", dsts), ("--ext", exts)):
            if len(values) > 1:
                errors.append(f"--mode img_conv では {name} は1つだけ指定できます（{len(values)}個指定されています）")
        ext = exts[0] if exts else "pdf"
        if ext not in OUTPUT_FORMATS:
            errors.append(f"--ext には {', '.join(OUTPUT_FORMATS)} のどれかを指定してください（指定値: \"{ext}\"）")
        src_raw = srcs[0] if srcs else "fig_src"
        src = resolve_path(src_raw, root)
        if not src.is_dir():
            errors.append(f"--src のフォルダが見つかりません\n指定値: \"{src_raw}\"\n探した場所: {src}")
        if errors:
            raise ConfigError(errors, title=_PARAM_ERROR, hint=f"相対パスは --root（{root}）を基準に探します")
        tasks.append(
            ImgConvTaskConfig(
                src=src,
                dst=resolve_path(dsts[0] if dsts else "fig_gen", root),
                ext=ext,
                gray=args.gray,
                crop=not args.no_crop,
            )
        )
    else:
        if not srcs or not dsts:
            missing = " と ".join(n for n, v in (("--src", srcs), ("--dst", dsts)) if not v)
            errors.append(f"--mode copy では {missing} を指定してください")
        elif len(dsts) != 1 and len(srcs) != len(dsts):
            errors.append(f"--src（{len(srcs)}個）と --dst（{len(dsts)}個）の数が合いません")
        if errors:
            raise ConfigError(
                errors, title=_PARAM_ERROR,
                hint=f"例: {PROG_NAME} --mode copy --src ~/Documents/BibTexExported --dst bib\n"
                     "--src と --dst は同じ数だけ指定するか、--dst を1つだけ指定してください",
            )
        if len(dsts) == 1:
            dsts = dsts * len(srcs)
        copy_exts = tuple(exts or DEFAULT_COPY_EXTS)
        for src_dir, dst_dir in zip(srcs, dsts):
            src = resolve_path(src_dir, root)
            if not src.is_dir():
                errors.append(f"--src のフォルダが見つかりません\n指定値: \"{src_dir}\"\n探した場所: {src}")
            tasks.append(CopyTaskConfig(src=src, dst=resolve_path(dst_dir, root), exts=copy_exts, diff_sec=args.diff_sec))
        if errors:
            raise ConfigError(errors, title=_PARAM_ERROR, hint=f"相対パスは --root（{root}）を基準に探します")

    return WatchConfig(
        tasks=tasks, observer=args.observer, sleep_sec=args.sleep_sec, log_level=args.log_level, monitor=args.monitor
    )


def _doc_conv_config_from_cli(
        args: argparse.Namespace,
        root: Path,
        srcs: list[str],
        dsts: list[str],
        exts: list[str],
        errors: list[str],
) -> DocConvTaskConfig:
    """Build the doc_conv task of `--mode doc_conv`. Raises ConfigError."""
    for name, values in (("--src", srcs), ("--dst", dsts)):
        if len(values) > 1:
            errors.append(f"--mode doc_conv では {name} は1つだけ指定できます（{len(values)}個指定されています）")
    formats = tuple(dict.fromkeys(exts or ["pdf"]))
    bad = [f for f in formats if f not in DOC_OUTPUT_FORMATS]
    if bad:
        errors.append(f"--ext には {', '.join(DOC_OUTPUT_FORMATS)} を指定してください（指定値: {', '.join(bad)}）")
    patterns = tuple(args.pattern or ["*.md"])
    try:
        _ = normalize_input_patterns(patterns)
    except ValueError as e:
        errors.append(f"--pattern の書き方に誤りがあります（{e}）")
    src_raw = srcs[0] if srcs else "."
    src = resolve_path(src_raw, root)
    if not src.is_dir():
        errors.append(f"--src のフォルダが見つかりません\n指定値: \"{src_raw}\"\n探した場所: {src}")
    headers = tuple(resolve_path(h, root) for h in args.header or [])
    for raw, h in zip(args.header or [], headers):
        if not h.is_file():
            errors.append(f"--header のファイルが見つかりません\n指定値: \"{raw}\"\n探した場所: {h}")
    if errors:
        raise ConfigError(errors, title=_PARAM_ERROR, hint=f"相対パスは --root（{root}）を基準に探します")
    return DocConvTaskConfig(
        src=src,
        dst=resolve_path(dsts[0], root) if dsts else src,
        formats=formats,
        engine=args.engine or DEFAULT_DOC_ENGINE,
        patterns=patterns,
        headers=headers,
        diff_sec=args.diff_sec,
    )


def _scorm_config_from_cli(
        args: argparse.Namespace,
        root: Path,
        srcs: list[str],
        dsts: list[str],
        exts: list[str],
        errors: list[str],
) -> ScormTaskConfig:
    """Build the scorm task of `--mode scorm`. Raises ConfigError."""
    for name, values in (("--src", srcs), ("--dst", dsts)):
        if len(values) > 1:
            errors.append(f"--mode scorm では {name} は1つだけ指定できます（{len(values)}個指定されています）")
    if exts:
        errors.append("--mode scorm では --ext は使えません（出力は常に SCORM 1.2 の .zip です）")
    patterns = tuple(args.pattern or DEFAULT_SCORM_PATTERNS)
    try:
        _ = normalize_input_patterns(patterns)
    except ValueError as e:
        errors.append(f"--pattern の書き方に誤りがあります（{e}）")
    src_raw = srcs[0] if srcs else "."
    src = resolve_path(src_raw, root)
    if not src.exists():
        errors.append(f"--src の Markdown ファイルかフォルダが見つかりません\n指定値: \"{src_raw}\"\n探した場所: {src}")
    dst = resolve_path(dsts[0], root) if dsts else (src.parent if src.is_file() else src)
    if dst.suffix.lower() == ".zip" and src.is_dir():
        errors.append("--src がフォルダのときは --dst に .zip ではなく出力先のフォルダを指定してください")
    if errors:
        raise ConfigError(
            errors, title=_PARAM_ERROR,
            hint=f"例: {PROG_NAME} --mode scorm --src quiz.md --dst quiz_scorm12.zip\n"
                 f"相対パスは --root（{root}）を基準に探します",
        )
    return ScormTaskConfig(src=src, dst=dst, patterns=patterns, diff_sec=args.diff_sec)


def _check_watch_args(args: argparse.Namespace) -> str | None:
    """Check the combination of `ml_writing_helper` options. Returns the chosen launcher, or None for help."""
    launchers = [name for name in WATCH_LAUNCHERS if getattr(args, name) is not None]
    mode_options = [_opt(name) for name in WATCH_MODE_OPTIONS if getattr(args, name) not in (None, False)]
    how_to = (
        "次のどれか1つを指定してください\n"
        "  --json [ファイルのパス または JSON 文字列]\n"
        "  --mode img_conv|copy|doc_conv|scorm [パラメータ...]\n"
        "  --conf-maker-web [ファイルのパス]\n"
        "  --conf-maker-cli [ファイルのパス]\n"
        "変更を監視し続けるには --monitor を付けてください\n"
        f"使い方は {PROG_NAME} --help で確認できます"
    )
    if not launchers:
        if args.monitor and not mode_options:
            raise ConfigError(
                ["--monitor は --json / --mode / --conf-maker-web / --conf-maker-cli と一緒に指定してください"],
                title="起動方法が指定されていません",
                hint=how_to,
            )
        if not mode_options:
            return None
        raise ConfigError(
            [f"{', '.join(mode_options)} は --mode と一緒に指定してください"],
            title="起動方法が指定されていません",
            hint=how_to,
        )
    if len(launchers) > 1:
        raise ConfigError(
            [f"{' と '.join(_opt(n) for n in launchers)} は同時に指定できません"],
            title="パラメータの組み合わせが正しくありません",
            hint=how_to,
        )
    launcher = launchers[0]
    if launcher != "mode" and mode_options:
        raise ConfigError(
            [f"{_opt(launcher)} と一緒に {', '.join(mode_options)} は指定できません"],
            title="パラメータの組み合わせが正しくありません",
            hint="これらは --mode と一緒に使うパラメータです。設定ファイルを使う場合は、ファイルの中に書いてください",
        )
    return launcher


def _maker_save_path(value: str, option: str) -> Path:
    path = resolve_path(value, Path.cwd())
    if path.is_dir():
        path = path / CONFIG_FILENAME
    if not path.parent.is_dir():
        raise ConfigError(
            [f"保存先のフォルダが見つかりません\n指定値: \"{value}\"\n探した場所: {path.parent}"],
            title=f"{option} の保存先に誤りがあります",
        )
    return path


def _resolve_watch_config(args: argparse.Namespace, launcher: str) -> WatchConfig | None:
    """Return the config to watch for the chosen launcher. None means nothing to run."""
    observers = _available_observer_backends()

    if launcher == "json":
        logger.info(f"Load tasks from --json {args.json}")
        return load_config_arg(args.json, cwd=Path.cwd(), available_observers=observers)

    if launcher == "mode":
        return _watch_config_from_cli(args)

    if launcher == "conf_maker_web":
        from ml_writing_helper.webui import run_webui

        save_path = _maker_save_path(args.conf_maker_web, "--conf-maker-web")
        result = run_webui(save_path=save_path, available_observers=observers)
    else:
        from ml_writing_helper.conf_maker_cli import run_cli_maker

        save_path = _maker_save_path(args.conf_maker_cli, "--conf-maker-cli")
        result = run_cli_maker(save_path=save_path, available_observers=observers)
    if not (result.saved and result.start_watch):
        return None
    return load_config(save_path, available_observers=observers)


def _run_watch_config(config: WatchConfig, monitor: bool = False) -> int:
    """Run the tasks. Keep watching if ``monitor`` (CLI --monitor) or ``config.monitor`` (json) is True."""
    _set_log_level(config.log_level)
    monitor_ins = Monitor(observer_backend=config.observer)
    for task in config.tasks:
        if isinstance(task, ImgConvTaskConfig):
            logger.info(f"Figure conversion: {task.src} -> {task.dst} (.{task.ext})")
            monitor_ins.set_img_conv(
                src_dir=task.src,
                dst_dir=task.dst,
                to_fmt=task.ext,
                is_crop=task.crop,
                gray=task.gray,
                mk_dst_dir=True,
            )
        elif isinstance(task, DocConvTaskConfig):
            logger.info(f"Document conversion: {task.src} -> {task.dst} ({', '.join(task.formats)}, engine={task.engine})")
            monitor_ins.set_doc_conv(
                src_dir=task.src,
                dst_dir=task.dst,
                formats=task.formats,
                engine=task.engine,
                patterns=task.patterns,
                headers=task.headers,
                marp_headers=task.marp_headers,
                copy_exts=task.copy_exts,
                diff_sec=task.diff_sec,
            )
        elif isinstance(task, ScormTaskConfig):
            logger.info(f"SCORM 1.2: {task.src} -> {task.dst} ({', '.join(task.patterns)})")
            monitor_ins.set_scorm(src=task.src, dst=task.dst, patterns=task.patterns, diff_sec=task.diff_sec)
        else:
            if not task.dst.suffix:
                task.dst.mkdir(parents=True, exist_ok=True)
            logger.info(f"Copy: {task.src} -> {task.dst} ({', '.join(task.exts)})")
            monitor_ins.set_copy_task(
                src_dir=task.src,
                dst_dir=task.dst,
                src_suffixes=list(task.exts),
                diff_sec=task.diff_sec,
            )
    keep_watching = monitor or config.monitor
    if not keep_watching:
        logger.info("Run all tasks once (add --monitor or \"monitor\": true to keep watching)")
    monitor_ins.start_monitors(sleep_sec=config.sleep_sec, monitor=keep_watching)
    return 0


def _run_watch_cli(args: argparse.Namespace) -> int:
    _set_log_level(args.log_level or DEFAULT_LOG_LEVEL)
    try:
        launcher = _check_watch_args(args)
        if launcher is None:
            args.print_watch_help()
            return 0
        config = _resolve_watch_config(args, launcher)
    except ConfigError as e:
        print(format_config_error(e), file=sys.stderr)
        return 2
    if config is None:
        return 0
    return _run_watch_config(config, monitor=args.monitor)


def main(argv: list[str] | None = None) -> int:
    """Entry point of the `ml_writing_helper` command. --monitor decides run-once or keep-watching."""
    args = _parse_cli_args(argv=argv)
    if args.command == "convert":
        return _run_convert_cli(args)
    if args.command == "monitor":
        return _run_monitor_cli(args)
    return _run_watch_cli(args)


def _main_with_command(command: str, argv: list[str] | None) -> int:
    args_in = list(sys.argv[1:] if argv is None else argv)
    if not args_in or args_in[0] != command:
        args_in = [command, *args_in]
    return main(args_in)


_ENTRY_REMOVED: Final[str] = f"廃止。watch4ml/convert4ml は {PROG_NAME} コマンド（main）に統合された"


@removals.remove(message=_ENTRY_REMOVED)
def watch(argv: list[str] | None = None) -> int:
    return _main_with_command(LEGACY_WATCH_COMMAND, argv)


@removals.remove(message=_ENTRY_REMOVED)
def monitor(argv: list[str] | None = None) -> int:
    return _main_with_command("monitor", argv)


@removals.remove(message=_ENTRY_REMOVED)
def convert(argv: list[str] | None = None) -> int:
    logger.debug("sys.argv:%s" % sys.argv)
    return main(argv)


if __name__ == "__main__":
    raise SystemExit(main())
