import shlex
import shutil
from enum import StrEnum
from pathlib import Path
from subprocess import check_output, STDOUT

from PIL import Image, ImageChops
from PIL.Image import Image as ImageClsType
from loguru import logger
from pdf2image import convert_from_path

from pdfCropMargins import crop
from ml_writing_helper.util import Util


class SlideAndImgConverter:
    """1対1formatでの直接画像変換用クラス
    - フォーマット変換のclassmethodが主のクラス
    """
    imagic_fmt_conv_out: tuple[str, ...] = (".png", ".jpg", ".jpeg", ".png", ".eps", ".svg")

    _ext_pluntuml: tuple[str, ...] = (".pu", ".puml")

    plantuml_fmt_out: tuple[str, ...] = (".png", ".svg", ".pdf", ".eps", ".html", ".txt", ".tex")
    mermaid_fmt_in: tuple[str, ...] = (".svg", ".png", ".pdf")
    _paths_soffice: list[str] = [
        "soffice",
        "/Applications/LibreOffice.app/Contents/MacOS/soffice",
        r"C:\Program Files\LibreOffice\program\soffice.exe"
    ]
    imagic_fmt_conv_in: tuple[str, ...] = (
        ".png",
        ".jpg",
        ".jpeg",
        ".png",
        ".eps",
        ".svg",
        ".pdf",
    )

    @classmethod
    def _ppaths_soffice(cls) -> tuple[Path, ...]:
        return tuple([Path(x) for x in cls._paths_soffice])

    @staticmethod
    def _run_cmd(cmd: str, short_msg: str = "", is_print: bool = True) -> str:
        """
        コマンド(CLI)の実行
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

    @classmethod
    def pdf2img(cls, src_pl: Path, dst_pl: Path) -> None:
        pages = convert_from_path(src_pl.as_posix())
        if not pages:
            raise ValueError(f"No pages found in PDF: {src_pl}")

        # PILのformatは "EPS" のようにドットなしが必要
        fmt = dst_pl.suffix.lstrip(".").upper()
        pages[0].save(dst_pl.as_posix(), format=fmt)

    @classmethod
    def plantuml2img(cls, src_pl: Path, dst_pl: Path, need_pre_proc: bool = False) -> None:
        """PlantUML

        :param src_pl:
        :param dst_pl:
        :param need_pre_proc:
        :return:
        """
        logger.debug("Start converting plantuml")
        if need_pre_proc:
            src_pl, dst_pl = Util.preprocess(src_pl, dst_pl)
        # to abs. path
        dst_pl = dst_pl.resolve()
        cls._cmd_plantuml = "plantuml"
        # FIXME: dst_plにfullPATHであるかのチェックをする必要がある
        path_cmd = shutil.which(cls._cmd_plantuml)
        if path_cmd is None:
            logger.error(
                "%s not found. Can't convert from PlantUML" % cls._cmd_plantuml
            )
            return
        if dst_pl.suffix not in cls.plantuml_fmt_out:
            logger.error("Indicated Formatは未対応 in converting with plantuml")
            return
        # FIXME: dst_pathがない場合、再帰的に生成する様に要修正
        # cmd = "{cmd_pu} -o {dst_abs_dir_only} -t{fmt} {src}".format(
        #     cmd_pu=cls._cmd_plantuml,
        #     src=src_pl.as_posix(),
        #     dst_abs_dir_only=dst_pl.parent,
        #     fmt=dst_pl.suffix[1:]
        # )
        """注意
        - `-o`: 絶対PATHなら問題なさそうだが、相対PATHでは、srcファイルからの相対PATHとなる模様。よって、dst_plを絶対PATHに変更する必要がある
        """
        cmd = f"{cls._cmd_plantuml} -o {dst_pl.parent} -t{dst_pl.suffix[1:]} {src_pl.as_posix()}"
        res = cls._run_cmd(cmd=cmd, short_msg="Converting with %s" % cls._cmd_plantuml)
        # Move generated file to dst_pl
        pl_out = dst_pl.parent.joinpath(src_pl.stem + dst_pl.suffix)
        shutil.move(pl_out, dst_pl)
        """Show output msg"""
        if res is None or res == "":
            logger.info("Completed. ")
        else:
            logger.info("Finished with msg: %s" % res)

    # @classmethod
    #     :param src_pl:
    #     :param dst_pl:
    #     :param to_fmt:
    #     :return:
    #     """
    #     need_conv = Tru
    # def _conv_and_crop(cls, src_pl: Path, dst_pl: Path) -> Path:
    #     """
    #     イメージを変換して、cropする。
    #     - Step by Stepな変換。もし、変換, cropの両方を_conv_with_crop_bothメソッドで行え
    #     - (注意) img変換とcropを同時にimagemagickで実現する別methodを設けた
    #     :param cls:e
    #     # path_dst = cls.mgr_conv_img(src_pl=src_pl, dst_pl=dst_pl)  # conv both crop and imgconv stimulatelly
    #     # if path_dst:
    #     #     need_conv = False
    #     """ 上記、変換が失敗した場合 """
    #     if need_conv:
    #         tmp_dst_pl = cls.util_manage_tmp_path(dst_pl)
    #         # dst_pl2, tmp_dst_pl = cls.util_update_dst_path(base_dst_pl=src_pl, fname_str_or_pl=dst_pl, fmt=to_fmt,
    #         #                                                is_tmp=True)
    #         # 変換後にcrop
    #         path_dst = cls._conv2img(src_pl=src_pl, dst_pl=tmp_dst_pl)  # , fmt_if_dst_without_ext=fmt)
    #         path_dst = cls._crop_all_fmt(src_img_pl=path_dst, dst_pl=dst_pl)
    #
    #         # Crop後に変換
    #         # path_dst = cls._crop_all_fmt(src_img_pl=src_pl, dst_pl=tmp_dst_pl)
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
    #         #     path_dst = cls._crop_all_fmt(src_pl=path_dst, dst_pl=dst_pl)
    #         # else:
    #         #     tmp_dst_pl = tmp_dst_pl.with_suffix(src_pl.suffix)
    #         #     path_dst = cls._crop_all_fmt(src_pl=src_pl, dst_pl=tmp_dst_pl)
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
    # def conv_mermaid(cls, src_pl: Path, dst_pl: Path, to_fmt=".svg") -> tuple[bool, Path]:
    def conv_mermaid(cls, src_pl: Path, dst_pl: Path) -> tuple[bool, Path | None]:
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
            return False, None

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
            src_path=src_pl.as_posix(),
        )
        # FIXME:
        out_msg = cls._run_cmd(cmd=cmd, short_msg="Converting mermaid file")
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
    def conv_pandoc(cls, src: Path, dst: Path) -> None:
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
        cmd = cmd_pandoc + "-N -TOC-F pandoc-citeproc -F pandoc-crossref {src}".format(
            src=src
        )

    @staticmethod
    def remove_transparency(
            im: Image.Image,
            bg_color: tuple[int, int, int] = (255, 255, 255),
    ) -> Image.Image:
        """
        Taken from https://stackoverflow.com/a/35859141/7444782
        """
        # Only process if image has transparency (http://stackoverflow.com/a/1963146)
        if im.mode in ("RGBA", "LA") or (im.mode == "P" and "transparency" in im.info):

            # Need to convert to RGBA if LA format due to a bug in PIL (http://stackoverflow.com/a/1963146)
            alpha = im.convert("RGBA").split()[-1]

            # Create a new background image of our matt color.
            # Must be RGBA because paste requires both images have the same format
            # (http://stackoverflow.com/a/8720632  and  http://stackoverflow.com/a/9459208)
            bg = Image.new("RGBA", im.size, bg_color + (255,))
            bg.paste(im, mask=alpha)
            return bg
        else:
            return im

    @classmethod
    def conv_manipulation_img(
            cls,
            src_pl: Path,
            dst_pl: Path,
            do_trim: bool = True,
            gray: bool = False,
            eps_ver: int = 2,
    ) -> Path | None:
        """
        Manipulation (Convert/Crop/Gray) Image
        :param src_pl:
        :param dst_pl:
        :param do_trim:
        :param gray: conv to gray
        :param eps_ver: eps_ver2に変換する？defaultはTrue
        :return:
        """
        # if not src_pl.exists():
        #     raise Exception(f"指定ファイルが存在しない:{src_pl.as_posix()}")
        if do_trim and src_pl.suffix.lower() == dst_pl.suffix:
            logger.warning("ImageMagick変換において、Trim(Crop)付きで別Formatへ変換すると、Crop失敗する可能性あり")
        # # TODO: in,outのfmtの要チェック?いらんかも
        # conv_name = "convert"
        # conv_path = shutil.which(conv_name)
        # if not conv_path:
        #     logger.error("convert command not found")
        #     return None
        # head = ""
        # if dst_pl.suffix == ".eps" and is_eps2:
        #     head = "eps3:"  # FIXME: eps3にしている。eps3はGIFのLZW圧縮？
        # param = ""
        # if do_trim:
        #     param = "-trim"
        # cmd = "{cmd_path} {src} {param} -quality 100 -density 200 -resize 4000x4000 {head}{dst}".format(
        #     cmd_path=conv_path
        #     , param=param
        #     , head=head
        #     , src=src_pl
        #     , dst=dst_pl
        # )
        # cls._run_cmd(cmd, "Convert by ImageMagic")
        # FIXME: 中間生成ファイルを変換しようとして失敗している模様
        logger.debug(f"src: {src_pl.as_posix()}")
        logger.debug(f"dst: {dst_pl.as_posix()}")

        """
        下記は「Imageクラス」で画像データを処理を実施する
        """
        if src_pl.suffix.lower() == ".pdf":
            SlideAndImgConverter.pdf2img(src_pl=src_pl, dst_pl=dst_pl)
        else:
            """ Conversion other than pdf """
            dst_im = Image.open(src_pl.as_posix())
            if do_trim:
                dst_im = img_crop(image=dst_im)

            if src_pl.suffix.lower() == dst_pl.suffix.lower:
                logger.info("同一拡張子なので画像変換はしません。trimは実施するかも")
                return

            if dst_pl.suffix == ".eps":
                if dst_im.mode in ("RGBA", "LA"):
                    """ 透過画像を解除? """
                    # https://pillow.readthedocs.io/en/stable/handbook/image-file-formats.html?highlight=eps#eps
                    logger.warning(
                        f'[Try conversion] Current figure mode "{dst_im.mode}" cannot be directly saved to .eps and should be converted (e.g. to "RGB")')
                    dst_im = cls.remove_transparency(dst_im)
                    # dst_im = dst_im[:, :, 0:2]
                    dst_im = dst_im.convert("RGB")
                if dst_im.mode in ("RGBA", "LA"):
                    logger.error(
                        f'Failed: Current img mode "{dst_im.mode}" cannot be directly saved to .eps and tried to be converted (e.g. to "RGB")')
                else:
                    logger.info("Succeed? to RGB")

            if gray:
                """ Convert to gray img """
                dst_im = dst_im.convert("L")

            """保存"""
            if dst_pl.suffix in (".eps", ".png", ".gif"):
                dst_im.save(dst_pl.as_posix(), lossless=True)
            else:
                dst_im.save(dst_pl.as_posix())
        return dst_pl

    @classmethod
    def conv_mermaid_with_crop(
            cls,
            src_pl: Path,
            dst_pl: Path,
            gray: bool = False,
    ) -> tuple[bool, Path | None]:
        """
        mermaid markdownを変換 及び 特定のformatへ変換する
        :param src_pl:
        :param dst_pl:
        :param gray:
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
        res, tmp_dst_pl = cls.conv_mermaid(src_pl=src_pl, dst_pl=dst_pl)  # ,
        # to_fmt=tmp_fmt)
        """ Conversion: mermaid """
        if not res:
            return False, None
        if tmp_dst_pl is None:
            logger.error(f"Fail! {tmp_dst_pl} is NONE")
            return False, None
        """ Cropping image """
        tmp_dst_pl = cls.crop_all_fmt(src_img_pl=tmp_dst_pl, dst_pl=dst_pl)
        if tmp_dst_pl is None:
            logger.error("Failed crop: %s" % src_pl)
            return False, None

        if src_pl.suffix.lower() == dst_pl.suffix.lower():
            return True, tmp_dst_pl

        """ Image conversion"""
        tmp_dst_pl = cls.conv_manipulation_img(
            src_pl=tmp_dst_pl, dst_pl=dst_pl, gray=gray
        )
        if tmp_dst_pl is None:
            return False, None
        else:
            return True, tmp_dst_pl

    @classmethod
    def crop_all_fmt(cls, src_img_pl: Path, dst_pl: Path) -> Path:
        """
        PDFとimage(png,jpeg,eps?)をcroppingする
        - 必要。なぜならImage系はPillowのImageクラスで扱えるが、PDFはファイル単位で操作しなくてはならない
        :param src_img_pl:
        :param dst_pl:
        :return: 変換後のpath名
        :rtype: Path
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
            cls._crop_pdf_by_PDFCropMargin(src_pl=src_img_pl, dst_pl=dst_pl)
            # if dst_pl.exists():
            #     dst_pl.unlink()
            # shutil.move(src=src_img_pl.with_name(src_img_pl.stem + "-crop.pdf"), dst=dst_pl)

            # imagemagick mogrifyを使う->失敗
        #     shutil.copy(src_pl, dst_pl)
        #     cmd = "magick mogrify -format pdf -define pdf:use-trimbox=true {dst_path}".format(dst_path=dst_pl)
        elif src_img_pl.suffix in (".png", ".jpg", ".jpeg", ".eps"):  # pdfのcropはできない
            cls.conv_manipulation_img(src_pl=src_img_pl, dst_pl=dst_pl, do_trim=True)
            # dst_im = Image.open(src_img_pl.as_posix())
            # dst_im = img_crop(image=dst_im)
            # dst_im.save(dst_pl)
            # dst_im = Image.open(src_img_pl.as_posix())
            # dst_im = img_crop(image=dst_im)
            # dst_im.save(dst_pl)
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

    @classmethod
    def _crop_pdf_by_PDFCropMargin(
            cls,
            src_pl: Path,
            dst_pl: Path,
            margin: int | float = 0,
    ) -> Path:
        """
        PDFをcropする。autocropも対応
        -p: margin %
        -s: input path
        -o: output path
        :param src_pl:
        :param dst_pl:
        :param margin:
        :return:
        """

        crop(["-p", f"{margin}", "-s", f"{src_pl}", "-o", f"{dst_pl}"])
        return dst_pl

    @classmethod
    def _crop_pdf_by_pdfcrop(
            cls,
            src_pl: Path,
            dst_pl: Path,
            margin: int | float = 0,
    ) -> Path:
        """
        PDFをcropする。autocropも対応
        - 別CLIのpdfcropを使用する
        :param src_pl:
        :param dst_pl:
        :param margin:
        :return:
        """
        cmd_name = shutil.which("pdfcrop")
        if cmd_name is None:
            logger.error("pdfcrop not found")
        cmd = "{cmd_name} {path_in} {path_out}".format(
            cmd_name=cmd_name, path_in=src_pl, path_out=dst_pl
        )
        # rename cropped pdf(*_crop.pdf) to dst_pl
        res_msg = cls._run_cmd(cmd, short_msg="Cropping CMD:")
        if res_msg:
            logger.info(res_msg)
        return dst_pl

    @classmethod
    def mgr_conv_slide(
            cls,
            src_pl: Path,
            dst_pl: Path,
            gray: bool,
            is_crop: bool = True,
            via_ext: str = ".png",
            div_proc: tuple[str, ...] = (".pdf", ".eps"),
    ) -> None:
        """
        スライドの変換を制御するマネージャ
        TODO: mgr_conv_slideメソッドに統一すべき。
        :param src_pl:
        :param dst_pl:
        :param is_crop:
        :param via_ext:
        :param div_proc:
        :return:
        """
        is_mediate = False
        if dst_pl.suffix in div_proc:
            """
            - 注意) PowerPoint/LibreOffice(.odp)は.pdfへ変換してPDFCropで失敗する。そのため、一度、.png経由する。
            """
            # warn = """
            #   [Warning] スライドにはPowerPoint形式(.pptx)に変換して使ってください。
            #   """
            # # print(warn)
            logger.warning(f".ppt(x)/.odpから{div_proc}への変換は{via_ext}経由で変換します。")
            # 他のフォーマット経由で変換する
            is_mediate = True
            dst_tmp_pl = dst_pl.parent.joinpath(dst_pl.stem + "_tmp" + via_ext)
            logger.info(f"tmp: {dst_tmp_pl.as_posix()}")
        else:
            dst_tmp_pl = dst_pl

        # スライド変換 ※ ただし、変換のみ
        cls._conv_slide(src_pl=src_pl, dst_pl=dst_tmp_pl)

        if is_crop:
            if is_mediate:
                # croppingを含むPDFへ変換。
                cls.mgr_conv_img(dst_tmp_pl, dst_pl, gray=gray)
            else:
                # croppingのみ
                SlideAndImgConverter.crop_all_fmt(src_img_pl=dst_tmp_pl, dst_pl=dst_pl)

        # Del mediate file
        if is_mediate:
            dst_tmp_pl.unlink()

    @classmethod
    def _conv_slide(cls, src_pl: Path, dst_pl: Path) -> None:
        """
        :param src_pl:
        :param dst_pl: ファイル/folderまでのPATH.場合分けが必要
        :return:
        """
        cmd: None | str = None
        for p_soffice in [Path(x) for x in cls._paths_soffice]:
            if p_soffice.exists():
                cmd = "'{path_soffice}' --headless --norestore --convert-to {dst_ext} --outdir '{out_dir}' '{path_src}'".format(
                    # cmd = "'{path_soffice}' --headless --convert-to {dst_ext} {path_src}".format(
                    path_soffice=p_soffice,
                    dst_ext=dst_pl.suffix[1:],  # eliminate first "."
                    # , out_dir=dir_dst
                    out_dir=dst_pl.parent.as_posix(),
                    path_src=src_pl,
                )
                break
        else:
            logger.warning(f"LibreOfficeが見つかりません。探索したPATH:{cls._paths_soffice}")
            return None
        # *****
        if src_pl.suffix.lower() in (".pptx", ".ppt"):
            logger.warning(
                "(Math) symbols may be VANISH!!!!. Please confirm generated product not to disappear symbols")
        # output = cls._run_cmd(cmd)
        output = cls._run_cmd(cmd, "CMD(slide2img): ")
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
    def mgr_conv_img(cls, src_pl: Path, dst_pl: Path, gray: bool = False) -> None:
        """
        Image Conversion with other(e.g. cropping)
        FIXME: _conv_imgやらと重複しており、機能もそちらに移動している。もう、こちらは不要
        - 対象: 全ての画像, pdf, eps。それ以外の.md, .mmdなどから呼び出して使う様にすべきだろう。
        - ImageMagickのcropと画像変換を合わせ使う
        - ほぼ、ImageMagickだけでよく、PDF-Outのみ別分岐処理となった
        :param src_pl:
        :param dst_pl:
        :param gray:
        :return: 変換後のpath名
        :rtype: pathlib.Path
        """
        """ Calc path of base_dst_pl """
        # path_dst = pathlib.Path(dir_dst) / fname_str_or_pl.name
        # path_dst = pathlib.Path(dir_dst) / plib_src.with_suffix("." + cls._to_fmt).name
        if not src_pl.exists():
            logger.error(f"{src_pl} not found")
            return
        # if dst_pl.is_dir():
        #     dst_pl = dst_pl.joinpath(src_pl.name)  # if the path is dir, set src_filename_stem converted
        if (
                src_pl.suffix.lower() in cls.imagic_fmt_conv_in
                and dst_pl.suffix in cls.imagic_fmt_conv_out
                and dst_pl.suffix not in (".pdf", ".eps")
        ):
            """
            - (in,out)共にpdfのcropはできない. epsのin?,outは可
            - 処理対象
                - 一般画像(jpeg, epsなど)
                - pdf: inのみ。
            """
            SlideAndImgConverter.conv_manipulation_img(
                src_pl=src_pl, dst_pl=dst_pl, do_trim=False, gray=gray
            )
            SlideAndImgConverter.crop_all_fmt(dst_pl, dst_pl)
        else:
            """
            ★ こちらはImageMagicで直接Crop(Trim)できるfmtだけを処理する
            出力がPDFの場合のみ2段階変換(conv,crop)を実施
            pdf->image: OK!!!
                $ convert try2-crop.pdf eps2:try2-crop.eps
                >> try2-crop.eps という、トリミングされたepsができる。
                http://would-be-astronomer.hatenablog.com/entry/2015/03/26/214633
            pdfcrop機能しない事が多い？img_magickと併用でcropする事
            """
            _ = SlideAndImgConverter.conv_manipulation_img(
                src_pl, dst_pl, do_trim=True, gray=gray
            )  # TODO: 現状ImgMagickの-trimでPDFもcropされている！！
            # cls._crop_all_fmt(dst_pl, dst_pl)
        # else:
        #     logger.error("_conv_with_crop_bothがCalled.しかし何も変換せず。src:%s,dst:%s" % (src_pl, dst_pl))


