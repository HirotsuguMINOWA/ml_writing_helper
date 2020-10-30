# -*- coding:utf-8 -*-
from PIL import Image
from itertools import product

out_dir = "_fig_gen"
src = "fig_sample/sample.jpg"
dst = out_dir + "/" + "test_gray.png"
dst2 = out_dir + "/" + 'Lenna_gray_middle_value.png'
dst3 = out_dir + "/" + 'Lenna_gray_luminance.png'

img = Image.open(src)

# 参考までにPILの機能でグレー変換
gray_img = img.convert('L')
gray_img.save(dst)

# 以下自前グレースケール変換
rgb_img = img.convert('RGB')
w, h = rgb_img.size
my_img = Image.new('RGBA', (w, h))  # 同じ大きさの空画像を作成

# 中間値 : v = (max+min)/2
for x, y in product(range(w), range(h)):
    r, g, b = rgb_img.getpixel((x, y))
    val = int((min([r, g, b]) + max([r, g, b])) / 2)
    my_img.putpixel((x, y), (val, val, val))

my_img.save(dst2)

# 輝度計算(NTSC係数) : v = 0.299*r ＋ 0.587*g ＋ 0.114*b
for x, y in product(range(w), range(h)):
    r, g, b = rgb_img.getpixel((x, y))
    val = int(0.299 * r + 0.587 * g + 0.114 * b)
    my_img.putpixel((x, y), (val, val, val))

my_img.save(dst3)
