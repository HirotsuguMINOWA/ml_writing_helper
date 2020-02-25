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
handler_format = Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
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


class ChangeHandler(FileSystemEventHandler):
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

    # def __init__(self
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
        # self.target_dir = monitoring_dir
        # self._p_src = Path(monitoring_dir)
        # # self._p_dst_dir = output_dir
        # if Path(output_dir).is_absolute():
        #     self._p_dst_dir = Path(output_dir)
        # else:
        #     self._p_dst_dir = Path(monitoring_dir).joinpath(output_dir)
        self._src_pl = None
        self._dst_pl = None
        self._to_fmt = None
        self._monitors = {}
        self._ppaths_soffice = [Path(x) for x in self.paths_soffice]
        # #
        # # 拡張子チェック
        # #
        # if _to_fmt == "":
        #     self._to_fmt = self._p_src.suffix
        # elif _to_fmt[0] != ".":
        #     self._to_fmt = "." + _to_fmt
        # else:
        #     self._to_fmt = _to_fmt
        # TODO: 入力フォーマットか否か要チェック

    @staticmethod
    def which(name) -> bool:
        """
        which command wrapper on python
        :param name:
        :return:
        """
        # print(shutil.which('ls'))  # > '/bin/ls'
        # print(shutil.which('ssss'))  # > None
        res = shutil.which(name)
        if res:
            return True, res
        else:
            return False, ""

    @staticmethod
    def util_update_dst_path(base_pl: Path, name_pl_or_str, to_fmt) -> Path:
        """
        destionation path modifier

        :param base_pl:
        :param name_pl_or_str:
        :type name_pl_or_str: Path | str
        :param to_fmt:
        :return:
        """
        base_pl = base_pl.resolve()  # 相対PATH-> abs. path
        if isinstance(name_pl_or_str, Path):
            # conv path to str
            name_pl_or_str = name_pl_or_str.stem

        if base_pl.is_dir():
            return base_pl.joinpath(name_pl_or_str + to_fmt)
        else:
            return base_pl.with_suffix(to_fmt)

    @staticmethod
    def _crop_img(p_src_img, p_dst: Path) -> Path:
        """
        image(pdf/png,jpeg?)をcroppingする
        :param p_src:
        :param p_dst:
        :return: 変換後のpath名
        :rtype: pathlib.Path
        """
        """ Calc path of base_pl """
        # path_dst = pathlib.Path(dir_dst) / name_pl_or_str.name
        # path_dst = pathlib.Path(dir_dst) / plib_src.with_suffix("." + self._to_fmt).name
        if not p_src_img.exists():
            print("[Error] %s not found" % p_src_img)
            return
        if p_dst.is_dir():
            p_dst = p_dst.joinpath(p_src_img.name)  # if the path is dir, set src_filename_stem converted

        """ crop white space """
        # if p_src_img.suffix not in [".png", ".jpeg", ".jpeg"]:
        #     logging.error("source file is not 対応してないImage magickに。")
        #     return Path()

        if p_src_img.suffix in (".png", ".jpg", ".jpeg", ".eps"):  # pdfのcropはできない
            cmd_name = "convert"
            # p_conv = Path("/usr/local/bin/convert")
            # if not p_conv.exists():
            #     raise Exception("%s not found" % p_conv)
            cmd = "{cmd_name} {path_in} -trim {path_out} ".format(cmd_name=cmd_name,
                                                                  path_in=p_src_img,
                                                                  path_out=p_dst)
        elif p_src_img.suffix == ".pdf":
            cmd_name = "pdfcrop"
            cmd = "{cmd_name} {path_in} {path_out}".format(cmd_name=cmd_name, path_in=p_src_img, path_out=p_dst)
        else:
            # new_path = shutil.move(name_pl_or_str.as_posix(), dir_dst)
            raise Exception("対応していないFormatをcroppingしようとして停止: %s" % p_src_img)

        if shutil.which(cmd_name) is None:
            print("[Warning] cmd(%s) is not in path " % cmd)
        print("[Debug] Cropping CMD: " + cmd)
        tokens = shlex.split(cmd)
        subprocess.run(tokens)
        # output = check_output(tokens, stderr=STDOUT).decode("utf8")
        # return Path(p_dst.with_name(p_src_img.name).with_suffix("%s" % to_img_fmt))
        return p_dst

    @staticmethod
    def _run_cmd(cmd: str, short_msg="", is_print=True) -> str:
        """
        コマンド(CLI)の実行
        :param cmd:
        :param is_print:
        :return: output of rum
        """
        if is_print:
            print("[Debug] CMD(%s):%s" % (short_msg, cmd))
        tokens = shlex.split(cmd)
        output = check_output(tokens, stderr=STDOUT).decode("utf8")
        if is_print:
            print("Output(%s):%s" % (short_msg, cmd))
        return output

    @classmethod
    def _conv2img(cls, pl_src: Path, pl_dst_or_dir: Path, fmt_if_dst_without_ext: str, decode="utf8") -> Path:
        """
        Image magicによる画像変換
        :param pl_src:
        :param pl_dst_or_dir:
        :param fmt_if_dst_without_ext: pl_dst_or_dirがdirの場合、出力先に生成するPATHのファイルの拡張子になる。
        :return:
        """
        if not pl_src.exists():
            raise Exception("Input image not exists:%s" % pl_src)
        dst_pl = cls.util_update_dst_path(base_pl=pl_dst_or_dir, name_pl_or_str=pl_src, to_fmt=fmt_if_dst_without_ext)
        # if pl_dst_or_dir.is_dir():
        #     pl_dst_or_dir = pl_dst_or_dir / pl_src.stem.join(fmt_if_dst_without_ext)

        cmd = "{cmd_conv} {src} {dst}".format(
            cmd_conv="convert"
            , src=pl_src
            , dst=dst_pl
        )
        print("[Debug] CMD(convert): %s" % cmd)
        tokens = shlex.split(cmd)
        # subprocess.run(tokens)
        output = check_output(tokens, stderr=STDOUT).decode(decode)
        print("Output: %s" % output)
        return dst_pl

    # @classmethod
    # def _conv2eps(cls, pl_src: Path, pl_dst_dir: Path, del_src=True) -> Path:
    #     """
    #
    #     :param pl_src:
    #     :param pl_dst_dir: directoryのみ
    #     :param del_src: del src of as tmp
    #     :return: 変換後のPATH
    #     """
    #     if pl_src.suffix not in (".jpeg", ".jpg", ".png", ".pdf"):
    #         return
    #     print("[Info] Convert to eps")
    #
    #     if pl_dst_dir.is_dir():
    #         pl_dst_dir = pl_dst_dir.joinpath(pl_src.stem + ".eps")
    #     # else:
    #     #     raise Exception("ディレクトリ指定して下さい。")
    #     elif pl_dst_dir.suffix != ".eps":
    #         # raise Exception("出力ファイルの拡張子も.epsにして下さい")
    #         print("[Warning]出力拡張子を.epsに変えました")
    #         pl_dst_dir = pl_dst_dir.with_suffix(".eps")
    #     pl_dst_dir = cls._conv2img(pl_src, pl_dst_dir, fmt_if_dst_without_ext="png")
    #     if del_src:
    #         pl_src.unlink()
    #     return pl_dst_dir

    @classmethod
    def _conv_plantuml(cls, src_pl: Path, dst_pl: Path, to_fmt=".png"):
        cls._cmd_plantuml = "plantuml"
        if shutil.which(cls._cmd_plantuml) is None:
            print("[ERROR] %s not found" % cls._cmd_plantuml)
            return
        # todo: plantuml conv.
        if to_fmt not in (".png", ".pdf", ".eps"):
            print("[ERROR] Indicated Formatは未対応 in coverting with plantuml")
            return
        cmd = "{cmd_pu} -o {dst} -t{fmt} {src}".format(
            cmd_pu=cls._cmd_plantuml,
            src=src_pl.as_posix(),
            dst=dst_pl.as_posix(),
            fmt=to_fmt[1:]
        )
        res = cls._run_cmd(cmd=cmd, short_msg="Converting with %s" % cls._cmd_plantuml)
        print("Result:%s" % res)

    @classmethod
    def _conv_slide(self, src_pl: Path, dst_pl: Path, to_fmt=".png"):
        """

        :param src_pl:
        :param dst_pl: ファイル/folderまでのPATH.場合分けが必要
        :param to_fmt:
        :return:
        """

        # file_tmp="tmp_"+pathlib.Path(path_src).name
        # file_tmp=pathlib.Path(file_tmp).with_suffix(".pdf")
        # path_tmp=pathlib.Path(path_src).parent.joinpath(file_tmp).as_posix()
        # print("path_tmp:"+path_tmp)
        # out_dir = plib_src.parent.as_posix()
        # path_tmp="tmp_"+os.path.basename(path_src)
        if dst_pl.is_dir():
            pl_dst_dir = dst_pl
        else:
            pl_dst_dir = dst_pl.parent
        print("[Debug] pl_dst_or_dir: %s" % dst_pl)
        print("[Debug] CWD:%s" % os.getcwd())
        found_libreoffice = False

        for p_soffice in self._ppaths_soffice:  # type: Path
            if p_soffice.exists():
                cmd = "'{path_soffice}' --headless --convert-to {dst_ext} --outdir '{out_dir}' '{path_src}'".format(
                    # cmd = "'{path_soffice}' --headless --convert-to {dst_ext} {path_src}".format(
                    path_soffice=p_soffice
                    , dst_ext=to_fmt[1:],  # eliminate first "."
                    # , out_dir=dir_dst
                    out_dir=pl_dst_dir.as_posix()
                    , path_src=src_pl)
                break

        # output = self._run_cmd(cmd)
        print("[Debug] CMD(slide2img):" + cmd)
        tokens = shlex.split(cmd)
        # subprocess.run(tokens)
        output = check_output(tokens, stderr=STDOUT).decode("utf8")
        print("Output: %s" % output)
        if output == "Error: source file could not be loaded\n":
            """なぜかLO Vanillaで出現？"""
            # raise Exception("")
            print("[ERROR] なぜかLO Vanillaで出現？")

        ### 変換成功したはず
        #
        # 生成されたファイルPATH

        pl_out = pl_dst_dir.joinpath(src_pl.with_suffix(to_fmt).name)
        if dst_pl.is_dir():
            return pl_out
        else:
            """
            出力ファイルPATHが指定されているのでrenameする
            """
            # pl_dst_or_dir = pl_dst_or_dir.joinpath(pl_out.with_suffix(pl_out.suffix).name)
            # else:
            #     pl_out = pl_dst_or_dir.joinpath(name_pl_or_str.name + _to_fmt)

            # # 存在していたら削除
            # if pl_dst_or_dir.exists():
            #     pl_dst_or_dir.unlink()

            # rename
            pl_out.rename(dst_pl)

            # """ Add head "tmp_" to converted src_filename_stem """
            #
            # plib_pdf_convd = pl_dst_or_dir.joinpath(name_pl_or_str.name).with_suffix(cur_to_fmt)
            # # plib_pdf_convd_tmp = plib_pdf_convd.with_name("tmp_" + plib_pdf_convd.name)
            #
            # cmd_cp = "cp -f %s %s" % (plib_pdf_convd, plib_pdf_convd.with_name("pre-crop_" + plib_pdf_convd.name))
            # self._run_cmd(cmd)
            # # tokens = shlex.split(cmd_cp)
            # # output = check_output(tokens, stderr=STDOUT).decode("utf8")
            # # print("Output: %s" % output)
            #
            # # name_pl_or_str.rename(name_pl_or_str.with_name("tmp_"+name_pl_or_str.name))
            # # name_pl_or_str.rename(plib_pdf_convd_tmp)
            # # name_pl_or_str.with_name("tmp_"+name_pl_or_str.name)
            return dst_pl

    @classmethod
    def _conv_with_crop(cls, src_pl: Path, dst_pl: Path, to_fmt=".png") -> Path:
        """
        イメージをcrop込で変換する
        :param self:
        :param src_pl:
        :param dst_pl:
        :param to_fmt:
        :return:
        """
        path_dst = cls._conv2img(pl_src=src_pl, pl_dst_or_dir=dst_pl, fmt_if_dst_without_ext=to_fmt)
        path_dst = cls._crop_img(p_src_img=src_pl, p_dst=path_dst)
        return path_dst

    @classmethod
    def conv_mermaid(cls, src_pl: Path, dst_pl: Path, to_fmt=".svg") -> Tuple[bool, Path]:
        """
        Mermaid(*_mermaid.md) Conversion
        mermaid markdownを変換
        - 外部
        :param src_pl:
        :param dst_pl:
        :param to_fmt:
        :return:
        """
        # Check on format
        if to_fmt not in (".svg", ".png", ".pdf"):
            logger.error("Cannot conversion file type:%s" % to_fmt)
            return False, None

        """ Check exists of mermaid-cli """
        cmd_name_mermaid = "mmdc"
        res, path = cls.which(cmd_name_mermaid)
        if not res:
            msg = """
                mermaidコマンドに当たるmmdcにpathが通っていません。
                要PATH通し/インスト（下記参考）
                npm install -g mermaid
                npm install -g mermaid.cli
                """
            logging.error(msg)
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

        dst_pl_full = cls.util_update_dst_path(base_pl=dst_pl, name_pl_or_str=src_pl, to_fmt=to_fmt)

        cmd = "{cmd_mmdc} -i {src_path} -o {dst_filename_only}".format(
            cmd_mmdc=cmd_name_mermaid,
            dst_filename_only=dst_pl_full,
            src_path=src_pl.as_posix()
        )
        out_msg = cls._run_cmd(
            cmd=cmd
            , short_msg="Converting mermaid file"
        )
        if out_msg != "":
            logging.error("Failed conversion into mermaid image:%s" % src_pl)
            return False, None
        else:
            logging.info("Succeeded conversion due mermaid:%s" % src_pl)
            return True, dst_pl_full

    @classmethod
    def conv_mermaid_with_crop(cls, src_pl: Path, dst_pl: Path, to_fmt=".svg") -> Tuple[bool, Path]:
        """
        mermaid markdownを変換 及び 特定のformatへ変換する
        :param src_pl:
        :param dst_pl:
        :param to_fmt:
        :return: Success?, Output file's path
        """
        if to_fmt in ("svg", "png", "pdf"):
            tmp_fmt = to_fmt
        else:
            tmp_fmt = ".png"  # ImageMagickが対応しておりcropが利くフォーマット
        # base_pl filename
        # dst_fname = base_pl.stem
        dst_pl_full = cls.util_update_dst_path(base_pl=dst_pl, name_pl_or_str=src_pl, to_fmt=tmp_fmt)
        # Conversion
        res, tmp_dst_pl = cls.conv_mermaid(
            src_pl=src_pl,
            dst_pl=dst_pl_full,
            to_fmt=tmp_fmt)
        """ Conversion: mermaid """
        if not res:
            return False, None
        """ Cropping image """
        tmp_dst_pl = cls._crop_img(p_src_img=tmp_dst_pl, p_dst=dst_pl)
        if tmp_dst_pl is None:
            logging.error("Failed crop: %s" % src_pl)
            return False, None

        if src_pl.suffix == to_fmt:
            return True, tmp_dst_pl

        """ Image conversion"""
        tmp_dst_pl = cls._conv2img(pl_src=tmp_dst_pl, pl_dst_or_dir=dst_pl, fmt_if_dst_without_ext=to_fmt)
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
        if not src_pl.is_absolute():
            raise Exception("path_srcは絶対Pathで指定して下さい。src_path:%s" % src_pl)
        src_file_apath = None  # 誤って参照しないように

        # チェック
        to_fmt = self._validated_fmt(to_fmt=to_fmt, src_pl=src_pl)

        """ 無視すべき拡張子 """
        if src_pl.name.startswith("~"):
            print("[Info] Ingored: %s" % src_pl.stem + src_pl.suffix)
            return

        # 下記不要？
        if not src_pl.exists() and not to_fmt == ".bib":
            raise Exception("src path(1st-arg:%s)が見つかりません、訂正して下さい" % src_pl.as_posix())
        # init2
        # FIXME: Pathしか受け付けないように要修正
        dst_pl = Path(dst_dir_apath)
        if not dst_dir_apath.is_dir():
            raise Exception("dst_dir_apath(2nd-arg:%s)は、ファイルではなく、フォルダのPATHを指定して下さい" % dst_dir_apath)
        os.chdir(dst_pl.parent)  # important!

        ####### 拡張子毎に振り分け
        # TODO: odp?に要対応.LibreOffice
        if src_pl.suffix in (".png", ".jpg", ".jpeg", ".ai"):
            """Image Cropping and Conversion
            - [条件] ImageMagicが対応しているFOrmatのみ. Only the format which corresponded to ImageMagick
            - files entered in src_folder, converted into pl_dst_or_dir which cropping. and conv to eps
            """
            logger.info("Image cropping and Conversion")
            # pl_src2 = self._crop_img(src_pl, dst_pl.joinpath(src_pl.stem + src_pl.suffix),
            #                          to_img_fmt=src_pl.suffix)
            # if to_fmt == ".eps":
            #     self._conv2eps(pl_src=pl_src2, pl_dst_dir=dst_pl.joinpath(src_pl.stem + src_pl.suffix))
            # return
            _ = self._conv_with_crop(src_pl=src_pl, dst_pl=dst_pl, to_fmt=to_fmt)

        elif src_pl.suffix in (".ppt", ".pptx", ".odp") and not src_pl.name.startswith("~"):
            """
            スライドの変換
            """
            if src_pl.suffix == ".odp" and to_fmt in [".pdf", ".eps"]:
                """
                .odp formatはpdfに変換するとpdfcropで失敗する。
                よって、png形式で変換する
                """
                warn = """
                  [Warning]
                  [Warning].odpを.pdf/.epsへの変換はCropで失敗します!!!
                  [Warning] LibreOfficeではPowerPoint形式(.pptx)に変換して使ってください。
                  [Warning]
                  """
                print(warn)
                cur_to_fmt = ".pdf"
                # elif name_pl_or_str.suffix == ".odp" and _to_fmt in ["pdf", "eps"]:
                #     """
                #     .odp formatはpdfに変換するとpdfcropで失敗する。
                #     よって、png形式で変換する
                #     """
                #     cur_to_fmt = "png"
            elif to_fmt == ".eps":
                cur_to_fmt = ".pdf"
            else:
                cur_to_fmt = to_fmt
            pl_src2 = self._conv_slide(src_pl=src_pl, dst_pl=dst_pl, to_fmt=cur_to_fmt)
            if is_crop:
                p_src_cropped = self._crop_img(p_src_img=pl_src2, p_dst=dst_pl, to_img_fmt=cur_to_fmt)
            """ pdf 2 eps """
            if to_fmt == ".eps":
                self._conv2eps(pl_src=p_src_cropped, pl_dst_dir=dst_pl)
            """ rm tmpfile"""
            # if plib_pdf_convd_tmp.exists():
            #     pathlib.Path(plib_pdf_convd_tmp).unlink()
            print("Converted")
        # elif src_pl.suffix == ".ai":
        #     """
        #     - Image Conversion and Cropping
        #     - その他のフォーマット(eg. ai)を画像化してcrop
        #     """
        #     _ = self._conv_with_crop(src_pl=src_pl, dst_pl=dst_pl, to_fmt=to_fmt)

        elif src_pl.suffix == ".bib" or src_pl.suffix == to_fmt:  # and fmt_if_dst_without_ext == ".bib":
            """
            .bibファイルのコピー
            注意).bib.partが生成されるが、瞬間的に.bibになる。それを捉えて該当フォルダへコピーしている
            """
            # FIXME: 上記if、条件が重複しているので注
            tmp_src = src_pl  # .with_suffix("")
            tmp_dst = dst_pl.joinpath(src_pl.name)  # .with_suffix(".bib")
            new_path = shutil.copyfile(tmp_src, tmp_dst)
            print("[Info] copied %s to %s" % (tmp_src, tmp_dst))
        elif src_pl.suffix in self._ext_pluntuml:
            self._conv_plantuml(src_pl=src_pl, dst_pl=dst_pl, to_fmt=to_fmt)
        elif src_pl.name.endswith("_mermaid") and src_pl.suffix == ".md" or src_pl.suffix == ".mmd":
            print("[Info] Mermaid conversion:%s" % src_pl)
            self.conv_mermaid_with_crop(src_pl=src_pl, dst_pl=dst_pl, to_fmt=to_fmt)
        else:
            print("[Info] 未処理ファイル:%s" % src_pl)

    #
    # def conv2pnt(self, path_src, dir_dst):
    #     plib_src = pathlib.Path(path_src)  # pathlibのインスタンス
    #     if plib_src.suffix in (".ppt", ".pptx") and not plib_src.name.startswith("~"):
    #         path_dst = pathlib.Path(dir_dst) / plib_src.with_suffix(".pdf").name
    #         cmd = "/Applications/LibreOffice.app/Contents/MacOS/soffice --headless --convert-to pdf --outdir {out_dir} {path_src}".format(
    #             out_dir=out_dir, path_src=path_src)
    #         print("[Debug] CMD: ppt2pdf" + cmd)
    #         tokens = shlex.split(cmd)
    #         subprocess.run(tokens)

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
        print('%sが生成された' % filename)
        # self.convert(src_file_apath=event.src_path, dst_dir_apath=self._dst_pl, fmt_if_dst_without_ext=self._to_fmt)  # , _to_fmt="png")
        self._road_balancer(event=event)

    def on_modified(self, event):
        filepath = event.src_path
        filename = os.path.basename(filepath)
        print('%sが変更されました' % filename)
        self._road_balancer(event=event)

    def on_deleted(self, event):
        filepath = event.src_path
        filename = os.path.basename(filepath)
        print('%sを削除しました' % filename)
        # self._road_balancer(event=event)

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
        print('%s moved' % filename)
        # self.convert(src_file_apath=event.dest_path, dst_dir_apath=self._dst_pl,fmt_if_dst_without_ext=self._to_fmt)  # , _to_fmt="png")
        self._road_balancer(event=event)

    # def start(self, sleep_time=0.5):
    #     try:
    #         event_handler = self
    #         observer = Observer()
    #         observer.schedule(event_handler, self.target_dir, recursive=True)
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
        src and base_pl pathの読み込みを代理
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

    # def monitor(self, src_dir, dst_dir
    #             , fmt_if_dst_without_ext="png"
    #             , export_fmts=["png", "eps", "pdf"]
    #             , sleep_time=0.5
    #             ):
    #
    #     self._src_pl = self._get_internal_deal_path(src_dir)
    #     self._dst_pl = self._get_internal_deal_path(dst_dir)
    #
    #     # 拡張子チェック
    #     self._to_fmt = self._validated_fmt(fmt_if_dst_without_ext=fmt_if_dst_without_ext, name_pl_or_str=self._src_pl)
    #     try:
    #         event_handler = self
    #         observer = Observer()
    #         observer.schedule(event_handler, self._src_pl.as_posix(), recursive=True)
    #         # event_handler = ChangeHandler()
    #         observer.start()
    #         print("[Info] Start monitoring:%s" % self._src_pl)
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

        # return moniko(name_pl_or_str=name_pl_or_str, dst_dir_apath=dst_dir_apath, fmt_if_dst_without_ext=fmt_if_dst_without_ext, is_crop=is_crop)
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

                # Check base_pl path
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
    print("name_pl_or_str:%s" % src_pl)
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
