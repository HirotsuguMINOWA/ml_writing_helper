# -*- coding: utf-8 -*-

# TODO: bin(soffice, imagemagick'convert and so on)の存在確認
# TODO: pdfは透過png?が黒くなるためデフォルトはpng
# FIXME: croppingした結果をsrc pathに保存しているのではなく, dst pathに保存しろ
# TODO: dstとsrcフォルダの生成、実行時に。
# target_dir = "app_single/_fig_src"
# _p_dst_dir = "app_single/figs"

###############################################################

# import ftplib
import shutil

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

import os
import time
import shlex
import subprocess
from subprocess import check_output, STDOUT
import pathlib  # FIXME: 下記に統一
from pathlib import Path


# from strenum import StrEnum

# class Export(StrEnum)
#     png=auto()
#     jpeg=auto()
#     pdf=auto()
#     none=auto()

# 出力がepsの場合、監視folderにpngなど画像ファイルが書き込まれたらepsへ変換するコードをかけ

class ChangeHandler(FileSystemEventHandler):

    def __init__(self
                 , monitoring_dir
                 , output_dir=None
                 , dst_ext_no_period="png"
                 , export_fmts=["png", "eps", "pdf"]
                 , paths_soffice=['/Applications/LibreOffice.app/Contents/MacOS/soffice',
                                  '/Applications/LibreOffice Vanilla.app/Contents/MacOS/soffice']):
        """[summary]
        
        Arguments:
            monitoring_dir {[type]} -- [description]
            _p_dst_dir {str} -- [description]
            export_fmts {list} -- 出力フォーマット。複数指定すると、その全てのフォーマットに出力。
        
        Keyword Arguments:
            dst_ext_no_period {str} -- [description] (default: {"png"})
        """
        # TODO: startメソッドへmonitoring_dirやoutput_dirを移せ
        # TODO: 各コマンドのPATHのチェック。OSのPATHに登録されている事前提、加えてデフォルトのPATHチェック。それで見つからなければWarningだけだす。
        """[注意]
        本プログラムのScriptが存在するPATHをwcdへ移動とする
        """
        # print("Abs PATH:%s" % __file__)
        os.chdir(os.path.dirname(os.path.abspath(__file__)))
        # p=pathlib.Path.parent
        # p.as_posix()
        # os.chdir(pathlib.Path.parent.as_posix()) # Change directory into dir of this script
        #

        if not output_dir:
            output_dir = monitoring_dir
        self.target_dir = monitoring_dir
        self._p_src = Path(monitoring_dir)
        # self._p_dst_dir = output_dir
        if Path(output_dir).is_absolute():
            self._p_dst_dir = Path(output_dir)
        else:
            self._p_dst_dir = Path(monitoring_dir).joinpath(output_dir)
        self._ppaths_soffice = [Path(x) for x in paths_soffice]
        #
        # 拡張子チェック
        #
        if dst_ext_no_period == "":
            self.dst_ext_no_period = self._p_src.suffix
        elif dst_ext_no_period[0] != ".":
            self.dst_ext_no_period = "." + dst_ext_no_period
        else:
            self.dst_ext_no_period = dst_ext_no_period

    @staticmethod
    def _crop_img(p_src_img, p_dst: Path, to_img_fmt):
        """
        image(pdf/png,jpeg?)をcroppingする
        :param p_src:
        :param p_dst:
        :return: 変換後のpath名
        :rtype: pathlib.Path
        """
        """ Calc path of dst """
        # path_dst = pathlib.Path(dir_dst) / pl_src.name
        # path_dst = pathlib.Path(dir_dst) / plib_src.with_suffix("." + self.dst_ext_no_period).name
        if not p_src_img.exists():
            print("[Error] %s not found")
            return
        if p_dst.is_dir():
            p_dst = p_dst.joinpath(p_src_img.name)  # if the path is dir, set filename converted

        """ crop white space """
        if to_img_fmt in [".png", ".jpeg", ".jpg"]:  # pdfのcropはできない
            cmd_name = "convert"
            # p_conv = Path("/usr/local/bin/convert")
            # if not p_conv.exists():
            #     raise Exception("%s not found" % p_conv)
            cmd = "{cmd_name} {path_in} -trim {path_out} ".format(cmd_name=cmd_name,
                                                                  path_in=p_src_img,
                                                                  path_out=p_dst)
        elif to_img_fmt == ".pdf":
            cmd_name = "pdfcrop"
            cmd = "{cmd_name} {path_in} {path_out}".format(cmd_name=cmd_name, path_in=p_src_img, path_out=p_dst)
        else:
            # new_path = shutil.move(pl_src.as_posix(), dir_dst)
            raise Exception("対応していないFormatをcroppingしようとして停止.%s:%s" % ("to_img_fmt", to_img_fmt))

        if shutil.which(cmd_name) is None:
            print("[Warning] cmd(%s) is not in path " % cmd)
        print("[Debug] Cropping CMD: " + cmd)
        tokens = shlex.split(cmd)
        subprocess.run(tokens)
        # output = check_output(tokens, stderr=STDOUT).decode("utf8")
        # return Path(p_dst.with_name(p_src_img.name).with_suffix("%s" % to_img_fmt))
        return p_dst

    def _run_cmd(self, cmd: str, is_print=True):
        """
        コマンド(CLI)の実行
        :param cmd:
        :param is_print:
        :return:
        """
        tokens = shlex.split(cmd)
        # subprocess.run(tokens)
        output = check_output(tokens, stderr=STDOUT).decode("utf8")
        if is_print:
            print("Output: %s" % output)
        return output

    @staticmethod
    def _conv2eps(pl_src: Path, pl_dst: Path):
        # TODO: srcファイルを削除するargを設ける事
        if pl_src.suffix not in (".jpeg", ".jpg", ".png", ".pdf"):
            return
        print("[Info] Convert to eps")
        cmd = "{cmd_conv} {p_src} {p_dst}".format(
            cmd_conv="convert"
            , p_src=pl_src
            , p_dst=pl_dst
        )
        print("[Debug] CMD(convert): %s" % cmd)
        tokens = shlex.split(cmd)
        # subprocess.run(tokens)
        output = check_output(tokens, stderr=STDOUT).decode("utf8")
        print("Output: %s" % output)
        # elif to_fmt == "pdf" and pl_src.suffix == ".odp":
        #     ### conv png to pdf
        #     cmd = "convert %s %s" % (
        #         pl_src.with_suffix(".png")
        #         , pl_dst.joinpath(pl_src.name).with_suffix(".pdf")
        #     )
        #     self._run_cmd(cmd)

    def _conv(self, pl_src, pl_dst, to_fmt=".png"):
        """
        総合converter, ここから各subモジュールへ振り分ける
        :param pl_src:
        :param pl_dst:
        :param to_fmt:
        :return:
        """

    def convert(self, path_src, dir_dst, to_fmt=".png", is_crop=True):  # , dst_ext_no_period="pdf"):
        """
        ppt->pdf->cropping
        :param dst_ext: without period!!
        """

        # init1
        pl_src = Path(path_src)  # pathlibのインスタンス

        #
        # チェック
        #
        if to_fmt == "":
            to_fmt = pl_src.suffix
        elif to_fmt[0] != ".":
            to_fmt = "." + to_fmt

        # init2
        pl_dst = Path(dir_dst)
        os.chdir(pl_dst.parent)  # important!

        # TODO: odp?に要対応.LibreOffice
        if pl_src.suffix in (".png", ".jpg", ".jpeg") and not pl_src.name.startswith("~"):
            """
            files entered in src_folder, converted into pl_dst wich cropping. and conv to eps
            """
            print("[Info] Image->croppingしてdst pathへコピーします")
            pl_src2 = self._crop_img(pl_src, pl_dst.joinpath("tmp_" + pl_src.name).with_suffix(pl_src.suffix),
                                     to_img_fmt=pl_src.suffix)
            self._conv2eps(pl_src=pl_src2, pl_dst=pl_dst.joinpath(pl_src.with_suffix(to_fmt).name))
            return

        if pl_src.suffix not in (".ppt", ".pptx", ".odp") and not pl_src.name.startswith("~"):
            print("[Info] Powerpoint / LibreOffice以外は変換せず")
            return
        """
        一時的にepsは
        """
        if pl_src.suffix == ".odp" and to_fmt in [".pdf", ".eps"]:
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
        # elif pl_src.suffix == ".odp" and to_fmt in ["pdf", "eps"]:
        #     """
        #     .odp formatはpdfに変換するとpdfcropで失敗する。
        #     よって、png形式で変換する
        #     """
        #     cur_to_fmt = "png"
        elif to_fmt == ".eps":
            cur_to_fmt = ".pdf"
        else:
            cur_to_fmt = to_fmt

        # file_tmp="tmp_"+pathlib.Path(path_src).name
        # file_tmp=pathlib.Path(file_tmp).with_suffix(".pdf")
        # path_tmp=pathlib.Path(path_src).parent.joinpath(file_tmp).as_posix()
        # print("path_tmp:"+path_tmp)
        # out_dir = plib_src.parent.as_posix()
        # path_tmp="tmp_"+os.path.basename(path_src)
        print("[Debug] pl_dst: %s" % pl_dst)
        print("[Debug] CWD:%s" % os.getcwd())
        found_libreoffice = False

        for p_soffice in self._ppaths_soffice:  # type: Path
            if p_soffice.exists():
                cmd = "'{path_soffice}' --headless --convert-to {dst_ext} --outdir {out_dir} {path_src}".format(
                    path_soffice=p_soffice
                    , dst_ext=cur_to_fmt[1:],  # eliminate first "."
                    # , out_dir=dir_dst
                    out_dir=pl_dst.name
                    , path_src=pl_src)
                break
        print("[Debug] CMD(slide2img):" + cmd)
        tokens = shlex.split(cmd)
        # subprocess.run(tokens)
        output = check_output(tokens, stderr=STDOUT).decode("utf8")
        print("Output: %s" % output)
        if output == "Error: source file could not be loaded":
            """なぜかLO Vanillaで出現？"""
            # raise Exception("")
            print("[ERROR] なぜかLO Vanillaで出現？")

        """ Add head "tmp_" to converted filename """

        plib_pdf_convd = pl_dst.joinpath(pl_src.name).with_suffix(cur_to_fmt)
        plib_pdf_convd_tmp = plib_pdf_convd.with_name("tmp_" + plib_pdf_convd.name)

        cmd_cp = "cp -f %s %s" % (plib_pdf_convd, plib_pdf_convd.with_name("pre-crop_" + plib_pdf_convd.name))
        tokens = shlex.split(cmd_cp)
        output = check_output(tokens, stderr=STDOUT).decode("utf8")
        print("Output: %s" % output)

        # pl_src.rename(pl_src.with_name("tmp_"+pl_src.name))
        # pl_src.rename(plib_pdf_convd_tmp)
        # pl_src.with_name("tmp_"+pl_src.name)
        if is_crop:
            p_src_cropped = self._crop_img(p_src_img=plib_pdf_convd, p_dst=self._p_dst_dir, to_img_fmt=cur_to_fmt)
        """ pdf 2 eps """
        if to_fmt == "eps":
            self._conv2eps(pl_src=p_src_cropped, pl_dst=self._p_dst_dir)
        """ rm tmpfile"""
        if plib_pdf_convd_tmp.exists():
            pathlib.Path(plib_pdf_convd_tmp).unlink()
        print("Converted")

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

    def on_created(self, event):
        filepath = event.src_path
        filename = os.path.basename(filepath)
        print('%sができました' % filename)
        self.convert(path_src=event.src_path, dir_dst=self._p_dst_dir,
                     to_fmt=self.dst_ext_no_period)  # , dst_ext_no_period="png")

    def on_modified(self, event):
        filepath = event.src_path
        filename = os.path.basename(filepath)
        print('%sを変更しました' % filename)

    def on_deleted(self, event):
        filepath = event.src_path
        filename = os.path.basename(filepath)
        print('%sを削除しました' % filename)

    def start(self):
        try:
            while 1:
                # event_handler = ChangeHandler()
                event_handler = self
                observer = Observer()
                observer.schedule(event_handler, self.target_dir, recursive=True)
                observer.start()
                try:
                    while True:
                        time.sleep(0.1)
                except KeyboardInterrupt:
                    observer.stop()
                observer.join()
        except Exception as e:
            raise Exception("Current path: %s" % pathlib.Path.cwd())


if __name__ in '__main__':
    ins = ChangeHandler(monitoring_dir="app_single/_fig_src", output_dir="app_single/figs")
    ins.main()
