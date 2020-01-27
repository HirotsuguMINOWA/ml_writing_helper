# Caution
# Set src dir as source folder in projectPref.
# You can import by "from core import ChangeHandler"
from core import ChangeHandler

p = ChangeHandler()
p.set_monitor(
    src_dir="fig_src"
    , dst_dir="fig_gen"
    , to_fmt="eps"
)
p.start_monitors()
