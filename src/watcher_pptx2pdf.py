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

class ChangeHandler(FileSystemEventHandler):

    def __init__(self
                 , monitoring_dir
                 , output_dir=None
                 , dest_ext_no_period="png"
                 , export_fmts=["png", "eps", "pdf"]
                 , paths_libreoffice_app=['/Applications/LibreOffice.app/Contents/MacOS/soffice',
                                          '/Applications/LibreOffice Vanilla.app/Contents/MacOS/soffice']):
        """[summary]
        
        Arguments:
            monitoring_dir {[type]} -- [description]
            _p_dest_dir {str} -- [description]
            export_fmts {list} -- 出力フォーマット。複数指定すると、その全てのフォーマットに出力。
        
        Keyword Arguments:
            dest_ext_no_period {str} -- [description] (default: {"png"})
        """
        """[注意]
        本プログラムのScriptが存在するPATHをwcdへ移動とする
        """
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
        self._ppaths_soffice = [Path(x) for x in paths_libreoffice_app]
        self.dest_ext_no_period = dest_ext_no_period

    def _conv_ppt(self, src: pathlib.Path, dest: pathlib.Path):
        """[summary]
        
        Arguments:
            src {pathlib.Path} -- [description]
            dest {pathlib.Path} -- [description]
        """
        pass

    def _crop_img(self, p_src_img, p_dest: Path):
        """
        image(pdf/png,jpeg?)をcroppingする
        :param p_src:
        :param p_dest:
        :return:
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
        if self.dest_ext_no_period == "pdf":
            cmd_name = "pdfcrop"
            cmd = "{cmd_name} {path_in} {path_out}".format(cmd_name=cmd_name, path_in=p_src_img, path_out=p_dest)
        elif self.dest_ext_no_period in ["png", "jpeg", "jpg"]:
            cmd_name = "convert"
            # p_conv = Path("/usr/local/bin/convert")
            # if not p_conv.exists():
            #     raise Exception("%s not found" % p_conv)
            cmd = "{cmd_name} {path_in} -trim {path_out} ".format(cmd_name=cmd_name,
                                                                  path_in=p_src_img,
                                                                  path_out=p_dest)
        else:
            # new_path = shutil.move(plib_pdf_convd.as_posix(), dir_dest)
            raise Exception("対応していないFormatをcroppingしようとして停止")

        if shutil.which(cmd_name) is None:
            print("[Warning] cmd(%s) is not in path " % cmd)
        print("[Debug] Cropping CMD: " + cmd)
        tokens = shlex.split(cmd)
        subprocess.run(tokens)
        # output = check_output(tokens, stderr=STDOUT).decode("utf8")

    def conv_ppt2pdf(self, path_src, dir_dest):  # , dest_ext_no_period="pdf"):
        """
        ppt->pdf->cropping
        :param dest_ext: without period!!
        """
        plib_src = Path(path_src)  # pathlibのインスタンス
        p_dest = plib_src.parent.joinpath(dir_dest)
        os.chdir(p_dest.parent)  # important!
        if plib_src.suffix not in (".ppt", ".pptx") and not plib_src.name.startswith("~"):
            print("[Info] Powerpointファイルでないので変換せず")
            return
        # file_tmp="tmp_"+pathlib.Path(path_src).name
        # file_tmp=pathlib.Path(file_tmp).with_suffix(".pdf")
        # path_tmp=pathlib.Path(path_src).parent.joinpath(file_tmp).as_posix()
        # print("path_tmp:"+path_tmp)
        # out_dir = plib_src.parent.as_posix()
        # path_tmp="tmp_"+os.path.basename(path_src)
        print("[Debug] p_dest: %s" % p_dest)
        print("[Debug] CWD:%s" % os.getcwd())
        found_libreoffice = False
        for p_soffice in self._ppaths_soffice:  # type: Path
            if p_soffice.exists():
                cmd = "'{path_soffice}' --headless --convert-to {dest_ext} --outdir {out_dir} {path_src}".format(
                    path_soffice=p_soffice
                    , dest_ext=self.dest_ext_no_period
                    # , out_dir=dir_dest
                    , out_dir=p_dest.name
                    , path_src=path_src)
                break
        print("[Debug] CMD(ppt2pdf):" + cmd)
        tokens = shlex.split(cmd)
        # subprocess.run(tokens)
        output = check_output(tokens, stderr=STDOUT).decode("utf8")
        print("Output: %s" % output)
        if output == "Error: source file could not be loaded":
            """なぜかLO Vanillaで出現？"""
            # raise Exception("")
            print("[ERROR] なぜかLO Vanillaで出現？")

        """ Add head "tmp_" to converted filename """
        plib_pdf_convd = p_dest.joinpath(plib_src.name).with_suffix("." + self.dest_ext_no_period)
        plib_pdf_convd_tmp = plib_pdf_convd.with_name("tmp_" + plib_pdf_convd.name)
        # plib_pdf_convd.rename(plib_pdf_convd.with_name("tmp_"+plib_pdf_convd.name))
        # plib_pdf_convd.rename(plib_pdf_convd_tmp)
        # plib_pdf_convd.with_name("tmp_"+plib_pdf_convd.name)
        self._crop_img(p_src_img=plib_pdf_convd, p_dest=self._p_dest_dir)
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
        self.conv_ppt2pdf(path_src=event.src_path, dir_dest=self._p_dest_dir)  # , dest_ext_no_period="png")

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
