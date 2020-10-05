import re

import magic

t = magic.from_file("/Users/hirots-m/Documents/PyCharmProjects/ml_writing_helper/try/res_comp_force.png")
print(t)
img_size = re.search('(\d+) x (\d+)', t).groups()
print(img_size)
