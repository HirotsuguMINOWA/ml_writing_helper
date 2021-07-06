"""
- JPEGはOK
- PNGはAチャンネルが邪魔でうまくいってない。RGBA->RGBに変えて処理するしかない。
- Ref: https://triplepulu.blogspot.com/2015/03/pythonpil-pilautocrop.html
"""
from PIL import Image, ImageChops
from pathlib import Path


def img_crop(image: Image, debug=False) -> Image:
    """
    画像を切り抜く
    - jpeg, pngは確認済み。おそらくbmpやgifも大丈夫
    :param image:
    :param debug:
    :return:
    """
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


if __name__ == '__main__':
    # src_img = Path('/Users/hirots-m/Documents/PyCharmProjects/ml_writing_helper/sample/fig_sample/test_jpg.jpg')
    # src_img = Path('/Users/hirots-m/Documents/PyCharmProjects/ml_writing_helper/sample/fig_sample/test_png.png')
    src_img = Path('/Users/hirots-m/Documents/PyCharmProjects/ml_writing_helper/sample/fig_sample/test_large.png')
    # dst_path = Path(Path.cwd().joinpath(src_img.name))
    src_im = Image.open(src_img)
    convd_im = img_crop(src_im)
    convd_im.show()
