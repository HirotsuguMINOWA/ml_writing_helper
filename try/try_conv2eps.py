"""
PillowでPNGをepsに変換。
- 画質が落ちないか->losslessモードあり、落ちない。
"""
from PIL import Image

image_png = '/Users/hirots-m/Documents/PyCharmProjects/ml_writing_helper/try/res_comp_force.png'

im = Image.open(image_png)
print(im.mode)
fig = im.convert('RGB')
fig.save('logo-RGB.eps', lossless=True)

from PIL import Image
from autocrop import Cropper

cropper = Cropper()

# Get a Numpy array of the cropped image
cropped_array = cropper.crop('portrait.png')

# Save the cropped image with PIL
cropped_image = Image.fromarray(cropped_array)
cropped_image.save('cropped.png')