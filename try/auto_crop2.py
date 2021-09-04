# https://stackoverflow.com/questions/10615901/trim-whitespace-using-pil
# どうやらトリミングできている?
# しかし、epsがpngになってしまっている？？

from PIL import Image, ImageChops


def trim(im):
    bg = Image.new(im.mode, im.size, im.getpixel((0, 0)))
    diff = ImageChops.difference(im, bg)
    diff = ImageChops.add(diff, diff, 2.0, -100)
    bbox = diff.getbbox()
    if bbox:
        return im.crop(bbox)


im = Image.open("../sample/fig_sample/test_eps.eps")
im = trim(im)
im.show()
