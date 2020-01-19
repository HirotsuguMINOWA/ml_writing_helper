# -*- coding: utf-8 -*-

# TODO: bin(soffice, imagemagick'convert and so on)の存在確認
# TODO: pdfは透過png?が黒くなるためデフォルトはpng
# TODO: dstとsrcフォルダの生成、実行時に。
# TODO: LibreOffice Vanilla.appは変換失敗するので、注意を促す
# target_dir = "app_single/_fig_src"
# _p_dst_dir = "app_single/figs"

###############################################################

# import ftplib
import asyncio
import shutil
import sys

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

import os
import time
import shlex
import subprocess
from subprocess import check_output, STDOUT
import pathlib  # FIXME: 下記に統一
from pathlib import Path
from enum import auto
from strenum import StrEnum


# from strenum import StrEnum

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
        # path_dst = pathlib.Path(dir_dst) / plib_src.with_suffix("." + self._to_fmt).name
        if not p_src_img.exists():
            print("[Error] %s not found" % p_src_img)
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

    @staticmethod
    def _run_cmd(cmd: str, short_msg="", is_print=True):
        """
        コマンド(CLI)の実行
        :param cmd:
        :param is_print:
        :return:
        """
        if is_print:
            print("[Debug] CMD(%s):%s" % (short_msg, cmd))
        tokens = shlex.split(cmd)
        output = check_output(tokens, stderr=STDOUT).decode("utf8")
        if is_print:
            print("Output(%s):%s" % (short_msg, cmd))
        return output

    @staticmethod
    def _conv2eps(pl_src: Path, pl_dst_dir: Path, del_src=True):
        """

        :param pl_src:
        :param pl_dst_dir: directoryのみ
        :param del_src: del src of as tmp
        :return:
        """
        if pl_src.suffix not in (".jpeg", ".jpg", ".png", ".pdf"):
            return
        print("[Info] Convert to eps")

        if pl_dst_dir.is_dir():
            pl_dst_dir = pl_dst_dir.joinpath(pl_src.stem + ".eps")
        # else:
        #     raise Exception("ディレクトリ指定して下さい。")
        elif pl_dst_dir.suffix != ".eps":
            # raise Exception("出力ファイルの拡張子も.epsにして下さい")
            print("[Warning]出力拡張子を.epsに変えました")
            pl_dst_dir = pl_dst_dir.with_suffix(".eps")

        cmd = "{cmd_conv} {src} {dst}".format(
            cmd_conv="convert"
            , src=pl_src
            , dst=pl_dst_dir
        )
        print("[Debug] CMD(convert): %s" % cmd)
        tokens = shlex.split(cmd)
        # subprocess.run(tokens)
        output = check_output(tokens, stderr=STDOUT).decode("utf8")
        print("Output: %s" % output)
        # elif _to_fmt == "pdf" and pl_src.suffix == ".odp":
        #     ### conv png to pdf
        #     cmd = "convert %s %s" % (
        #         pl_src.with_suffix(".png")
        #         , pl_dst_dir.joinpath(pl_src.name).with_suffix(".pdf")
        #     )
        #     self._run_cmd(cmd)
        if del_src:
            pl_src.unlink()

    @classmethod
    def _conv_slide(self, pl_src: Path, pl_dst: Path, to_fmt=".png"):
        """

        :param pl_src:
        :param pl_dst: ファイル/folderまでのPATH.場合分けが必要
        :param to_fmt:
        :return:
        """

        # file_tmp="tmp_"+pathlib.Path(path_src).name
        # file_tmp=pathlib.Path(file_tmp).with_suffix(".pdf")
        # path_tmp=pathlib.Path(path_src).parent.joinpath(file_tmp).as_posix()
        # print("path_tmp:"+path_tmp)
        # out_dir = plib_src.parent.as_posix()
        # path_tmp="tmp_"+os.path.basename(path_src)
        if pl_dst.is_dir():
            pl_dst_dir = pl_dst
        else:
            pl_dst_dir = pl_dst.parent
        print("[Debug] pl_dst_dir: %s" % pl_dst)
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
                    , path_src=pl_src)
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

        pl_out = pl_dst_dir.joinpath(pl_src.with_suffix(to_fmt).name)
        if pl_dst.is_dir():
            return pl_out
        else:
            """
            出力ファイルPATHが指定されているのでrenameする
            """
            # pl_dst_dir = pl_dst_dir.joinpath(pl_out.with_suffix(pl_out.suffix).name)
            # else:
            #     pl_out = pl_dst_dir.joinpath(pl_src.name + _to_fmt)

            # # 存在していたら削除
            # if pl_dst_dir.exists():
            #     pl_dst_dir.unlink()

            # rename
            pl_out.rename(pl_dst)

            # """ Add head "tmp_" to converted filename """
            #
            # plib_pdf_convd = pl_dst_dir.joinpath(pl_src.name).with_suffix(cur_to_fmt)
            # # plib_pdf_convd_tmp = plib_pdf_convd.with_name("tmp_" + plib_pdf_convd.name)
            #
            # cmd_cp = "cp -f %s %s" % (plib_pdf_convd, plib_pdf_convd.with_name("pre-crop_" + plib_pdf_convd.name))
            # self._run_cmd(cmd)
            # # tokens = shlex.split(cmd_cp)
            # # output = check_output(tokens, stderr=STDOUT).decode("utf8")
            # # print("Output: %s" % output)
            #
            # # pl_src.rename(pl_src.with_name("tmp_"+pl_src.name))
            # # pl_src.rename(plib_pdf_convd_tmp)
            # # pl_src.with_name("tmp_"+pl_src.name)
            return pl_dst

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

        if not src_pl.exists() and not to_fmt == ".bib":
            raise Exception("src path(1st-arg:%s)が見つかりません、訂正して下さい" % src_pl.as_posix())
        # init2
        # FIXME: Pathしか受け付けないように要修正
        dst_pl = Path(dst_dir_apath)
        if not dst_dir_apath.exists():
            dst_dir_apath.mkdir()
        if not dst_dir_apath.is_dir():
            raise Exception("dst_dir_apath(2nd-arg:%s)は、ファイルではなく、フォルダのPATHを指定して下さい" % dst_dir_apath)
        os.chdir(dst_pl.parent)  # important!

        # TODO: odp?に要対応.LibreOffice
        if src_pl.suffix in (".png", ".jpg", ".jpeg") and not src_pl.name.startswith("~"):
            """
            files entered in src_folder, converted into pl_dst_dir wich cropping. and conv to eps
            """
            print("[Info] Image->croppingしてdst pathへコピーします")
            pl_src2 = self._crop_img(src_pl, dst_pl.joinpath(src_pl.stem + src_pl.suffix),
                                     to_img_fmt=src_pl.suffix)
            if to_fmt == ".eps":
                self._conv2eps(pl_src=pl_src2, pl_dst_dir=dst_pl.joinpath(src_pl.stem + src_pl.suffix))
            return

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
                # elif pl_src.suffix == ".odp" and _to_fmt in ["pdf", "eps"]:
                #     """
                #     .odp formatはpdfに変換するとpdfcropで失敗する。
                #     よって、png形式で変換する
                #     """
                #     cur_to_fmt = "png"
            elif to_fmt == ".eps":
                cur_to_fmt = ".pdf"
            else:
                cur_to_fmt = to_fmt
            pl_src2 = self._conv_slide(pl_src=src_pl, pl_dst=dst_pl, to_fmt=cur_to_fmt)
            if is_crop:
                p_src_cropped = self._crop_img(p_src_img=pl_src2, p_dst=dst_pl, to_img_fmt=cur_to_fmt)
            """ pdf 2 eps """
            if to_fmt == ".eps":
                self._conv2eps(pl_src=p_src_cropped, pl_dst_dir=dst_pl)
            """ rm tmpfile"""
            # if plib_pdf_convd_tmp.exists():
            #     pathlib.Path(plib_pdf_convd_tmp).unlink()
            print("Converted")
        elif src_pl.suffix == ".bib":  # and to_fmt == ".bib":
            """
            .bibファイルのコピー
            注意).bib.partが生成されるが、瞬間的に.bibになる。それを捉えて該当フォルダへコピーしている
            """
            tmp_src = src_pl  # .with_suffix("")
            tmp_dst = dst_pl.joinpath(src_pl.name)  # .with_suffix(".bib")
            new_path = shutil.copyfile(tmp_src, tmp_dst)
            print("[Info] copied %s to %s" % (tmp_src, tmp_dst))
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
        if self._monitors and not event.is_directory:
            for key_path, closure in self._monitors.items():
                if key_path in event.src_path:
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
        # self.convert(src_file_apath=event.src_path, dst_dir_apath=self._dst_pl, to_fmt=self._to_fmt)  # , _to_fmt="png")
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
        self._road_balancer(event=event)

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
        # self.convert(src_file_apath=event.dest_path, dst_dir_apath=self._dst_pl,to_fmt=self._to_fmt)  # , _to_fmt="png")
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
        src and dst pathの読み込みを代理
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
    #             , to_fmt="png"
    #             , export_fmts=["png", "eps", "pdf"]
    #             , sleep_time=0.5
    #             ):
    #
    #     self._src_pl = self._get_internal_deal_path(src_dir)
    #     self._dst_pl = self._get_internal_deal_path(dst_dir)
    #
    #     # 拡張子チェック
    #     self._to_fmt = self._validated_fmt(to_fmt=to_fmt, src_pl=self._src_pl)
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
        :param to_fmt:
        :param is_crop:
        :return:
        """

        # async def moniko(self
        def moniko(path_updated_file):
            self.convert(src_file_apath=path_updated_file, dst_dir_apath=dst_pl, to_fmt=to_fmt_in, is_crop=is_crop)
            # loop = asyncio.get_event_loop()
            # print(f'start:  {sec}秒待つよ')
            # await loop.run_in_executor(None, time.sleep, sec)
            # print(f'finish: {sec}秒待つよ')

        # return moniko(src_pl=src_pl, dst_dir_apath=dst_dir_apath, to_fmt=to_fmt, is_crop=is_crop)
        return moniko

    def set_monitor(self
                    , src_dir
                    , dst_dir
                    , to_fmt
                    , is_crop=True):
        src_pl = self._get_internal_deal_path(path=src_dir)
        dst_pl = self._get_internal_deal_path(path=dst_dir)
        to_fmt_in = self._validated_fmt(to_fmt=to_fmt, src_pl=src_pl)
        self._monitors[src_pl.as_posix()] = self._get_monitor_func(src_pl=src_pl, dst_pl=dst_pl, to_fmt_in=to_fmt_in,
                                                                   is_crop=is_crop)

    def start_monitors(self
                       , sleep_sec=1):
        try:
            event_handler = self
            observer = Observer()
            for src_path in self._monitors.keys():
                observer.schedule(event_handler, src_path, recursive=True)
                print("[Info] Set monitoring Path:%s" % src_path)
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
            raise Exception("Current path: %s" % pathlib.Path.cwd())


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
    print("src_pl:%s" % src_pl)
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
