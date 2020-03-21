src = "../sample/fig_sample/test_eps.eps"
dst_dir = "fig_gen"
#

from pathlib import Path
import shutil
from core import ChangeHandler

src_pl = Path(src).resolve()

# copy
dst_pl = src_pl.parent.parent.joinpath(dst_dir).joinpath("%s_fixed.eps" % src_pl.stem)
shutil.copy(src=src_pl, dst=dst_pl)
ChangeHandler.fix_eps(src_pl=dst_pl)
