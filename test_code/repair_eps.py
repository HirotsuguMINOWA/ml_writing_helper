# URL: https://shotanuki.com/python%E3%81%A7pdf%E3%82%92%E7%94%BB%E5%83%8F%E3%81%AB%E5%A4%89%E6%8F%9B%E3%81%99%E3%82%8B/
# pip install -U pdf2image pillow poppler
# 目的: epsの修復。 eps->pdf->epsでLaTeXで読めるように修正したい

from pathlib import Path

src_eps = Path(__file__).parent.parent
src_eps = src_eps.joinpath("sample/fig_sample/test_eps.eps")
dst_eps = ""

print("src_path:%s" % src_eps)

from pdf2image import convert_from_path
from PIL import Image
from pathlib import Path

import os, sys

# eps->pdf
im = Image.open(src_eps)
# bg = Image.new("RGB", im.size, (255,255,255))
# bg.paste(im,im)
src_pl = Path(src_eps)
tmp_path = src_pl.with_name("tmp_" + src_pl.stem).with_suffix(".eps")
im.save(tmp_path)

# pdf->eps
path = 'PDFを置いてる場所'
images = convert_from_path(tmp_path.as_posix())

i = 0
for image in images:
    image.save('test{}.png'.format(i), 'png')
    i += 1
