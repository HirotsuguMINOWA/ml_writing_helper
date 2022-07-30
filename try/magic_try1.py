import re

import magic

t = magic.from_file("src/try/res_comp_force.png")
print(t)
img_size = re.search('(\d+) x (\d+)', t).groups()
print(img_size)
