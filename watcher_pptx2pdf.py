# -*- coding: utf-8 -*-

# TODO: スクリプト開始時に、変換漏れを探せ
import shutil

target_dir = "app_single/_fig_src"
output_dir = "app_single/figs"

###############################################################

import ftplib

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

import os
import time
import shlex
import subprocess
import pathlib


class ChangeHandler(FileSystemEventHandler):

    def __ppt2pdf(self, src: pathlib, dest: pathlib):
        pass

    def conv_ppt2pdf(self, path_src, dir_dest, dest_ext_no_period="pdf"):
        """
        ppt->pdf->cropping
        :param dest_ext: without period!!
        """
        plib_src = pathlib.Path(path_src)  # pathlibのインスタンス
        if plib_src.suffix in (".ppt", ".pptx") and not plib_src.name.startswith("~"):
            # file_tmp="tmp_"+pathlib.Path(path_src).name
            # file_tmp=pathlib.Path(file_tmp).with_suffix(".pdf")
            # path_tmp=pathlib.Path(path_src).parent.joinpath(file_tmp).as_posix()
            # print("path_tmp:"+path_tmp)
            out_dir = plib_src.parent.as_posix()
            # path_tmp="tmp_"+os.path.basename(path_src)
            cmd = "/Applications/LibreOffice.app/Contents/MacOS/soffice --headless --convert-to {dest_ext} --outdir {out_dir} {path_src}".format(
                dest_ext=dest_ext_no_period, out_dir=out_dir, path_src=path_src)
            print("[Debug] CMD: ppt2pdf" + cmd)
            tokens = shlex.split(cmd)
            subprocess.run(tokens)

            """ Add head "tmp_" to converted filename """
            plib_pdf_convd = plib_src.with_suffix("." + dest_ext_no_period)
            plib_pdf_convd_tmp = pathlib.Path(plib_pdf_convd).with_name("tmp_" + plib_pdf_convd.name)
            # plib_pdf_convd.rename(plib_pdf_convd.with_name("tmp_"+plib_pdf_convd.name))
            plib_pdf_convd.rename(plib_pdf_convd_tmp)
            # plib_pdf_convd.with_name("tmp_"+plib_pdf_convd.name)
            """ Calc path of Dest """
            # path_dest = pathlib.Path(dir_dest) / plib_pdf_convd.name
            path_dest = pathlib.Path(dir_dest) / plib_src.with_suffix("."+dest_ext_no_period).name

            """ crop white space """
            if dest_ext_no_period == "pdf":
                cmd = "pdfcrop {path_in} {path_out}".format(path_in=plib_pdf_convd_tmp, path_out=path_dest)
            elif dest_ext_no_period in ["png", "jpeg", "jpg"]:
                cmd = "convert {path_in} -trim {path_out} ".format(path_in=plib_pdf_convd_tmp, path_out=path_dest)
            else:
                # new_path = shutil.move(plib_pdf_convd.as_posix(), dir_dest)
                raise Exception("対応していないFormatをcroppingしようとして停止")

            print("[Debug] Cropping : " + cmd)
            tokens = shlex.split(cmd)
            subprocess.run(tokens)
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
        self.conv_ppt2pdf(path_src=event.src_path, dir_dest=output_dir, dest_ext_no_period="png")

    def on_modified(self, event):
        filepath = event.src_path
        filename = os.path.basename(filepath)
        print('%sを変更しました' % filename)

    def on_deleted(self, event):
        filepath = event.src_path
        filename = os.path.basename(filepath)
        # TODO: 該当pdfを要削除
        print('%sを削除しました' % filename)


def main():
    while 1:
        event_handler = ChangeHandler()
        observer = Observer()
        observer.schedule(event_handler, target_dir, recursive=True)
        observer.start()
        try:
            while True:
                time.sleep(0.1)
        except KeyboardInterrupt:
            observer.stop()
        observer.join()


if __name__ in '__main__':
    main()