class ImgConvInputType(StrEnum):
    png = "png"
    jpg = "jpg"
    jpeg = "jpeg"
    pdf = "pdf"
    pptx = "pptx"
    ppt = "ppt"
    gif = "gif"  # TODO: GIFは可？


class ImgConvOutputType(StrEnum):
    eps = "eps"


def img_crop(image: ImageClsType, debug: bool = False) -> ImageClsType:
    """
    画像を切り抜く
    - jpeg, pngは確認済み。おそらくbmpやgifも大丈夫
    - JPEGはOK
    - PNGはAチャンネルが邪魔でうまくいってない。RGBA->RGBに変えて処理するしかない。
    - Ref: https://triplepulu.blogspot.com/2015/03/pythonpil-pilautocrop.html
    :param image:
    :param debug:
    :return:
    """
    # TODO: imgConvertクラスに統合するのが良さそう
    # image = Image.open()

    # image = image.copy()
    # image.show()
    if debug:
        print("image.getpixel", image.getpixel((0, 0)))
        # getpixel(0, 0) で左上の色を取得し、背景色のみの画像を作成する
        print(f"image size:{image.size}")
    bg = Image.new(image.mode, image.size, image.getpixel((0, 0)))
    # RGBA->RGBに変換したら.difference()で画像一致しないと現れた
    # bg = Image.new('RGB', image.size, image.getpixel((0, 0)))
    # bg.show()

    # 背景色画像と元画像の差分を取得
    # ->背景と重複する箇所が黒くなる？？背景色と違うところは残るはず。
    diff = ImageChops.difference(image, bg)

    # diff.show()

    # 画像の合成する
    # https://pillow.readthedocs.io/en/3.0.x/reference/ImageChops.html
    # PIL.ImageChops.add(image1, image2, scale=1.0, offset=0)
    # Adds two images, dividing the result by scale and adding the offset. If omitted, scale defaults to 1.0, and offset to 0.0.
    # out = ((image1 + image2) / scale + offset)

    # 消してみた。もしかしたら、要るかも
    # diff = ImageChops.add(diff, diff, 2.0, -100)
    # diff = ImageChops.add(diff, diff, 1.0, 0)
    # diff.show()
    # if image.mode == "RGBA":
    #     diff.putalpha(0)
    if debug:
        print("diff.getpixel", diff.getpixel((0, 0)))
    if image.mode == "RGBA":
        """
        Aチャンネルをもつ画像はAchを取り除かないと.getbboxが期待通り動作しない
        """
        diff = diff.convert("RGB")

    # 黒背景の境界Boxを取り出すF
    bbox = diff.getbbox()
    if debug:
        print("bbox", bbox)
    # 少し余白を付ける
    # offset = 30
    # bbox2 = (bbox[0] - offset, bbox[1] - offset, bbox[2] + offset, bbox[3] + offset)
    # 元画像を切り出す
    cropped = image.crop(bbox)
    # cropped.save('cropped_edge.jpg')
    # cropped.show()
    # cropped.save(f'cropped_edge{src_img.suffix}')
    # cropped = image.crop(bbox2)
    # cropped.save('cropped_edge_offset.jpg')
    return cropped


def test_img_crop():
    src_img = Path('sandbox/fig_sample/test_large.png')
    src_im = Image.open(src_img)
    convd_im = img_crop(src_im)
    convd_im.show()


if __name__ == "__main__":
    test_img_crop()
