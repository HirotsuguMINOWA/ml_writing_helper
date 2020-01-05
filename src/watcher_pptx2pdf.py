# -*- coding: utf-8 -*-

# TODO: bin(soffice, imagemagick'convert and so on)の存在確認
# TODO: pdfは透過png?が黒くなるためデフォルトはpng

# target_dir = "app_single/_fig_src"
# _p_dest_dir = "app_single/figs"

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
                 , dest_ext_no_period="png"
                 , export_fmts=["png", "eps", "pdf"]
                 , paths_soffice=['/Applications/LibreOffice.app/Contents/MacOS/soffice',
                                  '/Applications/LibreOffice Vanilla.app/Contents/MacOS/soffice']):
        """[summary]
        
        Arguments:
            monitoring_dir {[type]} -- [description]
            _p_dest_dir {str} -- [description]
            export_fmts {list} -- 出力フォーマット。複数指定すると、その全てのフォーマットに出力。
        
        Keyword Arguments:
            dest_ext_no_period {str} -- [description] (default: {"png"})
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
        if not output_dir:
            output_dir = monitoring_dir
        self.target_dir = monitoring_dir
        # self._p_dest_dir = output_dir
        if Path(output_dir).is_absolute():
            self._p_dest_dir = Path(output_dir)
        else:
            self._p_dest_dir = Path(monitoring_dir).joinpath(output_dir)
        self._ppaths_soffice = [Path(x) for x in paths_soffice]
        self.dest_ext_no_period = dest_ext_no_period

    @staticmethod
    def _crop_img(p_src_img, p_dest: Path, to_img_fmt):
        """
        image(pdf/png,jpeg?)をcroppingする
        :param p_src:
        :param p_dest:
        :return: 変換後のpath名
        :rtype: pathlib.Path
        """
        """ Calc path of Dest """
        # path_dest = pathlib.Path(dir_dest) / plib_pdf_convd.name
        # path_dest = pathlib.Path(dir_dest) / plib_src.with_suffix("." + self.dest_ext_no_period).name
        if not p_src_img.exists():
            print("[Error] %s not found")
            return
        if p_dest.is_dir():
            p_dest = p_dest.joinpath(p_src_img.name)  # if the path is dir, set filename converted

        """ crop white space """
        if to_img_fmt in ["png", "jpeg", "jpg"]:  # pdfのcropはできない
            cmd_name = "convert"
            # p_conv = Path("/usr/local/bin/convert")
            # if not p_conv.exists():
            #     raise Exception("%s not found" % p_conv)
            cmd = "{cmd_name} {path_in} -trim {path_out} ".format(cmd_name=cmd_name,
                                                                  path_in=p_src_img,
                                                                  path_out=p_dest)
        elif to_img_fmt == "pdf":
            cmd_name = "pdfcrop"
            cmd = "{cmd_name} {path_in} {path_out}".format(cmd_name=cmd_name, path_in=p_src_img, path_out=p_dest)
        else:
            # new_path = shutil.move(plib_pdf_convd.as_posix(), dir_dest)
            raise Exception("対応していないFormatをcroppingしようとして停止")

        if shutil.which(cmd_name) is None:
            print("[Warning] cmd(%s) is not in path " % cmd)
        print("[Debug] Cropping CMD: " + cmd)
        tokens = shlex.split(cmd)
        subprocess.run(tokens)
        # output = check_output(tokens, stderr=STDOUT).decode("utf8")
        return Path(p_dest.with_name(p_src_img.name).with_suffix(".%s" % to_img_fmt))

    def __run_cmd(self, cmd: str, is_print=True):
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

    def conv_slide(self):
        self._conv_slide(
            path_src=self.target_dir
            , dir_dest=self._p_dest_dir.name
            , to_fmt=self.dest_ext_no_period
        )

    def _conv_slide(self, path_src, dir_dest, to_fmt="png", is_crop=True):  # , dest_ext_no_period="pdf"):
        """
        ppt->pdf->cropping
        :param dest_ext: without period!!
        """
        pl_src = Path(path_src)  # pathlibのインスタンス
        pl_dest = pl_src.parent.joinpath(dir_dest)
        os.chdir(pl_dest.parent)  # important!

        # TODO: odp?に要対応.LibreOffice

        if pl_src.suffix not in (".ppt", ".pptx", ".odp") and not pl_src.name.startswith("~"):
            print("[Info] Powerpoint / LibreOffice以外は変換せず")
            return
        """
        一時的にepsは
        """
        if pl_src.suffix == ".odp" and to_fmt in ["pdf", "eps"]:
            """
            .odp formatはpdfに変換するとpdfcropで失敗する。
            よって、png形式で変換する
            """
            warn = """
            [Warning]
            [Warning].odpを.pdf/.epsへの変換はCropで失敗します!!!
            [Warning] PowerPointを使え
            [Warning]
            """
            print(warn)
            cur_to_fmt = "pdf"
        # elif pl_src.suffix == ".odp" and to_fmt in ["pdf", "eps"]:
        #     """
        #     .odp formatはpdfに変換するとpdfcropで失敗する。
        #     よって、png形式で変換する
        #     """
        #     cur_to_fmt = "png"
        else:
            if to_fmt == "eps":
                cur_to_fmt = "pdf"
            else:
                cur_to_fmt = to_fmt

        # file_tmp="tmp_"+pathlib.Path(path_src).name
        # file_tmp=pathlib.Path(file_tmp).with_suffix(".pdf")
        # path_tmp=pathlib.Path(path_src).parent.joinpath(file_tmp).as_posix()
        # print("path_tmp:"+path_tmp)
        # out_dir = plib_src.parent.as_posix()
        # path_tmp="tmp_"+os.path.basename(path_src)
        print("[Debug] pl_dest: %s" % pl_dest)
        print("[Debug] CWD:%s" % os.getcwd())
        found_libreoffice = False

        for p_soffice in self._ppaths_soffice:  # type: Path
            if p_soffice.exists():
                cmd = "'{path_soffice}' --headless --convert-to {dest_ext} --outdir {out_dir} {path_src}".format(
                    path_soffice=p_soffice
                    , dest_ext=cur_to_fmt
                    # , out_dir=dir_dest
                    , out_dir=pl_dest.name
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

        plib_pdf_convd = pl_dest.joinpath(pl_src.name).with_suffix("." + cur_to_fmt)
        plib_pdf_convd_tmp = plib_pdf_convd.with_name("tmp_" + plib_pdf_convd.name)

        cmd_cp = "cp -f %s %s" % (plib_pdf_convd, plib_pdf_convd.with_name("pre-crop_" + plib_pdf_convd.name))
        tokens = shlex.split(cmd_cp)
        output = check_output(tokens, stderr=STDOUT).decode("utf8")
        print("Output: %s" % output)

        # plib_pdf_convd.rename(plib_pdf_convd.with_name("tmp_"+plib_pdf_convd.name))
        # plib_pdf_convd.rename(plib_pdf_convd_tmp)
        # plib_pdf_convd.with_name("tmp_"+plib_pdf_convd.name)
        if is_crop:
            self._crop_img(p_src_img=plib_pdf_convd, p_dest=self._p_dest_dir, to_img_fmt=cur_to_fmt)
        """ pdf 2 eps """
        if to_fmt == "eps":
            print("[Info] Convert pdf to eps")
            cmd = "{cmd_conv} {p_src} {p_dest}".format(
                cmd_conv="convert"
                , p_src=plib_pdf_convd
                , p_dest=pl_dest.joinpath(plib_pdf_convd.name).with_suffix(".eps")
            )
            print("[Debug] CMD(convert): %s" % cmd)
            tokens = shlex.split(cmd)
            # subprocess.run(tokens)
            output = check_output(tokens, stderr=STDOUT).decode("utf8")
            print("Output: %s" % output)
        # elif to_fmt == "pdf" and pl_src.suffix == ".odp":
        #     ### conv png to pdf
        #     cmd = "convert %s %s" % (
        #         plib_pdf_convd.with_suffix(".png")
        #         , pl_dest.joinpath(plib_pdf_convd.name).with_suffix(".pdf")
        #     )
        #     self.__run_cmd(cmd)
        """ rm tmpfile"""
        if plib_pdf_convd_tmp.exists():
            pathlib.Path(plib_pdf_convd_tmp).unlink()
            print("Converted")

    #
    # def conv2pnt(self, path_src, dir_dest):
    #     plib_src = pathlib.Path(path_src)  # pathlibのインスタンス
    #     if plib_src.suffix in (".ppt", ".pptx") and not plib_src.name.startswith("~"):
    #         path_dest = pathlib.Path(dir_dest) / plib_src.with_suffix(".pdf").name
    #         cmd = "/Applications/LibreOffice.app/Contents/MacOS/soffice --headless --convert-to pdf --outdir {out_dir} {path_src}".format(
    #             out_dir=out_dir, path_src=path_src)
    #         print("[Debug] CMD: ppt2pdf" + cmd)
    #         tokens = shlex.split(cmd)
    #         subprocess.run(tokens)

    def on_created(self, event):
        filepath = event.src_path
        filename = os.path.basename(filepath)
        print('%sができました' % filename)
        self._conv_slide(path_src=event.src_path, dir_dest=self._p_dest_dir,
                         to_fmt=self.dest_ext_no_period)  # , dest_ext_no_period="png")

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
