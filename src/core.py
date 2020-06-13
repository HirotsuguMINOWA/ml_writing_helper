# -*- coding: utf-8 -*-


# target_dir = "app_single/_fig_src"
# _p_dst_dir = "app_single/figs"

###############################################################

import os
import shlex
# import ftplib
import shutil
import subprocess
import sys
import time
from enum import Enum
from pathlib import Path
from subprocess import check_output, STDOUT

from typing import Tuple
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer
# coding:utf-8

# ログのライブラリ
import logging
from logging import getLogger, StreamHandler, Formatter

# --------------------------------
# 1.loggerの設定
# --------------------------------
# loggerオブジェクトの宣言
logger = getLogger("LogTest")

# loggerのログレベル設定(ハンドラに渡すエラーメッセージのレベル)
logger.setLevel(logging.DEBUG)

# --------------------------------
# 2.handlerの設定
# --------------------------------
# handlerの生成
stream_handler = StreamHandler()

# handlerのログレベル設定(ハンドラが出力するエラーメッセージのレベル)
stream_handler.setLevel(logging.DEBUG)

# ログ出力フォーマット設定
# handler_format = Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
# handler_format = Formatter('%(asctime)-15s - %(name)s - %(levelname)s - %(message)s')
handler_format = Formatter('%(asctime)s[%(levelname)s] %(message)s', datefmt='%H:%M:%S')
stream_handler.setFormatter(handler_format)

# --------------------------------
# 3.loggerにhandlerをセット
# --------------------------------
logger.addHandler(stream_handler)


# --------------------------------
# ログ出力テスト
# --------------------------------
# logger.debug("Hello World!")


# 出力がepsの場合、監視folderにpngなど画像ファイルが書き込まれたらepsへ変換するコードをかけ

class Tool:
    def pdfcrop(self, src_pl, dst_pl):
        """

        :param src_pl:
        :param dst_pl:
        :return:
        """
        pass

    def img_magick(self, src_pl, dst_pl):
        """

        :param src_pl:
        :param dst_pl:
        :return:
        """
        pass


