from ml_writing_helper.__init__ import ChangeHandler
from pathlib import Path

ChangeHandler(
    monitoring_dir="fig_src", output_dir="fig_gen"
    , dst_ext_no_period="eps"
).start()
