# -*- coding: utf-8 -*-

# TODO: bin(soffice, imagemagick'convert and so on)の存在確認
# TODO: pdfは透過png?が黒くなるためデフォルトはpng

# target_dir = "app_single/_fig_src"
# output_dir = "app_single/figs"

###############################################################

# import ftplib
import shutil

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

import os
import time
import shlex
# import subprocess
from subprocess import check_output, STDOUT
import pathlib  # FIXME: 下記に統一
from pathlib import Path


class ChangeHandler(FileSystemEventHandler):

    def __init__(self
                 , monitoring_dir
                 , output_dir=None
                 , dest_ext_no_period="png"
                 , paths_libreoffice_app=['/Applications/LibreOffice.app', '/Applications/LibreOffice Vanilla.app']):
        """[summary]
        
        Arguments:
            monitoring_dir {[type]} -- [description]
            output_dir {str} -- [description]
        
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
        self.output_dir = output_dir
        self._ppaths_libreoffice_app = [Path(x) for x in paths_libreoffice_app]
        self.dest_ext_no_period = dest_ext_no_period

    def __ppt2pdf(self, src: pathlib.Path, dest: pathlib.Path):
        """[summary]
        
        Arguments:
            src {pathlib.Path} -- [description]
            dest {pathlib.Path} -- [description]
        """
        pass

    def _crop_img(self, p_src, p_dest):
        """
        imageをcroppingする
        :param p_src:
        :param p_dest:
        :return:
        """

    def conv_ppt2pdf(self, path_src, dir_dest):  # , dest_ext_no_period="pdf"):
        """
        ppt->pdf->cropping
        :param dest_ext: without period!!
        """
        plib_src = Path(path_src)  # pathlibのインスタンス
        p_dest = plib_src.parent.joinpath(dir_dest)
        os.chdir(p_dest.parent)  # important!
        if plib_src.suffix in (".ppt", ".pptx") and not plib_src.name.startswith("~"):
            # file_tmp="tmp_"+pathlib.Path(path_src).name
            # file_tmp=pathlib.Path(file_tmp).with_suffix(".pdf")
            # path_tmp=pathlib.Path(path_src).parent.joinpath(file_tmp).as_posix()
            # print("path_tmp:"+path_tmp)
            # out_dir = plib_src.parent.as_posix()
            # path_tmp="tmp_"+os.path.basename(path_src)
            print("[Debug] p_dest: %s" % p_dest)
            print("[Debug] CWD:%s" % os.getcwd())
            for p in self._ppaths_libreoffice_app:  # type: Path
                if p.exists():
                    cmd = "'{path_libreoffice}/Contents/MacOS/soffice' --headless --convert-to {dest_ext} --outdir {out_dir} {path_src}".format(
                        path_libreoffice=p
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
            plib_pdf_convd.rename(plib_pdf_convd_tmp)
            # plib_pdf_convd.with_name("tmp_"+plib_pdf_convd.name)
            """ Calc path of Dest """
            # path_dest = pathlib.Path(dir_dest) / plib_pdf_convd.name
            path_dest = pathlib.Path(dir_dest) / plib_src.with_suffix("." + self.dest_ext_no_period).name

            """ crop white space """
            if self.dest_ext_no_period == "pdf":
                cmd = "pdfcrop"
                if shutil.which(cmd) is None:
                    print("[Warning] %s not found" % cmd)
                    cmd = "pdfcrop {path_in} {path_out}".format(path_in=plib_pdf_convd_tmp, path_out=path_dest)
            elif self.dest_ext_no_period in ["png", "jpeg", "jpg"]:
                cmd = "convert"
                # p_conv = Path("/usr/local/bin/convert")
                # if not p_conv.exists():
                #     raise Exception("%s not found" % p_conv)
                if shutil.which(cmd) is None:
                    print("[Warning] %s not found" % cmd)
                cmd = "{cmd} {path_in} -trim {path_out} ".format(cmd=cmd,
                                                                 path_in=plib_pdf_convd_tmp,
                                                                 path_out=path_dest)
            else:
                # new_path = shutil.move(plib_pdf_convd.as_posix(), dir_dest)
                raise Exception("対応していないFormatをcroppingしようとして停止")

            print("[Debug] Cropping : " + cmd)
            tokens = shlex.split(cmd)
            # subprocess.run(tokens)
            output = check_output(tokens, stderr=STDOUT).decode("utf8")
            """ rm tmpfile"""
            # os.remove(path_tmp)
            # pathlib.Path(plib_pdf_convd).unlink()
            pathlib.Path(plib_pdf_convd_tmp).unlink()
            print("Converted")
        else:
            print("対象外だったので変換せず")

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
        self.conv_ppt2pdf(path_src=event.src_path, dir_dest=self.output_dir)  # , dest_ext_no_period="png")

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