class ChangeHandler(FileSystemEventHandler):
    """
    - Part:
        - event receiver : start trigger to convert
        - convert main method
        - convert sub methods
        - check_external_sub_modules: this checkes exists and proposes to install sub modules. e.g.: gs, pdf2eps and so on.
    """
    msg_event_start = "-------------------  Start Event  -------------------"
    app_in = (".jpeg", ".jpg", ".png")  # 本アプリのinput拡張子
    imagic_fmt_conv_in = (".png", ".jpg", ".jpeg", ".png", ".eps", ".svg", ".pdf")  # inにPDFはOK # TODO: 共通クラス化しろ
    imagic_fmt_conv_out = (".png", ".jpg", ".jpeg", ".png", ".eps", ".svg")
    mermaid_fmt_in = (".svg", ".png", ".pdf")
    plantuml_fmt_out = (".png", ".svg", ".pdf", ".eps", ".html", ".txt", ".tex")
    # FIXME: 下記２つのsofficeのlistは要整理
    paths_soffice = ['soffice',  # pathが通っている前提の場合
                     '/Applications/LibreOffice.app/Contents/MacOS/soffice',
                     # '/Applications/LibreOffice Vanilla.app/Contents/MacOS/soffice' # srcがないと言われる
                     ]
    _ppaths_soffice = [
        Path('soffice'),
        Path('/Applications/LibreOffice.app/Contents/MacOS/soffice')
    ]
    _ext_pluntuml = [".pu", ".puml"]

    # def __init__(cls
    #              , monitoring_dir
    #              , output_dir=None
    #              , _to_fmt="png"
    #              , export_fmts=["png", "eps", "pdf"]):
    def __init__(self):
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
        self._src_pl = None
        self._dst_pl = None
        self._to_fmt = None
        self._monitors = {}
        self._ppaths_soffice = [Path(x) for x in self.paths_soffice]
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
    # def which(name) -> Tuple[bool, str]:
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
    def util_manage_tmp_path(path: Path, is_remove_tmp_str=False, suffix_new=None) -> Path:
        """
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

    # @staticmethod
    # def util_update_dst_path(base_dst_pl: Path, fname_str_or_pl, fmt) -> Path:
    #     """
    #     Destination path modifier
    #     - base_dst_plがfilename,extを含んでいれば何もしない
    #     - bast_dst_plが上記含んでなければ追加して完全系へ。
    #     :param base_dst_pl: dst_plを基本設定
    #     :param fname_str_or_pl: ファイル名.多くはsrc_plをそのまま渡せばよい
    #     :type fname_str_or_pl: Path | str
    #     :param fmt: dst_pathに付記したい拡張子
    #     :return: dst_path, tmp_dst_path
    #     :rtype: Path
    #     """
    #     if not base_dst_pl.is_dir():
    #         return base_dst_pl
    #
    #     base_dst_pl = base_dst_pl.resolve()  # 相対PATH-> abs. path
    #     if isinstance(fname_str_or_pl, Path):
    #         # conv path to str
    #         filename = fname_str_or_pl.stem
    #
    #     if base_dst_pl.is_dir():
    #         base_dst_pl = base_dst_pl.joinpath(filename + fmt)
    #     # else:
    #     #     base_dst_pl = base_dst_pl.with_suffix(fmt)
    #
    #     if is_tmp:
    #         # Tempolized
    #         return base_dst_pl, base_dst_pl.with_name(base_dst_pl.stem + "_tmp")
    #     else:
    #         return base_dst_pl, None

    @classmethod
    def _crop_img(cls, src_img_pl: Path, dst_pl: Path) -> Path:
        """
        image(pdf/png,jpeg?)をcroppingする
        :param p_src:
        :param dst_pl:
        :return: 変換後のpath名
        :rtype: pathlib.Path
        """
        """ Calc path of base_dst_pl """
        # path_dst = pathlib.Path(dir_dst) / fname_str_or_pl.name
        # path_dst = pathlib.Path(dir_dst) / plib_src.with_suffix("." + cls._to_fmt).name
        if not src_img_pl.exists():
            print("[Error] %s not found" % src_img_pl)
            return Path()
        # if dst_pl.is_dir():
        #     dst_pl = dst_pl.joinpath(src_pl.name)  # if the path is dir, set src_filename_stem converted

        """ crop white space """
        # if src_pl.suffix not in [".png", ".jpeg", ".jpeg"]:
        #     logger.error("source file is not 対応してないImage magickに。")
        #     return Path()

        if src_img_pl.suffix == ".pdf":
            """
            時々pdfの自動cropは不可。原因不明。
            #TODO: ただ、sample_srcのpdfはcropできるのに、fig_genに入ったpdfはpdfcropできない。要原因を調べる事。ImageMagicで変換したPDFはcropできず？？
             - pdfcrop: AutoCrop可能. 引数にdstは指定しない、指定したsrc名+"-crop"が生成される
             - http://would-be-astronomer.hatenablog.com/entry/2015/03/26/214633
            """
            cmd_name = shutil.which("pdfcrop")
            if cmd_name is None:
                logger.error("pdfcrop not found")
            cmd = "{cmd_name} {path_in} {path_out}".format(cmd_name=cmd_name, path_in=src_img_pl, path_out=dst_pl)
            # rename cropped pdf(*_crop.pdf) to dst_pl
            res_msg = cls._run_cmd(cmd, short_msg="Cropping CMD:")
            if res_msg:
                logger.info(res_msg)
            # if dst_pl.exists():
            #     dst_pl.unlink()
            # shutil.move(src=src_img_pl.with_name(src_img_pl.stem + "-crop.pdf"), dst=dst_pl)

            # imagemagick mogrifyを使う->失敗
        #     shutil.copy(src_pl, dst_pl)
        #     cmd = "magick mogrify -format pdf -define pdf:use-trimbox=true {dst_path}".format(dst_path=dst_pl)
        elif src_img_pl.suffix in (".png", ".jpg", ".jpeg", ".eps"):  # pdfのcropはできない
            cls.img_magick(
                src_pl=src_img_pl,
                dst_pl=dst_pl
            )
            # cmd_name = "convert"
            # # p_conv = Path("/usr/local/bin/convert")
            # # if not p_conv.exists():
            # #     raise Exception("%s not found" % p_conv)
            # # if src_pl.suffix == ".pdf":
            # #     # url: https://www.imagemagick.org/discourse-server/viewtopic.php?t=15667
            # #     # src: mogrify -format pdf -define pdf:use-trimbox=true /TEMP/foo.pdf
            # #     trim_cmd = "-mogrify -format pdf -define pdf:use-trimbox=true"
            # # else:
            # trim_cmd = "-trim"
            # cmd = "{cmd_name} {path_in} {trim_cmd} {path_out}".format(cmd_name=cmd_name,
            #                                                           trim_cmd=trim_cmd,
            #                                                           path_in=src_img_pl,
            #                                                           path_out=dst_pl)
            # res_msg = cls._run_cmd(cmd, short_msg="Cropping CMD: %s" % cmd)
            # if res_msg:
            #     logger.info(res_msg)
        else:
            # new_path = shutil.move(fname_str_or_pl.as_posix(), dir_dst)
            logger.error("対応していないFormatをcroppingしようとして停止: %s" % src_img_pl)
            return Path()

        # if shutil.which(cmd_name) is None:
        #     logger.error("Conversion cmd(%s) is not in path " % cmd)
        # logger.debug("Cropping CMD: " + cmd)
        # tokens = shlex.split(cmd)
        # subprocess.run(tokens)
        # output = check_output(tokens, stderr=STDOUT).decode("utf8")
        # return Path(dst_pl.with_name(src_pl.name).with_suffix("%s" % to_img_fmt))
        return dst_pl

    @staticmethod
    def _run_cmd(cmd: str, short_msg="", is_print=True) -> str:
        """
        コマンド(CLI)の実行
        :param cmd:
        :param is_print:
        :return: output of rum
        """
        if is_print:
            logger.debug("CMD(%s):%s" % (short_msg, cmd))
        tokens = shlex.split(cmd)
        try:
            output = check_output(tokens, stderr=STDOUT).decode("utf8")
        except Exception as e:
            logger.error(e)
            return "Error occurred"
        if is_print:
            logger.debug("Output(%s):%s" % (short_msg, cmd))
        return output

    @classmethod
    def img_magick(cls, src_pl, dst_pl, do_trim=True, is_eps2=True):
        """
        Image Magicコマンド
        :param src_pl:
        :param dst_pl:
        :param do_trim:
        :param is_eps2:
        :return:
        """
        if do_trim and src_pl.suffix == dst_pl.suffix:
            logger.warning("ImageMagick変換において、Trim(Crop)付きで別Formatへ変換すると、Crop失敗する可能性あり")
        # TODO: in,outのfmtの要チェック?いらんかも
        conv_name = "convert"
        conv_path = shutil.which(conv_name)
        if not conv_path:
            logger.error("convert command not found")
            return None
        head = ""
        if dst_pl.suffix == ".eps" and is_eps2:
            head = "eps2:"
        param = ""
        if do_trim:
            param = "-trim"
        cmd = "{cmd_path} {src} {param} {head}{dst}".format(
            cmd_path=conv_path
            , param=param
            , head=head
            , src=src_pl
            , dst=dst_pl
        )
        cls._run_cmd(cmd, "Convert by ImageMagic")
        return dst_pl

    # @classmethod
    # # def _conv2img(cls, src_pl: Path, dst_pl: Path, fmt_if_dst_without_ext=None, decode="utf8") -> Path:
    # def _conv2img(cls, src_pl: Path, dst_pl: Path, decode="utf8") -> Path:
    #     """
    #     [要廃棄]Image magick等による画像変換
    #         - 代わりにimg_magickメソッドを使え
    #     - FIXME: 要廃止。cropメソッドでImageMagickを使えるのなら、そちらでcropと変換の両方を実現できるから！！！！
    #     - IN: jpeg, png, pdf
    #     - OUT: jpeg, png, eps, pdf
    #     :param src_pl:
    #     :param dst_pl:
    #     :param fmt_if_dst_without_ext: pl_dst_or_dirがdirの場合、出力先に生成するPATHのファイルの拡張子になる。
    #     :return:
    #     """
    #
    #     # Check src file exists
    #     if not src_pl.exists():
    #         raise Exception("Input image not exists:%s" % src_pl)
    #     # dst_pl, _ = cls.util_update_dst_path(base_dst_pl=dst_pl, fname_str_or_pl=src_pl,
    #     #                                      fmt=fmt_if_dst_without_ext)
    #     # if dst_pl.is_dir():
    #     #     dst_pl = dst_pl / src_pl.stem.join(fmt_if_dst_without_ext)
    #     #################################################
    #     # 同一FormatはIgnore
    #     if src_pl.suffix == dst_pl.suffix:
    #         logger.info("同一formatなので画像変換はせず、コピーだけ行う(srcとdstが同じでなければ)")
    #         if src_pl != dst_pl:
    #             shutil.copy(src_pl, dst_pl)
    #         return dst_pl
    #
    #     need_conv = True
    #     # cmd_conv = "pdftops"
    #     # if src_pl.suffix == dst_pl.suffix:
    #     #     if shutil.which(cmd_conv) != "":
    #     #         logger.info("pdftopsで変換します")
    #     #         cmd = "{cmd_conv} -eps {src} {dst}".format(
    #     #             cmd_conv=cmd_conv,
    #     #             src=src_pl,
    #     #             dst=dst_pl
    #     #         )
    #     #         need_conv = False
    #     #     else:
    #     #         logger.info("pdf->epsへの変換はpdftopsコマンドを推奨。pdftopsコマンドへpathが通ってません")
    #     if need_conv:
    #         #     cmd_conv = "convert"
    #         #     logger.info("ImageMagickで変換します")
    #         #     if dst_pl.suffix == ".eps":
    #         #         head = "eps2:"
    #         #     else:
    #         #         head = ""
    #         #     cmd = "{cmd_conv} {src} {head}{dst}".format(
    #         #         cmd_conv=cmd_conv
    #         #         , head=head
    #         #         , src=src_pl
    #         #         , dst=dst_pl
    #         #     )
    #         # logger.debug("CMD(%s): %s" % (cmd_conv, cmd))
    #         # tokens = shlex.split(cmd)
    #         # # subprocess.run(tokens)
    #         # output = check_output(tokens, stderr=STDOUT).decode(decode)
    #         # logger.debug("Output: %s" % output)
    #         dst_pl = cls.img_magick(src_pl, dst_pl)
    #     return dst_pl

    # @classmethod
    # def _conv2eps(cls, src_pl: Path, pl_dst_dir: Path, del_src=True) -> Path:
    #     """
    #
    #     :param src_pl:
    #     :param pl_dst_dir: directoryのみ
    #     :param del_src: del src of as tmp
    #     :return: 変換後のPATH
    #     """
    #     if src_pl.suffix not in (".jpeg", ".jpg", ".png", ".pdf"):
    #         return
    #     print("[Info] Convert to eps")
    #
    #     if pl_dst_dir.is_dir():
    #         pl_dst_dir = pl_dst_dir.joinpath(src_pl.stem + ".eps")
    #     # else:
    #     #     raise Exception("ディレクトリ指定して下さい。")
    #     elif pl_dst_dir.suffix != ".eps":
    #         # raise Exception("出力ファイルの拡張子も.epsにして下さい")
    #         print("[Warning]出力拡張子を.epsに変えました")
    #         pl_dst_dir = pl_dst_dir.with_suffix(".eps")
    #     pl_dst_dir = cls._conv2img(src_pl, pl_dst_dir, fmt_if_dst_without_ext="png")
    #     if del_src:
    #         src_pl.unlink()
    #     return pl_dst_dir

    @classmethod
    def _conv_plantuml(cls, src_pl: Path, dst_pl: Path):
        cls._cmd_plantuml = "plantuml"
        path_cmd = shutil.which(cls._cmd_plantuml)
        if path_cmd is None:
            logger.error("%s not found. Can't convert from PlantUML" % cls._cmd_plantuml)
            return
        # todo: plantuml conv.
        if dst_pl.suffix not in cls.plantuml_fmt_out:
            print("[ERROR] Indicated Formatは未対応 in coverting with plantuml")
            return
        cmd = "{cmd_pu} -o {dst_abs_dir_only} -t{fmt} {src}".format(
            cmd_pu=cls._cmd_plantuml,
            src=src_pl.as_posix(),
            dst_abs_dir_only=dst_pl.parent,
            fmt=dst_pl.suffix[1:]
        )
        res = cls._run_cmd(cmd=cmd, short_msg="Converting with %s" % cls._cmd_plantuml)
        print("Result:%s" % res)

    @classmethod
    def conv_slide_with_crop_both(cls, src_pl: Path, dst_pl: Path, is_crop=True, via_ext=".png"):
        """

        :param src_pl:
        :param dst_pl:
        :param is_crop:
        :param via_ext:
        :return:
        """
        is_mediate = False
        if dst_pl.suffix in (".pdf", ".eps"):
            """
            - 注意) PowerPoint/LibreOffice(.odp)は.pdf/.epsへ変換してPDFCropで失敗する。そのため、一度、.png経由する。   
            """
            # warn = """
            #   [Warning] スライドにはPowerPoint形式(.pptx)に変換して使ってください。
            #   """
            # # print(warn)
            logger.warning(".ppt(x)/.odpの.pdf/.epsへの変換は%s経由で変換します。" % via_ext)
            is_mediate = True
            dst_tmp_pl = dst_pl.parent.joinpath(dst_pl.stem + via_ext)
        else:
            dst_tmp_pl = dst_pl

        cls._conv_slide(src_pl=src_pl, dst_pl=dst_tmp_pl)
        if is_crop:
            if is_mediate:
                cls._conv_with_crop_both(dst_tmp_pl, dst_pl)
            else:
                cls._crop_img(src_img_pl=dst_tmp_pl, dst_pl=dst_pl)

        ### Del mediate file
        if is_mediate:
            dst_tmp_pl.unlink()

    @classmethod
    def _conv_slide(cls, src_pl: Path, dst_pl: Path):
        """

        :param src_pl:
        :param dst_pl: ファイル/folderまでのPATH.場合分けが必要
        :param to_fmt:
        :return:
        """
        for p_soffice in cls._ppaths_soffice:  # type: Path
            if p_soffice.exists():
                cmd = "'{path_soffice}' --headless --convert-to {dst_ext} --outdir '{out_dir}' '{path_src}'".format(
                    # cmd = "'{path_soffice}' --headless --convert-to {dst_ext} {path_src}".format(
                    path_soffice=p_soffice
                    , dst_ext=dst_pl.suffix[1:],  # eliminate first "."
                    # , out_dir=dir_dst
                    out_dir=dst_pl.parent.as_posix()
                    , path_src=src_pl
                )
                break

        if src_pl.suffix in (".pptx", ".ppt"):
            logger.warning(
                msg="(Math) symbols may be VANISH!!!!. Please confirm generated product not to disappear symbols")
        # output = cls._run_cmd(cmd)
        output = cls._run_cmd(cmd, "CMD(slide2img):")
        # logger.debug("CMD(slide2img):" + cmd)
        # tokens = shlex.split(cmd)
        # subprocess.run(tokens)
        # output = check_output(tokens, stderr=STDOUT).decode("utf8")
        logger.debug("Output: %s" % output)
        if output == "Error: source file could not be loaded\n":
            """なぜかLO Vanillaで出現？"""
            # raise Exception("")
            logger.error("なぜかLO Vanillaで出現？")

        # Change gen file name
        pl_out = dst_pl.parent.joinpath(src_pl.stem + dst_pl.suffix)
        shutil.move(pl_out, dst_pl)

    @classmethod
    def _conv_with_crop_both(cls, src_pl: Path, dst_pl: Path):
        """
        cropとconvertするメソッド
        - ImageMagickのcropと画像変換を合わせ使う
        - ほぼ、ImageMagickだけでよく、PDF-Outのみ別分岐処理となった
        :param src_pl:
        :param dst_pl:
        :return: 変換後のpath名
        :rtype: pathlib.Path
        """
        """ Calc path of base_dst_pl """
        # path_dst = pathlib.Path(dir_dst) / fname_str_or_pl.name
        # path_dst = pathlib.Path(dir_dst) / plib_src.with_suffix("." + cls._to_fmt).name
        if not src_pl.exists():
            print("[Error] %s not found" % src_pl)
            return
        # if dst_pl.is_dir():
        #     dst_pl = dst_pl.joinpath(src_pl.name)  # if the path is dir, set src_filename_stem converted
        if src_pl.suffix in cls.imagic_fmt_conv_in \
                and dst_pl.suffix in cls.imagic_fmt_conv_out \
                and dst_pl.suffix not in (".pdf", ".eps"):
            """
            - (in,out)共にpdfのcropはできない. epsのin?,outは可
            - 処理対象
                - 一般画像(jpeg, epsなど)
                - pdf: inのみ。
            """
            cls.img_magick(src_pl, dst_pl)
        else:
            """
            出力がPDFの場合のみ2段階変換(conv,crop)を実施
            pdf->image: OK!!!
                $ convert test-crop.pdf eps2:test-crop.eps
                ＞＞ test-crop.eps という、トリミングされたepsができる。
                http://would-be-astronomer.hatenablog.com/entry/2015/03/26/214633
            pdfcrop機能しない事が多い？img_magickと併用でcropする事
            """
            cls.img_magick(src_pl, dst_pl, do_trim=True)  # TODO: 現状ImgMagickの-trimでPDFもcropされている！！
            cls._crop_img(dst_pl, dst_pl)
        # else:
        #     logger.error("_conv_with_crop_bothがCalled.しかし何も変換せず。src:%s,dst:%s" % (src_pl, dst_pl))

    def show_warning_tool(self):
        """
        必要なツールの有無の確認？
        :return:
        """
        # TODO: 面倒なんとか最も簡単な方法できないか

    @classmethod
    def fix_eps(cls, src_pl: Path) -> Path:
        """
        Repair eps corruption
        - epsがlatex上でずれる問題の修正
        - epstopdf,pdf2epsを使うと「画質が落ちる?」
        :param src_pl:
        :return:
        """

        class MethodToFixEPS(Enum):
            gs = "gs"
            eps_pdf_converter = "eps2pdf&pdf2eps"

        method = MethodToFixEPS.eps_pdf_converter  # Current method
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
                cmd = "{gs} -dNOPAUSE -dBATCH -q -sDEVICE=bbox {src}".format(gs=path_cmd_gs, src=src_pl)
                out_msg = cls._run_cmd(
                    cmd=cmd
                    , short_msg="Repair .eps by Ghost Script"
                )
                if out_msg != "":
                    logger.info(out_msg)  # 生成したbbox情報など呈示
                    return None

        elif method == MethodToFixEPS.eps_pdf_converter:
            """ 効果アリ """
            path_epstopdf = "epstopdf"
            path_pdftops = "pdftops"
            path_epstopdf = shutil.which(path_epstopdf)
            path_pdftops = shutil.which(path_pdftops)
            if path_epstopdf is None or path_epstopdf == "" or path_pdftops is None or path_pdftops == "":
                # Failed due to commands are absent
                logger.error(".epsファイルを修正しようとしましたが、%sのコマンドにPATHが非存在/通ってません。" % (path_pdftops, path_epstopdf))
                return None

            # Generate tmp
            tmp_pl = cls.util_manage_tmp_path(src_pl)
            tmp_pl = tmp_pl.with_suffix(".pdf")

            # EPS to PDF
            cmd = "{path_epstopdf} -o={tmp} {src}".format(
                path_epstopdf=path_epstopdf,
                # path_pdftops=path_pdftops,
                tmp=tmp_pl,
                src=src_pl
            )
            out_msg = cls._run_cmd(
                cmd=cmd
                , short_msg="Repair1/2(.eps->.pdf):"
            )
            if out_msg != "":
                logger.error(out_msg)
                return None

            cmd = "{path_pdftops} -eps {tmp} {src}".format(
                path_pdftops=path_pdftops,
                tmp=tmp_pl,
                src=src_pl
            )
            out_msg = cls._run_cmd(
                cmd=cmd
                , short_msg="Repair2/2(.pdf->.eps):"
            )
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

    # @classmethod
    # def _conv_and_crop(cls, src_pl: Path, dst_pl: Path) -> Path:
    #     """
    #     イメージを変換して、cropする。
    #     - Step by Stepな変換。もし、変換, cropの両方を_conv_with_crop_bothメソッドで行え
    #     - (注意) img変換とcropを同時にimagemagickで実現する別methodを設けた
    #     :param cls:
    #     :param src_pl:
    #     :param dst_pl:
    #     :param to_fmt:
    #     :return:
    #     """
    #     need_conv = True
    #     # path_dst = cls._conv_with_crop_both(src_pl=src_pl, dst_pl=dst_pl)  # conv both crop and imgconv stimulatelly
    #     # if path_dst:
    #     #     need_conv = False
    #     """ 上記、変換が失敗した場合 """
    #     if need_conv:
    #         tmp_dst_pl = cls.util_manage_tmp_path(dst_pl)
    #         # dst_pl2, tmp_dst_pl = cls.util_update_dst_path(base_dst_pl=src_pl, fname_str_or_pl=dst_pl, fmt=to_fmt,
    #         #                                                is_tmp=True)
    #         # 変換後にcrop
    #         path_dst = cls._conv2img(src_pl=src_pl, dst_pl=tmp_dst_pl)  # , fmt_if_dst_without_ext=fmt)
    #         path_dst = cls._crop_img(src_img_pl=path_dst, dst_pl=dst_pl)
    #
    #         # Crop後に変換
    #         # path_dst = cls._crop_img(src_img_pl=src_pl, dst_pl=tmp_dst_pl)
    #         # path_dst = cls._conv2img(src_pl=path_dst, dst_pl=dst_pl)  # , fmt_if_dst_without_ext=fmt)
    #
    #         #
    #         # 下記で解像度向上させようとしたが、jpeg,pngがcropされない
    #         #
    #         # if src_pl.suffix == ".pdf":
    #         #     """
    #         #     - pdfはcropできないので、先に画像変換する。変換後があわよくばcrop_imgに対応したフォーマットなら画質落としにくい。
    #         #     - 一方、上記でなければ、先にcropする場合、元のソース画像の画像変換を行わないため、画質が落ちないと思われる
    #         #     """
    #         #     path_dst = cls._conv2img(src_pl=src_pl, dst_pl=tmp_dst_pl)  # , fmt_if_dst_without_ext=fmt)
    #         #     path_dst = cls._crop_img(src_pl=path_dst, dst_pl=dst_pl)
    #         # else:
    #         #     tmp_dst_pl = tmp_dst_pl.with_suffix(src_pl.suffix)
    #         #     path_dst = cls._crop_img(src_pl=src_pl, dst_pl=tmp_dst_pl)
    #         #     path_dst = cls._conv2img(src_pl=path_dst, dst_pl=cls.util_manage_tmp_path(dst_pl,
    #         #                                                                               is_remove_tmp_str=True))  # , fmt_if_dst_without_ext=fmt)
    #         if tmp_dst_pl.exists():
    #             tmp_dst_pl.unlink()
    #     if path_dst:
    #         return path_dst
    #     else:
    #         return None
    #     #     need_conv = False
    #     # if need_conv:
    #     #     return None  # Faild
    #     # else:
    #     #
    #     # return path_dst

    @classmethod
    # def conv_mermaid(cls, src_pl: Path, dst_pl: Path, to_fmt=".svg") -> Tuple[bool, Path]:
    def conv_mermaid(cls, src_pl: Path, dst_pl: Path) -> Tuple[bool, Path]:
        """
        Mermaid(*_mermaid.md) Conversion
        mermaid markdownを変換
        - dst_dir: cwdに生成されるので、生成時にchdirで出力先を調整しなければならない。
        :param src_pl:
        :param dst_pl:
        :param to_fmt:
        :return:
        """
        # Check on format
        if dst_pl.suffix not in (".svg", ".png", ".pdf"):
            logger.error("Cannot convert file type:%s. Skipped" % dst_pl.suffix)
            return False, None

        """ Check exists of mermaid-cli """
        cmd_name_mermaid = "mmdc"
        cmd_name_mermaid = shutil.which(cmd_name_mermaid)
        if cmd_name_mermaid == "":
            msg = """
                mermaidコマンドに当たるmmdcにpathが通っていません。
                要PATH通し/インスト（下記参考）
                npm install -g mermaid
                npm install -g mermaid.cli
                """
            logger.error(msg)
            return

        """  
        Usage: mmdc [options]

        Options:
          -V, --version                                   output the version number
          -t, --theme [theme]                             Theme of the chart, could be default, forest, dark or neutral. Optional. Default: default (default: "default")
          -w, --width [width]                             Width of the page. Optional. Default: 800 (default: "800")
          -H, --height [height]                           Height of the page. Optional. Default: 600 (default: "600")
          -i, --input <input>                             Input mermaid file. Required.
          -o, --output [output]                           Output file. It should be either svg, png or pdf. Optional. Default: input + ".svg"
          -b, --backgroundColor [backgroundColor]         Background color. Example: transparent, red, '#F0F0F0'. Optional. Default: white
          -c, --configFile [configFile]                   JSON configuration file for mermaid. Optional
          -C, --cssFile [cssFile]                         CSS file for the page. Optional
          -p --puppeteerConfigFile [puppeteerConfigFile]  JSON configuration file for puppeteer. Optional
          -h, --help                                      output usage information
        """

        # dst_pl_full, _ = cls.util_update_dst_path(base_dst_pl=dst_pl, fname_str_or_pl=src_pl, fmt=to_fmt)

        cmd = "{cmd_mmdc} -i {src_path} -o {dst_fullpath_ok}".format(
            cmd_mmdc=cmd_name_mermaid,
            dst_fullpath_ok=dst_pl,
            src_path=src_pl.as_posix()
        )
        # FIXME:
        out_msg = cls._run_cmd(
            cmd=cmd
            , short_msg="Converting mermaid file"
        )
        # # Move generated file
        # gen_path = src_pl.with_name(dst_pl.name)
        # shutil.move(gen_path, dst_pl)
        if out_msg != "":
            logger.error("Failed conversion into mermaid image:%s" % src_pl)
            return False, None
        else:
            logger.info("Succeeded conversion on mermaid:%s" % src_pl)
            return True, dst_pl

    @classmethod
    def conv_pandoc(cls, src: Path, dst: Path):
        """
        Pandocを用いた変換
        :param src:
        :param dst:
        :return: None
        """
        cmd_pandoc = "pandoc"
        if not shutil.which(cmd_pandoc):
            logger.error("command %s was not found" % cmd_pandoc)
            return None
        # pandoc is exists after here
        cmd = cmd_pandoc + "-N -TOC-F pandoc-citeproc -F pandoc-crossref {src}".format(src=src)

    @classmethod
    def conv_mermaid_with_crop(cls, src_pl: Path, dst_pl: Path) -> Tuple[bool, Path]:
        """
        mermaid markdownを変換 及び 特定のformatへ変換する
        :param src_pl:
        :param dst_pl:
        :param to_fmt:
        :return: Success?, Output file's path
        """
        if dst_pl.suffix in cls.mermaid_fmt_in:
            tmp_fmt = dst_pl.suffix
        else:
            tmp_fmt = ".png"  # ImageMagickが対応しておりcropが利くフォーマット
        # base_dst_pl filename
        # dst_fname = base_dst_pl.stem
        # dst_pl_full, _ = cls.util_update_dst_path(base_dst_pl=dst_pl, fname_str_or_pl=src_pl, fmt=tmp_fmt)
        # Conversion
        res, tmp_dst_pl = cls.conv_mermaid(
            src_pl=src_pl,
            dst_pl=dst_pl)  # ,
        # to_fmt=tmp_fmt)
        """ Conversion: mermaid """
        if not res:
            return False, None
        """ Cropping image """
        tmp_dst_pl = cls._crop_img(src_img_pl=tmp_dst_pl, dst_pl=dst_pl)
        if tmp_dst_pl is None:
            logger.error("Failed crop: %s" % src_pl)
            return False, None

        if src_pl.suffix == dst_pl.suffix:
            return True, tmp_dst_pl

        """ Image conversion"""
        tmp_dst_pl = cls.img_magick(src_pl=tmp_dst_pl, dst_pl=dst_pl)
        if tmp_dst_pl is None:
            return False, None
        else:
            return True, tmp_dst_pl

    def convert(self, src_file_apath, dst_dir_apath, to_fmt=".png", is_crop=True):  # , _to_fmt="pdf"):
        """
        ppt->pdf->cropping
        :param src_file_apath:
        :param dst_dir_apath: Indicating dir path. NOT file path
        :param to_fmt: format type converted
        :param is_crop: Whether crop or not
        """

        # init1
        # FIXME: Pathしか受け付けないように要修正
        src_pl = Path(src_file_apath)  # pathlibのインスタンス
        """ 無視すべき拡張子 """
        if src_pl.name.startswith("~") or src_pl.name.startswith(".") or src_pl.suffix in (".part", ".tmp") or \
                src_pl.stem.endswith("~"):  # for bibdesk
            logger.info("Ignored: %s" % src_pl.name)
            return
        if not src_pl.is_absolute():
            raise Exception("path_srcは絶対Pathで指定して下さい。src_path:%s" % src_pl)
        del src_file_apath
        # src_file_apath = None  # 誤って参照しないように

        tmp_dst = Path(dst_dir_apath)
        if tmp_dst.is_dir():
            dst_pl = tmp_dst.joinpath(src_pl.stem + to_fmt)
        else:
            dst_pl = tmp_dst
        del dst_dir_apath
        # dst_dir_apath = None  # Prevent Trouble
        # del to_fmt # 消すな. .bibコピー失敗するから. #FIXME: 要修正
        # to_fmt = None  # Prevent Trouble

        """ チェック """
        # to_fmt = cls._validated_fmt(to_fmt=to_fmt, src_pl=src_pl)
        if src_pl.suffix is None or src_pl.suffix == "":
            logger.error("Stop conversion because the indicated extension of source was wrong(file:%s)." % src_pl.name)
            return
        if dst_pl.suffix is None or dst_pl.suffix == "":
            logger.error(
                "Stop conversion because the indicated extension of destination was wrong(file:%s)." % dst_pl.name)
            return

        # 下記不要？
        if not src_pl.exists() and not dst_pl.suffix == ".bib":
            raise Exception("src path(1st-arg:%s)が見つかりません、訂正して下さい" % src_pl.as_posix())
        # init2
        # # FIXME: Pathしか受け付けないように要修正
        # dst_pl = Path(dst_dir_apath)
        # if not dst_dir_apath.is_dir():
        #     raise Exception("dst_dir_apath(2nd-arg:%s)は、ファイルではなく、フォルダのPATHを指定して下さい" % dst_dir_apath)
        # os.chdir(dst_pl.parent)  # important!

        ####### 拡張子毎に振り分け
        if src_pl.suffix in (".png", ".jpg", ".jpeg", ".ai", ".eps", ".pdf"):
            """Image Cropping and Conversion
            - [条件] ImageMagicが対応しているFOrmatのみ. Only the format which corresponded to ImageMagick
            - files entered in src_folder, converted into dst_pl which cropping. and conv to eps
            """
            logger.info("Image cropping and Conversion")
            # pl_src2 = cls._crop_img(src_pl, dst_pl.joinpath(src_pl.stem + src_pl.suffix),
            #                          to_img_fmt=src_pl.suffix)
            # if fmt == ".eps":
            #     cls._conv2eps(src_pl=pl_src2, pl_dst_dir=dst_pl.joinpath(src_pl.stem + src_pl.suffix))
            # return
            _ = self._conv_with_crop_both(src_pl=src_pl, dst_pl=dst_pl)
            # _ = cls._conv_and_crop(src_pl=src_pl, dst_pl=dst_pl)
        elif src_pl.suffix in (".ppt", ".pptx", ".odp") and not src_pl.name.startswith("~"):
            """ Slide Conversion """
            self.conv_slide_with_crop_both(src_pl, dst_pl)
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

        elif src_pl.suffix == ".bib":  # and fmt_if_dst_without_ext == ".bib":
            """
            .bibファイルのコピー
            注意).bib.partが生成されるが、瞬間的に.bibになる。それを捉えて該当フォルダへコピーしている
            """
            # FIXME: 上記if、条件が重複しているので注
            # tmp_src = src_pl  # .with_suffix("")
            # tmp_dst = dst_pl.joinpath(src_pl.name)  # .with_suffix(".bib")
            # new_path = shutil.copyfile(tmp_src, tmp_dst)
            shutil.copy(src_pl, dst_pl)
            logger.info("Copied %s to %s" % (src_pl, dst_pl))
        elif src_pl.suffix in self._ext_pluntuml:
            self._conv_plantuml(src_pl=src_pl, dst_pl=dst_pl)
        elif src_pl.name.endswith("_mermaid") and src_pl.suffix == ".md" or src_pl.suffix == ".mmd":
            print("[Info] Mermaid conversion:%s" % src_pl)
            self.conv_mermaid_with_crop(src_pl=src_pl, dst_pl=dst_pl)  # , to_fmt=to_fmt)
        else:
            logger.info("未処理ファイル:%s" % src_pl)

        if dst_pl.suffix == ".eps":
            dst_pl = self.fix_eps(dst_pl)

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

    @staticmethod
    def check_ghostscript(cmd="gs"):
        res = shutil.which(cmd)
        if res:
            return res
        else:
            msg = """
            Mac: brew isntall ghostscript
            """
            logger.error(msg)

    def _road_balancer(self, event):
        """

        :param event:
        :return:
        """
        if self._monitors and not event.is_directory:
            for key_path, closure in self._monitors.items():  # type:Tuple[Path,Path],function
                if key_path[0].as_posix() in event.src_path:  # 0: src_path, 1:dst_path
                    if event.event_type == "moved":
                        src_path = event.dest_path
                    else:
                        src_path = event.src_path
                    closure(src_path)  # run

    def on_created(self, event):
        """

        :param event:
        :return:
        """
        filepath = event.src_path
        filename = os.path.basename(filepath)
        print(self.msg_event_start)
        logger.info('Created: %s' % filename)
        # cls.convert(src_file_apath=event.src_path, dst_dir_apath=cls._dst_pl, fmt_if_dst_without_ext=cls._to_fmt)  # , _to_fmt="png")
        self._road_balancer(event=event)

    def on_modified(self, event):
        filepath = event.src_path
        filename = os.path.basename(filepath)
        print(self.msg_event_start)
        logger.info('Modified:%s' % filename)
        self._road_balancer(event=event)

    def on_deleted(self, event):
        filepath = event.src_path
        filename = os.path.basename(filepath)
        print("\n\n")
        logger.info('Deleted:%s' % filename)
        # cls._road_balancer(event=event)

    def on_moved(self, event):
        """
        ファイル移動時のイベント
        - Medeneley変換では、event.dest_pathが移動後のPATHを示し、それを変換に使えないかと思う
        :param event:
        :type event: FileMovedEvent | DirMovedEvent
        :return:
        """
        filepath = event.src_path
        filename = os.path.basename(filepath)
        print(self.msg_event_start)
        logger.info('Moved:%s' % filename)
        # cls.convert(src_file_apath=event.dest_path, dst_dir_apath=cls._dst_pl,fmt_if_dst_without_ext=cls._to_fmt)  # , _to_fmt="png")
        self._road_balancer(event=event)

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
    def _validated_fmt(to_fmt, src_pl: Path):
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
    def _get_internal_deal_path(path: (str, Path), pl_cwd=Path.cwd(), head_comment=""):
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
            raise Exception("%s %s is not type str or Path(pathlib)" % (head_comment, path))
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

    def _get_monitor_func(self
                          , src_pl
                          , dst_pl
                          , to_fmt_in
                          , is_crop=True
                          ):
        """
        closure type func return
        :param src_pl:
        :param dst_pl:
        :param fmt_if_dst_without_ext:
        :param is_crop:
        :return:
        """

        # async def moniko(sel
        def moniko(path_updated_file):
            self.convert(src_file_apath=path_updated_file, dst_dir_apath=dst_pl, to_fmt=to_fmt_in, is_crop=is_crop)
            # loop = asyncio.get_event_loop()
            # print(f'start:  {sec}秒待つよ')
            # await loop.run_in_executor(None, time.sleep, sec)
            # print(f'finish: {sec}秒待つよ')

        # return moniko(fname_str_or_pl=fname_str_or_pl, dst_dir_apath=dst_dir_apath, fmt_if_dst_without_ext=fmt_if_dst_without_ext, is_crop=is_crop)
        return moniko

    def set_monitor(self
                    , src_dir
                    , dst_dir
                    , to_fmt
                    , is_crop=True):
        src_pl = self._get_internal_deal_path(path=src_dir)
        dst_pl = self._get_internal_deal_path(path=dst_dir)
        to_fmt_in = self._validated_fmt(to_fmt=to_fmt, src_pl=src_pl)
        self._monitors[src_pl, dst_pl] = self._get_monitor_func(src_pl=src_pl, dst_pl=dst_pl,
                                                                to_fmt_in=to_fmt_in,
                                                                is_crop=is_crop)

    def start_monitors(self
                       , sleep_sec=1):
        """
        Start monitoring change on FS according to set
        :param sleep_sec:
        :return:
        """
        try:
            event_handler = self
            observer = Observer()
            for src_pl, dst_pl in self._monitors.keys():  # type: Path,Path

                # Check src path
                if not src_pl.exists():
                    raise Exception("[Error] The path was not exists: %s" % src_pl)
                print("[Info] Set monitoring Path:%s" % src_pl)

                # Check base_dst_pl path
                if not dst_pl.exists():
                    print("[Info] 右記PATH存在しません、作成しますか?:%s" % dst_pl)
                    res = ""
                    while res not in ("y", "n", "Y", "N"):
                        res = input("make dir?(y/n)")
                    if res in ("y", "Y"):
                        dst_pl.mkdir()
                    else:
                        raise Exception("[Error] dst_pathが存在しないので終了しました")
                print("[Info] Set exporting Path:%s" % dst_pl)

                # set into scheduling
                observer.schedule(event_handler, src_pl.as_posix(), recursive=True)
            # event_handler = ChangeHandler()
            observer.start()
            print("[Info] Start Monitoring")
            while True:
                try:
                    time.sleep(sleep_sec)
                except KeyboardInterrupt:
                    observer.stop()
                observer.join()
        except Exception as e:
            raise Exception("Current path: %s" % Path.cwd())


@classmethod
def cli_watch():
    """
    監視を開始する
    :param src_path:
    :param dst_dir_apath:
    :param _to_fmt:
    :param is_crop:
    :return:
    """
    pass


def convert():
    """
    CLI entry point:
    :param src_path:
    :param dst_dir_apath:
    :param _to_fmt:
    :param is_crop:
    :return:
    """
    # import argparse
    #
    # parser = argparse.ArgumentParser(description='Markuplanguage(.md, .tex) Helper', epilog="詳しい説明")
    # parser.add_argument('integers', metavar='N', type=int, nargs='+',
    #                     help='an integer for the accumulator')
    # parser.add_argument('--sum', dest='accumulate', action='store_const',
    #                     const=sum, default=max,
    #                     help='sum the integers (default: find the max)')
    # parser.add_argument()
    #
    # args = parser.parse_args()
    # print(args.accumulate(args.integers))

    # TODO: 下記argparseで書き直せ
    # TODO: [Debug]ラインを消せ、if debugなら。
    print("[Debug] sys.argv:%s" % sys.argv)
    src_pl = Path(sys.argv[1])
    if not src_pl.is_absolute():
        src_pl = Path(os.getcwd()).joinpath(sys.argv[1])
    print("fname_str_or_pl:%s" % src_pl)
    ChangeHandler.convert(src_file_apath=src_pl.as_posix(), dst_dir_apath=sys.argv[2],
                          to_fmt=sys.argv[3])  # , is_crop=sys.argv[4])
    print("END-END-END")
    # if len(sys.argv) == 5:
    #     print("[Debug] sys.argv:%s" % sys.argv)
    #     ChangeHandler.convert(path_src=sys.argv[1], dir_dst=sys.argv[2], _to_fmt=sys.argv[3], is_crop=sys.argv[4])
    # else:
    #     print('please specify 4 arguments', file=sys.stderr)
    #     sys.exit(1)


if __name__ in '__main__':
    ins = ChangeHandler(monitoring_dir="app_single/_fig_src", output_dir="app_single/figs")
    ins.convert()
